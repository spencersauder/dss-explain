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

from .schemas import CodingScheme, StageName


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


def _band_limited_awgn(signal: FloatArray, noise_power: float, bandwidth: float, sample_rate: float) -> FloatArray:
    if noise_power <= 0 or bandwidth <= 0:
        return signal

    rng = np.random.default_rng()
    raw_noise = rng.normal(0.0, 1.0, size=signal.shape)

    n = signal.size
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    spectrum = np.fft.rfft(raw_noise)
    half_bw = min(bandwidth / 2.0, sample_rate / 2)
    mask = (freqs >= -half_bw) & (freqs <= half_bw)
    if not np.any(mask):
        return signal
    spectrum[~mask] = 0
    shaped_noise = np.fft.irfft(spectrum, n=n)
    std = np.std(shaped_noise)
    if std > 0:
        shaped_noise = shaped_noise / std * math.sqrt(noise_power)
    else:
        shaped_noise = np.zeros_like(signal)
    return signal + shaped_noise


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
        noise_bandwidth: float,
        oversampling: int,
        coding_scheme: CodingScheme,
    ) -> SimulationResult:
        message_bytes = message.encode("utf-8")
        payload_bits = _text_to_bits(message_bytes)
        expected_bytes = len(message_bytes)
        chips_per_bit = max(8, len(tx_secret) * 4)
        sample_rate = chip_rate * oversampling

        encoded_bits, coding_meta = self._encode_bits(payload_bits, coding_scheme)

        tx_prn = _generate_prn(tx_secret, chips_per_bit)
        spread_chips = self._spread_bits(encoded_bits, tx_prn, chips_per_bit)
        chip_waveform = _repeat(spread_chips, oversampling)
        source_waveform = self._build_source_waveform(encoded_bits, chips_per_bit * oversampling)

        time = np.arange(chip_waveform.size, dtype=np.float64) / sample_rate
        carrier = np.cos(2.0 * np.pi * carrier_freq * time)
        tx_signal = chip_waveform * carrier
        channel_output = _band_limited_awgn(tx_signal, noise_power, noise_bandwidth, sample_rate)

        # Receiver side ----------------------------------------------------------
        rx_demod = channel_output * carrier
        rx_chips = _chunk_mean(rx_demod, oversampling)

        rx_prn = _generate_prn(rx_secret, chips_per_bit)
        despread = rx_chips * np.tile(rx_prn, len(encoded_bits) or 1)
        bit_metrics = _chunk_mean(despread, chips_per_bit)
        recovered_bits = (bit_metrics > 0).astype(np.uint8)

        decoded_bits = self._decode_bits(recovered_bits, coding_scheme, coding_meta)
        decoded = _bits_to_text(decoded_bits, expected_bytes)
        mismatch = decoded != message

        decoder_symbols = decoded_bits if decoded_bits.size else recovered_bits
        decoder_waveform = _repeat(_nrz(decoder_symbols), chips_per_bit * oversampling)

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

    # Coding helpers ------------------------------------------------------------
    def _encode_bits(
        self, bits: NDArray[np.uint8], scheme: CodingScheme
    ) -> Tuple[NDArray[np.uint8], Dict[str, int]]:
        meta: Dict[str, int] = {"payload_bits": int(bits.size)}
        if scheme == CodingScheme.NRZ:
            return bits.copy(), meta
        if scheme == CodingScheme.MANCHESTER:
            encoded = np.empty(bits.size * 2, dtype=np.uint8)
            mask = bits.astype(bool)
            encoded[0::2] = np.where(mask, 1, 0)
            encoded[1::2] = np.where(mask, 0, 1)
            return encoded, meta
        if scheme == CodingScheme.REP3:
            meta["repeat"] = 3
            return np.repeat(bits, 3), meta
        if scheme == CodingScheme.HAMMING74:
            padding = (-bits.size) % 4
            if padding:
                bits = np.pad(bits, (0, padding))
            meta["padding"] = padding
            reshaped = bits.reshape(-1, 4)
            d1, d2, d3, d4 = reshaped.T
            p1 = (d1 ^ d2 ^ d4).astype(np.uint8)
            p2 = (d1 ^ d3 ^ d4).astype(np.uint8)
            p3 = (d2 ^ d3 ^ d4).astype(np.uint8)
            codewords = np.stack((p1, p2, d1, p3, d2, d3, d4), axis=1)
            return codewords.reshape(-1), meta
        raise ValueError(f"Unsupported coding scheme: {scheme}")

    def _decode_bits(
        self,
        bits: NDArray[np.uint8],
        scheme: CodingScheme,
        meta: Dict[str, int],
    ) -> NDArray[np.uint8]:
        payload_len = meta.get("payload_bits", bits.size)
        if scheme == CodingScheme.NRZ:
            return bits[:payload_len]
        if scheme == CodingScheme.MANCHESTER:
            trimmed = bits[: (bits.size // 2) * 2].reshape(-1, 2)
            decoded = (trimmed[:, 0] > trimmed[:, 1]).astype(np.uint8)
            return decoded[:payload_len]
        if scheme == CodingScheme.REP3:
            repeat = meta.get("repeat", 3)
            trimmed = bits[: (bits.size // repeat) * repeat]
            if trimmed.size == 0:
                return trimmed
            votes = trimmed.reshape(-1, repeat).sum(axis=1)
            decoded = (votes >= math.ceil(repeat / 2)).astype(np.uint8)
            return decoded[:payload_len]
        if scheme == CodingScheme.HAMMING74:
            trimmed = bits[: (bits.size // 7) * 7]
            if trimmed.size == 0:
                return trimmed
            blocks = trimmed.reshape(-1, 7)
            c1, c2, c3, c4, c5, c6, c7 = blocks.T
            s1 = c1 ^ c3 ^ c5 ^ c7
            s2 = c2 ^ c3 ^ c6 ^ c7
            s3 = c4 ^ c5 ^ c6 ^ c7
            syndrome = s1 + (s2 << 1) + (s3 << 2)
            for idx, syn in enumerate(syndrome):
                if syn == 0:
                    continue
                pos = syn - 1
                blocks[idx, pos] ^= 1
            data = blocks[:, [2, 4, 5, 6]].reshape(-1)
            padding = meta.get("padding", 0)
            if padding:
                data = data[: -(padding)]
            return data[:payload_len]
        raise ValueError(f"Unsupported coding scheme: {scheme}")
