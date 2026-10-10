import sys, pandas as pd
path = sys.argv[1]
head = pd.read_csv(path, nrows=5)
print("COLUMNS:", list(head.columns))
print(head.T.to_string())
n = sum(len(c) for c in pd.read_csv(path, usecols=[0], chunksize=200_000))
print("ROWS:", n)