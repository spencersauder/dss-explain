import numpy as np

from app.dsss_engine import DSSSEngine
from app.schemas import CodingScheme, StageName


def test_simulation_round_trip():
    engine = DSSSEngine()
    result = engine.simulate(
        message="HELLO DSSS",
        tx_secret="alpha",
        rx_secret="alpha",
        chip_rate=50_000,
        carrier_freq=500_000,
        noise_power=0.0,
        noise_bandwidth=20_000,
        oversampling=4,
        coding_scheme=CodingScheme.NRZ,
    )

    assert result.decoded_message == "HELLO DSSS"
    assert result.mismatch is False
    assert set(result.stages.keys()) == set(StageName)
    stage = engine.get_stage(result.simulation_id, StageName.MODULATOR)
    assert stage.sample_rate == result.stages[StageName.MODULATOR].sample_rate


def test_secret_mismatch_flags_error():
    engine = DSSSEngine()
    result = engine.simulate(
        message="HELLO DSSS",
        tx_secret="alpha",
        rx_secret="impostor-key",
        chip_rate=50_000,
        carrier_freq=500_000,
        noise_power=0.0,
        noise_bandwidth=20_000,
        oversampling=4,
        coding_scheme=CodingScheme.NRZ,
    )

    assert result.mismatch is True
    assert result.decoded_message != "HELLO DSSS"


def test_hamming_encoder_decoder_round_trip():
    engine = DSSSEngine()
    bits = np.array([1, 0, 1, 1, 0, 1, 0, 0], dtype=np.uint8)
    encoded, meta = engine._encode_bits(bits, CodingScheme.HAMMING74)
    recovered = engine._decode_bits(encoded, CodingScheme.HAMMING74, meta)
    assert np.array_equal(recovered, bits)
