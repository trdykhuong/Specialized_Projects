import pandas as pd
import re
from pyvi import ViTokenizer

# 1. Làm sạch văn bản
def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# 2. Tách từ tiếng Việt
def tokenize_vi(text):
    return ViTokenizer.tokenize(text)


# 3. Pipeline tiền xử lý
def preprocess_pipeline(df):

    text_cols = [
        'Job Title',
        'Company Overview',
        'Job Description',
        'Job Requirements',
        'Benefits'
    ]

    # Làm sạch + tách từ từng cột text
    # Lưu ý: KHÔNG xử lý 'Name Company' — giữ nguyên tên gốc để
    # enrich_company_features.py tra cứu masothue chính xác
    for col in text_cols:
        if col in df.columns:
            print(f"Xử lý cột: {col}")
            df[col] = df[col].fillna("").apply(clean_text)
            df[col] = df[col].apply(tokenize_vi)

    # Gộp các cột text → 1 cột duy nhất dùng cho TF-IDF
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

    import os
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    DATA_DIR = os.path.join(BASE_DIR, 'data')

    df = pd.read_csv(os.path.join(DATA_DIR, "JOB_DATA_FINAL.csv"))
    print(f"Đã load: {len(df)} mẫu, {len(df.columns)} cột")

    df_processed = preprocess_pipeline(df)

    # Các cột giữ lại:
    # - Name Company    : để enrich_company_features tra cứu MST (KHÔNG đưa vào FULL_TEXT)
    # - FULL_TEXT       : văn bản đã xử lý dùng cho TF-IDF
    # - Company Overview: để advanced_features tính company_overview_length
    # - Company Size    : để advanced_features tính company_size_value
    # - Job Requirements: để advanced_features tính requirements_length  ← quan trọng
    # - Years of Experience, Number Cadidate, Salary: các features số
    # - Job Description : fallback cho enrich khi Name Company trống
    final_cols = [
        'Name Company',
        'FULL_TEXT',
        'Company Overview',
        'Company Size',
        'Years of Experience',
        'Number Cadidate',
        'Salary',
        'Job Requirements',
        'Job Description',
    ]

    available = [c for c in final_cols if c in df_processed.columns]
    missing   = [c for c in final_cols if c not in df_processed.columns]
    if missing:
        print(f"[WARN] Cột không có trong data (bỏ qua): {missing}")

    df_final = df_processed[available]

    out_path = os.path.join(DATA_DIR, "JOB_DATA_LABELLED.csv")
    df_final.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"Đã lưu: {out_path}")
    print(f"Shape : {df_final.shape}")
    print(f"Cột   : {df_final.columns.tolist()}")