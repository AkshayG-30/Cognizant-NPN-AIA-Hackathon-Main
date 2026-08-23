"""Export full master dataset as CSV."""
import pandas as pd
import os

master = pd.read_parquet(r'd:\CTS\data\master\MASTER_DATASET.parquet')
csv_path = r'd:\CTS\data\master\MASTER_DATASET.csv'
print(f"Writing {len(master):,} rows x {len(master.columns)} cols to CSV...")
master.to_csv(csv_path, index=False)
size_mb = os.path.getsize(csv_path) / (1024*1024)
print(f"Done: {csv_path} ({size_mb:.1f} MB)")
