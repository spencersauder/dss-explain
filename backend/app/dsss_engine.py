"""DSP helpers backing the DSSS simulator endpoints."""
from __future__ import annotations

import hashlib
import math
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, MutableMapping, Tuple

import numpy as np
from numpy.typing import NDArray

from .schemas import StageName


FloatArray = NDArray[np.float64]


@dataclass
class StageSnapshot:
    waveform: FloatArray
    sample_rate: float

    def spectrum(self) -> Tuple[FloatArray, FloatArray]:
        """Return (frequency axis, magnitude) for the waveform."""
        if len(self.waveform) == 0:
            return np.array([0.0]), np.array([0.0])

        n = len(self.waveform)
        freqs = np.fft.rfftfreq(n, d=1.0 / self.sample_rate)
        mags = np.abs(np.fft.rfft(self.waveform)) / max(n, 1)
        return freqs, mags


@dataclass
class SimulationResult:
    simulation_id: str
    decoded_message: str
    mismatch: bool
    stages: Dict[StageName, StageSnapshot]


def _text_to_bits(data: bytes) -> NDArray[np.uint8]:
    if not data:
        return np.zeros(0, dtype=np.uint8)
    bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
    return bits.astype(np.uint8)


def _bits_to_text(bits: NDArray[np.uint8], expected_bytes: int) -> str:
    if bits.size == 0:
        return ""
    trimmed = bits[: expected_bytes * 8]
    padded = np.pad(trimmed, (0, (-trimmed.size) % 8), constant_values=0)
    packed = np.packbits(padded)[:expected_bytes]
    return packed.tobytes().decode("utf-8", errors="replace")


def _nrz(bits: NDArray[np.uint8]) -> FloatArray:
    return 2.0 * bits.astype(np.float64) - 1.0


def _generate_seed(secret: str) -> int:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def _generate_prn(secret: str, chips_per_bit: int) -> FloatArray:
    rng = np.random.default_rng(_generate_seed(secret))
    chips = rng.choice([-1.0, 1.0], size=chips_per_bit, replace=True)
    return chips.astype(np.float64)


def _repeat(sequence: FloatArray, repeat_factor: int) -> FloatArray:
    return np.repeat(sequence, repeat_factor)


def _awgn(signal: FloatArray, noise_power: float) -> FloatArray:
    if noise_power <= 0:
        return signal
    rng = np.random.default_rng()
    noise = rng.normal(0.0, math.sqrt(noise_power), size=signal.shape)
    return signal + noise


def _chunk_mean(values: FloatArray, chunk_size: int) -> FloatArray:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    trimmed = values[: (len(values) // chunk_size) * chunk_size]
    return trimmed.reshape(-1, chunk_size).mean(axis=1)


class DSSSEngine:
    """Numerical DSSS simulator with lightweight caching for spectra taps."""

    def __init__(self, cache_size: int = 16) -> None:
        self._cache: MutableMapping[str, Dict[StageName, StageSnapshot]] = OrderedDict()
        self._cache_size = cache_size

    # Public API -----------------------------------------------------------------
    def simulate(
        self,
        message: str,
        tx_secret: str,
        rx_secret: str,
        chip_rate: float,
        carrier_freq: float,
        noise_power: float,
        oversampling: int,
    ) -> SimulationResult:
        message_bytes = message.encode("utf-8")
        bits = _text_to_bits(message_bytes)
        expected_bytes = len(message_bytes)
        chips_per_bit = max(8, len(tx_secret) * 4)
        sample_rate = chip_rate * oversampling

        tx_prn = _generate_prn(tx_secret, chips_per_bit)
        spread_chips = self._spread_bits(bits, tx_prn, chips_per_bit)
        chip_waveform = _repeat(spread_chips, oversampling)
        source_waveform = self._build_source_waveform(bits, chips_per_bit * oversampling)

        time = np.arange(chip_waveform.size, dtype=np.float64) / sample_rate
        carrier = np.cos(2.0 * np.pi * carrier_freq * time)
        tx_signal = chip_waveform * carrier
        channel_output = _awgn(tx_signal, noise_power)

        # Receiver side ----------------------------------------------------------
        rx_demod = channel_output * carrier
        rx_chips = _chunk_mean(rx_demod, oversampling)

        rx_prn = _generate_prn(rx_secret, chips_per_bit)
        despread = rx_chips * np.tile(rx_prn, len(bits) or 1)
        bit_metrics = _chunk_mean(despread, chips_per_bit)
        recovered_bits = (bit_metrics > 0).astype(np.uint8)

        decoded = _bits_to_text(recovered_bits, expected_bytes)
        mismatch = decoded != message

        decoder_waveform = _repeat(_nrz(recovered_bits), chips_per_bit * oversampling)

        stages = {
            StageName.SOURCE: StageSnapshot(source_waveform, sample_rate),
            StageName.SPREADER: StageSnapshot(chip_waveform, sample_rate),
            StageName.MODULATOR: StageSnapshot(tx_signal, sample_rate),
            StageName.CHANNEL: StageSnapshot(channel_output, sample_rate),
            StageName.CORRELATOR: StageSnapshot(rx_demod, sample_rate),
            StageName.DECODER: StageSnapshot(decoder_waveform, sample_rate),
        }

        sim_id = uuid.uuid4().hex
        self._store(sim_id, stages)
        return SimulationResult(simulation_id=sim_id, decoded_message=decoded, mismatch=mismatch, stages=stages)

    def get_stage(self, simulation_id: str, stage: StageName) -> StageSnapshot:
        try:
            return self._cache[simulation_id][stage]
        except KeyError as exc:  # pragma: no cover - guard clause
            raise KeyError(f"Unknown simulation_id/stage combination: {simulation_id}/{stage}") from exc

    # Internal helpers -----------------------------------------------------------
    @staticmethod
    def _spread_bits(bits: NDArray[np.uint8], prn: FloatArray, chips_per_bit: int) -> FloatArray:
        if bits.size == 0:
            return np.zeros(chips_per_bit, dtype=np.float64)
        bit_symbols = _nrz(bits)
        expanded_bits = np.repeat(bit_symbols, chips_per_bit)
        tiled_prn = np.tile(prn, bits.size)
        return expanded_bits * tiled_prn

    @staticmethod
    def _build_source_waveform(bits: NDArray[np.uint8], repeats: int) -> FloatArray:
        if bits.size == 0:
            return np.zeros(repeats or 1, dtype=np.float64)
        symbols = _nrz(bits)
        return np.repeat(symbols, repeats)

    def _store(self, simulation_id: str, stages: Dict[StageName, StageSnapshot]) -> None:
        if simulation_id in self._cache:
            del self._cache[simulation_id]
        self._cache[simulation_id] = stages
        if len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)
