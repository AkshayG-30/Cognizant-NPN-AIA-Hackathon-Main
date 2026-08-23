"""
Integration tests for FastAPI backend endpoints.
Suppresses library deprecation warnings and provides robust client execution.
"""
import sys
import warnings
from pathlib import Path

# Suppress library deprecation and scikit-learn warnings for clean test output
warnings.filterwarnings("ignore")

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_and_health_endpoints():
    res_root = client.get("/")
    assert res_root.status_code == 200, f"Root endpoint failed: {res_root.text}"
    assert res_root.json()["status"] == "online"

    res_health = client.get("/api/health")
    assert res_health.status_code == 200, f"Health endpoint failed: {res_health.text}"
    assert res_health.json()["db_status"] == "connected"


def test_patient_list_and_pagination():
    res = client.get("/api/patients?limit=15")
    assert res.status_code == 200, f"Patients list failed: {res.text}"
    data = res.json()
    assert len(data["patients"]) == 15
    assert data["total_dataset"] > 0
    assert "top1000_cutoff_risk" in data


def test_patient_detail_and_journey():
    res_p = client.get("/api/patients/P-1000")
    assert res_p.status_code == 200, f"Patient detail failed: {res_p.text}"
    patient = res_p.json()
    assert patient["name"] == "Maya Thompson"

    res_j = client.get("/api/patients/P-1000/journey")
    assert res_j.status_code == 200, f"Journey timeline failed: {res_j.text}"
    journey = res_j.json()
    assert "events" in journey
    assert len(journey["events"]) > 0


def test_dashboards():
    res_hosp = client.get("/api/dashboard/hospital")
    assert res_hosp.status_code == 200, f"Hospital dashboard failed: {res_hosp.text}"
    assert res_hosp.json()["total_patients"] > 0

    res_ins = client.get("/api/dashboard/insurance")
    assert res_ins.status_code == 200, f"Insurance dashboard failed: {res_ins.text}"
    assert res_ins.json()["total_members"] > 0


def test_ml_rescoring_trigger():
    res = client.post("/api/patients/P-1000/predict")
    assert res.status_code == 200, f"ML rescore trigger failed: {res.text}"
    data = res.json()
    assert "risk_score" in data
    assert "prediction_id" in data


if __name__ == "__main__":
    test_root_and_health_endpoints()
    test_patient_list_and_pagination()
    test_patient_detail_and_journey()
    test_dashboards()
    test_ml_rescoring_trigger()
    print("[OK] All FastAPI route integration tests passed successfully!")
