# Hệ thống quản lý & đánh giá độ tin cậy tin tuyển dụng — Backend

Flask REST API cung cấp phân tích ML/heuristic cho tin tuyển dụng,
kết hợp quản lý người dùng, theo dõi ứng tuyển và thống kê cá nhân.

---

## Yêu cầu hệ thống

| Thành phần | Phiên bản tối thiểu |
|---|---|
| Python | 3.11+ |
| pip | 23+ |
| SQLite | có sẵn trong Python (mặc định) |
| PostgreSQL | tuỳ chọn — dùng khi deploy production |

---

## Cấu trúc thư mục

```
project_root/
├── backend/                  ← thư mục này
│   ├── app.py
│   ├── extensions.py
│   ├── blacklist.json        ← tự tạo lần đầu chạy
│   ├── recruitment.db        ← tự tạo lần đầu chạy (SQLite)
│   ├── blueprints/
│   │   ├── auth.py           /api/auth/*
│   │   ├── jobs.py           /api/jobs/*
│   │   ├── dashboard.py      /api/dashboard/*
│   │   ├── applications.py   /api/applications/*
│   │   ├── saved_jobs.py     /api/saved-jobs/*
│   │   └── stats.py          /api/stats/*
│   ├── models/
│   │   ├── user.py
│   │   ├── application.py
│   │   └── saved_job.py
│   └── services/
│       ├── recruitment_trust.py
│       ├── user_service.py
│       ├── application_service.py
│       └── stats_service.py
├── data/
│   └── JOB_DATA_HIGH_CONFIDENCE_KHOA.csv
├── models/                   ← ML model artifacts
│   ├── best_model.pkl
│   ├── tfidf_vectorizer.pkl
│   ├── scaler.pkl
│   └── feature_names.pkl
└── ml_pipeline/
    └── src/
        └── advanced_features.py
```

---

## Cài đặt

### 1. Tạo môi trường ảo

```bash
# Tạo venv
python -m venv venv

# Kích hoạt — macOS / Linux
source venv/bin/activate

# Kích hoạt — Windows
venv\Scripts\activate
```

### 2. Cài dependencies

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

Nội dung `requirements.txt` đầy đủ:

```
flask
flask-cors
flask-sqlalchemy>=3.1
flask-jwt-extended>=4.6
flask-migrate>=4.0
werkzeug>=3.0
joblib
pandas
scipy
scikit-learn
```

### 3. Tạo file biến môi trường

Tạo file `.env` trong thư mục `backend/`:

```bash
# backend/.env

SECRET_KEY=thay-bang-chuoi-ngau-nhien-dai-it-nhat-32-ky-tu
JWT_SECRET_KEY=thay-bang-chuoi-khac-cung-ngau-nhien

# SQLite (mặc định, không cần thay đổi khi chạy local)
DATABASE_URL=sqlite:///recruitment.db

# PostgreSQL (bỏ comment khi deploy production)
# DATABASE_URL=postgresql://user:password@localhost:5432/recruitment_db
```

> **Quan trọng:** Không commit file `.env` lên git. Thêm `.env` vào `.gitignore`.

Để tạo secret key ngẫu nhiên nhanh:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Tạo database

### Lần đầu tiên — dùng `db.create_all()` (đơn giản nhất)

`app.py` đã gọi `db.create_all()` tự động trong `create_app()`, nên khi chạy server lần đầu, file `recruitment.db` và toàn bộ bảng sẽ được tạo ra mà không cần làm gì thêm.

```bash
cd backend
python app.py
# → File recruitment.db xuất hiện trong thư mục backend/
# → Các bảng users, applications, saved_jobs được tạo tự động
```

Kiểm tra database vừa tạo:

```bash
python - <<'EOF'
from app import create_app
from extensions import db

app = create_app()
with app.app_context():
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    print("Các bảng đã tạo:", inspector.get_table_names())
EOF
```

Kết quả mong đợi:

```
Các bảng đã tạo: ['applications', 'saved_jobs', 'users']
```

---

### Dùng Flask-Migrate (khuyên dùng khi develop)

Flask-Migrate cho phép thay đổi schema (thêm cột, sửa bảng) mà không mất dữ liệu.

**Khởi tạo migrate lần đầu** (chỉ chạy một lần duy nhất):

```bash
cd backend
flask --app app db init
```

Lệnh này tạo thư mục `migrations/` trong `backend/`.

**Tạo migration đầu tiên** từ các model hiện có:

```bash
flask --app app db migrate -m "init"
```

**Áp dụng migration vào database:**

```bash
flask --app app db upgrade
```

**Quy trình khi thêm/sửa model về sau:**

```bash
# 1. Chỉnh sửa file trong models/
# 2. Tạo migration mới
flask --app app db migrate -m "mo ta thay doi"

# 3. Áp dụng
flask --app app db upgrade

# Xem lịch sử migration
flask --app app db history

# Rollback về migration trước nếu cần
flask --app app db downgrade
```

---

## Chạy server

### Development

```bash
cd flask_backend

start swagger.html

# Cách 1 — Flask CLI (khuyên dùng)
flask --app app run --debug --port 5000

# Cách 2 — chạy trực tiếp
python app.py
```

Server khởi động tại: `http://localhost:5000`


Kiểm tra health:

```bash
curl http://localhost:5000/api/health
```

Kết quả mong đợi:

```json
{
  "status": "ok",
  "message": "Hệ thống hoạt động bình thường.",
  "modelLoaded": true,
  "datasetLoaded": true
}
```

<!-- ### Production (Gunicorn)

```bash
pip install gunicorn

gunicorn "app:create_app()" \
  --bind 0.0.0.0:5000 \
  --workers 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

> Dùng 2 workers vì `RecruitmentTrustService` load toàn bộ dataset vào RAM —
> nhiều workers hơn sẽ nhân bội lượng RAM cần dùng.

--- -->

## Danh sách API endpoint

### Auth — `/api/auth`

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| `POST` | `/api/auth/register` | — | Đăng ký tài khoản mới |
| `POST` | `/api/auth/login` | — | Đăng nhập, nhận JWT |
| `GET` | `/api/auth/profile` | JWT | Xem thông tin + preferences |
| `POST` | `/api/auth/change-password` | JWT | Đổi mật khẩu |

### Jobs — `/api/jobs`

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| `GET` | `/api/jobs` | — | Danh sách job (phân trang, lọc rủi ro) |
| `POST` | `/api/jobs/analyze` | tuỳ chọn | Phân tích một tin tuyển dụng |
| `POST` | `/api/jobs/batch-analyze` | — | Phân tích nhiều tin cùng lúc |
| `POST` | `/api/jobs/recommend` | tuỳ chọn | Gợi ý job cá nhân hóa |
| `GET` | `/api/jobs/blacklist` | — | Xem danh sách blacklist |
| `POST` | `/api/jobs/blacklist/check` | — | Kiểm tra job với blacklist |
| `POST` | `/api/jobs/blacklist/update` | — | Cập nhật blacklist |

### Dashboard — `/api/dashboard`

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| `GET` | `/api/dashboard/overview` | — | Tổng quan toàn bộ dataset |
| `GET` | `/api/dashboard/personal` | JWT | Tổng quan cá nhân + system |

### Theo dõi ứng tuyển — `/api/applications`

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| `GET` | `/api/applications` | JWT | Danh sách lần đã ứng tuyển |
| `POST` | `/api/applications` | JWT | Thêm một lần ứng tuyển mới |
| `GET` | `/api/applications/:id` | JWT | Chi tiết một lần ứng tuyển |
| `PATCH` | `/api/applications/:id` | JWT | Cập nhật trạng thái, ghi chú, rating |
| `DELETE` | `/api/applications/:id` | JWT | Xóa |

Các giá trị `status` hợp lệ: `saved` · `applied` · `interviewing` · `offered` · `rejected` · `withdrawn`

### Tin đã lưu — `/api/saved-jobs`

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| `GET` | `/api/saved-jobs` | JWT | Danh sách tin đã lưu |
| `POST` | `/api/saved-jobs` | JWT | Lưu tin để ứng tuyển sau |
| `PATCH` | `/api/saved-jobs/:id` | JWT | Cập nhật ghi chú |
| `DELETE` | `/api/saved-jobs/:id` | JWT | Bỏ lưu |
| `POST` | `/api/saved-jobs/:id/apply` | JWT | Chuyển sang applied, xóa khỏi saved |

### Thống kê cá nhân — `/api/stats`

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| `GET` | `/api/stats/overview` | JWT | Tổng quan: tỷ lệ, phân bố trạng thái/rủi ro |
| `GET` | `/api/stats/risk-summary` | JWT | Phân tích rủi ro theo trạng thái |

### Health

| Method | Endpoint | Auth | Mô tả |
|--------|----------|------|-------|
| `GET` | `/api/health` | — | Trạng thái server, model, dataset |

---

## Ví dụ sử dụng API

### Đăng ký và lấy JWT

```bash
# Đăng ký
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "name": "Nguyễn Văn A", "password": "matkhau123"}'

# Đăng nhập
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "matkhau123"}'
# → Lấy "accessToken" từ response, dùng cho các request cần JWT
```

### Lưu một tin tuyển dụng

```bash
curl -X POST http://localhost:5000/api/saved-jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <accessToken>" \
  -d '{
    "job": {
      "title": "Lập trình viên Python",
      "companyName": "Công ty ABC",
      "salary": "20-30 triệu",
      "location": "Hà Nội"
    },
    "jobId": 42,
    "note": "Deadline nộp 30/4",
    "trustScore": 85.5,
    "riskScore": 14.5,
    "riskLevel": "LOW"
  }'
```

### Ghi nhận ứng tuyển và cập nhật trạng thái

```bash
# Tạo application
curl -X POST http://localhost:5000/api/applications \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <accessToken>" \
  -d '{
    "job": {"title": "Backend Developer", "companyName": "Startup XYZ"},
    "status": "applied",
    "note": "Gửi CV qua email ngày 1/4",
    "trustScore": 78.0,
    "riskScore": 22.0,
    "riskLevel": "LOW"
  }'

# Cập nhật sau khi có lịch phỏng vấn
curl -X PATCH http://localhost:5000/api/applications/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <accessToken>" \
  -d '{"status": "interviewing", "note": "Phỏng vấn vòng 1 ngày 10/4 lúc 9h"}'
```

### Xem thống kê cá nhân

```bash
curl http://localhost:5000/api/stats/overview \
  -H "Authorization: Bearer <accessToken>"
```

---

## Chuyển sang PostgreSQL

Khi deploy, thay `DATABASE_URL` trong `.env`:

```
DATABASE_URL=postgresql://user:password@localhost:5432/recruitment_db
```

Cài thêm driver:

```bash
pip install psycopg2-binary
```

Tạo database trên PostgreSQL:

```sql
CREATE DATABASE recruitment_db;
CREATE USER recruitment_user WITH PASSWORD 'matkhau_manh';
GRANT ALL PRIVILEGES ON DATABASE recruitment_db TO recruitment_user;
```

Áp dụng migration:

```bash
flask --app app db upgrade
```

---

## Xử lý sự cố thường gặp

**`ModuleNotFoundError: ml_pipeline`**
Đảm bảo chạy từ đúng thư mục và `BASE_DIR` trỏ đúng về project root. Kiểm tra `sys.path` in ra trong `app.py`.

**`Model not loaded` (modelLoaded: false)**
Kiểm tra các file `.pkl` tồn tại trong `models/`: `best_model.pkl`, `tfidf_vectorizer.pkl`, `scaler.pkl`, `feature_names.pkl`. Server vẫn chạy bình thường, chỉ fallback sang heuristic.

**`Dataset not loaded` (datasetLoaded: false)**
Kiểm tra file CSV tồn tại tại `data/JOB_DATA_HIGH_CONFIDENCE_KHOA.csv`.

**Lỗi `JWT` — 401 Unauthorized**
Đảm bảo gửi header đúng định dạng: `Authorization: Bearer <token>`. Token mặc định hết hạn sau 1 giờ — đăng nhập lại để lấy token mới.

**SQLite bị lock khi chạy nhiều request đồng thời**
Chuyển sang PostgreSQL, hoặc giảm workers Gunicorn xuống còn 1 khi dùng SQLite.