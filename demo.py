import pandas as pd
import numpy as np

from underthesea import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from scipy.sparse import hstack

# =========================
# 1. Load dữ liệu
# =========================
df = pd.read_csv("jobs_dataset.csv")

# =========================
# 2. Ghép các cột TEXT
# =========================
df["full_text"] = (
    df["Job Title"].fillna("") + " " +
    df["Company Overview"].fillna("") + " " +
    df["Job Description"].fillna("") + " " +
    df["Job Requirements"].fillna("") + " " +
    df["Benefits"].fillna("")
)

# =========================
# 3. Tiền xử lý NLP tiếng Việt
# =========================
def preprocess_vietnamese(text):
    text = str(text).lower()
    text = word_tokenize(text, format="text")
    return text

df["full_text"] = df["full_text"].apply(preprocess_vietnamese)

# =========================
# 4. TF-IDF cho văn bản
# =========================
tfidf = TfidfVectorizer(
    max_features=10000,
    ngram_range=(1, 2)
)

X_text = tfidf.fit_transform(df["full_text"])

# =========================
# 5. Xử lý feature số
# =========================
numeric_cols = [
    "Company Size",
    "Years of Experience",
    "Number Cadidate",
    "Salary"
]

numeric_data = df[numeric_cols].fillna(0)

scaler = StandardScaler()
X_num = scaler.fit_transform(numeric_data)

# =========================
# 6. Ghép TEXT + NUMERIC
# =========================
X = hstack([X_text, X_num])

y = df["Label"]  # 0 = Fake, 1 = Real

# =========================
# 7. Chia tập train / test
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# =========================
# 8. Train Logistic Regression
# =========================
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# =========================
# 9. Dự đoán XÁC SUẤT
# =========================
probabilities = model.predict_proba(X_test)

prob_real = probabilities[:, 1]

# =========================
# 10. In kết quả mẫu
# =========================
for i in range(5):
    print(f"Tin tuyển dụng {i+1}")
    print(f"  ✔ Xác suất là việc làm THẬT: {prob_real[i]*100:.2f}%")
    print(f"  ✖ Xác suất là việc làm GIẢ: {(1 - prob_real[i])*100:.2f}%")
    print("-" * 50)
