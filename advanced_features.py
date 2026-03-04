import pandas as pd
import re
from collections import Counter
import numpy as np

class AdvancedFeatureExtractor:
    """
    Trích xuất các features nâng cao để phát hiện tin tuyển dụng giả
    """
    
    def __init__(self):
        # Danh sách domain email đáng tin cậy
        self.trusted_domains = [
            'gmail.com', 'yahoo.com', 'outlook.com',
            'vn', 'com.vn', 'edu.vn', 'gov.vn'
        ]
        
        # Từ khóa báo hiệu fake (mở rộng)
        self.scam_keywords = [
            'việc_nhẹ', 'lương_cao', 'thu_nhập không giới_hạn',
            'không cần kinh_nghiệm', 'kiếm tiền nhanh',
            'tuyển gấp', 'làm tại nhà', 'tuyển_dụng online',
            'cộng_tác_viên', 'bán hàng online', 'mmo',
            'đa_cấp', 'hoa_hồng cao', 'passive income'
        ]
        
        # Từ khóa tích cực (công ty uy tín)
        self.positive_keywords = [
            'bảo_hiểm', 'hợp_đồng lao_động', 'đóng bảo_hiểm',
            'phụ_cấp', 'thưởng', 'du_lịch', 'đào_tạo',
            'nghỉ phép', 'tăng lương', 'thăng_tiến'
        ]
    
    def extract_text_features(self, text):
        """Trích xuất features từ văn bản"""
        if not isinstance(text, str):
            text = ""
        
        features = {}
        
        # 1. Độ dài văn bản
        words = text.split()
        features['text_length'] = len(words)
        features['char_length'] = len(text)
        features['avg_word_length'] = np.mean([len(w) for w in words]) if words else 0
        
        # 2. Tỷ lệ chữ hoa (SPAM thường dùng nhiều chữ hoa)
        features['uppercase_ratio'] = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        
        # 3. Tỷ lệ dấu chấm than (!!!)
        features['exclamation_count'] = text.count('!')
        features['question_count'] = text.count('?')
        
        # 4. Số lượng số (tin fake thường nhấn mạnh số tiền)
        features['number_count'] = len(re.findall(r'\d+', text))
        
        # 5. Độ đa dạng từ vựng (vocabulary richness)
        unique_words = set(words)
        features['vocab_diversity'] = len(unique_words) / len(words) if words else 0
        
        # 6. Scam keywords
        features['scam_keyword_count'] = sum(1 for kw in self.scam_keywords if kw in text)
        
        # 7. Positive keywords
        features['positive_keyword_count'] = sum(1 for kw in self.positive_keywords if kw in text)
        
        # 8. Tỷ lệ từ lặp lại (spam thường lặp từ khóa)
        word_freq = Counter(words)
        if words:
            max_freq = max(word_freq.values())
            features['max_word_repetition'] = max_freq / len(words)
        else:
            features['max_word_repetition'] = 0
        
        return features
    
    def extract_salary_features(self, salary_text):
        """Trích xuất features từ thông tin lương"""
        features = {}
        
        if not isinstance(salary_text, str):
            features['salary_missing'] = 1
            features['salary_negotiable'] = 0
            features['salary_range_width'] = 0
            features['salary_avg'] = 0
            return features
        
        salary_text = salary_text.lower()
        
        # 1. Thiếu thông tin lương
        features['salary_missing'] = 0
        
        # 2. Lương thỏa thuận
        features['salary_negotiable'] = 1 if 'thỏa thuận' in salary_text or 'negotiable' in salary_text else 0
        
        # 3. Phân tích khoảng lương
        numbers = re.findall(r'\d+', salary_text.replace(',', ''))
        
        if len(numbers) == 0:
            features['salary_range_width'] = 0
            features['salary_avg'] = 0
        elif len(numbers) == 1:
            features['salary_range_width'] = 0
            features['salary_avg'] = int(numbers[0])
        else:
            nums = [int(n) for n in numbers]
            features['salary_avg'] = sum(nums) / len(nums)
            features['salary_range_width'] = max(nums) - min(nums)
        
        # 4. Lương quá cao đáng ngờ (>50M cho junior)
        features['salary_suspiciously_high'] = 1 if features['salary_avg'] > 50000000 else 0
        
        # 5. Lương quá thấp (<3M)
        features['salary_too_low'] = 1 if 0 < features['salary_avg'] < 3000000 else 0
        
        return features
    
    def extract_company_features(self, row):
        """Trích xuất features từ thông tin công ty"""
        features = {}
        
        # 1. Kích thước công ty
        company_size = row.get('Company Size', '')
        if pd.isna(company_size) or company_size == 0 or company_size == '':
            features['company_size_missing'] = 1
            features['company_size_value'] = 0
        else:
            features['company_size_missing'] = 0
            features['company_size_value'] = self._parse_company_size(company_size)
        
        # 2. Công ty nhỏ (<50 người) - rủi ro cao hơn
        features['is_small_company'] = 1 if 0 < features['company_size_value'] < 50 else 0
        
        # 3. Tên công ty
        company_overview = str(row.get('Company Overview', ''))
        features['company_overview_length'] = len(company_overview)
        features['company_overview_missing'] = 1 if len(company_overview) < 50 else 0
        
        return features
    
    def extract_requirement_features(self, row):
        """Trích xuất features từ yêu cầu công việc"""
        features = {}
        
        # 1. Kinh nghiệm
        exp_text = str(row.get('Years of Experience', ''))
        
        if 'không' in exp_text.lower() or exp_text == '':
            features['no_experience_required'] = 1
            features['experience_years'] = 0
        else:
            features['no_experience_required'] = 0
            features['experience_years'] = self._parse_experience(exp_text)
        
        # 2. Số lượng tuyển
        num_candidate = row.get('Number Cadidate', 0)
        if pd.isna(num_candidate):
            num_candidate = 0
        
        features['num_candidates'] = num_candidate
        features['mass_recruitment'] = 1 if num_candidate > 20 else 0  # Tuyển hàng loạt
        
        # 3. Yêu cầu công việc
        job_req = str(row.get('Job Requirements', ''))
        features['requirements_length'] = len(job_req.split())
        features['requirements_missing'] = 1 if len(job_req.split()) < 20 else 0
        
        return features
    
    def _parse_company_size(self, size_text):
        """Parse company size to number"""
        if not isinstance(size_text, str):
            return 0
        
        size_text = size_text.lower()
        
        if "trên" in size_text or "more" in size_text:
            numbers = re.findall(r'\d+', size_text)
            return int(numbers[0]) if numbers else 0
        
        numbers = re.findall(r'\d+', size_text)
        if len(numbers) == 0:
            return 0
        
        numbers = list(map(int, numbers))
        return sum(numbers) // len(numbers)
    
    def _parse_experience(self, exp_text):
        """Parse experience to years"""
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
    
    def extract_all_features(self, row):
        """Trích xuất tất cả features từ một hàng dữ liệu"""
        all_features = {}
        
        # Text features
        text_features = self.extract_text_features(row.get('FULL_TEXT', ''))
        all_features.update(text_features)
        
        # Salary features
        salary_features = self.extract_salary_features(row.get('Salary', ''))
        all_features.update(salary_features)
        
        # Company features
        company_features = self.extract_company_features(row)
        all_features.update(company_features)
        
        # Requirement features
        requirement_features = self.extract_requirement_features(row)
        all_features.update(requirement_features)
        
        return all_features


# MAIN: Áp dụng feature extraction
if __name__ == "__main__":
    # Load dữ liệu đã preprocess
    df = pd.read_csv("data/JOB_DATA_LABELLED.csv")
    
    # Khởi tạo feature extractor
    extractor = AdvancedFeatureExtractor()
    
    # Trích xuất features cho từng hàng
    print("Đang trích xuất features nâng cao...")
    features_list = []
    
    for idx, row in df.iterrows():
        if idx % 100 == 0:
            print(f"Đã xử lý {idx}/{len(df)} hàng")
        
        features = extractor.extract_all_features(row)
        features_list.append(features)
    
    # Chuyển thành DataFrame
    features_df = pd.DataFrame(features_list)
    
    # Ghép với dữ liệu gốc
    df_enhanced = pd.concat([df, features_df], axis=1)
    
    # Lưu file
    df_enhanced.to_csv(
        "data/JOB_DATA_ENHANCED_FEATURES.csv",
        index=False,
        encoding="utf-8-sig"
    )
    
    print(f"\nĐã lưu file với {len(features_df.columns)} features mới!")
    print("\nDanh sách features:")
    print(features_df.columns.tolist())
    print("\nThống kê features:")
    print(features_df.describe())
