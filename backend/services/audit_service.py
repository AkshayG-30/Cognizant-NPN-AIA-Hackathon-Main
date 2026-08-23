"""
audit_service.py — Audit Logging and Compliance Trail Service

Maintains immutable records of clinical interventions, data access, ML inferences,
and SMS outreach events to ensure regulatory compliance and operational observability.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import json
import logging

log = logging.getLogger("carepath.audit")


class AuditService:
    """Structured audit trail recorder for patient journey and clinical interactions."""

    ACTION_VIEW_PATIENT = "PATIENT_RECORD_ACCESSED"
    ACTION_ML_INFERENCE = "ML_RISK_INFERENCE_TRIGGERED"
    ACTION_OUTREACH_DISPATCH = "SMS_OUTREACH_DISPATCHED"
    ACTION_DOCUMENT_INGESTION = "CLINICAL_DOCUMENT_INGESTED"
    ACTION_MANUAL_OVERRIDE = "CARE_PLAN_OVERRIDE"

    @classmethod
    def log_event(cls, action_type: str, patient_id: str, actor_id: str = "SYSTEM", details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Creates a structured, timestamped audit log entry.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action_type": action_type,
            "patient_id": patient_id,
            "actor_id": actor_id,
            "details": details or {},
            "status": "LOGGED"
        }
        
        log.info(f"[AUDIT] {entry['timestamp']} | action={action_type} | patient={patient_id} | actor={actor_id}")
        return entry

    @classmethod
    def log_ml_prediction(cls, patient_id: str, risk_score: float, model_version: str = "V2", trigger: str = "SCHEDULED") -> Dict[str, Any]:
        """Logs an ML inference execution."""
        return cls.log_event(
            action_type=cls.ACTION_ML_INFERENCE,
            patient_id=patient_id,
            actor_id="ML_ENGINE",
            details={
                "risk_score": risk_score,
                "model_version": model_version,
                "trigger_reason": trigger
            }
        )

    @classmethod
    def log_outreach(cls, patient_id: str, recipient_phone: str, channel: str = "SMS", template_id: Optional[str] = None) -> Dict[str, Any]:
        """Logs an automated or manual outreach dispatch."""
        masked_phone = "*" * max(0, len(recipient_phone) - 4) + recipient_phone[-4:] if len(recipient_phone) >= 4 else "****"
        return cls.log_event(
            action_type=cls.ACTION_OUTREACH_DISPATCH,
            patient_id=patient_id,
            actor_id="CARE_MANAGER",
            details={
                "channel": channel,
                "recipient_masked": masked_phone,
                "template_id": template_id or "POST_ED_FOLLOWUP_CARE"
            }
        )
