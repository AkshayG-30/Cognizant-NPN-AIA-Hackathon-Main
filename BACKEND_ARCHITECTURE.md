# CarePath Navigator — Backend Architecture & System Design

## 1. System Overview

The **CarePath Backend Service** is an enterprise-grade population health analytics engine built with **FastAPI**, **SQLite / PostgreSQL**, and a **Tri-Model Ensemble Machine Learning Engine** (Logistic Regression, Random Forest, XGBoost). It ingests longitudinal CMS Medicare claims, generates patient-level journey event graphs, and delivers real-time risk predictions with SHAP explainability.

```mermaid
flowchart TD
    subgraph Data Layer
        A[CMS Raw Claims Parquet] -->|ETL Ingestion| B[(carepath_journey.db)]
        B --> C[Patients Table]
        B --> D[Journey Events Table]
        B --> E[Feature Snapshots Table]
        B --> F[Prediction History Table]
    end

    subgraph Analytics & ML Engine
        G[Weighted ML V2 Ensemble] -->|LR + RF + XGBoost| H[Real-Time Risk Scoring]
        I[SHAP Explainability] --> H
        J[Cohort Stratification Service] --> K[Avoidable Spend Modeling]
    end

    subgraph API Layer
        L[FastAPI REST Engine] --> M[/api/patients]
        L --> N[/api/dashboard/hospital]
        L --> O[/api/dashboard/insurance]
        L --> P[/api/patients/:id/predict]
        L --> Q[/api/patients/:id/journey]
    end

    subgraph Presentation & Client
        R[Next.js 16 Web Dashboard] <-->|REST / JSON| L
    end

    B <--> L
    H <--> L
    J <--> L
```

---

## 2. Core Backend Components

### 2.1 Normalized Longitudinal Event Model (`patient_journey_db.py`)
- **Single-Table Multi-Tenant Patient Architecture**: Normalized storage supporting 7,750+ Medicare beneficiaries.
- **Event Sourcing Pattern**: Claims and clinical interactions are stored as immutable chronological events with full provenance to source claim IDs (`CLM_ID`).
- **Idempotent Data Access**: Atomic transactions, WAL mode SQLite fallback, and PostgreSQL connection wrapper.

### 2.2 Clinical Cohort & Cost Modeling Service (`services/cohort_service.py`)
- **Comorbidity Index Scoring**: Weighted risk burden based on CMS Hierarchical Condition Categories (HCC) across Heart Failure, COPD, CKD, Diabetes, and Hypertension.
- **Avoidable Spend Projections**: Algorithmic cost-benefit modeling estimating preventable emergency encounters and return-on-investment (ROI) for care management outreach.

### 2.3 Audit & Compliance Service (`services/audit_service.py`)
- **Structured Audit Logging**: Real-time tracking of patient record views, ML inference triggers, care plan overrides, and automated outreach dispatches with phone masking.

### 2.4 ML Inference & Explainability Pipeline (`main.py`)
- **Tri-Model Weighted Ensemble**: Combines calibrated probabilities from Logistic Regression (L2 regularized), Random Forest (100 estimators), and XGBoost (Gradient Boosted Trees).
- **On-Demand Feature Rescoring**: Real-time evaluation of patient feature snapshots triggered by manual inputs or uploaded medical documentation.

---

## 3. Database Schema Reference

| Table Name | Primary Key | Description |
| :--- | :--- | :--- |
| `patients` | `patient_id` | Master demographic, clinical condition, and risk profile records |
| `patient_journey_events` | `event_id` | Longitudinal clinical encounters (ED visits, Inpatient, Outpatient, Outreach) |
| `patient_feature_snapshots` | `snapshot_id` | 58-dimension ML feature vectors captured at specific points in time |
| `patient_risk_predictions` | `prediction_id` | Complete historical audit of risk scores, levels, and triggers |
| `patient_alerts` | `alert_id` | Dispatched outreach notifications and intervention records |

---

## 4. API Endpoints Specification

### Healthcare Provider & Hospital Operations
- `GET /api/dashboard/hospital`: Aggregated population health KPIs, ED surge forecasts, and risk stratification metrics.
- `GET /api/patients?limit=50`: Paginated cohort directory sorted by risk trajectory.
- `GET /api/patients/{patient_id}`: Comprehensive patient 360 profile with chronic conditions and continuity index.
- `GET /api/patients/{patient_id}/journey`: Complete chronological care journey event timeline.

### Payer & Health Plan Financial Operations
- `GET /api/dashboard/insurance`: High-value member opportunities, preventable spend totals, and cost distributions.
- `GET /api/members`: Prioritized member list ranked by intervention ROI and opportunity score.

### Clinical ML & Real-Time Rescoring
- `POST /api/patients/{patient_id}/predict`: On-demand ML inference execution appending to trajectory history.
- `POST /api/patients/{patient_id}/alert`: Dispatch targeted SMS outreach via carrier gateway.
- `GET /api/model/info`: Model performance metadata (ROC-AUC: `0.8816`, PR-AUC: `0.1842`).

---

## 5. Automated Verification & Testing

The backend includes automated test suites covering all architectural layers:

```bash
# Run backend DB layer tests
python tests/test_patient_db.py

# Run clinical cohort service tests
python tests/test_cohort_service.py

# Run REST API endpoint integration tests
python tests/test_api_endpoints.py

# Run comprehensive full-system verification
python scripts/verify_status.py
```
