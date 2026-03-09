import time
import numpy as np
import pandas as pd
from scripts.gelismis_analiz import anomali_tespiti

# Generate a large wide dataset
np.random.seed(42)
n_rows = 1000
n_cols = 1000
data = np.random.randn(n_rows, n_cols)
df = pd.DataFrame(data, columns=[f'col_{i}' for i in range(n_cols)])

# Add some nans and outliers
for col in df.columns[:100]:
    df.loc[np.random.choice(df.index, size=10, replace=False), col] = np.nan
    df.loc[np.random.choice(df.index, size=5, replace=False), col] = 10.0
    df.loc[np.random.choice(df.index, size=5, replace=False), col] = -10.0

start = time.time()
res_zscore = anomali_tespiti(df, metot='zscore')
end = time.time()
print(f"Z-Score Time (Optimized): {end - start:.4f} seconds")
