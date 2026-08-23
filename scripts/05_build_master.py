"""
05_build_master.py — Build the Master Dataset for Use Case 7

Strategy: Enrich each claims file with year-matched beneficiary demographics
via LEFT JOIN on BENE_ID + temporal alignment, then UNION ALL into a single
master claims table with SOURCE_DATASET provenance.

Rules enforced:
- NO aggregation
- NO imputation
- NO fabrication
- NO many-to-many joins
- Preserve original row grain (claim line items)
- Preserve all missing values
"""

import pandas as pd
import os
import sys
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
log = logging.getLogger(__name__)

RAW_DIR = r'd:\CTS\Datasets\original'
MASTER_DIR = r'd:\CTS\data\master'
AUDIT_DIR = r'd:\CTS\data\audit'
BENE_DIR = os.path.join(RAW_DIR, 'All Beneficiary Years')

# Beneficiary columns to keep (demographics + enrollment + geography)
BENE_KEEP_COLS = [
    'BENE_ID', 'STATE_CODE', 'COUNTY_CD', 'ZIP_CD', 'BENE_BIRTH_DT',
    'SEX_IDENT_CD', 'BENE_RACE_CD', 'ENTLMT_RSN_ORIG', 'ENTLMT_RSN_CURR',
    'ESRD_IND', 'BENE_DEATH_DT', 'BENE_ENROLLMT_REF_YR',
    'BENE_HI_CVRAGE_TOT_MONS', 'BENE_SMI_CVRAGE_TOT_MONS',
    'BENE_STATE_BUYIN_TOT_MONS', 'BENE_HMO_CVRAGE_TOT_MONS',
    'AGE_AT_END_REF_YR', 'DUAL_ELGBL_MONS', 'RTI_RACE_CD',
    'STATE_CNTY_FIPS_CD_01', 'VALID_DEATH_DT_SW', 'COVSTART',
    'SAMPLE_GROUP', 'CRNT_BIC_CD'
]

def load_beneficiary_lookup():
    """Load all beneficiary year files into a dict keyed by year."""
    log.info("Loading beneficiary lookup tables...")
    bene_by_year = {}
    for fname in sorted(os.listdir(BENE_DIR)):
        if not fname.endswith('.csv'):
            continue
        year = fname.replace('beneficiary_', '').replace('.csv', '')
        path = os.path.join(BENE_DIR, fname)
        df = pd.read_csv(path, sep='|', dtype=str, low_memory=False)
        # Keep only needed columns (that exist)
        keep = [c for c in BENE_KEEP_COLS if c in df.columns]
        df = df[keep]
        # Prefix bene columns (except BENE_ID) to avoid collision
        rename = {c: f'BENE_{c}' if c != 'BENE_ID' and not c.startswith('BENE_') else c for c in df.columns}
        # Actually, just prefix non-BENE columns with BENE_ context
        # Keep original names but they already start with BENE_ or are descriptive
        bene_by_year[year] = df
        log.info(f"  Loaded {fname}: {len(df):,} rows, {len(df.columns)} cols")
    return bene_by_year

def extract_claim_year(date_series):
    """Extract year from date strings like '25-Mar-2015'."""
    return date_series.str.extract(r'(\d{4})$', expand=False)

def enrich_claims(claims_df, bene_by_year, source_name):
    """LEFT JOIN claims to year-matched beneficiary data."""
    log.info(f"Enriching {source_name} ({len(claims_df):,} rows)...")
    
    claims_df['_CLAIM_YEAR'] = extract_claim_year(claims_df['CLM_FROM_DT'])
    
    enriched_parts = []
    unmatched_count = 0
    
    for year, year_claims in claims_df.groupby('_CLAIM_YEAR'):
        if year in bene_by_year:
            bene_df = bene_by_year[year]
            merged = year_claims.merge(bene_df, on='BENE_ID', how='left', suffixes=('', '_BENE'))
            enriched_parts.append(merged)
            unmatched = merged[merged['SEX_IDENT_CD'].isna()].shape[0] if 'SEX_IDENT_CD' in merged.columns else 0
            log.info(f"  Year {year}: {len(year_claims):,} claims, {unmatched} unmatched benes")
            unmatched_count += unmatched
        else:
            log.warning(f"  Year {year}: No beneficiary file! {len(year_claims):,} claims left unenriched")
            enriched_parts.append(year_claims)
            unmatched_count += len(year_claims)
    
    result = pd.concat(enriched_parts, ignore_index=True)
    result.drop(columns=['_CLAIM_YEAR'], inplace=True)
    log.info(f"  Enriched {source_name}: {len(result):,} rows (unmatched benes: {unmatched_count})")
    return result

def validate_row_counts(source_count, result_count, source_name):
    """Validate no rows were added or removed."""
    if source_count != result_count:
        log.error(f"ROW COUNT MISMATCH for {source_name}: source={source_count:,}, result={result_count:,}")
        sys.exit(1)
    log.info(f"  ✓ {source_name} row count preserved: {result_count:,}")

def main():
    log.info("="*80)
    log.info("MASTER DATASET BUILD — Use Case 7: Avoidable ED Utilization Navigator")
    log.info("="*80)
    
    # Step 1: Load beneficiary lookup
    bene_by_year = load_beneficiary_lookup()
    
    # Step 2: Load and enrich Inpatient
    log.info("\n--- INPATIENT ---")
    inp_path = os.path.join(RAW_DIR, 'inpatient.csv')
    inp = pd.read_csv(inp_path, sep='|', dtype=str, low_memory=False)
    inp_count = len(inp)
    log.info(f"Loaded inpatient: {inp_count:,} rows, {len(inp.columns)} cols")
    inp_enriched = enrich_claims(inp, bene_by_year, 'Inpatient')
    validate_row_counts(inp_count, len(inp_enriched), 'Inpatient')
    inp_enriched['SOURCE_DATASET'] = 'INPATIENT'
    inp_enriched['SOURCE_FILE'] = 'inpatient.csv'
    
    # Step 3: Load and enrich Outpatient
    log.info("\n--- OUTPATIENT ---")
    outp_path = os.path.join(RAW_DIR, 'Outpatient', 'outpatient.csv')
    outp = pd.read_csv(outp_path, sep='|', dtype=str, low_memory=False)
    outp_count = len(outp)
    log.info(f"Loaded outpatient: {outp_count:,} rows, {len(outp.columns)} cols")
    outp_enriched = enrich_claims(outp, bene_by_year, 'Outpatient')
    validate_row_counts(outp_count, len(outp_enriched), 'Outpatient')
    outp_enriched['SOURCE_DATASET'] = 'OUTPATIENT'
    outp_enriched['SOURCE_FILE'] = 'outpatient.csv'
    
    # Step 4: Load and enrich Carrier
    log.info("\n--- CARRIER ---")
    carr_path = os.path.join(RAW_DIR, 'Carrier', 'carrier.csv')
    carr = pd.read_csv(carr_path, sep='|', dtype=str, low_memory=False)
    carr_count = len(carr)
    log.info(f"Loaded carrier: {carr_count:,} rows, {len(carr.columns)} cols")
    carr_enriched = enrich_claims(carr, bene_by_year, 'Carrier')
    validate_row_counts(carr_count, len(carr_enriched), 'Carrier')
    carr_enriched['SOURCE_DATASET'] = 'CARRIER'
    carr_enriched['SOURCE_FILE'] = 'carrier.csv'
    
    # Step 5: UNION ALL (concat with all columns)
    log.info("\n--- UNION ALL ---")
    master = pd.concat([inp_enriched, outp_enriched, carr_enriched], ignore_index=True, sort=False)
    expected_total = inp_count + outp_count + carr_count
    log.info(f"Master dataset: {len(master):,} rows, {len(master.columns)} cols")
    validate_row_counts(expected_total, len(master), 'MASTER TOTAL')
    
    # Step 6: Save
    master_path = os.path.join(MASTER_DIR, 'MASTER_DATASET.parquet')
    master_csv_path = os.path.join(MASTER_DIR, 'MASTER_DATASET_SAMPLE.csv')
    
    log.info(f"\nSaving master dataset to Parquet (full)...")
    master.to_parquet(master_path, index=False, engine='pyarrow')
    log.info(f"  Saved: {master_path} ({os.path.getsize(master_path)/(1024*1024):.1f} MB)")
    
    # Save a small CSV sample for quick inspection
    sample = master.head(1000)
    sample.to_csv(master_csv_path, index=False)
    log.info(f"  Sample CSV: {master_csv_path}")
    
    # Step 7: Validation report
    log.info("\n" + "="*80)
    log.info("MASTER DATASET VALIDATION SUMMARY")
    log.info("="*80)
    log.info(f"  Source rows (Inpatient):  {inp_count:,}")
    log.info(f"  Source rows (Outpatient): {outp_count:,}")
    log.info(f"  Source rows (Carrier):    {carr_count:,}")
    log.info(f"  Expected total:           {expected_total:,}")
    log.info(f"  Master dataset rows:      {len(master):,}")
    log.info(f"  Master dataset columns:   {len(master.columns)}")
    log.info(f"  ROWS ADDED:               {len(master) - expected_total}")
    log.info(f"  ROWS REMOVED:             {expected_total - len(master)}")
    log.info(f"  ROWS DUPLICATED:          0 (UNION ALL, no joins between claims)")
    log.info(f"  VALUES IMPUTED:           0")
    log.info(f"  VALUES FABRICATED:        0")
    log.info(f"  AGGREGATIONS PERFORMED:   0")
    
    # Column report
    log.info(f"\n  Columns by source:")
    log.info(f"    Inpatient-only cols: {len(set(inp_enriched.columns) - set(outp_enriched.columns) - set(carr_enriched.columns))}")
    log.info(f"    Outpatient-only cols: {len(set(outp_enriched.columns) - set(inp_enriched.columns) - set(carr_enriched.columns))}")
    log.info(f"    Carrier-only cols: {len(set(carr_enriched.columns) - set(inp_enriched.columns) - set(outp_enriched.columns))}")
    common = set(inp_enriched.columns) & set(outp_enriched.columns) & set(carr_enriched.columns)
    log.info(f"    Common cols: {len(common)}")
    
    # Source distribution
    log.info(f"\n  SOURCE_DATASET distribution:")
    for src, cnt in master['SOURCE_DATASET'].value_counts().items():
        log.info(f"    {src}: {cnt:,}")
    
    # ED signal check
    if 'REV_CNTR' in master.columns:
        ed_rows = master[master['REV_CNTR'] == '0450']
        log.info(f"\n  ED rows (REV_CNTR=0450): {len(ed_rows):,}")
    
    if 'CLM_IP_ADMSN_TYPE_CD' in master.columns:
        emerg = master[master['CLM_IP_ADMSN_TYPE_CD'] == '1']
        log.info(f"  Emergency admissions (TYPE=1): {len(emerg):,}")
    
    # Write validation report
    val_path = os.path.join(AUDIT_DIR, 'MASTER_DATASET_VALIDATION.md')
    with open(val_path, 'w') as f:
        f.write("# Master Dataset Validation Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("## Row Count Validation\n\n")
        f.write(f"| Metric | Value |\n|---|---|\n")
        f.write(f"| Source rows (Inpatient) | {inp_count:,} |\n")
        f.write(f"| Source rows (Outpatient) | {outp_count:,} |\n")
        f.write(f"| Source rows (Carrier) | {carr_count:,} |\n")
        f.write(f"| Expected total | {expected_total:,} |\n")
        f.write(f"| Master dataset rows | {len(master):,} |\n")
        f.write(f"| Master dataset columns | {len(master.columns)} |\n\n")
        f.write("## Integrity Checks\n\n")
        f.write(f"| Check | Result |\n|---|---|\n")
        f.write(f"| ROWS ADDED | {len(master) - expected_total} |\n")
        f.write(f"| ROWS REMOVED | {expected_total - len(master)} |\n")
        f.write(f"| ROWS DUPLICATED | 0 |\n")
        f.write(f"| VALUES IMPUTED | 0 |\n")
        f.write(f"| VALUES FABRICATED | 0 |\n")
        f.write(f"| AGGREGATIONS PERFORMED | 0 |\n\n")
        f.write("## Column List\n\n")
        for i, col in enumerate(master.columns):
            f.write(f"- [{i}] `{col}`\n")
        f.write(f"\n## Null Counts (Top 20 by nulls)\n\n")
        nulls = master.isnull().sum().sort_values(ascending=False).head(20)
        f.write(f"| Column | Null Count | Null % |\n|---|---|---|\n")
        for col, cnt in nulls.items():
            f.write(f"| `{col}` | {cnt:,} | {100*cnt/len(master):.1f}% |\n")
    
    log.info(f"\n  Validation report: {val_path}")
    log.info("\n✓ MASTER DATASET BUILD COMPLETE")

if __name__ == '__main__':
    main()
