"""
Unit tests for patient_journey_db data access layer.
"""
import sys
from pathlib import Path
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
import patient_journey_db as db


def test_database_connectivity_and_stats():
    conn = db.get_connection()
    assert conn is not None
    
    total = db.get_total_patient_count()
    assert total > 0
    
    dist = db.get_risk_distribution()
    assert "High" in dist
    assert "Low" in dist


def test_patient_crud_and_lookup():
    # Test retrieving sample patient P-1000
    p = db.get_patient("P-1000")
    assert p is not None
    assert p["patient_id"] == "P-1000"
    assert "name" in p
    assert p["current_risk"] > 0.0


def test_journey_event_recording():
    pid = "P-1000"
    test_event_id = str(uuid.uuid4())
    
    # Save a test journey event
    eid = db.insert_journey_event(
        patient_id=pid,
        event_date="2026-08-23T10:00:00",
        event_type="CARE_MANAGEMENT",
        event_source="APPLICATION",
        title="Test Audit Event",
        description="Automated backend integration verification event",
        event_status="Completed",
        metadata={"automated_test": True},
        event_id=test_event_id
    )
    assert eid == test_event_id
    
    events = db.get_patient_journey(pid, limit=10)
    assert len(events) > 0
    assert any(e.get("title") == "Test Audit Event" for e in events)


def test_prediction_history_logging():
    pid = "P-1000"
    pred_id = db.save_prediction(
        patient_id=pid,
        risk_score=0.8850,
        risk_level="High",
        trigger="TEST_SUITE"
    )
    assert pred_id is not None
    
    history = db.get_prediction_history(pid, limit=5)
    assert len(history) >= 1
    assert any(h["prediction_id"] == pred_id for h in history)


if __name__ == "__main__":
    test_database_connectivity_and_stats()
    test_patient_crud_and_lookup()
    test_journey_event_recording()
    test_prediction_history_logging()
    print("[OK] All Patient Journey DB unit tests passed successfully!")
