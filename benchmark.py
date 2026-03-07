import pandas as pd
import numpy as np
import time

# Create dummy data
dates = pd.date_range(start='2000-01-01', periods=10000)
df = pd.DataFrame({'A': np.random.randn(10000)}, index=dates)
seri = df['A']

# Original way
start_time = time.time()
for _ in range(100):
    result1 = [d.strftime('%Y-%m-%d') for d in seri.index]
time_orig = (time.time() - start_time) / 100

# Optimized way
start_time = time.time()
for _ in range(100):
    result2 = seri.index.strftime('%Y-%m-%d').tolist()
time_opt = (time.time() - start_time) / 100

print(f"Original list comp time: {time_orig*1000:.4f} ms")
print(f"Optimized pandas time:   {time_opt*1000:.4f} ms")
print(f"Speedup:                 {time_orig/time_opt:.2f}x faster")
assert result1 == result2
