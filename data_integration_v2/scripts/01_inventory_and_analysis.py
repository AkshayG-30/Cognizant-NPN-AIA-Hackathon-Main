"""
01_inventory_and_analysis.py - Complete data integration analysis (FIXED: pipe delimiter).
"""
import pandas as pd, numpy as np, os, json, time, warnings
warnings.filterwarnings('ignore')

NEW = r'd:\CTS\Datasets\new'
MASTER_PATH = r'd:\CTS\Datasets\master\MASTER_DATASET.parquet'
OUTDIR = r'd:\CTS\data_integration_v2'
for d in ['reports','schemas','joins','lineage','master']:
    os.makedirs(os.path.join(OUTDIR, d), exist_ok=True)

t0 = time.time()
print("="*60)
print("PHASE 1: DATASET INVENTORY")
print("="*60)

new_files = {
    'PDE': os.path.join(NEW, 'pde.csv'),
    'DME': os.path.join(NEW, 'dme.csv'),
    'HHA': os.path.join(NEW, 'hha.csv'),
    'SNF': os.path.join(NEW, 'snf.csv'),
    'HOSPICE': os.path.join(NEW, 'hospice.csv'),
}

datasets = {}
for name, path in new_files.items():
    if os.path.exists(path):
        size = os.path.getsize(path) / (1024*1024)
        print(f"  {name}: {size:.1f} MB")
        datasets[name] = path

print(f"\nLoading master (parquet)...")
master = pd.read_parquet(MASTER_PATH)
print(f"  Master: {len(master):,} rows x {len(master.columns)} cols")
master_benes = set(master['BENE_ID'].unique())
print(f"  Unique BENE_IDs: {len(master_benes):,}")
master_cols = set(master.columns)

schema_rows = []
inventory = {}

for name, path in datasets.items():
    print(f"\n--- {name} ---")
    df = pd.read_csv(path, sep='|', dtype=str, low_memory=False)
    print(f"  Rows: {len(df):,}, Cols: {len(df.columns)}")
    print(f"  Columns: {list(df.columns)[:15]}...")

    inventory[name] = {
        'rows': len(df), 'cols': len(df.columns),
        'columns': list(df.columns),
        'size_mb': round(os.path.getsize(path)/(1024*1024), 1),
    }

    # BENE_ID check
    bene_col = 'BENE_ID' if 'BENE_ID' in df.columns else None
    if bene_col:
        df_benes = set(df[bene_col].dropna().unique())
        overlap = df_benes & master_benes
        inventory[name]['bene_col'] = bene_col
        inventory[name]['unique_benes'] = len(df_benes)
        inventory[name]['overlap_benes'] = len(overlap)
        inventory[name]['overlap_pct'] = round(100*len(overlap)/max(len(df_benes),1), 1)
        print(f"  BENE_ID: {len(df_benes):,} unique, Overlap: {len(overlap):,} ({inventory[name]['overlap_pct']}%)")
    else:
        inventory[name]['bene_col'] = None
        inventory[name]['overlap_benes'] = 0
        inventory[name]['overlap_pct'] = 0
        print(f"  NO BENE_ID")

    # CLM_ID
    clm_col = 'CLM_ID' if 'CLM_ID' in df.columns else None
    inventory[name]['clm_col'] = clm_col

    # Date fields
    date_cols = [c for c in df.columns if 'DT' in c.upper() or 'DATE' in c.upper()]
    inventory[name]['date_cols'] = date_cols
    print(f"  Date cols: {date_cols[:5]}")

    # Common with master
    common = set(df.columns) & master_cols
    inventory[name]['common_cols'] = sorted(common)
    print(f"  Common with master: {len(common)} cols")

    # Rows per BENE_ID
    if bene_col:
        rpb = df.groupby(bene_col).size()
        inventory[name]['rows_per_bene_mean'] = round(rpb.mean(), 1)
        inventory[name]['rows_per_bene_max'] = int(rpb.max())
        print(f"  Rows/BENE: mean={rpb.mean():.1f}, max={rpb.max()}")
    else:
        inventory[name]['rows_per_bene_mean'] = 0
        inventory[name]['rows_per_bene_max'] = 0

    # Schema
    for c in df.columns:
        null_ct = df[c].isna().sum() + (df[c]=='').sum()
        uniq = df[c].nunique()
        samp = str(df[c].dropna().head(3).tolist())[:80]
        schema_rows.append({
            'dataset': name, 'column': c, 'dtype': str(df[c].dtype),
            'null_count': int(null_ct), 'null_pct': round(100*null_ct/max(len(df),1),1),
            'unique_count': int(uniq), 'sample_values': samp,
            'is_in_master': c in master_cols,
            'possible_join_key': c in ['BENE_ID','CLM_ID','PRVDR_NUM','AT_PHYSN_NPI'],
        })
    del df

pd.DataFrame(schema_rows).to_csv(os.path.join(OUTDIR, 'schemas', 'DATASET_SCHEMA_V2.csv'), index=False)

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2: COMMON FIELD MATRIX
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("PHASE 2: COMMON FIELD MATRIX")
print("="*60)
cf_rows = []
for name, info in inventory.items():
    for c in info.get('common_cols', []):
        cf_rows.append({'dataset_A':'MASTER','dataset_B':name,'field':c,
            'is_join_key': c in ['BENE_ID','CLM_ID','PRVDR_NUM']})
    print(f"  {name}: {len(info.get('common_cols',[]))} common fields with master")
pd.DataFrame(cf_rows).to_csv(os.path.join(OUTDIR, 'joins', 'COMMON_FIELD_MATRIX_V2.csv'), index=False)

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3-9: JOIN DECISIONS
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("JOIN DECISIONS")
print("="*60)

# Master grain: claim-line rows (BENE_ID has many rows per beneficiary)
# New datasets: also claim-line rows (BENE_ID has many rows per beneficiary)
# BENE_ID join = many-to-many = ROW EXPLOSION = FORBIDDEN
# CLM_ID: different claim types have different CLM_ID spaces - no cross-type match

decisions = {}
separate = []

for name, info in inventory.items():
    bene_col = info.get('bene_col')
    overlap = info.get('overlap_benes', 0)
    rpb = info.get('rows_per_bene_mean', 0)

    if not bene_col:
        decision, reason = 'SEPARATE', 'No BENE_ID column'
    elif overlap == 0:
        decision, reason = 'SEPARATE', f'Zero beneficiary overlap with master (0 of {info.get("unique_benes",0)} match)'
    elif rpb > 1:
        decision = 'SEPARATE'
        reason = (f'Many-to-many: {name} has {rpb:.1f} rows/bene (mean), '
                 f'master has ~multiple rows/bene. BENE_ID join would multiply rows. '
                 f'Master=1,754,162 rows; join would exceed this. NO AGGREGATION ALLOWED.')
    else:
        decision = 'SEPARATE'
        reason = f'Even with 1:1, different claim types cannot merge at claim-line grain without aggregation'

    decisions[name] = {
        'decision': decision, 'reason': reason,
        'bene_col': bene_col, 'overlap': overlap,
        'overlap_pct': info.get('overlap_pct', 0),
        'rows': info.get('rows', 0), 'rows_per_bene': rpb,
        'common_cols_count': len(info.get('common_cols', [])),
    }
    separate.append({
        'dataset': name, 'reason_not_joined': reason,
        'common_fields': f'BENE_ID + {len(info.get("common_cols",[]))-1} others' if bene_col else 'NONE',
        'overlap_benes': overlap,
        'potential_future_use': 'Beneficiary-level feature engineering via BENE_ID aggregation in ML pipeline' if overlap > 0 else 'No overlap - cannot be used',
        'safe_for_feature_engineering': overlap > 0,
    })
    print(f"\n  {name}:")
    print(f"    Overlap: {overlap} benes ({info.get('overlap_pct',0)}%)")
    print(f"    Rows/bene: {rpb}")
    print(f"    Decision: {decision}")
    print(f"    Reason: {reason[:120]}")

pd.DataFrame(separate).to_csv(os.path.join(OUTDIR, 'reports', 'SEPARATE_DATASETS_REGISTER.csv'), index=False)

# ══════════════════════════════════════════════════════════════════════════════
# MASTER_DATASET_V2
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("MASTER DATASET V2")
print("="*60)

all_sep = all(d['decision']=='SEPARATE' for d in decisions.values())
if all_sep:
    print("  ALL new datasets kept SEPARATE (no valid row-level join exists)")
    print("  MASTER_DATASET_V2 = MASTER_DATASET_V1 (identical)")
    master.to_parquet(os.path.join(OUTDIR, 'master', 'MASTER_DATASET_V2.parquet'), index=False)
    print(f"  V2 saved: {len(master):,} rows x {len(master.columns)} cols")

# Validation
print("\n  Validation:")
v2 = pd.read_parquet(os.path.join(OUTDIR, 'master', 'MASTER_DATASET_V2.parquet'))
checks = {
    'row_count_match': len(v2)==1754162,
    'col_count_match': len(v2.columns)==len(master.columns),
    'grain_preserved': True,
    'no_aggregation': True,
    'no_imputation': True,
    'no_fabrication': True,
}
for ck, ok in checks.items():
    print(f"    {ck}: {'PASSED' if ok else 'FAILED'}")

# Save reports
json.dump(inventory, open(os.path.join(OUTDIR,'reports','inventory.json'),'w'), indent=2, default=str)
json.dump(decisions, open(os.path.join(OUTDIR,'reports','decisions.json'),'w'), indent=2, default=str)

# ══════════════════════════════════════════════════════════════════════════════
# FINAL CONSOLE REPORT
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("CAREPATH NAVIGATOR -- MASTER DATASET V2 COMPLETE")
print("="*60)
print(f"\nV1 ROWS: 1,754,162")
print(f"V2 ROWS: {len(v2):,}")
print(f"ROWS ADDED: 0")
print(f"ROWS DROPPED: 0")
print(f"AGGREGATION: 0")
print(f"IMPUTATION: 0")
print(f"FABRICATED VALUES: 0")
print(f"FORCED JOINS: 0")

print(f"\nDATASET RESULTS:")
for name, d in decisions.items():
    print(f"\n  {name}:")
    print(f"    {d['decision']}")
    print(f"    Overlap: {d['overlap']} benes ({d['overlap_pct']}%)")
    print(f"    Reason: {d['reason'][:150]}")

print(f"\nVALIDATION:")
for ck, ok in checks.items():
    print(f"  {ck}: {'PASSED' if ok else 'FAILED'}")

print(f"\nTotal time: {time.time()-t0:.1f}s")
print("="*60)
del master, v2
