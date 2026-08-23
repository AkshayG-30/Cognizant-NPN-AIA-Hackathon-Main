import os

# 1. REV_CNTR in Outpatient
print("="*80)
print("1. REV_CNTR VALUES (Outpatient) - ED Indicator Check")
print("="*80)
rev_cntr_vals = {}
with open(r'd:\CTS\Datasets\original\Outpatient\outpatient.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    idx = header.index('REV_CNTR')
    for line in f:
        cols = line.strip().split('|')
        if len(cols) > idx:
            v = cols[idx].strip()
            rev_cntr_vals[v] = rev_cntr_vals.get(v, 0) + 1

print(f"  Total unique REV_CNTR values: {len(rev_cntr_vals)}")
for v, c in sorted(rev_cntr_vals.items(), key=lambda x: -x[1])[:30]:
    ed_flag = " <-- ED-RELATED" if v.startswith('045') else ""
    print(f"    {v}: {c:,}{ed_flag}")

ed_codes = {k: v for k, v in rev_cntr_vals.items() if k.startswith('045')}
if ed_codes:
    print(f"\n  ED-related codes (045x):")
    for v, c in sorted(ed_codes.items()):
        print(f"    {v}: {c:,}")
else:
    print(f"\n  NO 045x ED codes found in outpatient!")

# 2. LINE_PLACE_OF_SRVC_CD in Carrier
print("\n" + "="*80)
print("2. LINE_PLACE_OF_SRVC_CD VALUES (Carrier)")
print("="*80)
pos_vals = {}
with open(r'd:\CTS\Datasets\original\Carrier\carrier.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    idx = header.index('LINE_PLACE_OF_SRVC_CD')
    for line in f:
        cols = line.strip().split('|')
        if len(cols) > idx:
            v = cols[idx].strip()
            pos_vals[v] = pos_vals.get(v, 0) + 1

print(f"  Total unique POS values: {len(pos_vals)}")
for v, c in sorted(pos_vals.items(), key=lambda x: -x[1])[:30]:
    ed_flag = " <-- ED (POS=23)" if v == '23' else ""
    print(f"    {v}: {c:,}{ed_flag}")

# 3. CLM_ID uniqueness in Outpatient
print("\n" + "="*80)
print("3. CLM_ID UNIQUENESS (Outpatient)")
print("="*80)
clm_ids = []
with open(r'd:\CTS\Datasets\original\Outpatient\outpatient.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    idx = header.index('CLM_ID')
    for line in f:
        cols = line.strip().split('|')
        if len(cols) > idx:
            clm_ids.append(cols[idx])
print(f"  Total rows: {len(clm_ids):,}")
print(f"  Unique CLM_IDs: {len(set(clm_ids)):,}")
print(f"  Rows per CLM_ID (avg): {len(clm_ids)/max(1,len(set(clm_ids))):.1f}")

# 4. CLM_ID uniqueness in Carrier
print("\n" + "="*80)
print("4. CLM_ID UNIQUENESS (Carrier)")
print("="*80)
clm_ids_c = []
with open(r'd:\CTS\Datasets\original\Carrier\carrier.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    idx = header.index('CLM_ID')
    for line in f:
        cols = line.strip().split('|')
        if len(cols) > idx:
            clm_ids_c.append(cols[idx])
print(f"  Total rows: {len(clm_ids_c):,}")
print(f"  Unique CLM_IDs: {len(set(clm_ids_c)):,}")
print(f"  Rows per CLM_ID (avg): {len(clm_ids_c)/max(1,len(set(clm_ids_c))):.1f}")

# 5. NPI Overlap: Claims NPI vs DAC NPI
print("\n" + "="*80)
print("5. NPI OVERLAP: Claims vs DAC Provider Data")
print("="*80)

# Collect NPIs from inpatient (ORG_NPI_NUM, AT_PHYSN_NPI)
inp_npis = set()
with open(r'd:\CTS\Datasets\original\inpatient.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    org_idx = header.index('ORG_NPI_NUM')
    at_idx = header.index('AT_PHYSN_NPI')
    for line in f:
        cols = line.strip().split('|')
        if len(cols) > max(org_idx, at_idx):
            v1 = cols[org_idx].strip()
            v2 = cols[at_idx].strip()
            if v1: inp_npis.add(v1)
            if v2: inp_npis.add(v2)
print(f"  Unique NPIs from inpatient: {len(inp_npis):,}")

# Collect NPIs from carrier (PRF_PHYSN_NPI)
carr_npis = set()
with open(r'd:\CTS\Datasets\original\Carrier\carrier.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    prf_idx = header.index('PRF_PHYSN_NPI')
    for line in f:
        cols = line.strip().split('|')
        if len(cols) > prf_idx:
            v = cols[prf_idx].strip()
            if v: carr_npis.add(v)
print(f"  Unique NPIs from carrier (PRF_PHYSN_NPI): {len(carr_npis):,}")

all_claims_npis = inp_npis | carr_npis
print(f"  Unique NPIs across all claims: {len(all_claims_npis):,}")

# Check if claims NPIs look synthetic
sample_claims_npis = list(all_claims_npis)[:20]
print(f"  Sample claims NPIs: {sample_claims_npis}")

# Collect DAC NPIs (first column)
dac_npis = set()
with open(r'd:\CTS\Datasets\original\theme_doctors-clinicians_current\DAC_NationalDownloadableFile.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split(',')
    idx = header.index('NPI')
    count = 0
    for line in f:
        cols = line.strip().split(',')
        if len(cols) > idx:
            v = cols[idx].strip()
            if v: dac_npis.add(v)
        count += 1
        if count > 500000:  # sample first 500k for speed
            break
print(f"  DAC NPIs (first 500k rows): {len(dac_npis):,}")

overlap = all_claims_npis & dac_npis
print(f"  Overlap (claims NPIs in DAC): {len(overlap):,}")
print(f"  Overlap %: {100*len(overlap)/max(1,len(all_claims_npis)):.1f}%")

# 6. HRRP Facility_ID check
print("\n" + "="*80)
print("6. HRRP FACILITY ID vs CLAIMS PRVDR_NUM")
print("="*80)
hrrp_fac_ids = set()
import csv as csvmod
with open(r'd:\CTS\Datasets\original\FY_2026_Hospital_Readmissions_Reduction_Program_Hospital.csv', 'r', encoding='utf-8', errors='replace') as f:
    reader = csvmod.reader(f)
    header = next(reader)
    fac_idx = header.index('Facility ID')
    for row in reader:
        if len(row) > fac_idx:
            hrrp_fac_ids.add(row[fac_idx].strip())
print(f"  Unique HRRP Facility IDs: {len(hrrp_fac_ids):,}")
print(f"  Sample HRRP Facility IDs: {sorted(list(hrrp_fac_ids))[:10]}")

# Get PRVDR_NUM from inpatient
inp_prvdr = set()
with open(r'd:\CTS\Datasets\original\inpatient.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    idx = header.index('PRVDR_NUM')
    for line in f:
        cols = line.strip().split('|')
        if len(cols) > idx:
            v = cols[idx].strip()
            if v: inp_prvdr.add(v)
print(f"  Unique inpatient PRVDR_NUMs: {len(inp_prvdr):,}")
print(f"  Sample inpatient PRVDR_NUMs: {sorted(list(inp_prvdr))[:10]}")

hrrp_overlap = hrrp_fac_ids & inp_prvdr
print(f"  HRRP Facility ID in inpatient PRVDR_NUM: {len(hrrp_overlap):,}")
print(f"  Overlap %: {100*len(hrrp_overlap)/max(1,len(hrrp_fac_ids)):.1f}%")
