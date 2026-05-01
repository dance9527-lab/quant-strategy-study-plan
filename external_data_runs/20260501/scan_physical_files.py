import os
import pandas as pd

base = "D:/quantum_a0/quant-strategy-study-plan/external_data_runs/20260501"

# 1. Scan all raw/staging CSV/parquet data files
print("=== Physical Files Scan ===", flush=True)
results = []
for worker in ['deepseek', 'coder', 'mimo', 'review']:
    for layer in ['raw', 'staging']:
        dir_path = f"{base}/{worker}/{layer}"
        if not os.path.exists(dir_path):
            continue
        for root, dirs, files in os.walk(dir_path):
            for f in files:
                if f.endswith('.csv') or f.endswith('.parquet'):
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, base)
                    rows = 0
                    if f.endswith('.csv'):
                        try:
                            with open(full, 'r', encoding='utf-8', errors='ignore') as fh:
                                rows = sum(1 for _ in fh) - 1
                        except:
                            rows = -1
                    elif f.endswith('.parquet'):
                        try:
                            import pyarrow.parquet as pq
                            rows = pq.read_metadata(full).num_rows
                        except:
                            try:
                                rows = len(pd.read_parquet(full))
                            except:
                                rows = -1
                    results.append({
                        'worker': worker,
                        'layer': layer,
                        'physical_path': rel,
                        'row_count': rows,
                    })

df = pd.DataFrame(results)
df.to_csv(f"{base}/physical_files_scan.csv", index=False)

print(f"\nTotal files: {len(df)}", flush=True)
print(f"Total rows: {df['row_count'].sum()}", flush=True)
print(f"\nBy worker/layer:", flush=True)
for (w, l), g in df.groupby(['worker', 'layer']):
    print(f"  {w}/{l}: {len(g)} files, {g['row_count'].sum():,} rows", flush=True)

# 2. GMSL parquet detail
print(f"\n=== GMSL Parquet Detail ===", flush=True)
gmsl = df[(df['worker'] == 'mimo') & (df['layer'] == 'staging')]
print(f"Count: {len(gmsl)}", flush=True)
print(f"Total rows: {gmsl['row_count'].sum():,}", flush=True)
for _, r in gmsl.iterrows():
    print(f"  {r['physical_path']}: {r['row_count']:,}", flush=True)
