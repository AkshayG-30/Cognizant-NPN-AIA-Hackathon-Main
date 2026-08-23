import pandas as pd
# Check inpatient columns
inp = pd.read_csv(r'd:\CTS\Datasets\original\inpatient.csv', sep='|', dtype=str, nrows=2)
print("=== INPATIENT COLUMNS ===")
for c in inp.columns: print(f"  {c}")
print(f"\nTotal: {len(inp.columns)}")

# Check outpatient columns
outp = pd.read_csv(r'd:\CTS\Datasets\original\Outpatient\outpatient.csv', sep='|', dtype=str, nrows=2)
print("\n=== OUTPATIENT COLUMNS ===")
for c in outp.columns: print(f"  {c}")
print(f"\nTotal: {len(outp.columns)}")

# Check carrier columns
carr = pd.read_csv(r'd:\CTS\Datasets\original\Carrier\carrier.csv', sep='|', dtype=str, nrows=2)
print("\n=== CARRIER COLUMNS ===")
for c in carr.columns: print(f"  {c}")
print(f"\nTotal: {len(carr.columns)}")

# Check beneficiary columns
bene = pd.read_csv(r'd:\CTS\Datasets\original\All Beneficiary Years\beneficiary_2020.csv', sep='|', dtype=str, nrows=2)
print("\n=== BENEFICIARY COLUMNS ===")
for c in bene.columns: print(f"  {c}")
print(f"\nTotal: {len(bene.columns)}")
