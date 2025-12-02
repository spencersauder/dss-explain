from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_simulate_endpoint_returns_decoded_message():
    payload = {
        "message": "test",
        "tx_secret": "secret",
        "rx_secret": "secret",
        "chip_rate": 50000.0,
        "carrier_freq": 500000.0,
        "noise_power": 0.0,
        "noise_bandwidth": 20000.0,
        "oversampling": 4,
        "coding_scheme": "nrz",
    }

    response = client.post("/api/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decoded_message"] == payload["message"]
    assert data["mismatch"] is False
    assert len(data["available_stages"]) > 0
    assert data["coding_scheme"] == "nrz"
    assert data["noise_bandwidth"] == payload["noise_bandwidth"]


def test_stage_detail_endpoint_requires_simulation():
    payload = {
        "message": "test",
        "tx_secret": "secret",
        "rx_secret": "secret",
        "chip_rate": 40000.0,
        "carrier_freq": 400000.0,
        "noise_power": 0.0,
        "noise_bandwidth": 15000.0,
        "oversampling": 4,
        "coding_scheme": "manchester",
    }
    sim_data = client.post("/api/simulate", json=payload).json()

    response = client.get(f"/api/spectra/modulator", params={"simulation_id": sim_data["simulation_id"]})
    assert response.status_code == 200
    stage = response.json()
    assert stage["spectrum"]["frequencies"], "frequencies missing"
