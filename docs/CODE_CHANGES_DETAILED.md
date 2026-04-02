# 📝 Chi tiết Code - Trước & Sau

## 1. Load Data

### ❌ TRƯỚC
```python
def load_and_prepare_data(self):
    print("Đang load dữ liệu...")
    
    # Load dữ liệu của Khoa
    df = pd.read_csv("../../data/JOB_DATA_IMPROVED_LABELS_KHOA.csv")
    # Lọc theo confidence nếu cần
    if self.use_high_confidence:
        original_size = len(df)
        df = df[df['confidence'] >= self.confidence_threshold]
        print(f"Lọc high-confidence: {original_size} -> {len(df)} mẫu")
    
    return df
```

**Vấn đề:**
- ❌ File path cứng
- ❌ Không xử lý nếu thiếu column
- ❌ Không tạo FULL_TEXT
- ❌ Output không rõ ràng

### ✅ SAU
```python
def load_and_prepare_data(self, data_path="../../data/JOB_DATA_IMPROVED_LABELS_KHOA.csv"):
    print(f"📂 Đang load dữ liệu từ: {data_path}")
    
    df = pd.read_csv(data_path)
    print(f"✓ Kích thước: {df.shape[0]} dòng, {df.shape[1]} cột")
    print(f"✓ Các cột: {df.columns.tolist()[:10]}...")
    
    # Nếu chưa có FULL_TEXT, tạo từ các cột text có sẵn
    if 'FULL_TEXT' not in df.columns:
        print("\n⚙️  Tạo FULL_TEXT từ các cột có sẵn...")
        text_cols = [col for col in df.columns 
                    if col in ['Job Title', 'Job Description', 'Job Requirements', 
                              'Benefits', 'Company Overview']]
        
        df['FULL_TEXT'] = df[text_cols].fillna('').agg(' '.join, axis=1)
        print(f"✓ Đã tạo FULL_TEXT từ {len(text_cols)} cột: {text_cols}")
    
    # Nếu chưa có Label, liệu có cách để tạo không?
    if 'Label' not in df.columns:
        print("\n⚠️  Cảnh báo: Không tìm thấy cột 'Label'")
        print("   Các cột có sẵn:", df.columns.tolist()[:15])
        raise ValueError("File CSV cần phải có cột 'Label' cho training")
    
    # Lọc theo confidence nếu cần
    if self.use_high_confidence and 'confidence' in df.columns:
        original_size = len(df)
        df = df[df['confidence'] >= self.confidence_threshold]
        print(f"✓ Lọc high-confidence: {original_size} → {len(df)} mẫu")
    elif self.use_high_confidence:
        print("⚠️  Không tìm thấy cột 'confidence', bỏ qua bước lọc")
    
    return df
```

**Cải tiến:**
- ✅ Linh hoạt: có thể pass `data_path` bất kỳ
- ✅ Auto-create FULL_TEXT nếu không có
- ✅ Kiểm tra Label column
- ✅ Logging chi tiết với emoji
- ✅ Xử lý gracefully khi thiếu dữ liệu

---

## 2. Prepare Features

### ❌ TRƯỚC
```python
def prepare_features(self, df, fit=True):
    """Chuẩn bị features"""
    
    # 1. Text features (TF-IDF)
    X_text_raw = df['FULL_TEXT'].fillna("")
    
    if fit:
        X_text = self.tfidf.fit_transform(X_text_raw)
    else:
        X_text = self.tfidf.transform(X_text_raw)
    
    # 2. Numeric features (engineered features)
    numeric_features = [...]
    
    # Lọc các features có trong data
    available_features = [f for f in numeric_features if f in df.columns]
    print(f"Sử dụng {len(available_features)} numeric features")
    
    X_num = df[available_features].fillna(0)
    
    if fit:
        X_num_scaled = self.scaler.fit_transform(X_num)
    else:
        X_num_scaled = self.scaler.transform(X_num)
    
    # 3. Combine
    X = hstack([X_text, X_num_scaled])
    
    return X
```

**Vấn đề:**
- ❌ Không xử lý nếu không có numeric features
- ❌ Output không rõ ràng về kích thước features

### ✅ SAU
```python
def prepare_features(self, df, fit=True):
    """Chuẩn bị features - Xử lý 2 trường hợp:
    1. Dữ liệu đã được xử lý: có FULL_TEXT + numeric features
    2. Dữ liệu thô: chỉ có FULL_TEXT
    """
    print("\n🔧 Chuẩn bị features...")
    
    # 1. Text features (TF-IDF)
    print("  1️⃣  TF-IDF vectorization...")
    X_text_raw = df['FULL_TEXT'].fillna("")
    
    if fit:
        X_text = self.tfidf.fit_transform(X_text_raw)
    else:
        X_text = self.tfidf.transform(X_text_raw)
    
    print(f"     ✓ Shape: {X_text.shape}")
    
    # 2. Numeric features (nếu có)
    numeric_features = [...]
    
    # Lọc các features có trong data
    available_features = [f for f in numeric_features if f in df.columns]
    
    if available_features:
        print(f"  2️⃣  Numeric features: {len(available_features)}/{len(numeric_features)} có sẵn")
        X_num = df[available_features].fillna(0)
        
        if fit:
            X_num_scaled = self.scaler.fit_transform(X_num)
        else:
            X_num_scaled = self.scaler.transform(X_num)
        
        # 3. Combine
        X = hstack([X_text, X_num_scaled])
        print(f"     ✓ Combined shape: {X.shape}")
    else:
        print(f"  2️⃣  Không có numeric features sẵn, sử dụng TF-IDF text features")
        X = X_text
    
    return X
```

**Cải tiến:**
- ✅ Xử lý cả 2 trường hợp: có/không có numeric features
- ✅ Chi tiết logging cho mỗi bước
- ✅ In kích thước features
- ✅ Graceful fallback nếu thiếu dữ liệu

---

## 3. Run Pipeline

### ❌ TRƯỚC
```python
def run_complete_pipeline(self):
    """Chạy toàn bộ pipeline"""
    
    # 1. Load data
    df = self.load_and_prepare_data()
    
    print(f"\nPhân bố labels:")
    print(df['Label'].value_counts())
    print(f"Tỷ lệ FAKE: {(1 - df['Label'].mean())*100:.2f}%")
    
    # ... rest của code
```

**Vấn đề:**
- ❌ Không có parameter cho data_path
- ❌ Logging không rõ ràng bước nào

### ✅ SAU
```python
def run_complete_pipeline(self, data_path="../../data/JOB_DATA_IMPROVED_LABELS_KHOA.csv"):
    """Chạy toàn bộ pipeline
    
    Args:
        data_path: Đường dẫn tới file CSV training
    """
    
    print("\n" + "="*80)
    print("BƯỚC 1: LOAD VÀ KIỂM TRA DỮ LIỆU")
    print("="*80)
    
    # 1. Load data
    df = self.load_and_prepare_data(data_path)
    
    print(f"\n📊 Phân bố labels:")
    label_counts = df['Label'].value_counts()
    for label, count in label_counts.items():
        percentage = (count / len(df)) * 100
        label_name = 'REAL' if label == 1 else 'FAKE'
        print(f"   {label_name}: {count:,} ({percentage:.2f}%)")
    
    # 2. Prepare features
    print("\n" + "="*80)
    print("BƯỚC 2: CHUẨN BỊ FEATURES")
    print("="*80)
    X = self.prepare_features(df, fit=True)
    y = df['Label']
    
    # ... rest
```

**Cải tiến:**
- ✅ Thêm parameter `data_path`
- ✅ Rõ ràng các bước (BƯỚC 1, 2, 3, ...)
- ✅ Chi tiết hơn output với formatting

---

## 4. Main Function

### ❌ TRƯỚC
```python
if __name__ == "__main__":
    
    print("="*80)
    print("HỆ THỐNG PHÂN LOẠI TIN TUYỂN DỤNG - ENSEMBLE MODELS")
    print("="*80)
    
    classifier = EnsembleJobClassifier(
        use_high_confidence_only=True,
        confidence_threshold=0.7
    )
    
    results, voting_clf = classifier.run_complete_pipeline()
    
    print("\n\n" + "="*80)
    print("HOÀN THÀNH!")
    print("="*80)
    print("\nĐã tạo các file:")
    print("  - model_comparison.png: Biểu đồ so sánh models")
    
    joblib.dump(classifier.best_model, 'best_model.pkl')
    joblib.dump(voting_clf, 'voting_ensemble.pkl')
    joblib.dump(classifier.tfidf, 'tfidf_vectorizer.pkl')
    joblib.dump(classifier.scaler, 'scaler.pkl')
    
    print("  - best_model.pkl: Best single model")
    print("  - voting_ensemble.pkl: Ensemble model")
    print("  - tfidf_vectorizer.pkl: TF-IDF vectorizer")
    print("  - scaler.pkl: Feature scaler")
```

**Vấn đề:**
- ❌ Models lưu ở thư mục hiện tại, không organized
- ❌ Không có comment hướng dẫn

### ✅ SAU
```python
if __name__ == "__main__":
    
    print("\n" + "="*80)
    print("🤖 HỆ THỐNG PHÂN LOẠI TIN TUYỂN DỤNG - ENSEMBLE MODELS")
    print("="*80)
    
    classifier = EnsembleJobClassifier(
        use_high_confidence_only=True,
        confidence_threshold=0.7
    )
    
    # Chạy pipeline với dữ liệu
    # Bạn có thể thay đổi data_path tại đây:
    # - "../../data/JOB_DATA_IMPROVED_LABELS_KHOA.csv" - Dữ liệu đã xử lý (mặc định)
    # - "../../data/JOB_DATA_FINAL.csv" - Dữ liệu thô (cần FULL_TEXT được tạo tự động)
    
    results, voting_clf = classifier.run_complete_pipeline(
        data_path="../../data/JOB_DATA_IMPROVED_LABELS_KHOA.csv"
    )
    
    print("\n\n" + "="*80)
    print("✅ HOÀN THÀNH!")
    print("="*80)
    print("\n📁 Các file được tạo:")
    print("   - model_comparison.png: Biểu đồ so sánh models")
    
    # Save models
    import os
    
    output_dir = "../../models"
    os.makedirs(output_dir, exist_ok=True)
    
    joblib.dump(classifier.best_model, f'{output_dir}/best_model.pkl')
    joblib.dump(voting_clf, f'{output_dir}/voting_ensemble.pkl')
    joblib.dump(classifier.tfidf, f'{output_dir}/tfidf_vectorizer.pkl')
    joblib.dump(classifier.scaler, f'{output_dir}/scaler.pkl')
    
    print(f"   - {output_dir}/best_model.pkl")
    print(f"   - {output_dir}/voting_ensemble.pkl")
    print(f"   - {output_dir}/tfidf_vectorizer.pkl")
    print(f"   - {output_dir}/scaler.pkl")
    print("\n🎯 Các models đã sẵn sàng để sử dụng!")
```

**Cải tiến:**
- ✅ Tạo output_dir nếu không tồn tại
- ✅ Lưu models vào `models/` folder
- ✅ Ghi chú hướng dẫn thay đổi data_path
- ✅ Emoji cho trực quan

---

## Summary

| Aspect | Trước | Sau |
|--------|-------|-----|
| **Linh hoạt** | Cứng file path | Linh hoạt data_path |
| **Xử lý lỗi** | Cơ bản | Chi tiết, graceful |
| **FULL_TEXT** | Phải có sẵn | Auto-create |
| **Features** | Cứng | Flexible |
| **Logging** | Cơ bản | Rõ ràng với emoji |
| **Organization** | Models ở current dir | Models ở `models/` folder |
| **Documentation** | Không có | Chi tiết trong code |

✅ **Kết quả:** Code mới linh hoạt, rõ ràng, dễ maintain!
