import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class ImprovedLabeling:
    """
    Hệ thống labeling cải tiến với:
    - Multiple heuristic rules (bao gồm company lookup features)
    - Confidence scoring
    - Anomaly detection
    - Semi-supervised approach
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.anomaly_detector = IsolationForest(
            contamination=0.15,
            random_state=42
        )

    def rule_based_score(self, row):
        """
        Tính điểm nghi ngờ dựa trên rules (0-10, càng cao càng nghi ngờ).
        """
        score = 0
        reasons = []

        # ── Rules cũ ─────────────────────────────────────────────────────────

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
        if row.get('positive_keyword_count', 0) == 0:
            score += 1
            reasons.append("Không có từ khóa tích cực")

        # Rule 6: Tuyển hàng loạt + không cần kinh nghiệm
        if row.get('mass_recruitment', 0) == 1 and row.get('no_experience_required', 0) == 1:
            score += 1.5
            reasons.append("Tuyển hàng loạt + không cần KN")

        # Rule 7: Công ty nhỏ + lương cao
        if row.get('is_small_company', 0) == 1 and row.get('salary_avg', 0) > 20_000_000:
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

        # ── Rules mới: Company Lookup features ───────────────────────────────

        # Rule 11: Không tìm thấy công ty trên masothue
        # (company_found = 0 khi đã có tên công ty nhưng không tra được MST)
        if row.get('company_extracted', 1) == 1 and row.get('company_found', 1) == 0:
            score += 1.5
            reasons.append("Không tìm thấy công ty trên masothue")

        # Rule 12: Công ty đã ngừng hoạt động
        if row.get('company_closed', 0) == 1:
            score += 3
            reasons.append("Công ty đã ngừng hoạt động")

        # Rule 13: Công ty mới thành lập (< 6 tháng) nhưng tuyển nhiều
        age = row.get('company_age_months', 999)
        if 0 < age < 6 and row.get('mass_recruitment', 0) == 1:
            score += 1.5
            reasons.append("Công ty mới < 6 tháng + tuyển hàng loạt")

        # Rule 14: Dư luận tiêu cực (keyword-based)
        rep_score = row.get('reputation_score', 0)
        if rep_score > 0.6:
            score += 2
            reasons.append(f"Dư luận tiêu cực cao ({rep_score:.2f})")
        elif rep_score > 0.3:
            score += 1
            reasons.append(f"Có dư luận tiêu cực ({rep_score:.2f})")

        # Rule 15: Nhiều hits tiêu cực (keyword)
        neg_hits = row.get('reputation_negative_hits', 0)
        if neg_hits >= 3:
            score += 1
            reasons.append(f"Nhiều kết quả phốt ({neg_hits} hits)")

        # Rule 16 (DL): Nếu có BERT reputation score
        dl_rep = row.get('dl_rep_score', None)
        if dl_rep is not None and dl_rep > 0.7:
            score += 2
            reasons.append(f"BERT rep score cao ({dl_rep:.2f})")

        # Rule ngược: công ty đã xác minh + đang hoạt động lâu năm → bớt nghi ngờ
        if row.get('company_active', 0) == 1 and age > 24:
            score = max(score - 1, 0)
            reasons.append(f"Công ty đang hoạt động ({age} tháng) [giảm điểm]")

        return min(score, 10), reasons  # Cap ở 10

    def anomaly_detection_label(self, df):
        """Isolation Forest để phát hiện outliers."""
        numeric_features = [
            'text_length', 'salary_avg', 'company_size_value',
            'experience_years', 'num_candidates',
            'scam_keyword_count', 'positive_keyword_count',
            'uppercase_ratio', 'vocab_diversity',
            # Thêm company features vào anomaly detection
            'company_found', 'company_active', 'company_closed',
            'company_age_months', 'reputation_score',
        ]
        available = [f for f in numeric_features if f in df.columns]
        X = df[available].fillna(0)
        X_scaled = self.scaler.fit_transform(X)
        labels = self.anomaly_detector.fit_predict(X_scaled)
        return (labels == 1).astype(int)

    def ensemble_labeling(self, df):
        """Kết hợp nhiều phương pháp labeling."""
        print("Bước 1: Rule-based scoring...")
        scores_and_reasons = df.apply(self.rule_based_score, axis=1)
        df['rule_score']   = scores_and_reasons.apply(lambda x: x[0])
        df['rule_reasons'] = scores_and_reasons.apply(lambda x: x[1])

        print("Bước 2: Anomaly detection...")
        df['anomaly_label'] = self.anomaly_detection_label(df)

        print("Bước 3: Ensemble voting...")

        df['rule_label'] = (df['rule_score'] < 4).astype(int)
        df['Label'] = 1  # Mặc định REAL

        # Cả 2 đều nói FAKE
        df.loc[(df['rule_label'] == 0) & (df['anomaly_label'] == 0), 'Label'] = 0
        # Rule-based score rất cao
        df.loc[df['rule_score'] >= 6, 'Label'] = 0
        # Công ty đã ngừng hoạt động → chắc chắn đáng ngờ
        if 'company_closed' in df.columns:
            df.loc[df['company_closed'] == 1, 'Label'] = 0

        # Confidence score
        df['confidence'] = 0.5
        df.loc[(df['rule_label'] == 1) & (df['anomaly_label'] == 1), 'confidence'] = 0.9
        df.loc[(df['rule_label'] == 0) & (df['anomaly_label'] == 0), 'confidence'] = 0.9
        df.loc[df['rule_score'] >= 7, 'confidence'] = 0.95
        df.loc[df['rule_score'] <= 2, 'confidence'] = 0.85
        df.loc[
            (df['rule_label'] != df['anomaly_label']) &
            (df['rule_score'] > 3) & (df['rule_score'] < 6),
            'confidence'
        ] = 0.4
        # Công ty active + tuổi cao → tăng confidence REAL
        if 'company_active' in df.columns and 'company_age_months' in df.columns:
            df.loc[
                (df['company_active'] == 1) & (df['company_age_months'] > 24) & (df['Label'] == 1),
                'confidence'
            ] = df['confidence'].clip(upper=1.0).apply(lambda x: min(x + 0.1, 1.0))

        return df

    def get_high_confidence_samples(self, df, min_confidence=0.7):
        return df[df['confidence'] >= min_confidence].copy()

    def analyze_labels(self, df):
        print("\n" + "=" * 60)
        print("PHÂN TÍCH KẾT QUẢ LABELING")
        print("=" * 60)
        print(f"\nTổng số mẫu: {len(df)}")
        print(f"\nPhân bố nhãn:")
        print(df['Label'].value_counts())
        print(f"\nTỷ lệ:")
        print(df['Label'].value_counts(normalize=True) * 100)
        print(f"\nPhân bố Confidence Score:")
        print(df['confidence'].describe())
        print(f"\nSố mẫu theo ngưỡng confidence:")
        for threshold in [0.5, 0.6, 0.7, 0.8, 0.9]:
            count = len(df[df['confidence'] >= threshold])
            print(f"  >= {threshold}: {count} mẫu ({count/len(df)*100:.1f}%)")

        if 'company_found' in df.columns:
            print(f"\nThống kê company features:")
            print(f"  Tìm thấy MST   : {df['company_found'].sum()} / {len(df)}")
            if 'company_active' in df.columns:
                print(f"  Đang hoạt động : {df['company_active'].sum()}")
            if 'company_closed' in df.columns:
                print(f"  Ngừng hoạt động: {df['company_closed'].sum()}")
            if 'reputation_score' in df.columns:
                print(f"  Có dư luận tiêu cực (>0.3): {(df['reputation_score'] > 0.3).sum()}")

        print(f"\nTop 10 lý do FAKE phổ biến:")
        from collections import Counter
        fake_df = df[df['Label'] == 0]
        all_reasons = []
        for r in fake_df['rule_reasons']:
            all_reasons.extend(r)
        for reason, count in Counter(all_reasons).most_common(10):
            print(f"  {reason}: {count} lần")

        return df


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    import os

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    DATA_DIR = os.path.join(BASE_DIR, "data")

    # ── Đọc từ JOB_DATA_WITH_COMPANY (đã có company + reputation features) ──
    input_path = os.path.join(DATA_DIR, "../data/JOB_DATA_WITH_COMPANY.csv")
    print(f"Đọc dữ liệu từ: {input_path}")
    df = pd.read_csv(input_path, encoding="utf-8-sig")
    print(f"Đã load {len(df)} mẫu")

    # In danh sách company features có trong file
    company_cols = [c for c in df.columns if c.startswith(('company_', 'reputation_', 'dl_rep'))]
    print(f"Company features có sẵn: {company_cols}")

    labeler = ImprovedLabeling()
    df_labeled = labeler.ensemble_labeling(df)
    df_labeled = labeler.analyze_labels(df_labeled)

    out_all = os.path.join(DATA_DIR, "../data/JOB_DATA_IMPROVED_LABELS.csv")
    df_labeled.to_csv(out_all, index=False, encoding="utf-8-sig")
    print(f"\nĐã lưu: {out_all}")

    df_hc = labeler.get_high_confidence_samples(df_labeled, min_confidence=0.7)
    out_hc = os.path.join(DATA_DIR, "../data/JOB_DATA_HIGH_CONFIDENCE.csv")
    df_hc.to_csv(out_hc, index=False, encoding="utf-8-sig")
    print(f"Đã lưu: {out_hc} ({len(df_hc)} mẫu)")