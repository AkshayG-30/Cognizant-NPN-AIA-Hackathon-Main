import os

# 1. Date ranges across claims datasets
print("="*80)
print("1. CLAIM DATE RANGES")
print("="*80)

# Inpatient dates
from collections import Counter

for dataset_name, path, date_col in [
    ('Inpatient', r'd:\CTS\Datasets\original\inpatient.csv', 'CLM_FROM_DT'),
    ('Outpatient', r'd:\CTS\Datasets\original\Outpatient\outpatient.csv', 'CLM_FROM_DT'),
    ('Carrier', r'd:\CTS\Datasets\original\Carrier\carrier.csv', 'CLM_FROM_DT'),
]:
    dates = []
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        header = f.readline().strip().split('|')
        idx = header.index(date_col)
        for line in f:
            cols = line.strip().split('|')
            if len(cols) > idx:
                v = cols[idx].strip()
                if v:
                    dates.append(v)
    
    # Parse and find min/max
    from datetime import datetime
    parsed = []
    for d in dates[:10]:
        try:
            parsed.append(d)
        except:
            pass
    
    print(f"\n  {dataset_name}:")
    print(f"    Date field: {date_col}")
    print(f"    Total non-empty dates: {len(dates):,}")
    print(f"    Sample dates: {dates[:5]}")
    
    # Extract years
    years = Counter()
    for d in dates:
        parts = d.split('-')
        if len(parts) == 3:
            years[parts[2]] += 1
    print(f"    Year distribution:")
    for y, c in sorted(years.items()):
        print(f"      {y}: {c:,}")

# 2. Inpatient: Check NCH_CLM_TYPE_CD distribution
print("\n" + "="*80)
print("2. NCH_CLM_TYPE_CD DISTRIBUTION")
print("="*80)

for dataset_name, path in [
    ('Inpatient', r'd:\CTS\Datasets\original\inpatient.csv'),
    ('Outpatient', r'd:\CTS\Datasets\original\Outpatient\outpatient.csv'),
    ('Carrier', r'd:\CTS\Datasets\original\Carrier\carrier.csv'),
]:
    type_vals = Counter()
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        header = f.readline().strip().split('|')
        idx = header.index('NCH_CLM_TYPE_CD')
        for line in f:
            cols = line.strip().split('|')
            if len(cols) > idx:
                type_vals[cols[idx].strip()] += 1
    print(f"\n  {dataset_name} NCH_CLM_TYPE_CD:")
    for v, c in sorted(type_vals.items(), key=lambda x: -x[1]):
        print(f"    {v}: {c:,}")

# 3. Check inpatient row grain: CLM_ID + CLM_LINE_NUM
print("\n" + "="*80)
print("3. INPATIENT ROW GRAIN: CLM_ID + CLM_LINE_NUM")
print("="*80)
combos = set()
total = 0
with open(r'd:\CTS\Datasets\original\inpatient.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    clm_idx = header.index('CLM_ID')
    line_idx = header.index('CLM_LINE_NUM')
    for line in f:
        cols = line.strip().split('|')
        if len(cols) > max(clm_idx, line_idx):
            combo = (cols[clm_idx], cols[line_idx])
            combos.add(combo)
            total += 1
print(f"  Total rows: {total:,}")
print(f"  Unique (CLM_ID, CLM_LINE_NUM): {len(combos):,}")
print(f"  Is unique key: {total == len(combos)}")

# 4. Check outpatient row grain: CLM_ID + CLM_LINE_NUM
print("\n" + "="*80)
print("4. OUTPATIENT ROW GRAIN: CLM_ID + CLM_LINE_NUM")
print("="*80)
combos = set()
total = 0
with open(r'd:\CTS\Datasets\original\Outpatient\outpatient.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    clm_idx = header.index('CLM_ID')
    line_idx = header.index('CLM_LINE_NUM')
    for line in f:
        cols = line.strip().split('|')
        if len(cols) > max(clm_idx, line_idx):
            combo = (cols[clm_idx], cols[line_idx])
            combos.add(combo)
            total += 1
print(f"  Total rows: {total:,}")
print(f"  Unique (CLM_ID, CLM_LINE_NUM): {len(combos):,}")
print(f"  Is unique key: {total == len(combos)}")

# 5. Check carrier row grain: CLM_ID + LINE_NUM
print("\n" + "="*80)
print("5. CARRIER ROW GRAIN: CLM_ID + LINE_NUM")
print("="*80)
combos = set()
total = 0
with open(r'd:\CTS\Datasets\original\Carrier\carrier.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    clm_idx = header.index('CLM_ID')
    line_idx = header.index('LINE_NUM')
    for line in f:
        cols = line.strip().split('|')
        if len(cols) > max(clm_idx, line_idx):
            combo = (cols[clm_idx], cols[line_idx])
            combos.add(combo)
            total += 1
print(f"  Total rows: {total:,}")
print(f"  Unique (CLM_ID, LINE_NUM): {len(combos):,}")
print(f"  Is unique key: {total == len(combos)}")

# 6. Beneficiary geographic fields
print("\n" + "="*80)
print("6. BENEFICIARY GEOGRAPHIC IDENTIFIERS (2020 sample)")
print("="*80)
geo_fields = ['STATE_CODE', 'COUNTY_CD', 'ZIP_CD', 'STATE_CNTY_FIPS_CD_01']
with open(r'd:\CTS\Datasets\original\All Beneficiary Years\beneficiary_2020.csv', 'r', encoding='utf-8', errors='replace') as f:
    header = f.readline().strip().split('|')
    indices = {g: header.index(g) for g in geo_fields}
    vals = {g: Counter() for g in geo_fields}
    for line in f:
        cols = line.strip().split('|')
        for g, idx in indices.items():
            if len(cols) > idx:
                vals[g][cols[idx].strip()] += 1
    
    for g in geo_fields:
        print(f"\n  {g}: {len(vals[g])} unique values")
        top5 = sorted(vals[g].items(), key=lambda x: -x[1])[:5]
        for v, c in top5:
            print(f"    '{v}': {c}")
