import pandas as pd
import numpy as np
import time

# Create dummy data
np.random.seed(42)
rows = 100000
cols = 20
data = {f"col_{i}": [f"{np.random.randint(1000)},{np.random.randint(99)}" if np.random.rand() > 0.1 else " " for _ in range(rows)] for i in range(cols)}

df_orig = pd.DataFrame(data)

# Baseline: The code in the prompt ("Current Code" which had a loop)
start = time.time()
for _ in range(5):
    df = df_orig.copy()
    for col in df.columns:
        if df[col].dtype == object:
            temiz = df[col].astype(str).str.replace(',', '.', regex=False)
            df[col] = temiz.replace(r'^\s*$', pd.NA, regex=True)
        df[col] = pd.to_numeric(df[col], errors='coerce')
time_baseline_loop = (time.time() - start) / 5

# The current code in the repo (vectorized replace with regex)
start = time.time()
for _ in range(5):
    df = df_orig.copy()
    obj_cols = df.select_dtypes(include=['object', 'string']).columns
    if len(obj_cols) > 0:
        df[obj_cols] = df[obj_cols].replace(',', '.', regex=True).replace(r'^\s*$', pd.NA, regex=True)
    df = df.apply(pd.to_numeric, errors='coerce')
time_repo_current = (time.time() - start) / 5

# Vectorized using apply + str.replace
start = time.time()
for _ in range(5):
    df = df_orig.copy()
    obj_cols = df.select_dtypes(include=['object', 'string']).columns
    if len(obj_cols) > 0:
        df[obj_cols] = df[obj_cols].apply(lambda x: x.str.replace(',', '.', regex=False).replace(r'^\s*$', pd.NA, regex=True))
    df = df.apply(pd.to_numeric, errors='coerce')
time_apply_str = (time.time() - start) / 5

# Vectorized using apply with lambda and str.replace directly
start = time.time()
for _ in range(5):
    df = df_orig.copy()
    obj_cols = df.select_dtypes(include=['object', 'string']).columns
    if len(obj_cols) > 0:
        # Instead of dataframe-wide replace which uses slow regex on object columns, we apply string methods per column.
        df[obj_cols] = df[obj_cols].apply(lambda col: col.str.replace(',', '.', regex=False))
    df = df.apply(pd.to_numeric, errors='coerce')
time_fast = (time.time() - start) / 5

print(f"Original prompt loop: {time_baseline_loop*1000:.2f} ms")
print(f"Repo current code: {time_repo_current*1000:.2f} ms")
print(f"Apply + str.replace: {time_apply_str*1000:.2f} ms")
print(f"Apply + str.replace without NA regex: {time_fast*1000:.2f} ms")
