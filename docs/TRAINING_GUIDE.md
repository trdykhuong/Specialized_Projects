# 📋 HƯỚNG DẪN SỬ DỤNG ENSEMBLE TRAINING

## Thay đổi chính

### 1. **Hỗ trợ dữ liệu mới linh hoạt**
   - ✅ Tự động tạo `FULL_TEXT` từ các cột text (Job Title, Description, Requirements, Benefits, Company Overview)
   - ✅ Có thể training trên `JOB_DATA_FINAL.csv` hoặc `JOB_DATA_IMPROVED_LABELS_KHOA.csv`
   - ✅ Xử lý features engineered nếu có, nếu không thì chỉ dùng TF-IDF

### 2. **Cải thiện logging & error handling**
   - 📊 Thêm emoji và formating để dễ đọc output
   - ⚠️ Cảnh báo rõ ràng khi thiếu dữ liệu
   - 📐 In chi tiết kích thước features ở mỗi bước

### 3. **Tham số hóa data_path**
   - Có thể pass `data_path` vào `run_complete_pipeline()`
   - Mặc định: `"../../data/JOB_DATA_IMPROVED_LABELS_KHOA.csv"`

## Cách sử dụng

### Option 1: Sử dụng dữ liệu đã xử lý (khuyến nghị)
```python
# File: ml_pipeline/src/ensemble_training.py
classifier = EnsembleJobClassifier(use_high_confidence_only=True)
results, voting_clf = classifier.run_complete_pipeline(
    data_path="../../data/JOB_DATA_IMPROVED_LABELS_KHOA.csv"
)
```

### Option 2: Sử dụng dữ liệu thô
```python
# Tự động tạo FULL_TEXT từ các cột
classifier = EnsembleJobClassifier(use_high_confidence_only=False)
results, voting_clf = classifier.run_complete_pipeline(
    data_path="../../data/JOB_DATA_FINAL.csv"
)
```

### Option 3: Từ command line
```bash
cd ml_pipeline/src
python ensemble_training.py
```

## Yêu cầu dữ liệu

### Dữ liệu phải có:
- **Cột 'Label'**: 0 (FAKE) hoặc 1 (REAL)
- **Cột 'FULL_TEXT'** HOẶC các cột text:
  - Job Title
  - Job Description
  - Job Requirements
  - Benefits
  - Company Overview

### Optional (tăng accuracy):
- `confidence`: Độ tin cậy của label (0-1)
- Engineered features: `salary_avg`, `text_length`, `vocab_diversity`, v.v.

## Output

- **model_comparison.png**: Biểu đồ so sánh 5 models
- **best_model.pkl**: Model tốt nhất
- **voting_ensemble.pkl**: Ensemble model
- **tfidf_vectorizer.pkl**: TF-IDF vectorizer (dùng cho prediction)
- **scaler.pkl**: Feature scaler

## Các bước trong pipeline

1. 📂 **Load dữ liệu** - Đọc CSV và kiểm tra cấu trúc
2. 🔧 **Chuẩn bị features** - TF-IDF + numeric features (nếu có)
3. ✂️ **Chia train/test** - 80/20 split với stratification
4. 🤖 **Huấn luyện** - 5 models: LogisticRegression, RandomForest, GradientBoosting, XGBoost, LightGBM
5. 📊 **Cross-validation** - 5-fold CV
6. 🎯 **Ensemble** - Voting ensemble từ top 3 models
7. 📈 **Đánh giá** - Metrics: Accuracy, Precision, Recall, F1, AUC-ROC
8. 📉 **Visualization** - Biểu đồ chi tiết

## Ví dụ chi tiết

### Nếu bạn có dữ liệu mới tương tự như `JOB_DATA_FINAL.csv`:

```python
from ensemble_training import EnsembleJobClassifier

# 1. Khởi tạo
classifier = EnsembleJobClassifier(
    use_high_confidence_only=False,  # Không lọc
    confidence_threshold=0.7
)

# 2. Training
results, voting_clf = classifier.run_complete_pipeline(
    data_path="../../data/JOB_DATA_FINAL.csv"  # Dữ liệu mới của bạn
)

# 3. Sử dụng model
import joblib
model = joblib.load("../../models/best_model.pkl")
tfidf = joblib.load("../../models/tfidf_vectorizer.pkl")

# Predict
new_text = "Job description text here..."
X_new = tfidf.transform([new_text])
prediction = model.predict(X_new)
```

## Ghi chú

- Training mặc định lọc high-confidence mẫu (confidence >= 0.7)
- Để training trên toàn bộ dữ liệu: `EnsembleJobClassifier(use_high_confidence_only=False)`
- Nếu không có features engineered, chỉ dùng TF-IDF + kết hợp features text lại
- Thời gian training phụ thuộc vào kích thước dữ liệu (~5-10 phút cho 10k+ mẫu)
