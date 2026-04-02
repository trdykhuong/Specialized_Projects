"""
API Demo cho hệ thống phát hiện tin tuyển dụng giả
Sử dụng Flask để tạo REST API
"""

from flask import Flask, request, jsonify
import joblib
import pandas as pd
import numpy as np
from scipy.sparse import hstack
import sys
import os

# Import feature extractor
from BE.advanced_features import AdvancedFeatureExtractor

app = Flask(__name__)

# Load models và transformers
print("Đang load models...")
try:
    best_model = joblib.load('best_model.pkl')
    voting_ensemble = joblib.load('voting_ensemble.pkl')
    tfidf = joblib.load('tfidf_vectorizer.pkl')
    scaler = joblib.load('scaler.pkl')
    print("✓ Models loaded successfully!")
except Exception as e:
    print(f"Lỗi khi load models: {e}")
    print("Vui lòng chạy ensemble_training.py trước để tạo models")
    best_model = None

# Feature extractor
feature_extractor = AdvancedFeatureExtractor()


class JobPostingPredictor:
    """Class để dự đoán độ tin cậy của tin tuyển dụng"""
    
    def __init__(self, model, ensemble, tfidf, scaler, extractor):
        self.model = model
        self.ensemble = ensemble
        self.tfidf = tfidf
        self.scaler = scaler
        self.extractor = extractor
    
    def preprocess_text(self, text):
        """Tiền xử lý văn bản đơn giản"""
        if not isinstance(text, str):
            return ""
        
        import re
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Tách từ tiếng Việt (có thể bỏ qua nếu không có PyVi)
        try:
            from pyvi import ViTokenizer
            text = ViTokenizer.tokenize(text)
        except:
            pass
        
        return text
    
    def prepare_input(self, job_data):
        """
        Chuẩn bị input từ dữ liệu tin tuyển dụng
        
        job_data = {
            'job_title': str,
            'company_overview': str,
            'job_description': str,
            'job_requirements': str,
            'benefits': str,
            'salary': str,
            'company_size': str,
            'years_of_experience': str,
            'number_candidates': int
        }
        """
        
        # 1. Tạo FULL_TEXT
        full_text = " ".join([
            self.preprocess_text(job_data.get('job_title', '')),
            self.preprocess_text(job_data.get('company_overview', '')),
            self.preprocess_text(job_data.get('job_description', '')),
            self.preprocess_text(job_data.get('job_requirements', '')),
            self.preprocess_text(job_data.get('benefits', ''))
        ])
        
        # 2. Tạo DataFrame từ input
        df_input = pd.DataFrame([{
            'FULL_TEXT': full_text,
            'Job Title': job_data.get('job_title', ''),
            'Company Overview': job_data.get('company_overview', ''),
            'Job Description': job_data.get('job_description', ''),
            'Job Requirements': job_data.get('job_requirements', ''),
            'Benefits': job_data.get('benefits', ''),
            'Salary': job_data.get('salary', ''),
            'Company Size': job_data.get('company_size', ''),
            'Years of Experience': job_data.get('years_of_experience', ''),
            'Number Cadidate': job_data.get('number_candidates', 0)
        }])
        
        # 3. Trích xuất features
        features = self.extractor.extract_all_features(df_input.iloc[0])
        for key, value in features.items():
            df_input[key] = value
        
        # 4. TF-IDF
        X_text = self.tfidf.transform([full_text])
        
        # 5. Numeric features
        numeric_features = [
            'text_length', 'char_length', 'avg_word_length',
            'uppercase_ratio', 'exclamation_count', 'number_count',
            'vocab_diversity', 'scam_keyword_count', 'positive_keyword_count',
            'max_word_repetition',
            'salary_missing', 'salary_negotiable', 'salary_avg',
            'salary_range_width', 'salary_suspiciously_high', 'salary_too_low',
            'company_size_missing', 'company_size_value', 'is_small_company',
            'company_overview_length', 'company_overview_missing',
            'no_experience_required', 'experience_years',
            'num_candidates', 'mass_recruitment',
            'requirements_length', 'requirements_missing'
        ]
        
        available_features = [f for f in numeric_features if f in df_input.columns]
        X_num = df_input[available_features].fillna(0).values
        X_num_scaled = self.scaler.transform(X_num)
        
        # 6. Combine
        X = hstack([X_text, X_num_scaled])
        
        return X, df_input
    
    def predict(self, job_data, use_ensemble=False):
        """
        Dự đoán độ tin cậy của tin tuyển dụng
        
        Returns:
        {
            'is_real': bool,
            'confidence': float (0-1),
            'probability_real': float,
            'probability_fake': float,
            'risk_level': str,
            'warnings': list,
            'analysis': dict
        }
        """
        
        # Chuẩn bị input
        X, df_features = self.prepare_input(job_data)
        
        # Chọn model
        model = self.ensemble if use_ensemble else self.model
        
        # Dự đoán
        prediction = model.predict(X)[0]
        probabilities = model.predict_proba(X)[0]
        
        prob_fake = probabilities[0]
        prob_real = probabilities[1]
        
        # Phân loại risk level
        if prob_real >= 0.8:
            risk_level = "LOW"
        elif prob_real >= 0.6:
            risk_level = "MEDIUM"
        elif prob_real >= 0.4:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"
        
        # Phân tích warnings
        warnings = []
        row = df_features.iloc[0]
        
        if row.get('scam_keyword_count', 0) > 0:
            warnings.append(f"Phát hiện {int(row['scam_keyword_count'])} từ khóa nghi ngờ")
        
        if row.get('salary_suspiciously_high', 0) == 1:
            warnings.append("Mức lương bất thường cao")
        
        if row.get('text_length', 0) < 50:
            warnings.append("Nội dung quá ngắn, thiếu chi tiết")
        
        if row.get('company_overview_missing', 0) == 1:
            warnings.append("Thiếu thông tin về công ty")
        
        if row.get('requirements_missing', 0) == 1:
            warnings.append("Thiếu yêu cầu công việc chi tiết")
        
        if row.get('mass_recruitment', 0) == 1 and row.get('no_experience_required', 0) == 1:
            warnings.append("Tuyển hàng loạt + không cần kinh nghiệm (nghi ngờ cao)")
        
        if row.get('positive_keyword_count', 0) == 0:
            warnings.append("Không có thông tin về phúc lợi/quyền lợi")
        
        # Analysis
        analysis = {
            'text_quality': {
                'length': int(row.get('text_length', 0)),
                'vocabulary_diversity': float(row.get('vocab_diversity', 0)),
                'professional_level': 'Low' if row.get('text_length', 0) < 100 else 'Medium' if row.get('text_length', 0) < 300 else 'High'
            },
            'salary_info': {
                'average': int(row.get('salary_avg', 0)),
                'is_negotiable': bool(row.get('salary_negotiable', 0)),
                'is_suspicious': bool(row.get('salary_suspiciously_high', 0) or row.get('salary_too_low', 0))
            },
            'company_info': {
                'size': int(row.get('company_size_value', 0)),
                'has_overview': not bool(row.get('company_overview_missing', 0)),
                'is_small_company': bool(row.get('is_small_company', 0))
            },
            'keywords': {
                'scam_count': int(row.get('scam_keyword_count', 0)),
                'positive_count': int(row.get('positive_keyword_count', 0))
            }
        }
        
        return {
            'is_real': bool(prediction),
            'confidence': float(max(prob_real, prob_fake)),
            'probability_real': float(prob_real),
            'probability_fake': float(prob_fake),
            'risk_level': risk_level,
            'warnings': warnings,
            'analysis': analysis
        }


# Khởi tạo predictor
if best_model:
    predictor = JobPostingPredictor(
        best_model, voting_ensemble, tfidf, scaler, feature_extractor
    )
else:
    predictor = None


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': best_model is not None
    })


@app.route('/predict', methods=['POST'])
def predict():
    """
    Endpoint để dự đoán độ tin cậy của tin tuyển dụng
    
    Request body:
    {
        "job_title": "string",
        "company_overview": "string",
        "job_description": "string",
        "job_requirements": "string",
        "benefits": "string",
        "salary": "string",
        "company_size": "string",
        "years_of_experience": "string",
        "number_candidates": int,
        "use_ensemble": bool (optional, default: false)
    }
    """
    
    if not predictor:
        return jsonify({
            'error': 'Model not loaded'
        }), 500
    
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['job_title', 'job_description']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Dự đoán
        use_ensemble = data.get('use_ensemble', False)
        result = predictor.predict(data, use_ensemble=use_ensemble)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/batch_predict', methods=['POST'])
def batch_predict():
    """
    Endpoint để dự đoán nhiều tin tuyển dụng cùng lúc
    
    Request body:
    {
        "jobs": [
            {job_data_1},
            {job_data_2},
            ...
        ],
        "use_ensemble": bool (optional)
    }
    """
    
    if not predictor:
        return jsonify({
            'error': 'Model not loaded'
        }), 500
    
    try:
        data = request.json
        jobs = data.get('jobs', [])
        use_ensemble = data.get('use_ensemble', False)
        
        if not jobs:
            return jsonify({
                'error': 'No jobs provided'
            }), 400
        
        results = []
        for job in jobs:
            result = predictor.predict(job, use_ensemble=use_ensemble)
            results.append(result)
        
        # Tổng hợp thống kê
        summary = {
            'total': len(results),
            'real_count': sum(1 for r in results if r['is_real']),
            'fake_count': sum(1 for r in results if not r['is_real']),
            'high_risk_count': sum(1 for r in results if r['risk_level'] in ['HIGH', 'CRITICAL'])
        }
        
        return jsonify({
            'results': results,
            'summary': summary
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("API SERVER - Job Posting Authenticity Checker")
    print("="*60)
    print("\nEndpoints:")
    print("  GET  /health           - Health check")
    print("  POST /predict          - Predict single job")
    print("  POST /batch_predict    - Predict multiple jobs")
    print("\nStarting server...")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
