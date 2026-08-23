"""
cohort_service.py — Clinical Cohort & Risk Stratification Analytics Service

Provides enterprise-grade population health segmentation, avoidable cost modeling,
comorbidity burden scoring, and intervention prioritization metrics.
"""
from typing import Dict, List, Any, Optional
import math


class CohortService:
    """Service layer for cohort analytics, risk stratification, and avoidable cost estimation."""

    # Cost model baseline estimates (CMS average per encounter)
    AVOIDABLE_ED_COST_USD = 1850.0
    AVOIDABLE_INPATIENT_COST_USD = 14200.0
    PREVENTIVE_OUTREACH_COST_USD = 120.0

    @staticmethod
    def calculate_comorbidity_index(conditions: str) -> Dict[str, Any]:
        """
        Parses comma-separated clinical conditions and computes a weighted burden score.
        """
        if not conditions or conditions.strip() == "None identified":
            return {
                "condition_list": [],
                "count": 0,
                "burden_tier": "Low",
                "weighted_score": 0.0
            }

        cond_list = [c.strip() for c in conditions.split(",") if c.strip()]
        
        # Clinical weights based on CMS HCC (Hierarchical Condition Categories)
        weights = {
            "CHF": 1.8,
            "COPD": 1.5,
            "CKD": 1.6,
            "Diabetes": 1.2,
            "HTN": 1.0,
            "Asthma": 1.1
        }
        
        total_weight = sum(weights.get(c, 1.0) for c in cond_list)
        count = len(cond_list)
        
        if count >= 4 or total_weight >= 5.0:
            tier = "High"
        elif count >= 2 or total_weight >= 2.5:
            tier = "Moderate"
        else:
            tier = "Low"

        return {
            "condition_list": cond_list,
            "count": count,
            "burden_tier": tier,
            "weighted_score": round(total_weight, 2)
        }

    @classmethod
    def estimate_avoidable_spend(cls, risk_score: float, ed_visits: int, inpatient_admissions: int = 0) -> Dict[str, Any]:
        """
        Estimates potentially avoidable spend based on risk trajectory and historical utilization.
        """
        clamped_risk = max(0.0, min(1.0, float(risk_score)))
        
        # Projected probability that future encounters are preventable through proactive care navigation
        preventability_factor = 0.65 if clamped_risk > 0.8 else (0.45 if clamped_risk > 0.6 else 0.25)
        
        historical_avoidable_ed = ed_visits * cls.AVOIDABLE_ED_COST_USD * preventability_factor
        historical_avoidable_ip = inpatient_admissions * cls.AVOIDABLE_INPATIENT_COST_USD * preventability_factor
        total_avoidable_historical = historical_avoidable_ed + historical_avoidable_ip

        # 30-day forward projection
        projected_30d_avoidable = (clamped_risk * cls.AVOIDABLE_ED_COST_USD * 1.5) * preventability_factor
        estimated_roi = round((projected_30d_avoidable / cls.PREVENTIVE_OUTREACH_COST_USD), 2) if projected_30d_avoidable > 0 else 0.0

        return {
            "risk_score": round(clamped_risk, 4),
            "preventability_factor": round(preventability_factor, 2),
            "historical_avoidable_spend_usd": round(total_avoidable_historical, 2),
            "projected_30d_avoidable_spend_usd": round(projected_30d_avoidable, 2),
            "estimated_intervention_cost_usd": cls.PREVENTIVE_OUTREACH_COST_USD,
            "projected_net_savings_usd": round(max(0.0, projected_30d_avoidable - cls.PREVENTIVE_OUTREACH_COST_USD), 2),
            "projected_roi_ratio": estimated_roi
        }

    @staticmethod
    def stratify_population(patients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Performs multi-dimensional stratification across risk tiers, age groups, and care continuity.
        """
        total = len(patients)
        if total == 0:
            return {"total": 0, "distribution": {}, "tiers": {}}

        tier_counts = {"High": 0, "Medium": 0, "Low": 0}
        continuity_counts = {"Stable": 0, "Moderate": 0, "Fragmented": 0}
        total_risk_sum = 0.0

        for p in patients:
            level = p.get("current_level") or p.get("level") or "Low"
            tier_counts[level] = tier_counts.get(level, 0) + 1
            
            cont = p.get("continuity", "Moderate")
            continuity_counts[cont] = continuity_counts.get(cont, 0) + 1
            
            total_risk_sum += float(p.get("current_risk") or p.get("risk") or 0.0)

        avg_risk = round(total_risk_sum / total, 4) if total > 0 else 0.0

        return {
            "total_population": total,
            "average_risk_score": avg_risk,
            "risk_distribution": {
                "high_risk_count": tier_counts["High"],
                "high_risk_pct": round((tier_counts["High"] / total) * 100, 2),
                "medium_risk_count": tier_counts["Medium"],
                "medium_risk_pct": round((tier_counts["Medium"] / total) * 100, 2),
                "low_risk_count": tier_counts["Low"],
                "low_risk_pct": round((tier_counts["Low"] / total) * 100, 2)
            },
            "care_continuity_distribution": continuity_counts
        }
