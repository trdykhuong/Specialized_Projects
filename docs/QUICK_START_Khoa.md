# 🚀 QUICK START - Training dữ liệu mới

## 1️⃣ Cách chạy training

### Option A: Dữ liệu đã xử lý (KHOA)
```bash
cd ml_pipeline/src
python ensemble_training.py
```

### Option B: Dữ liệu khác
```python
from ensemble_training import EnsembleJobClassifier

classifier = EnsembleJobClassifier()
results, clf = classifier.run_complete_pipeline(
    data_path="../../data/JOB_DATA_FINAL.csv"  # Đường dẫn dữ liệu mới
)
```

## 2️⃣ Yêu cầu dữ liệu

Dữ liệu CSV cần có:

| Bắt buộc | Nội dung |
|---------|---------|
| **Label** | 0 (FAKE) hoặc 1 (REAL) - Nhãn phân loại |
| **Text fields** | Job Title, Job Description, Job Requirements, Benefits, Company Overview |
| hoặc | **FULL_TEXT** - Text đã kết hợp |

| Tùy chọn | Tác dụng |
|---------|---------|
| **confidence** | Độ tin cậy (0-1), lọc data high-confidence |
| **engineered features** | Các features đã tính toán (salary_avg, text_length, ...) |

## 3️⃣ Output

- ✅ **models/** folder - chứa 4 files models
- ✅ **model_comparison.png** - biểu đồ chi tiết
- ✅ **Console output** - metrics & analysis

## 4️⃣ Ví dụ dữ liệu

### Dữ liệu thô (Raw)
```csv
Job Title,Job Description,Job Requirements,Label
Python Dev,"Python job desc...",Requirements...,1
Tuyển toàn bộ,...,No exp required,0
```

### Dữ liệu xử lý (Enhanced)
```csv
FULL_TEXT,Label,salary_avg,text_length,confidence
Python Dev Python job...,1,25000000,500,0.95
Tuyển toàn bộ...,0,5000000,200,0.85
```

## 5️⃣ Kết quả expected

```
📊 Phân bố labels:
   REAL: 10,000 (68.37%)
   FAKE: 4,634 (31.63%)

🔧 Chuẩn bị features:
   1️⃣ TF-IDF vectorization...
      ✓ Shape: (14634, 10000)
   2️⃣ Numeric features: 40/50 có sẵn
      ✓ Combined shape: (14634, 10040)

✂️ Chia train/test:
   Train set: 11,707 mẫu
   Test set:  2,927 mẫu

🤖 Training các models:
   [LogisticRegression]
   Accuracy:  0.8521
   Precision: 0.8234
   Recall:    0.8912
   F1-Score:  0.8563
   AUC-ROC:   0.9123
   ...

🏆 Best Single Model: XGBoost
   F1-Score: 0.8623
```

## 6️⃣ Sử dụng models để predict

```python
import joblib

# Load models
model = joblib.load("models/best_model.pkl")
tfidf = joblib.load("models/tfidf_vectorizer.pkl")

# Predict
text = "Tuyển Lập trình viên Python, lương 20-30 triệu"
X = tfidf.transform([text])
prediction = model.predict(X)[0]
probability = model.predict_proba(X)[0]

print(f"Dự đoán: {'REAL' if prediction == 1 else 'FAKE'}")
print(f"Xác suất: REAL={probability[1]:.2%}")
```

## 7️⃣ Các tham số tuỳ chỉnh

```python
# Không lọc high-confidence
classifier = EnsembleJobClassifier(
    use_high_confidence_only=False
)

# Lọc strict (confidence >= 0.9)
classifier = EnsembleJobClassifier(
    use_high_confidence_only=True,
    confidence_threshold=0.9
)
```

## 8️⃣ Troubleshooting

| Lỗi | Giải pháp |
|-----|----------|
| `FileNotFoundError` | Kiểm tra đường dẫn `data_path` |
| `KeyError: 'Label'` | Dữ liệu thiếu cột 'Label' |
| `KeyError: 'FULL_TEXT'` | Thiếu cột text, auto-create từ Job Title, Description... |
| RAM hết | Giảm data size hoặc max_features TF-IDF |

---

📖 Chi tiết xem: [TRAINING_GUIDE.md](TRAINING_GUIDE.md)
