"""
Backend API Flask - Kết nối ML Model với Frontend
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
from scipy.sparse import hstack
import sys
import os
from datetime import datetime

# Import feature extractor
from BE.advanced_features import AdvancedFeatureExtractor

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# ============================================================================
# LOAD MODELS
# ============================================================================

print("🚀 Starting Job Tracker API Server...")
print("=" * 80)

try:
    best_model = joblib.load('best_model.pkl')
    voting_ensemble = joblib.load('voting_ensemble.pkl')
    tfidf = joblib.load('tfidf_vectorizer.pkl')
    scaler = joblib.load('scaler.pkl')
    print("✅ ML Models loaded successfully!")
except Exception as e:
    print(f"⚠️  Warning: Could not load models - {e}")
    print("⚠️  API will run in demo mode (heuristic scoring only)")
    best_model = None
    voting_ensemble = None
    tfidf = None
    scaler = None

# Feature extractor
feature_extractor = AdvancedFeatureExtractor()

print("=" * 80)

# ============================================================================
# JOB PREDICTOR CLASS
# ============================================================================

class JobPredictor:
    """Unified predictor combining ML model and heuristic rules"""
    
    def __init__(self, model, ensemble, tfidf, scaler, extractor):
        self.model = model
        self.ensemble = ensemble
        self.tfidf = tfidf
        self.scaler = scaler
        self.extractor = extractor
        self.has_ml_model = model is not None
    
    def preprocess_text(self, text):
        """Tiền xử lý văn bản đơn giản"""
        if not isinstance(text, str):
            return ""
        
        import re
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        try:
            from pyvi import ViTokenizer
            text = ViTokenizer.tokenize(text)
        except:
            pass
        
        return text
    
    def calculate_heuristic_score(self, job_data):
        """Calculate risk score using heuristic rules"""
        score = 0
        reasons = []
        
        # Extract text
        full_text = " ".join([
            str(job_data.get('title', '')),
            str(job_data.get('description', '')),
            str(job_data.get('companyName', ''))
        ]).lower()
        
        # Check salary
        salary_text = str(job_data.get('salary', ''))
        import re
        salary_numbers = re.findall(r'\d+', salary_text.replace(',', ''))
        
        if salary_numbers:
            avg_salary = sum(map(int, salary_numbers)) / len(salary_numbers)
            if avg_salary > 50000000:
                score += 20
                reasons.append("Mức lương bất thường cao")
            elif avg_salary < 3000000 and avg_salary > 0:
                score += 10
                reasons.append("Mức lương quá thấp")
        
        # Check scam keywords
        scam_keywords = [
            'đóng phí', 'cọc', 'việc nhẹ lương cao', 'kiếm tiền nhanh',
            'không cần kinh nghiệm', 'thu nhập không giới hạn', 'mlm', 'đa cấp',
            'bán hàng online', 'cộng tác viên', 'làm tại nhà', 'tuyển gấp'
        ]
        
        for keyword in scam_keywords:
            if keyword in full_text:
                score += 15
                reasons.append(f'Có từ khóa nghi ngờ: "{keyword}"')
        
        # Check email
        email = str(job_data.get('email', '')).lower()
        if '@gmail.com' in email or '@yahoo.com' in email:
            score += 10
            reasons.append("Email cá nhân (không phải email công ty)")
        
        # Check missing info
        if not job_data.get('address') or len(str(job_data.get('address', ''))) < 10:
            score += 15
            reasons.append("Thiếu địa chỉ công ty")
        
        if not job_data.get('companyName') or len(str(job_data.get('companyName', ''))) < 3:
            score += 10
            reasons.append("Thiếu thông tin công ty")
        
        if not job_data.get('description') or len(str(job_data.get('description', ''))) < 50:
            score += 10
            reasons.append("Mô tả công việc quá ngắn")
        
        return min(score, 100), reasons
    
    def predict_with_ml(self, job_data):
        """Predict using ML model"""
        if not self.has_ml_model:
            return None
        
        try:
            # Create FULL_TEXT
            full_text = " ".join([
                self.preprocess_text(job_data.get('title', '')),
                self.preprocess_text(job_data.get('companyName', '')),
                self.preprocess_text(job_data.get('description', '')),
            ])
            
            # Create DataFrame
            df_input = pd.DataFrame([{
                'FULL_TEXT': full_text,
                'Job Title': job_data.get('title', ''),
                'Company Overview': job_data.get('companyName', ''),
                'Job Description': job_data.get('description', ''),
                'Job Requirements': '',
                'Benefits': '',
                'Salary': job_data.get('salary', ''),
                'Company Size': '',
                'Years of Experience': '',
                'Number Cadidate': 0
            }])
            
            # Extract features
            features = self.extractor.extract_all_features(df_input.iloc[0])
            for key, value in features.items():
                df_input[key] = value
            
            # TF-IDF
            X_text = self.tfidf.transform([full_text])
            
            # Numeric features
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
            
            # Combine
            X = hstack([X_text, X_num_scaled])
            
            # Predict
            prediction = self.model.predict(X)[0]
            probabilities = self.model.predict_proba(X)[0]
            
            return {
                'is_real': bool(prediction),
                'probability_real': float(probabilities[1]),
                'probability_fake': float(probabilities[0]),
                'ml_score': float(probabilities[0] * 100)  # Convert to 0-100 scale
            }
        
        except Exception as e:
            print(f"ML prediction error: {e}")
            return None
    
    def predict(self, job_data, use_ensemble=False):
        """
        Combined prediction using both heuristic and ML
        """
        # Heuristic prediction (always available)
        heuristic_score, reasons = self.calculate_heuristic_score(job_data)
        
        # ML prediction (if available)
        ml_result = self.predict_with_ml(job_data) if self.has_ml_model else None
        
        # Combine scores
        if ml_result:
            # Weighted average: 60% ML, 40% heuristic
            final_score = ml_result['ml_score'] * 0.6 + heuristic_score * 0.4
            confidence = ml_result['probability_real'] if ml_result['is_real'] else ml_result['probability_fake']
            prediction_source = 'ml_hybrid'
        else:
            final_score = heuristic_score
            confidence = 0.5 + (abs(50 - heuristic_score) / 100)  # Higher confidence for extreme scores
            prediction_source = 'heuristic_only'
        
        # Risk level
        if final_score <= 30:
            risk_level = "LOW"
        elif final_score <= 60:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        # Detailed analysis
        analysis = {
            'text_quality': {
                'length': len(str(job_data.get('description', '')).split()),
                'has_details': len(str(job_data.get('description', ''))) > 100
            },
            'salary_info': {
                'provided': bool(job_data.get('salary')),
                'value': job_data.get('salary', 'Không rõ')
            },
            'company_info': {
                'name_provided': bool(job_data.get('companyName')),
                'address_provided': bool(job_data.get('address')),
                'email_provided': bool(job_data.get('email'))
            }
        }
        
        return {
            'risk_score': round(final_score, 2),
            'risk_level': risk_level,
            'confidence': round(confidence, 3),
            'reasons': reasons[:5],  # Top 5 reasons
            'is_safe': final_score <= 30,
            'prediction_source': prediction_source,
            'ml_available': self.has_ml_model,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        }


# Initialize predictor
predictor = JobPredictor(best_model, voting_ensemble, tfidf, scaler, feature_extractor)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'ml_model_loaded': predictor.has_ml_model,
        'server_time': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/analyze-job', methods=['POST'])
def analyze_job():
    """
    Analyze a single job posting
    
    Request body:
    {
        "title": "string",
        "companyName": "string",
        "description": "string",
        "salary": "string",
        "address": "string",
        "email": "string",
        "phone": "string",
        "url": "string"
    }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'error': 'Job title is required'}), 400
        
        # Analyze
        result = predictor.predict(data)
        
        return jsonify({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        print(f"Error in analyze_job: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/batch-analyze', methods=['POST'])
def batch_analyze():
    """
    Analyze multiple job postings
    
    Request body:
    {
        "jobs": [
            {job_data_1},
            {job_data_2},
            ...
        ]
    }
    """
    try:
        data = request.json
        jobs = data.get('jobs', [])
        
        if not jobs:
            return jsonify({'error': 'No jobs provided'}), 400
        
        if len(jobs) > 50:
            return jsonify({'error': 'Maximum 50 jobs per request'}), 400
        
        results = []
        for job in jobs:
            result = predictor.predict(job)
            results.append({
                'job_id': job.get('id'),
                'title': job.get('title'),
                'analysis': result
            })
        
        # Summary stats
        summary = {
            'total': len(results),
            'high_risk': sum(1 for r in results if r['analysis']['risk_level'] == 'HIGH'),
            'medium_risk': sum(1 for r in results if r['analysis']['risk_level'] == 'MEDIUM'),
            'low_risk': sum(1 for r in results if r['analysis']['risk_level'] == 'LOW'),
            'average_score': sum(r['analysis']['risk_score'] for r in results) / len(results)
        }
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': summary
        })
    
    except Exception as e:
        print(f"Error in batch_analyze: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/check-blacklist', methods=['POST'])
def check_blacklist():
    """
    Check if job matches blacklist criteria
    
    Request body:
    {
        "job": {job_data},
        "blacklist": {
            "emails": [],
            "companies": [],
            "phones": []
        }
    }
    """
    try:
        data = request.json
        job = data.get('job', {})
        blacklist = data.get('blacklist', {})
        
        matches = {
            'email': False,
            'company': False,
            'phone': False,
            'details': []
        }
        
        # Check email
        job_email = str(job.get('email', '')).lower()
        for bl_email in blacklist.get('emails', []):
            if bl_email.lower() in job_email:
                matches['email'] = True
                matches['details'].append(f"Email khớp với blacklist: {bl_email}")
        
        # Check company
        job_company = str(job.get('companyName', '')).lower()
        for bl_company in blacklist.get('companies', []):
            if bl_company.lower() in job_company:
                matches['company'] = True
                matches['details'].append(f"Công ty khớp với blacklist: {bl_company}")
        
        # Check phone
        job_phone = str(job.get('phone', ''))
        for bl_phone in blacklist.get('phones', []):
            if bl_phone in job_phone:
                matches['phone'] = True
                matches['details'].append(f"SĐT khớp với blacklist: {bl_phone}")
        
        matches['has_match'] = any([matches['email'], matches['company'], matches['phone']])
        
        return jsonify({
            'success': True,
            'matches': matches
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['POST'])
def get_stats():
    """
    Get statistics from job list
    
    Request body:
    {
        "jobs": [...]
    }
    """
    try:
        data = request.json
        jobs = data.get('jobs', [])
        
        if not jobs:
            return jsonify({'error': 'No jobs provided'}), 400
        
        # Calculate stats
        risk_distribution = {
            'low': 0,
            'medium': 0,
            'high': 0
        }
        
        status_distribution = {}
        total_risk_score = 0
        
        for job in jobs:
            # Risk level
            score = job.get('riskScore', 0)
            if score <= 30:
                risk_distribution['low'] += 1
            elif score <= 60:
                risk_distribution['medium'] += 1
            else:
                risk_distribution['high'] += 1
            
            total_risk_score += score
            
            # Status
            status = job.get('status', 'unknown')
            status_distribution[status] = status_distribution.get(status, 0) + 1
        
        avg_risk_score = total_risk_score / len(jobs) if jobs else 0
        
        return jsonify({
            'success': True,
            'stats': {
                'total_jobs': len(jobs),
                'risk_distribution': risk_distribution,
                'status_distribution': status_distribution,
                'average_risk_score': round(avg_risk_score, 2),
                'safety_rate': round((risk_distribution['low'] / len(jobs)) * 100, 1) if jobs else 0
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/model-info', methods=['GET'])
def model_info():
    """Get information about the ML model"""
    return jsonify({
        'success': True,
        'info': {
            'ml_model_available': predictor.has_ml_model,
            'model_type': 'Ensemble (RF + XGBoost + LightGBM)' if predictor.has_ml_model else 'Heuristic only',
            'features_count': 30 if predictor.has_ml_model else 'N/A',
            'expected_performance': {
                'f1_score': '0.85-0.92' if predictor.has_ml_model else 'N/A',
                'auc_roc': '0.90-0.95' if predictor.has_ml_model else 'N/A'
            },
            'supported_languages': ['Vietnamese'],
            'version': '1.0.0'
        }
    })

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 JOB TRACKER API SERVER")
    print("="*80)
    print("\n📡 Available Endpoints:")
    print("  GET  /health                - Health check")
    print("  POST /api/analyze-job       - Analyze single job posting")
    print("  POST /api/batch-analyze     - Analyze multiple jobs")
    print("  POST /api/check-blacklist   - Check blacklist matches")
    print("  POST /api/stats             - Get job statistics")
    print("  GET  /api/model-info        - Get model information")
    print("\n🔧 Configuration:")
    print(f"  ML Model: {'✅ Loaded' if predictor.has_ml_model else '⚠️  Not loaded (heuristic mode)'}")
    print(f"  CORS: ✅ Enabled")
    print(f"  Port: 5000")
    print("\n" + "="*80)
    print("Starting server...\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
