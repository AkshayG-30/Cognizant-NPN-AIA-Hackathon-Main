# Contribution Artifact: Data Analyst / Data Engineer

## Role Overview
**Role:** Data Analyst / Data Engineer
**Domain:** Data Pipelines, ETL, & Master Dataset Generation
**Primary Focus:** Designing robust Extract, Transform, and Load (ETL) pipelines to ingest raw CMS claims data, generate model-ready master datasets, and translate billing codes into human-readable patient journey events.

## Key Responsibilities & Elaborated Technical Contributions

### 1. Master Dataset Construction (ML Readiness)
* **Evidence:** `scripts/05_build_master.py`
* **Elaborated Details:** You architected the foundational data pipeline that powers the entire CarePath system. Dealing with millions of rows of raw Medicare/CMS claims data (Inpatient, Outpatient, and Carrier datasets), you built an optimized ETL script (`05_build_master.py`). You successfully joined disparate claims files with Beneficiary demographics using `BENE_ID` and temporal year-matching. You strictly enforced data integrity rules: absolutely no data imputation, no row fabrication, and the preservation of original claim-line grains. To handle memory constraints and ensure rapid downstream processing by the ML team, you converted the final massive output into compressed, columnar Parquet format (`MASTER_DATASET.parquet`).

### 2. Claims to Journey Event ETL Transformation
* **Evidence:** `backend/etl_claims_to_journey.py`
* **Elaborated Details:** Raw claims data is incomprehensible to clinical end-users. You wrote the pipeline that reads the massive Parquet master dataset and transforms raw billing lines into standardized, human-readable "Patient Journey Events." You implemented complex business logic to classify encounters—for example, correctly identifying an Emergency Department visit by parsing `REV_CNTR=0450` or detecting emergency admissions via `CLM_IP_ADMSN_TYPE_CD`. This script normalizes the data and bulk-inserts it into the application database, creating the longitudinal history visible on the frontend.

### 3. AHRQ PQE Medical Logic Mapping
* **Evidence:** `backend/etl_claims_to_journey.py` (`_is_pqe` function)
* **Elaborated Details:** To bridge the gap between raw data and actionable clinical insights, you implemented logic based on the Agency for Healthcare Research and Quality (AHRQ) Prevention Quality Indicators (PQE). You mapped hundreds of raw ICD-10 diagnosis codes to specific ambulatory-sensitive condition flags (e.g., mapping specific code prefixes to COPD, Diabetes, or Heart Failure). This logic directly enables the system to identify which ED visits were potentially avoidable, forming the core value proposition of the CarePath platform.

### 4. Rigorous Data Auditing & Profiling
* **Evidence:** `scripts/00_row_counts.py`, `scripts/01_deep_analysis.py`, Validation Report Generation
* **Elaborated Details:** Data leakage and join-explosion are fatal flaws in healthcare ML. You developed a suite of analytical scripts to validate row counts at every step of the pipeline, ensuring that a LEFT JOIN never inadvertently duplicated claims. Your scripts automatically generate detailed Markdown validation reports, documenting null percentages, column distributions, and row integrity checks. This transparency guaranteed that the datasets handed off to the ML Engineer were mathematically sound and scientifically defensible.

## Technologies Utilized
- **Pandas:** The primary engine for large-scale DataFrame manipulation, filtering, and complex multi-table joins.
- **PyArrow & Parquet:** Utilized for high-performance, compressed columnar data storage, significantly reducing disk I/O and memory usage.
- **Python Logging:** Implemented comprehensive, timestamped terminal logging and file-based validation reporting for ETL auditing.

## Strategic Integration Points
- You are the sole provider of the `MASTER_DATASET.parquet` file, which is absolutely critical for the **ML Engineer** to train the predictive models.
- Your ETL scripts pre-populate the SQLite database managed by the **Backend Developer**, ensuring the frontend has rich, longitudinal patient histories to display upon launch.
