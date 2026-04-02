
# 🚀 DEPLOYMENT GUIDE

## Local Development

### 1. Install dependencies
```bash
pip install flask flask-cors pandas numpy scikit-learn scipy xgboost lightgbm joblib
```

### 2. Ensure models are present
```
project/
├── best_model.pkl
├── voting_ensemble.pkl
├── tfidf_vectorizer.pkl
├── scaler.pkl
└── backend_api.py  (or flask_api_server.py)
```

### 3. Start server
```bash
python backend_api.py
```

Server will run at: http://localhost:5000

---

## Production Deployment

### Option A: Heroku

1. Create `Procfile`:
```
web: python backend_api.py
```

2. Create `runtime.txt`:
```
python-3.9.16
```

3. Deploy:
```bash
git init
git add .
git commit -m "Initial commit"
heroku create job-tracker-api
git push heroku main
```

### Option B: Railway

1. Push to GitHub
2. Go to railway.app
3. "New Project" → "Deploy from GitHub"
4. Select your repo
5. Railway auto-detects Flask and deploys

### Option C: Docker

1. Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "backend_api.py"]
```

2. Build and run:
```bash
docker build -t job-tracker-api .
docker run -p 5000:5000 job-tracker-api
```

---

## Frontend Integration

Update API_BASE_URL in frontend:
```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
```

For production:
```bash
REACT_APP_API_URL=https://your-api.herokuapp.com npm run build
```

---

## Testing

```bash
# Health check
curl http://localhost:5000/health

# Analyze job
curl -X POST http://localhost:5000/api/analyze-job \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Developer",
    "description": "Build web apps",
    "salary": "20-30 triệu"
  }'
```
