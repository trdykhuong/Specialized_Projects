import json
import re
import sys
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from scipy.sparse import hstack

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "JOB_DATA_HIGH_CONFIDENCE_KHOA.csv"
MODELS_DIR = BASE_DIR / "models"
BLACKLIST_PATH = Path(__file__).resolve().parent / "blacklist.json"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml_pipeline.src.advanced_features import AdvancedFeatureExtractor


def create_app():
    app = Flask(__name__)
    CORS(app)

    predictor = RecruitmentTrustService()
    predictor.load_assets()

    @app.get("/api/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "message": "Hệ thống hoạt động bình thường.",
                "timestamp": datetime.utcnow().isoformat(),
                "modelLoaded": predictor.model_ready,
                "datasetLoaded": predictor.dataset_ready,
            }
        )

    @app.get("/api/dashboard/overview")
    def dashboard_overview():
        return jsonify(predictor.get_dashboard_overview())

    @app.get("/api/jobs")
    def list_jobs():
        query = request.args.get("query", "")
        risk = request.args.get("risk", "ALL")
        page = max(int(request.args.get("page", 1)), 1)
        page_size = max(int(request.args.get("pageSize", request.args.get("limit", 12))), 1)
        return jsonify(
            predictor.list_jobs(query=query, risk=risk, page=page, page_size=page_size)
        )

    @app.post("/api/jobs/analyze")
    def analyze_job():
        payload = request.get_json(silent=True) or {}
        return jsonify(predictor.analyze_job(payload))

    @app.post("/api/jobs/batch-analyze")
    def batch_analyze():
        payload = request.get_json(silent=True) or {}
        jobs = payload.get("jobs", [])
        return jsonify(predictor.batch_analyze(jobs))

    @app.post("/api/personalization/recommend")
    def personalized_recommendation():
        payload = request.get_json(silent=True) or {}
        return jsonify(predictor.recommend_jobs(payload))

    @app.get("/api/blacklist")
    def get_blacklist():
        return jsonify(predictor.get_blacklist())

    @app.post("/api/blacklist/check")
    def check_blacklist():
        payload = request.get_json(silent=True) or {}
        return jsonify(predictor.check_blacklist(payload.get("job", {})))

    @app.post("/api/blacklist/update")
    def update_blacklist():
        payload = request.get_json(silent=True) or {}
        return jsonify(predictor.update_blacklist(payload))

    return app


class RecruitmentTrustService:
    def __init__(self):
        self.dataset = pd.DataFrame()
        self.extractor = AdvancedFeatureExtractor()
        self.model = None
        self.tfidf = None
        self.scaler = None
        self.feature_names = []
        self.model_ready = False
        self.dataset_ready = False
        self.blacklist = {
            "companies": ["Công ty TNHH Việc Nhẹ Lương Cao"],
            "emails": ["tuyendungnhanh@gmail.com"],
            "phones": ["0900000000"],
        }

    def load_assets(self):
        self._load_models()
        self._load_dataset()
        self._load_blacklist()

    def _load_models(self):
        try:
            self.model = joblib.load(MODELS_DIR / "best_model.pkl")
            self.tfidf = joblib.load(MODELS_DIR / "tfidf_vectorizer.pkl")
            self.scaler = joblib.load(MODELS_DIR / "scaler.pkl")
            self.feature_names = joblib.load(MODELS_DIR / "feature_names.pkl")
            self.model_ready = True
        except Exception:
            self.model_ready = False

    def _load_dataset(self):
        if not DATA_PATH.exists():
            return

        df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
        df = df.fillna("")
        df["risk_level"] = df.apply(self._risk_from_row, axis=1)
        df["risk_score"] = df.apply(self._risk_score_from_row, axis=1)
        df["job_title"] = df.apply(self._derive_title, axis=1)
        df["company_name"] = df.get("Name Company", "")
        df["location"] = df.apply(self._derive_location, axis=1)
        self.dataset = df
        self.dataset_ready = not df.empty

    def _load_blacklist(self):
        if BLACKLIST_PATH.exists():
            self.blacklist = json.loads(BLACKLIST_PATH.read_text(encoding="utf-8"))
        else:
            BLACKLIST_PATH.write_text(
                json.dumps(self.blacklist, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    def get_dashboard_overview(self):
        if not self.dataset_ready:
            return {
                "summary": {
                    "totalJobs": 0,
                    "lowRiskJobs": 0,
                    "mediumRiskJobs": 0,
                    "highRiskJobs": 0,
                    "averageConfidence": 0,
                },
                "charts": {"riskDistribution": [], "topCompanies": [], "topReasons": []},
                "system": {
                    "modelReady": self.model_ready,
                    "datasetReady": self.dataset_ready,
                    "modelMessage": "Chưa tải được mô hình." if not self.model_ready else "Mô hình đã sẵn sàng.",
                    "datasetMessage": "Chưa tải được dữ liệu." if not self.dataset_ready else "Dữ liệu đã sẵn sàng.",
                },
            }

        low = int((self.dataset["risk_level"] == "LOW").sum())
        medium = int((self.dataset["risk_level"] == "MEDIUM").sum())
        high = int((self.dataset["risk_level"] == "HIGH").sum())
        confidence = round(float(self.dataset["confidence"].astype(float).mean()), 3)

        top_companies = (
            self.dataset["company_name"]
            .replace("", "Chưa rõ")
            .value_counts()
            .head(5)
            .items()
        )
        top_reasons = {}
        for raw_reasons in self.dataset["rule_reasons"].head(300):
            for reason in self._parse_reason_list(raw_reasons):
                top_reasons[reason] = top_reasons.get(reason, 0) + 1

        return {
            "summary": {
                "totalJobs": int(len(self.dataset)),
                "lowRiskJobs": low,
                "mediumRiskJobs": medium,
                "highRiskJobs": high,
                "averageConfidence": confidence,
            },
            "charts": {
                "riskDistribution": [
                    {"label": "Thấp", "value": low},
                    {"label": "Trung bình", "value": medium},
                    {"label": "Cao", "value": high},
                ],
                "topCompanies": [
                    {"name": company, "value": int(count)} for company, count in top_companies
                ],
                "topReasons": [
                    {"reason": reason, "value": count}
                    for reason, count in sorted(top_reasons.items(), key=lambda item: item[1], reverse=True)[:5]
                ],
            },
            "system": {
                "modelReady": self.model_ready,
                "datasetReady": self.dataset_ready,
                "modelMessage": "Mô hình đã sẵn sàng." if self.model_ready else "Chưa tải được mô hình.",
                "datasetMessage": "Dữ liệu đã sẵn sàng." if self.dataset_ready else "Chưa tải được dữ liệu.",
            },
        }

    def list_jobs(self, query="", risk="ALL", page=1, page_size=12):
        if not self.dataset_ready:
            return {
                "items": [],
                "total": 0,
                "page": 1,
                "pageSize": page_size,
                "totalPages": 0,
                "hasNext": False,
                "hasPrevious": False,
            }

        df = self.dataset.copy()
        if query:
            q = query.lower()
            mask = (
                df["job_title"].str.lower().str.contains(q, na=False)
                | df["company_name"].str.lower().str.contains(q, na=False)
                | df["FULL_TEXT"].str.lower().str.contains(q, na=False)
            )
            df = df[mask]

        if risk != "ALL":
            df = df[df["risk_level"] == risk.upper()]

        total = int(len(df))
        total_pages = (total + page_size - 1) // page_size if total else 0
        if total_pages > 0:
            page = min(page, total_pages)
        else:
            page = 1

        start = (page - 1) * page_size
        end = start + page_size
        paged_df = df.iloc[start:end]

        items = [self._serialize_job(row) for _, row in paged_df.iterrows()]
        return {
            "items": items,
            "total": total,
            "page": page,
            "pageSize": page_size,
            "totalPages": total_pages,
            "hasNext": page < total_pages,
            "hasPrevious": page > 1 and total_pages > 0,
        }

    def analyze_job(self, payload):
        job = self._normalize_input(payload)
        heuristic = self._heuristic_analysis(job)
        blacklist = self._blacklist_matches(job)
        recommendation = self._personalization_score(job, payload.get("candidateProfile", {}))
        model_result = self._model_predict(job)

        if model_result:
            model_risk = model_result["probability_fake"] * 100
            risk_score = round(model_risk * 0.65 + heuristic["riskScore"] * 0.35, 2)
            trust_score = round(100 - risk_score, 2)
            confidence = round(
                (max(model_result["probability_real"], model_result["probability_fake"]) * 0.7)
                + (heuristic["confidence"] * 0.3),
                3,
            )
        else:
            risk_score = heuristic["riskScore"]
            trust_score = 100 - risk_score
            confidence = heuristic["confidence"]

        if blacklist["hasMatch"]:
            risk_score = min(100, risk_score + 20)
            trust_score = max(0, 100 - risk_score)

        return {
            "job": job,
            "result": {
                "trustScore": trust_score,
                "riskScore": risk_score,
                "riskLevel": self._risk_label_from_score(risk_score),
                "riskLabel": self._risk_label_vi(risk_score),
                "confidence": confidence,
                "decision": "Tin cậy" if risk_score < 40 else "Cần kiểm tra" if risk_score < 70 else "Nguy cơ cao",
                "modelReady": self.model_ready,
                "modelMessage": "Đã dùng mô hình máy học." if model_result else "Đang dùng heuristic vì chưa có mô hình phù hợp.",
            },
            "signals": heuristic["signals"],
            "blacklist": blacklist,
            "personalization": recommendation,
        }

    def batch_analyze(self, jobs):
        results = [self.analyze_job(job) for job in jobs[:50]]
        risk_levels = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
        for item in results:
            risk_levels[item["result"]["riskLevel"]] += 1

        average_trust = round(
            sum(item["result"]["trustScore"] for item in results) / len(results), 2
        ) if results else 0
        return {
            "items": results,
            "summary": {
                "total": len(results),
                "riskLevels": risk_levels,
                "riskLevelsVi": {
                    "Thấp": risk_levels["LOW"],
                    "Trung bình": risk_levels["MEDIUM"],
                    "Cao": risk_levels["HIGH"],
                },
                "averageTrustScore": average_trust,
                "message": "Đã phân tích danh sách tin tuyển dụng.",
            },
        }

    def recommend_jobs(self, payload):
        if not self.dataset_ready:
            return {"profile": payload, "message": "Chưa có dữ liệu để gợi ý.", "items": []}

        profile = payload or {}
        target_keywords = self._tokenize(" ".join(profile.get("keywords", [])))
        preferred_levels = {level.lower() for level in profile.get("preferredRisk", ["LOW", "MEDIUM"])}
        items = []

        for _, row in self.dataset.head(500).iterrows():
            text_tokens = self._tokenize(f"{row['job_title']} {row['FULL_TEXT']} {row['company_name']}")
            overlap = len(target_keywords.intersection(text_tokens)) if target_keywords else 0
            safe_bonus = 20 if row["risk_level"].lower() in preferred_levels else 0
            score = overlap * 15 + safe_bonus + float(row.get("confidence", 0)) * 30
            items.append(
                {
                    **self._serialize_job(row),
                    "personalizationScore": round(score, 2),
                    "matchedKeywords": sorted(target_keywords.intersection(text_tokens))[:6],
                }
            )

        items.sort(key=lambda item: item["personalizationScore"], reverse=True)
        return {"profile": profile, "message": "Đã tạo danh sách gợi ý cá nhân hóa.", "items": items[:8]}

    def get_blacklist(self):
        return self.blacklist

    def check_blacklist(self, job):
        return self._blacklist_matches(self._normalize_input(job))

    def update_blacklist(self, payload):
        self.blacklist = {
            "companies": payload.get("companies", []),
            "emails": payload.get("emails", []),
            "phones": payload.get("phones", []),
        }
        BLACKLIST_PATH.write_text(
            json.dumps(self.blacklist, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return self.blacklist

    def _model_predict(self, job):
        if not self.model_ready:
            return None

        try:
            full_text = " ".join(
                [
                    job["title"],
                    job["companyName"],
                    job["description"],
                    job["requirements"],
                    job["benefits"],
                ]
            )
            row = {
                "FULL_TEXT": full_text,
                "Company Overview": job["companyName"],
                "Salary": job["salary"],
                "Company Size": job["companySize"],
                "Years of Experience": job["experience"],
                "Number Cadidate": job["candidates"],
                "Job Requirements": job["requirements"],
                "Job Description": job["description"],
                "Career Level": job["careerLevel"],
                "Job Type": job["jobType"],
            }

            features = self.extractor.extract_all_features(row)
            frame = pd.DataFrame([{**row, **features}])
            for name in self.feature_names:
                if name not in frame.columns:
                    frame[name] = 0

            x_text = self.tfidf.transform([full_text])
            x_num = frame[self.feature_names].fillna(0)
            x_num_scaled = self.scaler.transform(x_num)
            matrix = hstack([x_text, x_num_scaled])
            probs = self.model.predict_proba(matrix)[0]
            return {"probability_fake": float(probs[0]), "probability_real": float(probs[1])}
        except Exception:
            return None

    def _heuristic_analysis(self, job):
        signals = []
        risk_score = 15

        if len(job["description"].split()) < 60:
            risk_score += 15
            signals.append("Mô tả ngắn, thiếu chi tiết công việc.")
        if any(keyword in job["description"].lower() for keyword in ["dong phi", "viec nhe luong cao", "tuyen gap", "khong can kinh nghiem"]):
            risk_score += 20
            signals.append("Nội dung chứa từ khóa có nguy cơ lừa đảo.")
        if "gmail.com" in job["email"].lower() or "yahoo.com" in job["email"].lower():
            risk_score += 10
            signals.append("Sử dụng email cá nhân thay vì email doanh nghiệp.")
        if not job["companyName"]:
            risk_score += 15
            signals.append("Thiếu thông tin doanh nghiệp.")
        if not job["address"]:
            risk_score += 10
            signals.append("Không có địa chỉ doanh nghiệp rõ ràng.")
        if self._extract_average_salary(job["salary"]) > 50000000:
            risk_score += 15
            signals.append("Mức lương cao bất thường so với thị trường.")

        risk_score = min(100, risk_score)
        confidence = round(0.55 + abs(50 - risk_score) / 100, 3)
        return {"riskScore": risk_score, "confidence": min(0.95, confidence), "signals": signals}

    def _blacklist_matches(self, job):
        company = job["companyName"].lower()
        email = job["email"].lower()
        phone = re.sub(r"\D", "", job["phone"])
        details = []

        for entry in self.blacklist["companies"]:
            if entry.lower() and entry.lower() in company:
                details.append(f"Công ty nằm trong blacklist: {entry}")
        for entry in self.blacklist["emails"]:
            if entry.lower() and entry.lower() in email:
                details.append(f"Email nằm trong blacklist: {entry}")
        for entry in self.blacklist["phones"]:
            if re.sub(r"\D", "", entry) and re.sub(r"\D", "", entry) in phone:
                details.append(f"Số điện thoại nằm trong blacklist: {entry}")

        return {"hasMatch": bool(details), "details": details}

    def _normalize_input(self, payload):
        return {
            "title": str(payload.get("title", "")).strip(),
            "companyName": str(payload.get("companyName", "")).strip(),
            "description": str(payload.get("description", "")).strip(),
            "requirements": str(payload.get("requirements", "")).strip(),
            "benefits": str(payload.get("benefits", "")).strip(),
            "salary": str(payload.get("salary", "")).strip(),
            "address": str(payload.get("address", "")).strip(),
            "email": str(payload.get("email", "")).strip(),
            "phone": str(payload.get("phone", "")).strip(),
            "companySize": str(payload.get("companySize", "")).strip(),
            "experience": str(payload.get("experience", "")).strip(),
            "candidates": int(payload.get("candidates", 0) or 0),
            "careerLevel": str(payload.get("careerLevel", "")).strip(),
            "jobType": str(payload.get("jobType", "")).strip(),
        }

    def _serialize_job(self, row):
        trust_score = round(100 - float(row["risk_score"]), 2)
        return {
            "id": int(row.name),
            "title": row["job_title"],
            "companyName": row["company_name"],
            "salary": row.get("Salary", ""),
            "location": row["location"],
            "confidence": float(row.get("confidence", 0)),
            "trustScore": trust_score,
            "riskScore": float(row["risk_score"]),
            "riskLevel": row["risk_level"],
            "riskLabel": self._risk_label_vi(row["risk_level"]),
            "reputationScore": float(row.get("reputation_score", 0) or 0),
            "companyActive": bool(row.get("company_active", 0)),
            "ruleScore": float(row.get("rule_score", 0) or 0),
            "statusText": "Doanh nghiệp đang hoạt động" if bool(row.get("company_active", 0)) else "Chưa xác minh trạng thái doanh nghiệp",
        }

    def _derive_title(self, row):
        full_text = str(row.get("FULL_TEXT", "")).strip()
        words = full_text.split()
        return " ".join(words[:10]) if words else "Tin tuyển dụng"

    def _derive_location(self, row):
        text = str(row.get("FULL_TEXT", "")).lower()
        cities = {
            "ha noi": "Hà Nội",
            "ho chi minh": "TP Hồ Chí Minh",
            "da nang": "Đà Nẵng",
            "can tho": "Cần Thơ",
            "hai phong": "Hải Phòng",
        }
        for city, label in cities.items():
            if city in text:
                return label
        return "Toàn quốc"

    def _risk_from_row(self, row):
        score = self._risk_score_from_row(row)
        return self._risk_label_from_score(score)

    def _risk_score_from_row(self, row):
        confidence = float(row.get("confidence", 0) or 0)
        rule_score = float(row.get("rule_score", 0) or 0)
        reputation = float(row.get("reputation_score", 0) or 0)
        closed = 25 if float(row.get("company_closed", 0) or 0) else 0
        return round(min(100, rule_score * 10 + reputation * 35 + (1 - confidence) * 40 + closed), 2)

    def _risk_label_from_score(self, score):
        if score < 35:
            return "LOW"
        if score < 65:
            return "MEDIUM"
        return "HIGH"

    def _risk_label_vi(self, score_or_level):
        level = score_or_level if isinstance(score_or_level, str) else self._risk_label_from_score(score_or_level)
        mapping = {
            "LOW": "Thấp",
            "MEDIUM": "Trung bình",
            "HIGH": "Cao",
        }
        return mapping.get(level, "Chưa xác định")

    def _extract_average_salary(self, salary_text):
        nums = [int(num) for num in re.findall(r"\d+", salary_text.replace(",", ""))]
        if not nums:
            return 0
        return sum(nums) / len(nums)

    def _parse_reason_list(self, raw):
        if not raw:
            return []
        cleaned = str(raw).strip("[]")
        parts = [part.strip().strip("'").strip('"') for part in cleaned.split(",")]
        return [part for part in parts if part]

    def _tokenize(self, text):
        return {token for token in re.findall(r"\w+", text.lower()) if len(token) > 2}

    def _personalization_score(self, job, profile):
        profile = profile or {}
        keywords = self._tokenize(" ".join(profile.get("keywords", [])))
        job_tokens = self._tokenize(" ".join([job["title"], job["description"], job["requirements"]]))
        overlap = sorted(keywords.intersection(job_tokens))
        return {
            "fitScore": round(min(100, len(overlap) * 20 + (20 if job["jobType"] in profile.get("jobTypes", []) else 0)), 2),
            "matchedKeywords": overlap[:6],
        }


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
