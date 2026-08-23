import os
import sys
import json
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from main import app

client = TestClient(app)

def test_api():
    print("=== TESTING CAREPATH LONGITUDINAL BACKEND API ===")
    
    # 1. Health Check
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[OK] Health Check Passed:", res.json())
    
    # 2. Patients List (Top 1000)
    res = client.get("/api/patients?limit=10")
    assert res.status_code == 200, f"List patients failed: {res.text}"
    data = res.json()
    assert len(data["patients"]) == 10
    assert data["total_dataset"] == 7754
    print("[OK] Patient List Endpoint Passed. Top Cutoff Risk:", data["top1000_cutoff_risk"])
    
    # 3. Patient Detail (P-1000)
    res = client.get("/api/patients/P-1000")
    assert res.status_code == 200, f"Get P-1000 failed: {res.text}"
    p = res.json()
    assert p["name"] == "Maya Thompson"
    print("[OK] Patient Detail Endpoint (P-1000) Passed:", p["name"], f"Risk: {p['risk']}")
    
    # 4. Predict Risk (Manual ML Trigger)
    res = client.post("/api/patients/P-1000/predict")
    assert res.status_code == 200, f"Predict risk failed: {res.text}"
    pred_data = res.json()
    assert "risk_score" in pred_data
    assert "prediction_id" in pred_data
    print("[OK] Predict Risk Trigger Passed. Prediction ID:", pred_data["prediction_id"], f"Score: {pred_data['risk_score']}")
    
    # 5. Get History Trajectory
    res = client.get("/api/patients/P-1000/history")
    assert res.status_code == 200, f"History trajectory failed: {res.text}"
    hist = res.json()
    assert len(hist["predictions"]) >= 1
    assert len(hist["snapshots"]) >= 1
    print(f"[OK] History Trajectory Passed. Total Predictions Tracked: {len(hist['predictions'])}, Total Snapshots: {len(hist['snapshots'])}")

    # 6. Test Free2SMS Alert Dispatch
    res = client.post("/api/patients/P-1000/alert", json={
        "intervention_type": "Follow-up Care Plan",
        "message": "CarePath Alert: Please confirm your follow-up appointment.",
        "phone_number": "7598070435"
    })
    assert res.status_code == 200, f"Alert dispatch failed: {res.text}"
    alert_res = res.json()
    print("[OK] SMS Alert Dispatch Endpoint Passed:", alert_res["alert"]["note"])

    print("\nALL API INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_api()
