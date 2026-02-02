import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler
from scipy.sparse import hstack

# 1. Load dữ liệu đã gán label
df = pd.read_csv("data/JOB_DATA_FOR_MODEL.csv")

# 2. Chuẩn hóa dư liệu số 
# Xử lý lương (text → số)
def parse_salary(salary_text):
    if not isinstance(salary_text, str):
        return 0

    salary_text = salary_text.lower()

    if "thỏa thuận" in salary_text or "negotiable" in salary_text:
        return 0

    numbers = re.findall(r'\d+', salary_text.replace(',', ''))
    if len(numbers) == 0:
        return 0

    numbers = list(map(int, numbers))
    return sum(numbers) // len(numbers)

# Áp dụng cho cột Salary
df["Salary_Value"] = df["Salary"].apply(parse_salary)

# Áp dụng hàm xử lý kích thước công ty
def parse_company_size(size_text):
    if not isinstance(size_text, str):
        return 0

    size_text = size_text.lower()

    # Trường hợp "Trên 1000", "More than 500"
    if "trên" in size_text or "more" in size_text:
        numbers = re.findall(r'\d+', size_text)
        return int(numbers[0]) if numbers else 0

    # Trường hợp "100-499"
    numbers = re.findall(r'\d+', size_text)
    if len(numbers) == 0:
        return 0

    numbers = list(map(int, numbers))
    return sum(numbers) // len(numbers)

# Áp dụng cho cột Company Size
df["Company_Size_Value"] = df["Company Size"].apply(parse_company_size)


# Áp dụng hàm xử lý Years of Experience
def parse_experience(exp_text):
    """
    Chuyển Years of Experience về số (năm):
    - '1-3 năm' -> 2
    - 'Trên 5 năm' -> 5
    - 'Không yêu cầu' -> 0
    """
    if not isinstance(exp_text, str):
        return 0

    exp_text = exp_text.lower()

    if "không" in exp_text:
        return 0

    if "trên" in exp_text or "more" in exp_text:
        numbers = re.findall(r'\d+', exp_text)
        return int(numbers[0]) if numbers else 0

    numbers = re.findall(r'\d+', exp_text)
    if len(numbers) == 0:
        return 0

    numbers = list(map(int, numbers))
    return sum(numbers) // len(numbers)

# Áp dụng cho cột Years of Experience
df["Experience_Value"] = df["Years of Experience"].apply(parse_experience)


# 3. Chuẩn bị X / y
X_text_raw = df["FULL_TEXT"].fillna("")
y = df["Label"]  # 0 = Fake, 1 = Real


# 4. TF-IDF cho văn bản
tfidf = TfidfVectorizer(
    max_features=8000,
    ngram_range=(1, 2),
    min_df=3
)

X_text = tfidf.fit_transform(X_text_raw)


# 5. Feature số
numeric_cols = [
    "Company_Size_Value",
    "Experience_Value",
    "Number Cadidate",
    "Salary_Value"
]


X_num = df[numeric_cols].fillna(0)

scaler = StandardScaler()
X_num_scaled = scaler.fit_transform(X_num)


# 6. Ghép TEXT + NUMERIC
X = hstack([X_text, X_num_scaled])


# 7. Train / Test split
X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
    X,
    y,
    df.index,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# 8. Train Logistic Regression
model = LogisticRegression(
    max_iter=1000,
    class_weight="balanced"
)

model.fit(X_train, y_train)


# 9. Đánh giá mô hình
y_pred = model.predict(X_test)
print("Kết quả đánh giá:")
print(classification_report(y_test, y_pred))


# 10. Dự đoán XÁC SUẤT
y_proba = model.predict_proba(X_test)

print("Ví dụ dự đoán xác suất:\n")

for i in range(5):
    row = df.loc[idx_test[i]]

    print(f"Tin {i+1}")
    print(f"Nội dung (rút gọn): {row['FULL_TEXT'][:300]}...")
    print(f"Salary    : {row['Salary']}")
    print(f"REAL      : {y_proba[i][1]*100:.2f}%")
    print(f"FAKE      : {y_proba[i][0]*100:.2f}%")
    print("-" * 50)

