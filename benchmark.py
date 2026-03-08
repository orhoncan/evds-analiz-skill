import pandas as pd
import numpy as np
import time
from scripts.gelismis_analiz import veri_kalitesi_kontrolu

# Create dummy data
np.random.seed(42)
rows = 100000
cols = 100
df = pd.DataFrame(np.random.randn(rows, cols), columns=[f'col_{i}' for i in range(cols)])
mask = np.random.rand(rows, cols) < 0.1
df = df.mask(mask)

# Using our script functions
start_time = time.time()
for _ in range(5):
    res = veri_kalitesi_kontrolu(df)
time_taken = (time.time() - start_time) / 5

print(f"Time taken to run veri_kalitesi_kontrolu: {time_taken*1000:.2f} ms")
