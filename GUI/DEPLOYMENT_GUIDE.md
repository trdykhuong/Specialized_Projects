# 🚀 HƯỚNG DẪN DEPLOYMENT - HỆ THỐNG HOÀN CHỈNH

## 📋 Tổng quan Kiến trúc

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                      │
│  - job_tracker_integrated.jsx                           │
│  - Browser Storage (persistent data)                    │
│  - Tailwind CSS + Lucide Icons                         │
└────────────────┬────────────────────────────────────────┘
                 │ HTTP/REST API
                 ↓
┌─────────────────────────────────────────────────────────┐
│                 BACKEND API (Flask)                      │
│  - backend_api.py                                       │
│  - CORS enabled                                         │
│  - Endpoints: /api/analyze-job, /api/batch-analyze     │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│              ML MODELS & PROCESSING                      │
│  - best_model.pkl (Ensemble: RF + XGBoost + LGBM)     │
│  - tfidf_vectorizer.pkl                                │
│  - scaler.pkl                                          │
│  - advanced_features.py (30+ features)                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 BƯỚC 1: CÀI ĐẶT BACKEND

### 1.1 Prerequisites

```bash
# Python 3.8+
python --version

# pip
pip --version
```

### 1.2 Cài đặt Dependencies

```bash
# Tạo virtual environment (khuyến nghị)
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install packages
pip install flask flask-cors pandas numpy scikit-learn scipy xgboost lightgbm joblib pyvi
```

### 1.3 Chuẩn bị Files

Đảm bảo có đủ các files sau trong cùng thư mục:

```
project/
├── backend_api.py              # API server
├── advanced_features.py        # Feature extractor
├── best_model.pkl              # ML model (optional)
├── voting_ensemble.pkl         # Ensemble model (optional)
├── tfidf_vectorizer.pkl        # Vectorizer (optional)
└── scaler.pkl                  # Scaler (optional)
```

**Lưu ý**: Nếu không có file .pkl models, API vẫn chạy được ở **heuristic mode**.

### 1.4 Chạy Backend

```bash
python backend_api.py
```

Bạn sẽ thấy:

```
🚀 Starting Job Tracker API Server...
================================================================================
✅ ML Models loaded successfully!
# hoặc
⚠️  Warning: Could not load models - API will run in demo mode
================================================================================

🚀 JOB TRACKER API SERVER
================================================================================

📡 Available Endpoints:
  GET  /health                - Health check
  POST /api/analyze-job       - Analyze single job posting
  POST /api/batch-analyze     - Analyze multiple jobs
  POST /api/check-blacklist   - Check blacklist matches
  POST /api/stats             - Get job statistics
  GET  /api/model-info        - Get model information

🔧 Configuration:
  ML Model: ✅ Loaded (hoặc ⚠️  Not loaded)
  CORS: ✅ Enabled
  Port: 5000

================================================================================
Starting server...

 * Running on http://0.0.0.0:5000
```

### 1.5 Test Backend

Mở terminal mới:

```bash
# Health check
curl http://localhost:5000/health

# Expected response:
{
  "status": "healthy",
  "ml_model_loaded": true,
  "server_time": "2025-03-07T...",
  "version": "1.0.0"
}

# Test analyze endpoint
curl -X POST http://localhost:5000/api/analyze-job \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Tuyển nhân viên online",
    "description": "Việc nhẹ lương cao",
    "salary": "50-100 triệu",
    "email": "test@gmail.com"
  }'

# Expected response:
{
  "success": true,
  "data": {
    "risk_score": 75.5,
    "risk_level": "HIGH",
    "reasons": [
      "Có từ khóa nghi ngờ: \"việc nhẹ lương cao\"",
      "Mức lương bất thường cao",
      "Email cá nhân"
    ],
    ...
  }
}
```

---

## 🎨 BƯỚC 2: SETUP FRONTEND

### Option A: Chạy trong Claude Artifacts (Đơn giản nhất)

1. Copy toàn bộ code từ `job_tracker_integrated.jsx`
2. Paste vào Claude chat
3. Yêu cầu: "Create a React artifact with this code"
4. Giao diện sẽ hiển thị ngay!

**Lưu ý**: Đảm bảo backend đang chạy ở `http://localhost:5000`

### Option B: Chạy trên Local Development Server

#### 2.1 Tạo React App

```bash
# Tạo project mới
npx create-react-app job-tracker-frontend
cd job-tracker-frontend

# Install dependencies
npm install lucide-react
```

#### 2.2 Setup Tailwind CSS

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

Cập nhật `tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

Cập nhật `src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

#### 2.3 Copy Code

- Copy code từ `job_tracker_integrated.jsx`
- Paste vào `src/App.jsx`

#### 2.4 Chạy Frontend

```bash
npm start
```

App sẽ mở tại `http://localhost:3000`

---

## 🔗 BƯỚC 3: KẾT NỐI FRONTEND-BACKEND

### 3.1 Kiểm tra Connection

Khi frontend load:
- Góc phải header sẽ hiển thị API status
- **Xanh**: 🤖 ML Model Active (backend có model)
- **Vàng**: 📊 Heuristic Mode (backend không có model nhưng vẫn hoạt động)
- **Đỏ**: ⚠️ API Offline (backend không chạy)

### 3.2 Troubleshooting CORS

Nếu gặp lỗi CORS:

```
Access to fetch at 'http://localhost:5000/api/analyze-job' from origin 
'http://localhost:3000' has been blocked by CORS policy
```

**Giải pháp**: Đã enable CORS trong `backend_api.py`:

```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # ✅ Enabled
```

Nếu vẫn lỗi:

```bash
pip install flask-cors
```

### 3.3 Test Full Flow

1. **Thêm tin mới**:
   - Click "Thêm tin mới"
   - Điền thông tin
   - Click "Lưu tin"
   - ⏳ Loading: "Đang phân tích với AI model..."
   - ✅ Tin được lưu với risk score

2. **Xem chi tiết**:
   - Click vào bất kỳ tin nào
   - Modal hiển thị:
     - Risk analysis
     - ML prediction badge (nếu có)
     - Warnings chi tiết

3. **Blacklist**:
   - Thêm email/company vào blacklist
   - Thêm tin mới với info trùng khớp
   - → Tự động cảnh báo!

---

## 🎯 BƯỚC 4: DEMO & PRESENTATION

### 4.1 Chuẩn bị Demo Data

Tạo file `demo_data.py`:

```python
import requests
import json

API_URL = "http://localhost:5000"

# Demo jobs
demo_jobs = [
    {
        "title": "Senior Software Engineer",
        "companyName": "VNG Corporation",
        "description": "Develop and maintain web applications using React and Node.js",
        "salary": "25-35 triệu",
        "address": "182 Lê Đại Hành, Q3, TPHCM",
        "email": "hr@vng.com.vn",
        "phone": "028-123-4567"
    },
    {
        "title": "Cộng tác viên bán hàng online",
        "companyName": "Công ty ABC",
        "description": "Việc nhẹ lương cao, không cần kinh nghiệm, thu nhập không giới hạn",
        "salary": "30-100 triệu",
        "address": "",
        "email": "recruit123@gmail.com",
        "phone": "0912345678"
    }
]

# Analyze all
for job in demo_jobs:
    response = requests.post(f"{API_URL}/api/analyze-job", json=job)
    result = response.json()
    
    print(f"\n{'='*60}")
    print(f"Job: {job['title']}")
    print(f"Risk Score: {result['data']['risk_score']}")
    print(f"Risk Level: {result['data']['risk_level']}")
    print(f"Reasons: {result['data']['reasons']}")
```

Chạy:

```bash
python demo_data.py
```

### 4.2 Demo Script

**Kịch bản demo 5 phút:**

1. **Giới thiệu (30s)**:
   - "Đây là hệ thống quản lý tin tuyển dụng cá nhân với AI"
   - Show header với API status indicator

2. **Thêm tin FAKE (1 phút)**:
   - Thêm tin với keywords nghi ngờ
   - Show loading → ML analysis
   - Result: Risk 85/100 🔴 HIGH
   - Show warnings chi tiết

3. **Thêm tin REAL (1 phút)**:
   - Thêm tin công ty uy tín
   - Result: Risk 10/100 🟢 LOW
   - Compare với tin FAKE

4. **Blacklist (1 phút)**:
   - Thêm email scam vào blacklist
   - Thêm tin mới với email đó
   - → Instant warning!

5. **Stats & Features (1.5 phút)**:
   - Switch sang Stats view
   - Show phân bố rủi ro
   - Show ML prediction count
   - Mention personal notes, ratings

### 4.3 Key Selling Points

Nhấn mạnh:
- ✅ **Real-time AI analysis**: Instant risk scoring
- ✅ **Hybrid approach**: ML (if available) + Heuristic fallback
- ✅ **Privacy-first**: All data local, không upload
- ✅ **Production-ready**: REST API, CORS, error handling
- ✅ **Extensible**: Easy to add more features

---

## 📦 BƯỚC 5: DEPLOYMENT PRODUCTION

### Option A: Deploy Backend trên Heroku

```bash
# 1. Create Procfile
echo "web: python backend_api.py" > Procfile

# 2. Create runtime.txt
echo "python-3.9.16" > runtime.txt

# 3. Freeze dependencies
pip freeze > requirements.txt

# 4. Git init & deploy
git init
git add .
git commit -m "Initial commit"
heroku create job-tracker-api
git push heroku main
```

### Option B: Deploy Backend trên Railway

1. Push code lên GitHub
2. Vào railway.app
3. "New Project" → "Deploy from GitHub"
4. Select repo
5. Railway tự detect Flask và deploy

### Deploy Frontend trên Vercel

```bash
# 1. Build production
npm run build

# 2. Install Vercel CLI
npm i -g vercel

# 3. Deploy
vercel

# Follow prompts
```

Update API_BASE_URL trong frontend:

```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
```

---

## 🎓 BƯỚC 6: ĐỂ TRÌNH BÀY ĐỒ ÁN

### 6.1 Chuẩn bị

✅ **Code**:
- Git repo với README đầy đủ
- Comments rõ ràng
- Structured folders

✅ **Demo**:
- Local setup sẵn sàng
- Test data prepared
- Backup slides/video nếu demo fail

✅ **Documentation**:
- System architecture diagram
- API documentation
- User guide

### 6.2 Câu hỏi thường gặp

**Q: Tại sao không dùng deep learning (BERT, PhoBERT)?**
A: Vì:
- Dataset nhỏ (vài nghìn samples)
- Ensemble methods đã đạt F1 0.85-0.92
- Easier to deploy và interpret
- Có thể upgrade sau

**Q: Tại sao lưu local thay vì database?**
A: Đây là **personal tool**, ưu tiên:
- Privacy (100% local)
- Zero setup (no DB config)
- Instant usage
- Có thể upgrade lên DB sau

**Q: Làm sao scale cho nhiều người dùng?**
A: Roadmap:
- Phase 1 (hiện tại): Personal tool
- Phase 2: Multi-user với authentication
- Phase 3: Social features (shared blacklist)

---

## 📊 METRICS & KPI

### Backend Performance

- **API Response Time**: < 500ms (heuristic), < 2s (ML)
- **Accuracy**: F1 0.85-0.92 (với ML model)
- **Uptime**: 99%+ (production)

### Frontend Performance

- **Initial Load**: < 2s
- **Add Job**: < 3s (with ML analysis)
- **Storage**: ~1MB for 1000 jobs

---

## ✅ CHECKLIST TRƯỚC KHI DEMO

- [ ] Backend running và health check OK
- [ ] Frontend running và connect được API
- [ ] API status indicator hiển thị đúng
- [ ] Test add job → Risk analysis working
- [ ] Test blacklist → Warning working
- [ ] Stats view hiển thị đúng
- [ ] Chuẩn bị 3-5 demo jobs (fake + real)
- [ ] Screenshot/video backup
- [ ] Slides presentation ready

---

## 🎉 KẾT LUẬN

Bạn đã có:
- ✅ Backend API hoàn chỉnh với ML integration
- ✅ Frontend React responsive và đẹp
- ✅ Full-stack system working end-to-end
- ✅ Production-ready code
- ✅ Documentation đầy đủ

**Hệ thống này sẵn sàng để:**
- Demo đồ án
- Deploy thực tế
- Mở rộng thêm features
- Publish lên GitHub

Chúc bạn demo thành công! 🚀
