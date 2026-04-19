import re
import joblib
import numpy as np
import pandas as pd
from collections import Counter
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from scipy.sparse import hstack

app = Flask(__name__)
CORS(app)

# ============================================================
# LOAD MODELS
# ============================================================

print("Loading models...")
try:
    import os
    MODEL_DIR = os.path.join(os.path.dirname(__file__), '../../models')
    best_model     = joblib.load(os.path.join(MODEL_DIR, 'best_model.pkl'))
    voting_ensemble= joblib.load(os.path.join(MODEL_DIR, 'voting_ensemble.pkl'))
    tfidf          = joblib.load(os.path.join(MODEL_DIR, 'tfidf_vectorizer.pkl'))
    scaler         = joblib.load(os.path.join(MODEL_DIR, 'scaler.pkl'))
    feature_names  = joblib.load(os.path.join(MODEL_DIR, 'feature_names.pkl'))
    models_loaded  = True
    print(f"Models loaded — {len(feature_names)} numeric features")
except Exception as e:
    print(f"Error loading models: {e}")
    models_loaded = False
    feature_names = []

# ============================================================
# KEYWORD LISTS (khớp với advanced_features.py sau tokenize)
# ============================================================

_SCAM_KEYWORDS = [
    'việc nhẹ', 'lương cao', 'thu nhập không giới hạn',
    'không cần kinh nghiệm', 'kiếm tiền nhanh',
    'tuyển gấp', 'làm tại nhà', 'tuyển dụng online',
    'cộng tác viên', 'bán hàng online', 'đa cấp',
    'hoa hồng cao', 'passive income',
]

_POSITIVE_KEYWORDS = [
    'bảo hiểm', 'hợp đồng lao động', 'đóng bảo hiểm',
    'phụ cấp', 'thưởng', 'du lịch', 'đào tạo',
    'nghỉ phép', 'tăng lương', 'thăng tiến',
]

# ============================================================
# FEATURE HELPERS
# ============================================================

def _build_full_text(data: dict) -> str:
    parts = [
        data.get('title', ''),
        data.get('companyOverview', ''),
        data.get('description', ''),
        data.get('requirements', ''),
        data.get('benefits', ''),
    ]
    return ' '.join(p for p in parts if p).lower()


def _parse_salary(salary_text: str) -> dict:
    if not isinstance(salary_text, str) or not salary_text.strip():
        return {'missing': 1, 'negotiable': 0, 'avg': 0, 'range_width': 0,
                'suspiciously_high': 0, 'too_low': 0}
    s = salary_text.lower()
    negotiable = int('thỏa thuận' in s or 'negotiable' in s)
    numbers = [int(n) for n in re.findall(r'\d+', s.replace(',', '')) if int(n) > 0]
    if not numbers:
        avg, rng = 0, 0
    elif len(numbers) == 1:
        avg, rng = numbers[0], 0
    else:
        avg = sum(numbers) / len(numbers)
        rng = max(numbers) - min(numbers)
    return {
        'missing': 0,
        'negotiable': negotiable,
        'avg': avg,
        'range_width': rng,
        'suspiciously_high': int(avg > 50_000_000),
        'too_low': int(0 < avg < 3_000_000),
    }


def _parse_company_size(size_text: str) -> int:
    if not isinstance(size_text, str):
        return 0
    nums = list(map(int, re.findall(r'\d+', size_text)))
    if not nums:
        return 0
    return sum(nums) // len(nums)


def extract_numeric_features(data: dict) -> np.ndarray:
    """Trích xuất numeric features từ API input, zero-fill những gì không có."""
    text  = _build_full_text(data)
    words = text.split()
    sal   = _parse_salary(data.get('salary', ''))

    word_freq   = Counter(words)
    max_rep     = (max(word_freq.values()) / len(words)) if words else 0
    unique_ratio= len(set(words)) / len(words) if words else 0

    size_val = _parse_company_size(data.get('companySize', ''))

    num_cand = int(data.get('numCandidates', 0) or 0)
    exp_text = str(data.get('yearsExp', '')).lower()
    no_exp   = int('không' in exp_text or exp_text == '')
    exp_nums = list(map(int, re.findall(r'\d+', exp_text)))
    exp_yrs  = (sum(exp_nums) // len(exp_nums)) if exp_nums else 0

    overview = str(data.get('companyOverview', ''))
    req_text = str(data.get('requirements', ''))
    req_words= req_text.split()

    career   = str(data.get('careerLevel', '')).lower()
    job_type = str(data.get('jobType', '')).lower()

    feature_map = {
        # Text
        'text_length':            len(words),
        'char_length':            len(text),
        'avg_word_length':        (sum(len(w) for w in words) / len(words)) if words else 0,
        'uppercase_ratio':        sum(1 for c in text if c.isupper()) / len(text) if text else 0,
        'exclamation_count':      text.count('!'),
        'question_count':         text.count('?'),
        'number_count':           len(re.findall(r'\d+', text)),
        'vocab_diversity':        unique_ratio,
        'scam_keyword_count':     sum(1 for kw in _SCAM_KEYWORDS if kw in text),
        'positive_keyword_count': sum(1 for kw in _POSITIVE_KEYWORDS if kw in text),
        'max_word_repetition':    max_rep,
        # Salary
        'salary_missing':           sal['missing'],
        'salary_negotiable':        sal['negotiable'],
        'salary_avg':               sal['avg'],
        'salary_range_width':       sal['range_width'],
        'salary_suspiciously_high': sal['suspiciously_high'],
        'salary_too_low':           sal['too_low'],
        # Company basic
        'company_size_missing':    int(size_val == 0),
        'company_size_value':      size_val,
        'is_small_company':        int(0 < size_val < 50),
        'company_overview_length': len(overview),
        'company_overview_missing':int(len(overview) < 50),
        # Requirements
        'no_experience_required': no_exp,
        'experience_years':       exp_yrs,
        'num_candidates':         num_cand,
        'mass_recruitment':       int(num_cand > 20),
        'requirements_length':    len(req_words),
        'requirements_missing':   int(len(req_words) < 20),
        'is_management_level':    int(any(kw in career for kw in ['quản lý', 'manager', 'lead', 'director', 'supervisor'])),
        'is_entry_level':         int(any(kw in career for kw in ['nhân viên', 'entry', 'junior', 'fresher'])),
        'is_part_time':           int('part' in job_type or 'bán thời gian' in job_type),
        'is_full_time':           int('full' in job_type or 'toàn thời gian' in job_type),
        'is_freelance':           int('freelance' in job_type or 'tự do' in job_type),
        # Company enrich + reputation: không có tại inference → 0
    }

    return np.array([feature_map.get(f, 0) for f in feature_names], dtype=float)


# ============================================================
# ML PREDICTION
# ============================================================

def get_ml_risk(data: dict) -> float:
    """Trả về P(FAKE) từ voting ensemble — [0, 1]."""
    full_text   = _build_full_text(data)
    X_text      = tfidf.transform([full_text])
    X_num_raw   = extract_numeric_features(data).reshape(1, -1)
    X_num_scaled= scaler.transform(X_num_raw)
    X           = hstack([X_text, X_num_scaled])
    # Label 0=FAKE, 1=REAL → P(FAKE) = proba[:, 0]
    return float(voting_ensemble.predict_proba(X)[0, 0])


# ============================================================
# HEURISTIC RISK
# ============================================================

def get_heuristic_risk(data: dict) -> tuple[float, list[str]]:
    """Rule-based risk score [0, 1] + danh sách lý do."""
    text  = _build_full_text(data)
    words = text.split()
    sal   = _parse_salary(data.get('salary', ''))
    score = 0.0
    reasons: list[str] = []

    if len(words) < 50:
        score += 2; reasons.append("Nội dung quá ngắn")

    scam_count = sum(1 for kw in _SCAM_KEYWORDS if kw in text)
    if scam_count > 0:
        score += min(scam_count * 1.5, 3)
        reasons.append(f"Có {scam_count} từ khóa nghi ngờ")

    if sal['suspiciously_high']:
        score += 2; reasons.append("Lương quá cao đáng ngờ (>50M)")
    if sal['too_low']:
        score += 1; reasons.append("Lương quá thấp (<3M)")
    if sal['negotiable'] and len(words) < 100:
        score += 1; reasons.append("Lương thỏa thuận kèm nội dung ngắn")

    if not any(kw in text for kw in _POSITIVE_KEYWORDS):
        score += 1; reasons.append("Không có từ khóa quyền lợi chuẩn")

    overview_len = len(str(data.get('companyOverview', '')))
    if overview_len < 50:
        score += 1.5; reasons.append("Thiếu thông tin công ty")

    req_words = str(data.get('requirements', '')).split()
    if len(req_words) < 20:
        score += 1; reasons.append("Yêu cầu công việc quá sơ sài")

    if text.count('!') > 3:
        score += 0.5; reasons.append("Quá nhiều dấu !")

    upper_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
    if upper_ratio > 0.3:
        score += 1; reasons.append("Quá nhiều chữ hoa")

    num_cand = int(data.get('numCandidates', 0) or 0)
    no_exp   = 'không' in str(data.get('yearsExp', '')).lower()
    if num_cand > 20 and no_exp:
        score += 1.5; reasons.append("Tuyển hàng loạt + không cần kinh nghiệm")

    return min(score / 10.0, 1.0), reasons


# ============================================================
# CONDITIONAL BLEND
# ============================================================

def blend_risk(model_risk: float, heuristic_risk: float) -> tuple[float, str]:
    """
    Chỉ blend khi model không chắc (0.3 < model_risk < 0.7).
    Khi model đã chắc → tin model, không cần heuristic.
    """
    if 0.3 < model_risk < 0.7:
        blended = model_risk * 0.65 + heuristic_risk * 0.35
        method  = f"blend (model={model_risk:.2f} uncertain → 0.65×ML + 0.35×heuristic)"
    else:
        blended = model_risk
        method  = f"model only (confident: {model_risk:.2f})"
    return blended, method


def risk_to_level(risk: float) -> str:
    if risk >= 0.7:
        return "HIGH"
    if risk >= 0.4:
        return "MEDIUM"
    return "LOW"


# ============================================================
# ENDPOINTS
# ============================================================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'ml_model_loaded': models_loaded,
        'server_time': datetime.now().isoformat(),
        'version': '2.0.0',
    })


@app.route('/api/analyze-job', methods=['POST'])
def analyze_job():
    if not models_loaded:
        return jsonify({'error': 'Models not loaded'}), 500

    data = request.json or {}
    if not data.get('title'):
        return jsonify({'error': 'title is required'}), 400

    try:
        # 1. ML prediction
        model_risk = get_ml_risk(data)

        # 2. Heuristic scoring
        heuristic_risk, reasons = get_heuristic_risk(data)

        # 3. Conditional blend
        final_risk, blend_method = blend_risk(model_risk, heuristic_risk)

        return jsonify({
            'success': True,
            'data': {
                'risk_score':     round(final_risk * 100),
                'risk_level':     risk_to_level(final_risk),
                'confidence':     round(abs(final_risk - 0.5) * 2, 3),
                'reasons':        reasons,
                'debug': {
                    'model_risk':     round(model_risk, 4),
                    'heuristic_risk': round(heuristic_risk, 4),
                    'final_risk':     round(final_risk, 4),
                    'blend_method':   blend_method,
                },
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/model-info', methods=['GET'])
def model_info():
    return jsonify({
        'success': True,
        'info': {
            'ml_model_available': models_loaded,
            'model_type':        'Voting Ensemble (diversity-aware)',
            'numeric_features':  len(feature_names),
            'blend_strategy':    'conditional: blend only when 0.3 < model_risk < 0.7',
            'version':           '2.0.0',
        }
    })


if __name__ == '__main__':
    print("Starting Flask API Server v2...")
    app.run(host='0.0.0.0', port=5000, debug=True)
