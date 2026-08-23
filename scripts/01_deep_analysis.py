import csv

# 1. Check if beneficiary headers are consistent across years
print("="*80)
print("1. BENEFICIARY HEADER CONSISTENCY CHECK")
print("="*80)
import os
bene_dir = r'd:\CTS\Datasets\original\All Beneficiary Years'
headers = {}
for fname in sorted(os.listdir(bene_dir)):
    path = os.path.join(bene_dir, fname)
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        h = f.readline().strip().split('|')
        headers[fname] = h
        
ref = headers['beneficiary_2015.csv']
for fname, h in headers.items():
    if h == ref:
        print(f"  {fname}: MATCHES 2015 ({len(h)} cols)")
    else:
        print(f"  {fname}: DIFFERS from 2015! ({len(h)} cols)")
        diff_new = set(h) - set(ref)
        diff_missing = set(ref) - set(h)
        if diff_new: print(f"    New cols: {diff_new}")
        if diff_missing: print(f"    Missing cols: {diff_missing}")

# 2. Check BENE_ENROLLMT_REF_YR values in a sample of beneficiary files
print("\n" + "="*80)
print("2. BENE_ENROLLMT_REF_YR VALUES PER FILE")
print("="*80)
for fname in ['beneficiary_2015.csv', 'beneficiary_2020.csv', 'beneficiary_2025.csv']:
    path = os.path.join(bene_dir, fname)
    ref_years = set()
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        header = f.readline().strip().split('|')
        idx = header.index('BENE_ENROLLMT_REF_YR')
        for line in f:
            cols = line.strip().split('|')
            if len(cols) > idx:
                ref_years.add(cols[idx])
    print(f"  {fname}: BENE_ENROLLMT_REF_YR values = {sorted(ref_years)}")

# 3. Check BENE_ID overlap between beneficiary and claims
print("\n" + "="*80)
print("3. BENE_ID OVERLAP ANALYSIS")
print("="*80)
# Get BENE_IDs from beneficiary 2015
bene_ids_2015 = set()
with open(os.path.join(bene_dir, 'beneficiary_2015.csv'), 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    idx = header.index('BENE_ID')
    for line in f:
        cols = line.strip().split('|')
        if len(cols) > idx:
            bene_ids_2015.add(cols[idx])

# Get all BENE_IDs across all bene years
all_bene_ids = set()
for fname in sorted(os.listdir(bene_dir)):
    path = os.path.join(bene_dir, fname)
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        header = f.readline().strip().split('|')
        idx = header.index('BENE_ID')
        for line in f:
            cols = line.strip().split('|')
            if len(cols) > idx:
                all_bene_ids.add(cols[idx])

print(f"  Unique BENE_IDs in 2015: {len(bene_ids_2015):,}")
print(f"  Unique BENE_IDs across all years: {len(all_bene_ids):,}")

# Get BENE_IDs from inpatient
inp_bene_ids = set()
with open(r'd:\CTS\Datasets\original\inpatient.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    idx = header.index('BENE_ID')
    for line in f:
        cols = line.strip().split('|')
        if len(cols) > idx:
            inp_bene_ids.add(cols[idx])

print(f"  Unique BENE_IDs in inpatient: {len(inp_bene_ids):,}")
print(f"  Inpatient BENE_IDs in all_bene: {len(inp_bene_ids & all_bene_ids):,} ({100*len(inp_bene_ids & all_bene_ids)/max(1,len(inp_bene_ids)):.1f}%)")

# Get first 100k BENE_IDs from outpatient for quick overlap
outp_bene_ids = set()
with open(r'd:\CTS\Datasets\original\Outpatient\outpatient.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    idx = header.index('BENE_ID')
    for line in f:
        cols = line.strip().split('|')
        if len(cols) > idx:
            outp_bene_ids.add(cols[idx])

print(f"  Unique BENE_IDs in outpatient: {len(outp_bene_ids):,}")
print(f"  Outpatient BENE_IDs in all_bene: {len(outp_bene_ids & all_bene_ids):,} ({100*len(outp_bene_ids & all_bene_ids)/max(1,len(outp_bene_ids)):.1f}%)")

# Get BENE_IDs from carrier (first 200k lines for speed)
carr_bene_ids = set()
with open(r'd:\CTS\Datasets\original\Carrier\carrier.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    idx = header.index('BENE_ID')
    for line in f:
        cols = line.strip().split('|')
        if len(cols) > idx:
            carr_bene_ids.add(cols[idx])

print(f"  Unique BENE_IDs in carrier: {len(carr_bene_ids):,}")
print(f"  Carrier BENE_IDs in all_bene: {len(carr_bene_ids & all_bene_ids):,} ({100*len(carr_bene_ids & all_bene_ids)/max(1,len(carr_bene_ids)):.1f}%)")

# 4. Check CLM_ID uniqueness in inpatient
print("\n" + "="*80)
print("4. CLM_ID UNIQUENESS (Inpatient)")
print("="*80)
clm_ids = []
with open(r'd:\CTS\Datasets\original\inpatient.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    idx = header.index('CLM_ID')
    for line in f:
        cols = line.strip().split('|')
        if len(cols) > idx:
            clm_ids.append(cols[idx])
print(f"  Total rows: {len(clm_ids):,}")
print(f"  Unique CLM_IDs: {len(set(clm_ids)):,}")
print(f"  Has duplicates: {len(clm_ids) != len(set(clm_ids))}")

# 5. Check REV_CNTR values in inpatient (ED indicator)
print("\n" + "="*80)
print("5. REV_CNTR VALUES (Inpatient) - ED Indicator Check")
print("="*80)
rev_cntr_vals = {}
with open(r'd:\CTS\Datasets\original\inpatient.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    idx = header.index('REV_CNTR')
    for line in f:
        cols = line.strip().split('|')
        if len(cols) > idx:
            v = cols[idx].strip()
            rev_cntr_vals[v] = rev_cntr_vals.get(v, 0) + 1

# Show top 20 and any ED-related codes
print(f"  Total unique REV_CNTR values: {len(rev_cntr_vals)}")
for v, c in sorted(rev_cntr_vals.items(), key=lambda x: -x[1])[:20]:
    ed_flag = " <-- ED-RELATED" if v.startswith('045') else ""
    print(f"    {v}: {c:,}{ed_flag}")

# Check for 045x codes specifically
ed_codes = {k: v for k, v in rev_cntr_vals.items() if k.startswith('045')}
if ed_codes:
    print(f"\n  ED-related codes (045x):")
    for v, c in sorted(ed_codes.items()):
        print(f"    {v}: {c:,}")
else:
    print(f"\n  NO 045x ED codes found in inpatient!")
