# CarePath Navigator — ML V2 Final Report

## 1. Executive Summary

ML V2 integrates **13 new features** from 5 previously separate datasets (PDE, DME, HHA, SNF, HOSPICE) into the modeling pipeline. The best V2 model (Weighted Ensemble) achieves **ROC-AUC = 0.8816**, a **+0.0098 improvement** over V1's 0.8718. The 0.92 target was **NOT achieved**.

## 2. Dataset

- Source: MASTER_DATASET (1,754,162 claim rows, 8,715 beneficiaries)
- New datasets: PDE (515K), DME (104K), HHA (6K), SNF (13K), HOSPICE (12K)
- Prediction unit: **Beneficiary-year**
- Features: **58** (V1: 45, new: 13)

## 3. New V2 Features (from separate datasets)

| Feature | Source | Description |
|---------|--------|-------------|
| n_prescriptions | PDE | Total prescription events in feature window |
| n_unique_drugs | PDE | Distinct drug products (NDC) |
| polypharmacy | PDE | ≥5 unique drugs (binary) |
| high_polypharmacy | PDE | ≥10 unique drugs (binary) |
| rx_per_year | PDE | Prescriptions per observed year |
| n_dme_claims / has_dme | DME | DME utilization count and flag |
| n_hha_claims / has_hha | HHA | Home health utilization |
| n_snf_claims / has_snf | SNF | Skilled nursing facility utilization |
| n_hospice_claims / has_hospice | HOSPICE | Hospice enrollment |

## 4. Temporal Split

| Split | Feature Years | Label Year | Benes | Positives |
|-------|--------------|------------|-------|-----------|
| Train | 2015-2018 | 2019 | 6,928 | 68 (1.0%) |
| Valid | 2016-2019 | 2020 | 7,373 | 47 (0.6%) |
| Test | 2017-2020 | 2021 | 7,754 | 77 (1.0%) |

## 5. V1 vs V2 Results (Test Set)

| Model | V1 ROC | V2 ROC | Delta | V2 PR-AUC |
|-------|--------|--------|-------|-----------|
| LR | 0.8704 | 0.8783 | **+0.0079** | 0.1535 |
| RF | 0.8517 | 0.8459 | -0.0058 | 0.1728 |
| XGB | 0.8607 | 0.8760 | **+0.0153** | 0.1647 |
| **Ensemble** | **0.8718** | **0.8816** | **+0.0098** | **0.1842** |

## 6. Best Model: Ensemble_V2

| Metric | Value |
|--------|-------|
| ROC-AUC | **0.8816** |
| PR-AUC | **0.1842** |
| F1 | 0.2202 |
| Recall | 0.6234 |
| Precision | (threshold-dependent) |
| Weights | LR=0.5, RF=0.3, XGB=0.2 |

## 7. Hyperparameters

**LR**: C=0.0005, balanced class_weight, lbfgs solver
**RF**: 300 trees, max_depth=12, min_samples_leaf=5, balanced_subsample
**XGB**: 200 trees, depth=6, lr=0.005, subsample=0.9, colsample=0.7, GPU (cuda)

## 8. Leakage Prevention

| Check | Status |
|-------|--------|
| No future claims in features | PASSED |
| No label-year data in features | PASSED |
| No target-derived features | PASSED |
| Train-only preprocessing | PASSED |
| No test-set tuning | PASSED |
| Temporal integrity | PASSED |

## 9. 0.92 Target

**NOT ACHIEVED.** Best = 0.8816. Same fundamental limitations as V1:
- Proxy target (AHRQ PQE weak supervision)
- 1% prevalence (68-77 positives per split)
- Synthetic CMS data artifacts
- ED undercount (inpatient-only)
- No SDOH features

## 10. What V2 Added

The PDE features (medication data) provided the most value among new features, with XGBoost showing the largest individual improvement (+0.0153 ROC-AUC). The ensemble shift from LR=0.4/RF=0.4/XGB=0.2 to LR=0.5/RF=0.3/XGB=0.2 reflects LR's stronger performance with the expanded feature set.

## 11. Hardware

| Component | Value |
|-----------|-------|
| GPU | NVIDIA RTX 5060 8GB |
| XGBoost | GPU (cuda) |
| LR/RF | CPU |

## 12. Limitations

1. 0.92 unreachable with this data quality
2. Proxy target has inherent noise ceiling
3. PDE/DME/HHA/SNF/HOSPICE features aggregated at beneficiary-year level
4. Small absolute positive counts limit statistical power
5. Validation prevalence shift (0.6% vs 1.0%) affects weight selection
