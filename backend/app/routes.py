"""API routers for the DSSS simulator."""
from __future__ import annotations

import math
from typing import Iterable, Sequence

import numpy as np
from fastapi import APIRouter, HTTPException, Query, status

from .dsss_engine import DSSSEngine, FloatArray, StageSnapshot
from .schemas import (
    ErrorResponse,
    SimulationRequest,
    SimulationResponse,
    StageDetailResponse,
    StageName,
    SpectrumSnapshot,
    WaveformSnapshot,
)

router = APIRouter(prefix="/api")
engine = DSSSEngine()
INLINE_SPECTRA: Sequence[StageName] = (
    StageName.MODULATOR,
    StageName.CHANNEL,
)


@router.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post(
    "/simulate",
    response_model=SimulationResponse,
    responses={status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse}},
    tags=["simulation"],
)
async def run_simulation(payload: SimulationRequest) -> SimulationResponse:
    try:
        result = engine.simulate(
            message=payload.message,
            tx_secret=payload.tx_secret,
            rx_secret=payload.rx_secret,
            chip_rate=payload.chip_rate,
            carrier_freq=payload.carrier_freq,
            noise_power=payload.noise_power,
            oversampling=payload.oversampling,
        )
    except ValueError as exc:  # pragma: no cover - fast path
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    inline = [
        _to_spectrum(stage, result.stages[stage])
        for stage in INLINE_SPECTRA
        if stage in result.stages
    ]

    return SimulationResponse(
        simulation_id=result.simulation_id,
        decoded_message=result.decoded_message,
        mismatch=result.mismatch,
        available_stages=list(result.stages.keys()),
        inline_spectra=inline or None,
    )


@router.get(
    "/spectra/{stage}",
    response_model=StageDetailResponse,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
    tags=["spectra"],
)
async def stage_detail(stage: StageName, simulation_id: str = Query(..., min_length=8)) -> StageDetailResponse:
    try:
        snapshot = engine.get_stage(simulation_id, stage)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation or stage not found") from exc

    spectrum = _to_spectrum(stage, snapshot)
    waveform = _to_waveform(stage, snapshot)
    return StageDetailResponse(stage=stage, spectrum=spectrum, waveform=waveform)


# --------------------------------------------------------------------------- utils
def _to_spectrum(stage: StageName, snapshot: StageSnapshot, max_points: int = 2048) -> SpectrumSnapshot:
    freqs, mags = snapshot.spectrum()
    freqs = _decimate(freqs, max_points)
    mags = _decimate(mags, max_points)
    return SpectrumSnapshot(
        stage=stage,
        frequencies=freqs.tolist(),
        magnitudes=mags.tolist(),
        sample_rate=snapshot.sample_rate,
    )


def _to_waveform(stage: StageName, snapshot: StageSnapshot, max_points: int = 2048) -> WaveformSnapshot:
    samples = _decimate(snapshot.waveform, max_points)
    return WaveformSnapshot(stage=stage, samples=samples.tolist(), sample_rate=snapshot.sample_rate)


def _decimate(values: Iterable[float], max_points: int) -> FloatArray:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size <= max_points:
        return arr
    step = math.ceil(arr.size / max_points)
    return arr[::step]
