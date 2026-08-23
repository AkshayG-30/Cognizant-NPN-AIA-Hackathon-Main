# ML V2 — CarePath Navigator

## Directory Structure
```
ML_V2/
├── config.yaml              — all configuration
├── requirements-ml-v2.txt   — pinned dependencies
├── data/prepared/           — train/valid/test parquet splits
├── models/                  — trained model artifacts
├── preprocessing/           — fitted scaler pipeline
├── predictions/             — final test predictions
├── metrics/                 — evaluation CSVs
├── plots/                   — ROC, PR, calibration, SHAP
├── explainability/          — feature importance + SHAP
├── experiments/             — hyperparameter search results
├── reports/                 — FINAL_ML_V2_REPORT.md, JUDGE_SUMMARY_V2.md
├── logs/                    — GPU test log
└── scripts/                 — reproducible pipeline
```

## Quick Start
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-ml-v2.txt
python scripts/02_prepare_data.py
python scripts/run_v2.py
```

## Results
Best model: **Ensemble (ROC-AUC = 0.8816)**
