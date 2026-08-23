"""
etl_claims_to_journey.py — Claims → Patient Journey Event Transformation

Reads the existing raw CMS claims master dataset (Parquet) and transforms
relevant claims into normalized patient journey events.

Rules:
  - Does NOT delete or modify the raw claims dataset
  - Does NOT copy every raw column — extracts clinically relevant event data
  - Preserves claim_id traceability back to raw data
  - Idempotent — safe to rerun (checks for existing claim_id before insert)
  - Does NOT fabricate events

Supported transformations:
  RAW INPATIENT + REV_CNTR=0450 → ED_VISIT
  RAW INPATIENT (emergency admission) → INPATIENT_ADMISSION
  RAW OUTPATIENT → OUTPATIENT_VISIT
  RAW CARRIER → PRIMARY_CARE_VISIT or SPECIALIST_VISIT
"""

import pandas as pd
import numpy as np
import json
import os
import sys
import time
import logging
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
import patient_journey_db as db

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
MASTER_PARQUET = ROOT / "Datasets" / "master" / "MASTER_DATASET.parquet"
if not MASTER_PARQUET.exists():
    MASTER_PARQUET = ROOT / "data_integration_v2" / "master" / "MASTER_DATASET_V2.parquet"
V2_TEST = ROOT / "ML_V2" / "data" / "prepared" / "test.parquet"
V2_PREDS = ROOT / "ML_V2" / "predictions" / "final_test_predictions.csv"
V2_PROFILE = ROOT / "ML_V2" / "data" / "metadata" / "dataset_profile.json"

# AHRQ PQE ICD-10 code prefixes (same as ML V2 pipeline)
PQE_CODES = [
    'K00','K01','K02','K03','K04','K05','K06','K08','K09','K11','K12','K13','K14',
    'E10','E11','E12','E13','J40','J41','J42','J43','J44','J47',
    'I10','I11','I12','I13','I50','J45','N10','N30','L03','E86','K35','M54'
]

CONDITIONS_MAP = {
    "has_diabetes": "Diabetes", "has_copd": "COPD", "has_chf": "CHF",
    "has_htn": "HTN", "has_asthma": "Asthma", "has_ckd": "CKD"
}

FIRST = ["Maya","Robert","Elena","James","Aisha","Samuel","Linda","Carlos","Grace","Thomas",
         "Patricia","David","Maria","William","Jennifer","Richard","Susan","Joseph","Margaret","Charles"]
LAST = ["Thompson","Chen","Rodriguez","Wilson","Patel","Brooks","Garcia","Martinez","Anderson","Taylor",
        "Thomas","Jackson","White","Harris","Martin","Clark","Lewis","Robinson","Walker","Young"]


def _safe_float(val) -> float:
    if pd.isna(val): return 0.0
    if isinstance(val, (int, float, np.integer, np.floating)): return float(val)
    if isinstance(val, str):
        if val.upper() in ('Y', 'YES', 'TRUE', '1'): return 1.0
        if val.upper() in ('N', 'NO', 'FALSE', '0', ''): return 0.0
        try: return float(val)
        except ValueError: return 0.0
    return 0.0


def _safe_int(val, default=0):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return default
    try: return int(float(val))
    except: return default


def _risk_level(score: float) -> str:
    if score > 0.8: return "High"
    if score > 0.6: return "Medium"
    return "Low"


def _continuity_label(bice: float) -> str:
    if bice > 0.6: return "Stable"
    if bice > 0.3: return "Moderate"
    return "Fragmented"


def _patient_conditions(row) -> str:
    conds = [v for k, v in CONDITIONS_MAP.items() if _safe_float(row.get(k, 0)) == 1]
    return ", ".join(conds) if conds else "None identified"


def _is_pqe(dx_code: str) -> bool:
    """Check if a diagnosis code is an AHRQ PQE indicator."""
    if not dx_code or pd.isna(dx_code):
        return False
    return dx_code[:3] in PQE_CODES or dx_code[:4] in PQE_CODES


def _extract_diagnosis_codes(row, prefix='ICD_DGNS_CD', max_n=10) -> list:
    """Extract non-null diagnosis codes from a claim row."""
    codes = []
    if 'PRNCPAL_DGNS_CD' in row and not pd.isna(row.get('PRNCPAL_DGNS_CD')):
        codes.append(str(row['PRNCPAL_DGNS_CD']))
    for i in range(1, max_n + 1):
        col = f"{prefix}{i}"
        if col in row and not pd.isna(row.get(col)):
            codes.append(str(row[col]))
    return list(set(codes))  # deduplicate


def _extract_procedure_codes(row, max_n=6) -> list:
    """Extract non-null procedure codes from a claim row."""
    codes = []
    for i in range(1, max_n + 1):
        col = f"ICD_PRCDR_CD{i}"
        if col in row and not pd.isna(row.get(col)):
            codes.append(str(row[col]))
    return list(set(codes))


def classify_claim_event(row) -> tuple:
    """
    Classify a raw claim into an event_type and title.
    Returns (event_type, title, description).
    """
    source = str(row.get('SOURCE_DATASET', ''))
    rev_cntr = str(row.get('REV_CNTR', ''))
    adm_type = str(row.get('CLM_IP_ADMSN_TYPE_CD', ''))
    principal_dx = str(row.get('PRNCPAL_DGNS_CD', ''))
    place_of_svc = str(row.get('LINE_PLACE_OF_SRVC_CD', ''))

    if source == 'INPATIENT':
        if rev_cntr == '0450':
            is_pqe = _is_pqe(principal_dx)
            pqe_label = " (PQE-preventable)" if is_pqe else ""
            return (
                "ED_VISIT",
                f"Emergency Department Visit{pqe_label}",
                f"ED encounter. Principal Dx: {principal_dx}{pqe_label}."
            )
        elif adm_type == '1':  # Emergency admission
            return (
                "INPATIENT_ADMISSION",
                "Emergency Inpatient Admission",
                f"Emergency hospital admission. Principal Dx: {principal_dx}."
            )
        else:
            return (
                "INPATIENT_ADMISSION",
                "Inpatient Hospital Stay",
                f"Inpatient admission. Principal Dx: {principal_dx}."
            )
    elif source == 'OUTPATIENT':
        if rev_cntr.startswith('045'):
            is_pqe = _is_pqe(principal_dx)
            pqe_label = " (PQE)" if is_pqe else ""
            return (
                "ED_VISIT",
                f"Outpatient ED Visit{pqe_label}",
                f"ED treat-and-release visit. Principal Dx: {principal_dx}{pqe_label}."
            )
        else:
            return (
                "OUTPATIENT_VISIT",
                "Outpatient Visit",
                f"Outpatient facility encounter. Principal Dx: {principal_dx}."
            )
    elif source == 'CARRIER':
        # Place of service: 11=Office, 22=Outpatient, 23=ED
        if place_of_svc == '23':
            return (
                "ED_VISIT",
                "Physician ED Encounter",
                f"Physician service in Emergency Department. Dx: {principal_dx}."
            )
        elif place_of_svc == '11':
            return (
                "PRIMARY_CARE_VISIT",
                "Office Visit",
                f"Physician office visit. Dx: {principal_dx}."
            )
        else:
            return (
                "SPECIALIST_VISIT",
                "Specialist/Other Visit",
                f"Professional service encounter. Dx: {principal_dx}."
            )
    else:
        return (
            "OTHER",
            f"{source} Claim",
            f"Claim from {source}. Dx: {principal_dx}."
        )


def run_etl():
    """Main ETL: load raw claims, transform to patient journey events, persist."""
    log.info("=" * 80)
    log.info("CAREPATH ETL: Claims → Patient Journey Events")
    log.info("=" * 80)

    # ── Step 0: Initialize DB ────────────────────────────────────────────────
    db.reset_db()
    db.init_db()

    # ── Step 1: Load ML V2 test data (scored patients) ───────────────────────
    log.info("Loading ML V2 test data and predictions...")
    test_df = pd.read_parquet(V2_TEST)
    preds_df = pd.read_csv(V2_PREDS)
    with open(V2_PROFILE) as f:
        profile = json.load(f)
        FEATURES = profile["features"]

    test_df["BENE_ID"] = test_df["BENE_ID"].astype(str)
    preds_df["BENE_ID"] = preds_df["BENE_ID"].astype(str)
    patients_df = test_df.merge(preds_df[["BENE_ID", "y_true", "ensemble"]], on="BENE_ID", how="inner")
    patients_df = patients_df.sort_values("ensemble", ascending=False).reset_index(drop=True)
    log.info(f"  {len(patients_df):,} scored patients loaded")

    # ── Step 2: Upsert patient records ───────────────────────────────────────
    log.info("Upserting patient records...")
    np.random.seed(42)
    demo_phone = os.environ.get("DEMO_SMS_PHONE_NUMBER", "7598070435").strip()
    digits_d = ''.join(c for c in demo_phone if c.isdigit())
    demo_masked = "*" * max(0, len(digits_d) - 4) + digits_d[-4:] if len(digits_d) >= 4 else "******0435"

    bene_to_pid = {}  # BENE_ID -> patient_id mapping

    for i, row in patients_df.iterrows():
        bene = str(row["BENE_ID"])
        pid = f"P-{1000 + i}"
        name = f"{FIRST[i % len(FIRST)]} {LAST[i % len(LAST)]}"
        score = float(row["ensemble"])
        age = _safe_int(row.get("AGE_AT_END_REF_YR"), 65)
        conds = _patient_conditions(row)
        bice = float(row.get("bice_boxerman", 0.5))
        cont = _continuity_label(bice)
        sex = str(row.get("SEX_IDENT_CD", ""))
        race = str(row.get("BENE_RACE_CD", ""))

        if i == 0:
            p_phone = demo_phone
            p_masked = demo_masked
            is_demo = True
            # Force Maya Thompson identity for P-1000
            name = "Maya Thompson"
        else:
            p_phone = f"+155501{i:04d}"
            p_masked = f"******{i:04d}"
            is_demo = False

        bene_to_pid[bene] = pid

        db.upsert_patient(
            patient_id=pid, bene_id=bene, name=name, age=age, sex=sex, race=race,
            conditions=conds, continuity=cont, current_risk=round(score, 4),
            current_level=_risk_level(score), status="Active",
            phone_number=p_phone, phone_masked=p_masked, is_demo_target=is_demo
        )

        # Save initial feature snapshot
        features = {f: _safe_float(row.get(f, 0)) for f in FEATURES}
        snap_id = db.save_feature_snapshot(pid, features, trigger="INITIAL")

        # Save initial prediction (the original ML V2 score)
        db.save_prediction(pid, round(score, 4), _risk_level(score),
                           trigger="INITIAL", snapshot_id=snap_id)

    log.info(f"  {len(bene_to_pid):,} patients upserted")

    # ── Step 3: Load raw master claims and transform to journey events ───────
    if MASTER_PARQUET.exists():
        log.info(f"Loading raw master claims from {MASTER_PARQUET}...")
        t0 = time.time()

        # Only read the columns we actually need (avoids OOM on 331-col dataset)
        needed_cols = ['BENE_ID', 'CLM_ID', 'CLM_FROM_DT', 'SOURCE_DATASET',
                       'PRNCPAL_DGNS_CD', 'REV_CNTR', 'AT_PHYSN_NPI', 'PRVDR_NUM',
                       'CLM_IP_ADMSN_TYPE_CD', 'LINE_PLACE_OF_SRVC_CD', 'PRF_PHYSN_NPI',
                       'ICD_DGNS_CD1', 'ICD_DGNS_CD2', 'ICD_DGNS_CD3', 'ICD_DGNS_CD4',
                       'ICD_DGNS_CD5', 'ICD_PRCDR_CD1', 'ICD_PRCDR_CD2', 'ICD_PRCDR_CD3']
        # Read only columns that exist in the parquet
        import pyarrow.parquet as pq
        pf = pq.ParquetFile(str(MASTER_PARQUET))
        available = set(pf.schema.names)
        read_cols = [c for c in needed_cols if c in available]

        master = pd.read_parquet(MASTER_PARQUET, columns=read_cols)
        log.info(f"  {len(master):,} raw claim lines loaded ({len(read_cols)} cols) in {time.time()-t0:.1f}s")

        # Parse dates
        master['CLM_DATE'] = pd.to_datetime(master['CLM_FROM_DT'], format='%d-%b-%Y', errors='coerce')

        # Filter to only our scored patients
        master['BENE_ID'] = master['BENE_ID'].astype(str)
        scored_benes = set(bene_to_pid.keys())
        relevant = master[master['BENE_ID'].isin(scored_benes)]
        log.info(f"  {len(relevant):,} claims belong to scored patients")
        del master  # free memory

        # Deduplicate to claim-level (not line-level) for journey events
        claims = relevant.drop_duplicates(subset=['CLM_ID'], keep='first')
        log.info(f"  {len(claims):,} unique claims (deduplicated from line items)")
        del relevant

        # Build event list in memory (fast), then bulk-insert
        log.info("  Transforming claims to journey events...")
        t1 = time.time()
        events_batch = []
        skipped = 0

        for _, row in claims.iterrows():
            bene = str(row['BENE_ID'])
            pid = bene_to_pid.get(bene)
            if not pid:
                skipped += 1
                continue

            clm_id = str(row['CLM_ID'])

            # Parse date
            clm_date = row.get('CLM_DATE')
            if pd.isna(clm_date):
                event_date = str(row.get('CLM_FROM_DT', ''))
            else:
                event_date = clm_date.isoformat()

            # Classify
            event_type, title, description = classify_claim_event(row)

            # Extract codes
            dx_codes = _extract_diagnosis_codes(row)
            px_codes = _extract_procedure_codes(row)

            # Provider
            npi = str(row.get('AT_PHYSN_NPI', '')) or str(row.get('PRF_PHYSN_NPI', ''))
            facility = str(row.get('PRVDR_NUM', ''))

            events_batch.append({
                "patient_id": pid,
                "event_date": event_date,
                "event_type": event_type,
                "event_source": "CLAIMS",
                "title": title,
                "description": description,
                "event_status": "Claims-derived",
                "claim_id": clm_id,
                "diagnosis_codes": dx_codes if dx_codes else None,
                "procedure_codes": px_codes if px_codes else None,
                "provider_npi": npi if npi and npi != 'nan' else None,
                "facility_id": facility if facility and facility != 'nan' else None
            })

        log.info(f"  Prepared {len(events_batch):,} events in {time.time()-t1:.1f}s, bulk inserting...")
        del claims

        t2 = time.time()
        inserted = db.bulk_insert_journey_events(events_batch, batch_size=10000)
        log.info(f"  Bulk insert complete: {inserted:,} events in {time.time()-t2:.1f}s (skipped {skipped:,} unmapped)")
    else:
        log.warning(f"  Master dataset not found at {MASTER_PARQUET}, skipping claims ETL")

    # ── Step 4: Validation ───────────────────────────────────────────────────
    log.info("\n" + "=" * 80)
    log.info("ETL VALIDATION SUMMARY")
    log.info("=" * 80)
    total_patients = db.get_total_patient_count()
    log.info(f"  Total patients in DB: {total_patients:,}")

    # Sample patient check
    maya = db.get_patient("P-1000")
    if maya:
        log.info(f"  P-1000: {maya['name']}, risk={maya['current_risk']}, level={maya['current_level']}")
        journey_count = db.get_journey_event_count("P-1000")
        log.info(f"  P-1000 journey events: {journey_count}")
        preds = db.get_prediction_history("P-1000", limit=5)
        log.info(f"  P-1000 predictions: {len(preds)}")
        snap = db.get_latest_snapshot("P-1000")
        if snap:
            log.info(f"  P-1000 latest snapshot: {snap['snapshot_ts']}, trigger={snap['trigger']}")

    dist = db.get_risk_distribution()
    log.info(f"  Risk distribution: {dist}")

    log.info("\n✓ ETL COMPLETE")


if __name__ == "__main__":
    run_etl()
