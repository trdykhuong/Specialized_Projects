import pandas as pd

# Check JOB_DATA_IMPROVED_LABELS_KHOA.csv
file1 = "data/JOB_DATA_IMPROVED_LABELS_KHOA.csv"
df1 = pd.read_csv(file1)
print(f"File: {file1}")
print(f"Columns: {df1.columns.tolist()}")
print(f"Shape: {df1.shape}")
print(f"Has Label: {'Label' in df1.columns}")
print(f"Has FULL_TEXT: {'FULL_TEXT' in df1.columns}")
print(f"First few rows:")
print(df1.head(1))
print()

# Check FINAL.csv
print("---")
file2 = "data/JOB_DATA_FINAL.csv"
df2 = pd.read_csv(file2)
print(f"File: {file2}")
print(f"Columns: {df2.columns.tolist()}")
print(f"Shape: {df2.shape}")
