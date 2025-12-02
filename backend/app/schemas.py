"""Pydantic models for the DSSS simulator API."""
from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class StageName(str, Enum):
    """Enumerates tap locations exposed to the UI."""

    SOURCE = "source"
    SPREADER = "spreader"
    MODULATOR = "modulator"
    CHANNEL = "channel"
    CORRELATOR = "correlator"
    DECODER = "decoder"


class CodingScheme(str, Enum):
    NRZ = "nrz"
    MANCHESTER = "manchester"
    REP3 = "rep3"
    HAMMING74 = "hamming74"


class SpectrumSnapshot(BaseModel):
    stage: StageName
    frequencies: List[float] = Field(..., description="Frequency axis in Hz")
    magnitudes: List[float] = Field(..., description="Magnitude (linear)")
    sample_rate: float = Field(..., gt=0)


class WaveformSnapshot(BaseModel):
    stage: StageName
    samples: List[float]
    sample_rate: float = Field(..., gt=0)


class StageDetailResponse(BaseModel):
    stage: StageName
    waveform: WaveformSnapshot
    spectrum: SpectrumSnapshot


class SimulationRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=256)
    tx_secret: str = Field(..., min_length=4, max_length=64)
    rx_secret: str = Field(..., min_length=4, max_length=64)
    chip_rate: float = Field(1e5, gt=0)
    carrier_freq: float = Field(1e6, gt=0)
    noise_power: float = Field(0.0, ge=0.0, le=100.0)
    noise_bandwidth: float = Field(5e3, gt=0, description="Interference bandwidth in Hz")
    oversampling: int = Field(8, ge=1, le=64)
    coding_scheme: CodingScheme = CodingScheme.NRZ


class SimulationStatus(str, Enum):
    COMPLETE = "complete"
    ERROR = "error"


class SimulationResponse(BaseModel):
    simulation_id: str
    decoded_message: str
    status: SimulationStatus = SimulationStatus.COMPLETE
    mismatch: bool = False
    coding_scheme: CodingScheme = CodingScheme.NRZ
    noise_bandwidth: float
    available_stages: List[StageName]
    inline_spectra: Optional[List[SpectrumSnapshot]] = None


class SpectrumRequest(BaseModel):
    simulation_id: str
    stage: StageName


class ErrorResponse(BaseModel):
    detail: str
