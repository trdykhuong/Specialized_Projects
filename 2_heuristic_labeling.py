import pandas as pd
import re


# 1. Load dữ liệu
df = pd.read_csv("data/JOB_DATA_LABELLED.csv")


# 2. Keyword nghi ngờ
FAKE_KEYWORDS = [
    "việc nhẹ lương cao",
    "thu nhập không giới hạn",
    "không cần kinh nghiệm",
    "kiếm tiền nhanh",
    "tuyển gấp",
    "làm tại nhà",
    "tuyển cộng tác viên cho Shopee",
    "tuyển ngay",
    "lương cao bất ngờ",
    "làm thêm tại nhà",
    "tuyển dụng online",
    "tuyển dụng khẩn",
    "làm việc tự do",
    "công việc online",
    "tuyển dụng 24/7",
    "tuyển cộng tác viên cho Lazada"
    
]


# 3. XỬ LÝ LƯƠNG
def parse_salary(salary_text):
    """
    Trả về:
    - salary_value (int) nếu trích xuất được
    - None nếu là 'thỏa thuận' hoặc không xác định
    """
    if not isinstance(salary_text, str):
        return None

    salary_text = salary_text.lower()

    # Trường hợp thỏa thuận
    if "thỏa thuận" in salary_text or "negotiable" in salary_text:
        return None

    # Lấy tất cả số trong chuỗi
    numbers = re.findall(r'\d+', salary_text.replace(',', ''))

    if len(numbers) == 0:
        return None

    numbers = list(map(int, numbers))

    # Nếu là khoảng → lấy trung bình
    return sum(numbers) // len(numbers)

# 4. Kiểm tra keyword fake
def contains_fake_keyword(text):
    if not isinstance(text, str):
        return False
    return any(kw in text for kw in FAKE_KEYWORDS)


# 5. Hàm gán nhãn heuristic
def assign_label(row):
    score = 0

    text = str(row["FULL_TEXT"])
    salary_value = parse_salary(row.get("Salary", ""))

    # (1) Nội dung quá ngắn
    if len(text.split()) < 50:
        score += 1

    # (2) Lương bất thường
    if salary_value is None:
        score += 1  # thiếu thông tin
    elif salary_value > 50000000:
        score += 2  # quá cao

    # (3) Thiếu thông tin công ty
    if pd.isna(row.get("Company Size")) or row.get("Company Size", 0) == 0:
        score += 1

    # (4) Keyword nghi ngờ
    if contains_fake_keyword(text):
        score += 2

    # Quy tắc quyết định
    if score >= 2:
        return 0  # Fake
    return 1      # Real


# 6. Gán nhãn
df["Label"] = df.apply(assign_label, axis=1)

# 7. Thống kê
print("Phân bố nhãn:")
print(df["Label"].value_counts())

# 8. Lưu file
df.to_csv(
    "data/JOB_DATA_FOR_MODEL.csv",
    index=False,
    encoding="utf-8-sig"
)

print("Đã lưu JOB_DATA_FOR_MODEL.csv")
