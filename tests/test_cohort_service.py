"""
Unit tests for CohortService clinical analytics and cost modeling.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from services.cohort_service import CohortService


def test_comorbidity_index_calculation():
    # Test multiple severe conditions
    result = CohortService.calculate_comorbidity_index("CHF, COPD, Diabetes, CKD")
    assert result["count"] == 4
    assert result["burden_tier"] == "High"
    assert result["weighted_score"] >= 5.0
    assert "CHF" in result["condition_list"]

    # Test single condition
    single = CohortService.calculate_comorbidity_index("HTN")
    assert single["count"] == 1
    assert single["burden_tier"] == "Low"

    # Test empty conditions
    empty = CohortService.calculate_comorbidity_index("None identified")
    assert empty["count"] == 0
    assert empty["burden_tier"] == "Low"


def test_avoidable_spend_estimation():
    high_risk_spend = CohortService.estimate_avoidable_spend(risk_score=0.92, ed_visits=3, inpatient_admissions=1)
    assert high_risk_spend["risk_score"] == 0.92
    assert high_risk_spend["historical_avoidable_spend_usd"] > 0
    assert high_risk_spend["projected_30d_avoidable_spend_usd"] > 0
    assert high_risk_spend["projected_roi_ratio"] > 1.0


def test_population_stratification():
    mock_patients = [
        {"current_level": "High", "continuity": "Fragmented", "current_risk": 0.95},
        {"current_level": "High", "continuity": "Moderate", "current_risk": 0.85},
        {"current_level": "Medium", "continuity": "Stable", "current_risk": 0.65},
        {"current_level": "Low", "continuity": "Stable", "current_risk": 0.20},
    ]
    summary = CohortService.stratify_population(mock_patients)
    assert summary["total_population"] == 4
    assert summary["risk_distribution"]["high_risk_count"] == 2
    assert summary["risk_distribution"]["high_risk_pct"] == 50.0
    assert summary["care_continuity_distribution"]["Fragmented"] == 1


if __name__ == "__main__":
    test_comorbidity_index_calculation()
    test_avoidable_spend_estimation()
    test_population_stratification()
    print("[OK] All CohortService unit tests passed successfully!")
