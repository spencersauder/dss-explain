from app.dsss_engine import DSSSEngine
from app.schemas import StageName


def test_simulation_round_trip():
    engine = DSSSEngine()
    result = engine.simulate(
        message="HELLO DSSS",
        tx_secret="alpha",
        rx_secret="alpha",
        chip_rate=50_000,
        carrier_freq=500_000,
        noise_power=0.0,
        oversampling=4,
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
        oversampling=4,
    )

    assert result.mismatch is True
    assert result.decoded_message != "HELLO DSSS"
