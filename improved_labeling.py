import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class ImprovedLabeling:
    """
    Hệ thống labeling cải tiến với:
    - Multiple heuristic rules
    - Confidence scoring
    - Anomaly detection
    - Semi-supervised approach
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.anomaly_detector = IsolationForest(
            contamination=0.15,  # Giả định 15% là fake
            random_state=42
        )
    
    def rule_based_score(self, row):
        """
        Tính điểm nghi ngờ dựa trên rules (0-10, càng cao càng nghi ngờ)
        """
        score = 0
        reasons = []
        
        # Rule 1: Văn bản quá ngắn
        if row.get('text_length', 0) < 50:
            score += 2
            reasons.append("Nội dung quá ngắn")
        
        # Rule 2: Thiếu thông tin công ty
        if row.get('company_overview_missing', 0) == 1:
            score += 1.5
            reasons.append("Thiếu thông tin công ty")
        
        # Rule 3: Lương bất thường
        if row.get('salary_suspiciously_high', 0) == 1:
            score += 2
            reasons.append("Lương quá cao")
        
        if row.get('salary_too_low', 0) == 1:
            score += 1
            reasons.append("Lương quá thấp")
        
        if row.get('salary_negotiable', 0) == 1 and row.get('text_length', 0) < 100:
            score += 1
            reasons.append("Lương thỏa thuận + nội dung ngắn")
        
        # Rule 4: Scam keywords
        scam_count = row.get('scam_keyword_count', 0)
        if scam_count > 0:
            score += min(scam_count * 1.5, 3)
            reasons.append(f"Có {scam_count} từ khóa nghi ngờ")
        
        # Rule 5: Thiếu keywords tích cực
        positive_count = row.get('positive_keyword_count', 0)
        if positive_count == 0:
            score += 1
            reasons.append("Không có từ khóa tích cực")
        
        # Rule 6: Tuyển hàng loạt + không cần kinh nghiệm
        if row.get('mass_recruitment', 0) == 1 and row.get('no_experience_required', 0) == 1:
            score += 1.5
            reasons.append("Tuyển hàng loạt + không cần KN")
        
        # Rule 7: Công ty nhỏ + lương cao
        if row.get('is_small_company', 0) == 1 and row.get('salary_avg', 0) > 20000000:
            score += 1
            reasons.append("Công ty nhỏ nhưng lương cao")
        
        # Rule 8: Thiếu yêu cầu công việc
        if row.get('requirements_missing', 0) == 1:
            score += 1
            reasons.append("Thiếu yêu cầu công việc")
        
        # Rule 9: Chữ hoa quá nhiều (SPAM style)
        if row.get('uppercase_ratio', 0) > 0.3:
            score += 1
            reasons.append("Quá nhiều chữ hoa")
        
        # Rule 10: Dấu chấm than nhiều
        if row.get('exclamation_count', 0) > 3:
            score += 0.5
            reasons.append("Quá nhiều dấu !")
        
        # Rule 11: Job Type là Part-time + lương cao
        if row.get('is_part_time', 0) == 1 and row.get('salary_avg', 0) > 15000000:
            score += 1.5
            reasons.append("Part-time nhưng lương cao")
        
        # Rule 12: Job Type là Part-time + yêu cầu quản lý
        if row.get('is_part_time', 0) == 1 and row.get('is_management_level', 0) == 1:
            score += 1.5
            reasons.append("Part-time cho vị trí quản lý")
        
        # Rule 13: Career level quản lý + không cần kinh nghiệm
        if row.get('is_management_level', 0) == 1 and row.get('no_experience_required', 0) == 1:
            score += 2
            reasons.append("Quản lý nhưng không cần kinh nghiệm")
        
        # Rule 14: Career level quản lý + kinh nghiệm < 3 năm
        if row.get('is_management_level', 0) == 1 and 0 < row.get('experience_years', 0) < 3:
            score += 1.5
            reasons.append("Quản lý nhưng kinh nghiệm quá ít")
        
        # Rule 15: Entry level + lương quá cao (>20M)
        if row.get('is_entry_level', 0) == 1 and row.get('salary_avg', 0) > 20000000:
            score += 1.5
            reasons.append("Entry level nhưng lương quá cao")
        
        # Rule 16: Entry level + yêu cầu kinh nghiệm cao (>5 năm)
        if row.get('is_entry_level', 0) == 1 and row.get('experience_years', 0) >= 5:
            score += 1
            reasons.append("Entry level nhưng yêu cầu kinh nghiệm cao")
        
        # Rule 17: Career level thiếu (blank) hoặc không rõ
        if row.get('is_management_level', 0) == 0 and row.get('is_entry_level', 0) == 0:
            career_text = str(row.get('career_level_text', '')).strip()
            if not career_text or len(career_text) < 2:
                score += 0.5
                reasons.append("Không có thông tin Career Level")
        
        # Rule 18: Job Type thiếu hoặc không rõ
        if row.get('is_part_time', 0) == 0 and row.get('is_full_time', 0) == 0 and row.get('is_freelance', 0) == 0:
            job_type_text = str(row.get('job_type_text', '')).strip()
            if not job_type_text or len(job_type_text) < 2:
                score += 0.5
                reasons.append("Không có thông tin Job Type")
        
        return min(score, 10), reasons  # Cap ở 10
    
    def anomaly_detection_label(self, df):
        """
        Sử dụng Isolation Forest để phát hiện outliers
        """
        # Chọn features số cho anomaly detection
        numeric_features = [
            'text_length', 'salary_avg', 'company_size_value',
            'experience_years', 'num_candidates',
            'scam_keyword_count', 'positive_keyword_count',
            'uppercase_ratio', 'vocab_diversity'
        ]
        
        # Lọc các cột tồn tại
        available_features = [f for f in numeric_features if f in df.columns]
        
        X = df[available_features].fillna(0)
        
        # Chuẩn hóa
        X_scaled = self.scaler.fit_transform(X)
        
        # Dự đoán anomaly
        anomaly_labels = self.anomaly_detector.fit_predict(X_scaled)
        
        # -1 = anomaly (fake), 1 = normal (real)
        # Chuyển về 0/1
        return (anomaly_labels == 1).astype(int)
    
    def ensemble_labeling(self, df):
        """
        Kết hợp nhiều phương pháp labeling
        """
        print("Bước 1: Rule-based scoring...")
        scores_and_reasons = df.apply(self.rule_based_score, axis=1)
        df['rule_score'] = scores_and_reasons.apply(lambda x: x[0])
        df['rule_reasons'] = scores_and_reasons.apply(lambda x: x[1])
        
        print("Bước 2: Anomaly detection...")
        df['anomaly_label'] = self.anomaly_detection_label(df)
        
        print("Bước 3: Ensemble voting...")
        
        # Label từ rule-based (threshold = 4)
        df['rule_label'] = (df['rule_score'] < 4).astype(int)
        
        # Kết hợp 2 phương pháp
        # Nếu cả 2 đều nói FAKE → chắc chắn FAKE
        # Nếu cả 2 đều nói REAL → chắc chắn REAL
        # Nếu khác nhau → dùng confidence
        
        df['Label'] = 1  # Mặc định REAL
        
        # Cả 2 đều nói FAKE
        df.loc[(df['rule_label'] == 0) & (df['anomaly_label'] == 0), 'Label'] = 0
        
        # Rule-based nói FAKE với điểm cao
        df.loc[df['rule_score'] >= 6, 'Label'] = 0
        
        # Tính confidence score (0-1)
        # Confidence cao = 2 phương pháp đồng thuận
        df['confidence'] = 0.5  # Mặc định
        
        # Cả 2 cùng REAL
        df.loc[(df['rule_label'] == 1) & (df['anomaly_label'] == 1), 'confidence'] = 0.9
        
        # Cả 2 cùng FAKE
        df.loc[(df['rule_label'] == 0) & (df['anomaly_label'] == 0), 'confidence'] = 0.9
        
        # Rule score rất cao hoặc rất thấp
        df.loc[df['rule_score'] >= 7, 'confidence'] = 0.95
        df.loc[df['rule_score'] <= 2, 'confidence'] = 0.85
        
        # Trường hợp không chắc chắn
        df.loc[(df['rule_label'] != df['anomaly_label']) & 
               (df['rule_score'] > 3) & (df['rule_score'] < 6), 'confidence'] = 0.4
        
        return df
    
    def get_high_confidence_samples(self, df, min_confidence=0.7):
        """
        Lọc ra các samples có confidence cao để train model
        """
        return df[df['confidence'] >= min_confidence].copy()
    
    def analyze_labels(self, df):
        """
        Phân tích và thống kê labels
        """
        print("\n" + "="*60)
        print("PHÂN TÍCH KẾT QUẢ LABELING")
        print("="*60)
        
        print(f"\nTổng số mẫu: {len(df)}")
        print(f"\nPhân bố nhãn:")
        print(df['Label'].value_counts())
        print(f"\nTỷ lệ:")
        print(df['Label'].value_counts(normalize=True) * 100)
        
        print(f"\n\nPhân bố Confidence Score:")
        print(df['confidence'].describe())
        
        print(f"\n\nSố mẫu theo ngưỡng confidence:")
        for threshold in [0.5, 0.6, 0.7, 0.8, 0.9]:
            count = len(df[df['confidence'] >= threshold])
            print(f"  Confidence >= {threshold}: {count} mẫu ({count/len(df)*100:.1f}%)")
        
        print(f"\n\nTop 10 lý do tin FAKE phổ biến:")
        fake_samples = df[df['Label'] == 0]
        all_reasons = []
        for reasons_list in fake_samples['rule_reasons']:
            all_reasons.extend(reasons_list)
        
        from collections import Counter
        reason_counts = Counter(all_reasons)
        for reason, count in reason_counts.most_common(10):
            print(f"  {reason}: {count} lần")
        
        return df


# MAIN
if __name__ == "__main__":
    # Load dữ liệu có features nâng cao
    df = pd.read_csv("data/JOB_DATA_ENHANCED_FEATURES.csv")
    
    print(f"Đã load {len(df)} mẫu dữ liệu")
    
    # Khởi tạo labeling system
    labeler = ImprovedLabeling()
    
    # Thực hiện labeling
    df_labeled = labeler.ensemble_labeling(df)
    
    # Phân tích
    df_labeled = labeler.analyze_labels(df_labeled)
    
    # Lưu toàn bộ dữ liệu
    df_labeled.to_csv(
        "data/JOB_DATA_IMPROVED_LABELS.csv",
        index=False,
        encoding="utf-8-sig"
    )
    print(f"\nĐã lưu: JOB_DATA_IMPROVED_LABELS.csv")
    
    # Lưu high-confidence samples riêng (dùng để train)
    df_high_conf = labeler.get_high_confidence_samples(df_labeled, min_confidence=0.7)
    df_high_conf.to_csv(
        "data/JOB_DATA_HIGH_CONFIDENCE.csv",
        index=False,
        encoding="utf-8-sig"
    )
    print(f"Đã lưu: JOB_DATA_HIGH_CONFIDENCE.csv ({len(df_high_conf)} mẫu)")
    
    # Xuất samples để review thủ công
    print("\n" + "="*60)
    print("MẪU ĐỂ REVIEW THỦ CÔNG")
    print("="*60)
    
    # Lấy một số mẫu FAKE với confidence cao
    fake_samples = df_labeled[(df_labeled['Label'] == 0) & 
                              (df_labeled['confidence'] > 0.8)].head(3)
    
    for idx, row in fake_samples.iterrows():
        print(f"\n--- MẪU FAKE #{idx} (Confidence: {row['confidence']:.2f}) ---")
        print(f"Rule Score: {row['rule_score']:.1f}/10")
        print(f"Lý do: {', '.join(row['rule_reasons'])}")
        print(f"Tiêu đề: {row.get('Job Title', 'N/A')[:100]}")
        print(f"Lương: {row.get('Salary', 'N/A')}")
        print(f"Công ty: {row.get('Company Size', 'N/A')}")
