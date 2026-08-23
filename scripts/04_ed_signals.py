import os
from collections import Counter

# 1. Inpatient: REV_CNTR per CLM_LINE_NUM
print("="*80)
print("1. INPATIENT: CLM_LINE_NUM vs REV_CNTR relationship")
print("="*80)
line_rev = Counter()
lines_per_claim = Counter()
with open(r'd:\CTS\Datasets\original\inpatient.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    clm_idx = header.index('CLM_ID')
    line_idx = header.index('CLM_LINE_NUM')
    rev_idx = header.index('REV_CNTR')
    current_clm = None
    max_line = 0
    for line in f:
        cols = line.strip().split('|')
        clm_id = cols[clm_idx]
        line_num = cols[line_idx]
        rev_cntr = cols[rev_idx]
        line_rev[(line_num, rev_cntr)] += 1
        if clm_id != current_clm:
            if current_clm is not None:
                lines_per_claim[max_line] += 1
            current_clm = clm_id
            max_line = 0
        max_line = max(max_line, int(line_num))
    lines_per_claim[max_line] += 1

print("  (CLM_LINE_NUM, REV_CNTR) distribution:")
for (ln, rv), c in sorted(line_rev.items(), key=lambda x: -x[1]):
    print(f"    Line {ln}, Rev {rv}: {c:,}")

print(f"\n  Lines per claim distribution:")
for n, c in sorted(lines_per_claim.items()):
    print(f"    {n} lines: {c:,} claims")

# 2. Inpatient: CLM_SRC_IP_ADMSN_CD (admission source)
print("\n" + "="*80)
print("2. INPATIENT: CLM_SRC_IP_ADMSN_CD (Admission Source)")
print("="*80)
admsn_src = Counter()
with open(r'd:\CTS\Datasets\original\inpatient.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    idx = header.index('CLM_SRC_IP_ADMSN_CD')
    for line in f:
        cols = line.strip().split('|')
        if len(cols) > idx:
            admsn_src[cols[idx].strip()] += 1
print(f"  Values:")
for v, c in sorted(admsn_src.items(), key=lambda x: -x[1]):
    note = ""
    if v == '7': note = " <-- EMERGENCY ROOM"
    elif v == '1': note = " <-- Physician referral"
    elif v == '2': note = " <-- Clinic referral"
    elif v == '4': note = " <-- Transfer from hospital"
    elif v == '3': note = " <-- HMO referral"
    elif v == '5': note = " <-- Transfer from SNF"
    elif v == '6': note = " <-- Transfer from another HCF"
    print(f"    {v}: {c:,}{note}")

# 3. Inpatient: CLM_IP_ADMSN_TYPE_CD (admission type)
print("\n" + "="*80)
print("3. INPATIENT: CLM_IP_ADMSN_TYPE_CD (Admission Type)")
print("="*80)
admsn_type = Counter()
with open(r'd:\CTS\Datasets\original\inpatient.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    idx = header.index('CLM_IP_ADMSN_TYPE_CD')
    for line in f:
        cols = line.strip().split('|')
        if len(cols) > idx:
            admsn_type[cols[idx].strip()] += 1
print(f"  Values:")
for v, c in sorted(admsn_type.items(), key=lambda x: -x[1]):
    note = ""
    if v == '1': note = " <-- EMERGENCY"
    elif v == '2': note = " <-- URGENT"
    elif v == '3': note = " <-- ELECTIVE"
    elif v == '9': note = " <-- Unknown"
    print(f"    {v}: {c:,}{note}")

# 4. Check BENE_ID uniqueness per year in beneficiary
print("\n" + "="*80)
print("4. BENE_ID UNIQUENESS PER BENEFICIARY YEAR FILE")
print("="*80)
bene_dir = r'd:\CTS\Datasets\original\All Beneficiary Years'
for fname in ['beneficiary_2015.csv', 'beneficiary_2020.csv', 'beneficiary_2025.csv']:
    path = os.path.join(bene_dir, fname)
    bene_ids = []
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        header = f.readline().strip().split('|')
        idx = header.index('BENE_ID')
        for line in f:
            cols = line.strip().split('|')
            if len(cols) > idx:
                bene_ids.append(cols[idx])
    print(f"  {fname}: {len(bene_ids):,} rows, {len(set(bene_ids)):,} unique BENE_IDs, unique={len(bene_ids)==len(set(bene_ids))}")

# 5. Outpatient: Full column list
print("\n" + "="*80)
print("5. OUTPATIENT COLUMN LIST")
print("="*80)
with open(r'd:\CTS\Datasets\original\Outpatient\outpatient.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    for i, col in enumerate(header):
        print(f"  [{i}] {col}")

# 6. Carrier: LINE_CMS_TYPE_SRVC_CD distribution
print("\n" + "="*80)
print("6. CARRIER: LINE_CMS_TYPE_SRVC_CD")
print("="*80)
srvc_type = Counter()
with open(r'd:\CTS\Datasets\original\Carrier\carrier.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    idx = header.index('LINE_CMS_TYPE_SRVC_CD')
    for line in f:
        cols = line.strip().split('|')
        if len(cols) > idx:
            srvc_type[cols[idx].strip()] += 1
print(f"  Values:")
for v, c in sorted(srvc_type.items(), key=lambda x: -x[1]):
    print(f"    {v}: {c:,}")
