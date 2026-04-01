
from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
from scipy.sparse import hstack
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Load models
print("Loading models...")
try:
    best_model = joblib.load('best_model.pkl')
    voting_ensemble = joblib.load('voting_ensemble.pkl')
    tfidf = joblib.load('tfidf_vectorizer.pkl')
    scaler = joblib.load('scaler.pkl')
    print("✅ All models loaded!")
    models_loaded = True
except Exception as e:
    print(f"❌ Error loading models: {e}")
    models_loaded = False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'ml_model_loaded': models_loaded,
        'server_time': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/analyze-job', methods=['POST'])
def analyze_job():
    """Analyze a single job posting"""
    if not models_loaded:
        return jsonify({'error': 'Models not loaded'}), 500

    try:
        data = request.json

        # Validate
        if not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400

        # Predict (simplified - use full implementation from backend_api.py)
        result = {
            'risk_score': 50,
            'risk_level': 'MEDIUM',
            'confidence': 0.75,
            'reasons': ['Sample reason'],
            'ml_available': True
        }

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/model-info', methods=['GET'])
def model_info():
    """Get model information"""
    return jsonify({
        'success': True,
        'info': {
            'ml_model_available': models_loaded,
            'model_type': 'Ensemble (RF + XGBoost + LightGBM)',
            'version': '1.0.0'
        }
    })

if __name__ == '__main__':
    print("🚀 Starting Flask API Server...")
    app.run(host='0.0.0.0', port=5000, debug=True)
