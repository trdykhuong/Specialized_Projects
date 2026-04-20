# Frontend - Backend - Model Flow

## 1. Nhap va phan tich 1 tin tuyen dung

1. Nguoi dung nhap form o frontend React.
2. Frontend goi `POST /api/jobs/analyze`.
3. Payload chinh:
```json
{
  "title": "Backend Developer",
  "companyName": "Cong ty ABC",
  "description": "...",
  "requirements": "...",
  "benefits": "...",
  "salary": "20,000,000 - 30,000,000",
  "experience": "1-3 nam",
  "careerLevel": "Nhan vien",
  "jobType": "Toan thoi gian",
  "candidates": 3
}
```
4. Flask route trong `blueprints/jobs.py` nhan request va chuyen qua `RecruitmentTrustService.analyze_job(...)`.
5. `RecruitmentTrustService._normalize_input(...)` chuan hoa du lieu.
6. Backend tao input cho model:
   - text tong hop: `title + companyName + description + requirements + benefits`
   - cac truong cau truc: `salary`, `experience`, `candidates`, `careerLevel`, `jobType`
7. Backend thu enrich feature cong ty theo `companyName`.
8. Neu engine company lookup co san thi backend lay them:
   - `company_found`
   - `company_active`
   - `company_closed`
   - `reputation_score`
   - va cac feature company/reputation khac
9. Neu khong co engine hoac khong tim thay cong ty, backend gan gia tri mac dinh:
   - `company_found = 0`
   - `company_unknown = 1`
   - `reputation_score = 0`
   - `company_name_source = "Khong co"`
10. `AdvancedFeatureExtractor` trich xuat feature co ban.
11. Backend ghep feature company + feature text + feature salary + feature requirement.
12. Model du doan `probability_fake` va `probability_real`.
13. Backend ghep them heuristic, blacklist, personalization.
14. Frontend nhan ket qua roi hien `riskScore`, `trustScore`, `riskLevel`, `signals`.

## 2. Luu job tu form tay

1. Sau khi phan tich xong, frontend co the goi `POST /api/jobs`.
2. Backend luu snapshot vao `custom_jobs.job_data_json`.
3. Snapshot khong can ma so thue.

## 3. Xem job co san trong dataset

1. Frontend goi `GET /api/jobs?page=1&pageSize=9&query=...`.
2. Backend doc dataset CSV, serialize thanh cac job card.
3. Khi mo chi tiet, frontend co the goi `GET /api/jobs/<job_id>` hoac dung du lieu da co.
4. Neu bam Analyze, frontend lai goi `POST /api/jobs/analyze`.

## 4. Train pipeline va model cong ty

1. Chay `python ml_pipeline/run_full_pipeline.py`.
2. Pipeline hien tai se di theo thu tu:
   - preprocessing
   - advanced feature extraction
   - company enrichment theo `Name Company`
   - labeling
   - training
3. Buoc company enrichment dung script:
   - `ml_pipeline/src/enrich_company_features.py`
4. Script nay goi:
   - `process_company_features(company_name=..., text=...)`
   - `analyze_company_reputation(company_name=..., text=...)`
5. Neu module lookup co san, output se duoc ghi vao `data/JOB_DATA_WITH_COMPANY.csv`.
6. Neu module lookup khong co hoac loi, script van chay va dien gia tri mac dinh `Khong co`.
7. Sau do model train se doc cac company features nay neu file du lieu co chua.

## 5. Frontend dang giao tiep voi backend o dau

- `frontend_react/src/api.js`: dinh nghia ham fetch.
- `frontend_react/src/App.jsx`: map form thanh payload API.
- `frontend_react/src/components/AppSections.jsx`: UI form va trigger action.

## 6. Backend xu ly o dau

- `flask_backend/blueprints/jobs.py`: route nhan request.
- `flask_backend/services/recruitment_trust.py`: normalize, enrich company theo ten, heuristic, model predict.
- `ml_pipeline/src/advanced_features.py`: feature extraction co ban.
- `ml_pipeline/src/enrich_company_features.py`: feature cong ty cho train pipeline.
- `models/*.pkl`: artifact cua model.

## 7. Ghi chu hien tai

- Truong `Vi tri ung tuyen` dang map vao `careerLevel` de giu tuong thich voi dataset train cu.
- Truong `Quy mo cong ty` da bo khoi form nhap tay.
- Truong `Ma so thue` da bo khoi frontend va API public.
- Luong enrich cong ty hien dua vao `Ten cong ty`.
- Neu model lookup cong ty khong san sang, he thong se tra ve trang thai mac dinh `Khong co` thay vi loi.
