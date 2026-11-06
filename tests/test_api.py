"""
Unit and integration tests for FastAPI REST API endpoints.
"""
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_api_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["kb_chunks_indexed"] > 0
    assert "en" in data["supported_languages"]


def test_api_list_samples():
    response = client.get("/api/samples")
    assert response.status_code == 200
    samples = response.json()
    assert len(samples) == 5
    ids = [s["id"] for s in samples]
    assert "cbc_anemia" in ids
    assert "critical_panic" in ids


def test_api_get_sample():
    response = client.get("/api/samples/cbc_anemia?language=en")
    assert response.status_code == 200
    report = response.json()
    assert len(report["measurements"]) > 0
    # Check that citations are present
    assert len(report["measurements"][0]["citations"]) > 0
    assert "medlineplus.gov" in report["measurements"][0]["citations"][0]


def test_api_analyze_text():
    raw_text = "Hemoglobin: 10.2 g/dL (12.0 - 15.0)\nPlatelet Count: 210000 /uL (150000 - 450000)"
    response = client.post("/api/analyze-text", json={"raw_text": raw_text, "language": "en"})
    assert response.status_code == 200
    report = response.json()
    assert len(report["measurements"]) == 2
    hb = next(m for m in report["measurements"] if m["canonical_name"] == "Hemoglobin")
    assert hb["status"] == "LOW"
    assert not hb["is_critical"]


def test_api_evaluate_only():
    payload = [
        {
            "test_name": "Hemoglobin",
            "canonical_name": "Hemoglobin",
            "measured_value": 6.2,
            "unit": "g/dL",
            "ref_min": 12.0,
            "ref_max": 16.0
        }
    ]
    response = client.post("/api/evaluate-only", json=payload)
    assert response.status_code == 200
    report = response.json()
    assert report["overall_status"] == "CRITICAL"
    assert report["measurements"][0]["status"] == "CRITICAL_LOW"
    assert report["measurements"][0]["is_critical"] is True
