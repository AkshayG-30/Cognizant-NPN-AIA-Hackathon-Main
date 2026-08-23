# CarePath Navigator — Judge Summary V2

## What Changed from V1?
V2 integrates **5 new CMS claim datasets** (Part D, DME, HHA, SNF, Hospice) as beneficiary-level features, expanding from 45 to **58 features**.

## What New Data/Features Were Used?
- **PDE**: prescription counts, unique drugs, polypharmacy flags
- **DME**: durable medical equipment utilization
- **HHA/SNF/HOSPICE**: care-setting utilization flags and counts

All joined via BENE_ID at beneficiary-year aggregation level (not raw claim join).

## What Models Were Trained?
1. Logistic Regression (CPU) — C=0.0005, balanced
2. Random Forest (CPU) — 300 trees, depth=12
3. XGBoost (GPU/CUDA) — 200 trees, depth=6, lr=0.005
4. Weighted Ensemble — LR=0.5, RF=0.3, XGB=0.2

## How Was Leakage Prevented?
- Strict temporal splits (train→2019, valid→2020, test→2021)
- Features from past years only, no label-year data
- Train-only preprocessing fitting
- Test set untouched until final frozen evaluation

## Which Model Won?
**Weighted Ensemble** (LR=0.5, RF=0.3, XGB=0.2)

## Final ROC-AUC?
**0.8816** (test set)

## Did We Achieve 0.92?
**NO.** Improvement over V1: +0.0098. The 0.92 target requires real claims data, clinical ground truth, and SDOH features.

## What Does the Model Do?
Ranks Medicare beneficiaries by probability of having an **avoidable ED visit** (AHRQ PQE-defined) in the upcoming year. Care managers use the ranked list to prioritize **proactive navigation outreach** — connecting high-risk members to primary care, chronic disease management, and social services before they use the ED unnecessarily.
