# MASTER DATASET V2 — Validation Report

## V1 vs V2 Comparison

| Property | V1 | V2 | Match |
|----------|-----|-----|-------|
| Rows | 1,754,162 | 1,754,162 | PASSED |
| Columns | 331 | 331 | PASSED |
| File format | Parquet | Parquet | PASSED |

## Validation Checks

| Check | Status |
|-------|--------|
| Row count match (V1 == V2) | **PASSED** |
| Column count match | **PASSED** |
| Grain preserved (claim-line) | **PASSED** |
| No aggregation performed | **PASSED** |
| No imputation performed | **PASSED** |
| No fabricated data | **PASSED** |
| No forced joins | **PASSED** |
| Original values preserved | **PASSED** |
| No row multiplication | **PASSED** |
| No row loss | **PASSED** |

## Reason V2 = V1

All 5 new datasets (PDE, DME, HHA, SNF, HOSPICE) were analyzed and determined to require **SEPARATE** status due to many-to-many cardinality with the master claim-line grain. No valid row-level join exists without aggregation (prohibited) or row multiplication (prohibited).

## Output

- `MASTER_DATASET_V2.parquet` — identical to V1 (1,754,162 rows x 331 cols)
- Location: `data_integration_v2/master/`
