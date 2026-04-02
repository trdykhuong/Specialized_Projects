import pandas as pd
import re
from pyvi import ViTokenizer

# 1. Làm sạch văn bản
def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    # Xóa ký tự đặc biệt, giữ chữ + số
    text = re.sub(r'[^\w\s]', ' ', text)
    # Xóa khoảng trắng dư
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# 2. Tách từ tiếng Việt
def tokenize_vi(text):
    return ViTokenizer.tokenize(text)


# 3. Pipeline tiền xử lý
def preprocess_pipeline(df):

    # Các cột văn bản dùng cho NLP
    text_cols = [
        'Job Title',
        'Company Overview',
        'Job Description',
        'Job Requirements',
        'Benefits'
    ]

    # 3.1 Làm sạch + tách từ từng cột
    for col in text_cols:
        if col in df.columns:
            print(f"Xử lý cột: {col}")
            df[col] = df[col].fillna("").apply(clean_text)
            df[col] = df[col].apply(tokenize_vi)

    # 3.2 GỘP các cột text → 1 cột duy nhất
    df['FULL_TEXT'] = (
        df['Job Title'] + ' ' +
        df['Company Overview'] + ' ' +
        df['Job Description'] + ' ' +
        df['Job Requirements'] + ' ' +
        df['Benefits']
    )

    return df

# 4. MAIN
if __name__ == "__main__":

    # Load dữ liệu gốc
    df = pd.read_csv("../data/JOB_DATA_FINAL.csv")

    # Tiền xử lý
    df_processed = preprocess_pipeline(df)

    # CHỈ GIỮ CÁC CỘT CẦN CHO MODEL
    final_cols = [
        'FULL_TEXT',
        'Company Size',
        'Years of Experience',
        'Number Cadidate',
        'Salary'
    ]

    df_final = df_processed[final_cols]

    # Lưu ra file dùng cho AI
    df_final.to_csv(
        "../data/JOB_DATA_LABELLED.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("Đã lưu file: JOB_DATA_LABELLED.csv")
    print(df_final.head())
