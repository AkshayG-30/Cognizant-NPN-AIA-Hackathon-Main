# MASTER DATASET V2 — Join Decision Report

## Summary

**ALL 5 new datasets must be kept SEPARATE.** No valid row-level join exists without violating the master dataset's claim-line grain.

## Master Dataset V1

- Rows: **1,754,162**
- Grain: Claim-line (one row per revenue center line per claim)
- Sources: INPATIENT (58,066) + OUTPATIENT (575,092) + CARRIER (1,121,004)
- Unique beneficiaries: **8,715**

## New Datasets Analyzed

| Dataset | Rows | Cols | Size | Unique BENE_ID | Overlap | Overlap % | Rows/Bene |
|---------|------|------|------|---------------|---------|-----------|-----------|
| PDE | 515,520 | 36 | 86.8 MB | 7,403 | 7,401 | 100.0% | 69.6 |
| DME | 103,828 | 87 | 36.5 MB | 5,576 | 5,570 | 99.9% | 18.6 |
| HHA | 6,215 | 88 | 2.1 MB | 449 | 449 | 100.0% | 13.8 |
| SNF | 12,548 | 160 | 9.5 MB | 1,466 | 1,461 | 99.7% | 8.6 |
| HOSPICE | 12,107 | 86 | 4.4 MB | 1,086 | 1,081 | 99.5% | 11.1 |

**All files are pipe-delimited (`|`), not comma-separated.**

---

## Per-Dataset Decisions

### PDE (Part D Events)

| Property | Value |
|----------|-------|
| **JOIN POSSIBLE** | NO |
| **DECISION** | **KEEP SEPARATE** |
| **Common Field** | BENE_ID |
| **Overlap** | 7,401 beneficiaries (100%) |
| **Cardinality** | Many-to-many (69.6 PDE rows/bene x ~201 master rows/bene) |
| **Reason** | BENE_ID join would create 69.6 x 201 = ~14,000 row explosion per beneficiary. Master would grow from 1.75M to potentially 100M+ rows. NO AGGREGATION ALLOWED in this phase. |
| **Future Use** | YES — medication adherence features (drug counts, polypharmacy, days supply) via beneficiary-level aggregation in ML pipeline |

### DME (Durable Medical Equipment)

| Property | Value |
|----------|-------|
| **JOIN POSSIBLE** | NO |
| **DECISION** | **KEEP SEPARATE** |
| **Common Field** | BENE_ID + 78 common columns |
| **Overlap** | 5,570 beneficiaries (99.9%) |
| **Cardinality** | Many-to-many (18.6 DME rows/bene) |
| **Reason** | Same many-to-many grain problem. DME claims are a different claim type with their own CLM_ID space (no cross-type CLM_ID matching). |
| **Future Use** | YES — DME utilization features (equipment flags, home-bound indicators) |

### HHA (Home Health Agency)

| Property | Value |
|----------|-------|
| **JOIN POSSIBLE** | NO |
| **DECISION** | **KEEP SEPARATE** |
| **Common Field** | BENE_ID + 85 common columns |
| **Overlap** | 449 beneficiaries (100%) |
| **Cardinality** | Many-to-many (13.8 HHA rows/bene) |
| **Reason** | Many-to-many grain violation. Small overlap (449/8,715 = 5.2% of master benes). |
| **Future Use** | YES — home health utilization flag (binary: has HHA claims) |

### SNF (Skilled Nursing Facility)

| Property | Value |
|----------|-------|
| **JOIN POSSIBLE** | NO |
| **DECISION** | **KEEP SEPARATE** |
| **Common Field** | BENE_ID + 158 common columns |
| **Overlap** | 1,461 beneficiaries (99.7%) |
| **Cardinality** | Many-to-many (8.6 SNF rows/bene) |
| **Reason** | Same many-to-many problem. SNF has the highest column overlap (158/160 match master schema) because both are institutional claims, but the rows are distinct claim events. |
| **Future Use** | YES — SNF utilization, post-acute care transition features |

### HOSPICE

| Property | Value |
|----------|-------|
| **JOIN POSSIBLE** | NO |
| **DECISION** | **KEEP SEPARATE** |
| **Common Field** | BENE_ID + 84 common columns |
| **Overlap** | 1,081 beneficiaries (99.5%) |
| **Cardinality** | Many-to-many (11.1 rows/bene) |
| **Reason** | Many-to-many grain violation. Hospice claims represent a different care setting. |
| **Future Use** | YES — hospice enrollment flag (may indicate end-of-life, affects ED utilization) |

### CDC PLACES

| Property | Value |
|----------|-------|
| **STATUS** | NOT FOUND in datasets directory |
| **DECISION** | N/A — dataset not available |

---

## Why No Joins Were Possible

The fundamental constraint is **grain incompatibility**:

1. The master dataset is at **claim-line grain** (1.75M rows across 8,715 beneficiaries)
2. Every new dataset is also at **claim-line grain** with multiple rows per beneficiary
3. The only common join key is `BENE_ID`
4. A `BENE_ID` join between two many-row-per-bene datasets creates a **Cartesian product** (many-to-many)
5. This would multiply master rows from 1.75M to potentially 100M+
6. **Aggregation is prohibited** in this data engineering phase
7. `CLM_ID` cannot be used cross-dataset because each claim type has its own ID space

This is the correct engineering decision. The new datasets are preserved separately for downstream feature engineering where beneficiary-level aggregation IS permitted.

## MASTER_DATASET_V2

**V2 = V1 (identical)**

- V1 Rows: 1,754,162
- V2 Rows: 1,754,162
- Rows added: 0
- Rows dropped: 0
- Aggregation: 0
- Imputation: 0
- Fabrication: 0
