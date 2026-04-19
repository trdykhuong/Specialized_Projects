"""
services/recruitment_trust.py

Toàn bộ logic ML, heuristic, blacklist, dataset từ file app.py gốc
được chuyển vào đây. Không có gì thay đổi về thuật toán —
chỉ tách ra để app.py gọn hơn.

Sử dụng:
    predictor = RecruitmentTrustService()
    predictor.load_assets()
    result = predictor.analyze_job(payload)
"""
import json
import re
import sys
from pathlib import Path

import joblib
import pandas as pd
from scipy.sparse import hstack

BASE_DIR = Path(__file__).resolve().parents[2]   # project root
DATA_PATH = BASE_DIR / "data" / "JOB_DATA_FINAL.csv"
MODELS_DIR = BASE_DIR / "models"
BLACKLIST_PATH = Path(__file__).resolve().parent.parent / "blacklist.json"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml_pipeline.src.advanced_features import AdvancedFeatureExtractor


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

    # ------------------------------------------------------------------ #
    # Bootstrap
    # ------------------------------------------------------------------ #

    def load_assets(self):
        self._load_models()
        self._load_dataset()
        self._load_blacklist()

    def _load_models(self):
        try:
            self.model        = joblib.load(MODELS_DIR / "best_model.pkl")
            self.tfidf        = joblib.load(MODELS_DIR / "tfidf_vectorizer.pkl")
            self.scaler       = joblib.load(MODELS_DIR / "scaler.pkl")
            self.feature_names = joblib.load(MODELS_DIR / "feature_names.pkl")
            self.model_ready  = True
        except Exception:
            self.model_ready = False

    def _load_dataset(self):
        if not DATA_PATH.exists():
            return
        df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
        df = df.fillna("")
        df["job_title"] = df.get("Job Title", "").astype(str).str.strip()
        df["company_name"] = df.get("Name Company", "").astype(str).str.strip()
        df["location"] = df.apply(self._derive_location, axis=1)
        df["full_text"] = df.apply(self._build_full_text, axis=1)
        job_ids = pd.to_numeric(df.get("JobID"), errors="coerce")
        fallback_ids = pd.Series(df.index, index=df.index, dtype="int64")
        df["dataset_job_id"] = job_ids.where(job_ids.notna(), fallback_ids).astype(int)
        self.dataset       = df
        self.dataset_ready = not df.empty

    def _load_blacklist(self):
        if BLACKLIST_PATH.exists():
            self.blacklist = json.loads(BLACKLIST_PATH.read_text(encoding="utf-8"))
        else:
            BLACKLIST_PATH.write_text(
                json.dumps(self.blacklist, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    # ------------------------------------------------------------------ #
    # Dashboard
    # ------------------------------------------------------------------ #

    def get_dashboard_overview(self):
        if not self.dataset_ready:
            return {
                "summary": {
                    "totalJobs": 0, "lowRiskJobs": 0,
                    "mediumRiskJobs": 0, "highRiskJobs": 0, "averageConfidence": 0,
                },
                "charts": {"riskDistribution": [], "topCompanies": [], "topReasons": []},
                "system": {
                    "modelReady": self.model_ready,
                    "datasetReady": self.dataset_ready,
                    "modelMessage": "Chưa tải được mô hình.",
                    "datasetMessage": "Chưa tải được dữ liệu.",
                },
            }

        top_companies = (
            self.dataset["company_name"]
            .replace("", "Chưa rõ")
            .value_counts()
            .head(5)
            .items()
        )
        top_reasons: dict[str, int] = {}
        if "rule_reasons" in self.dataset.columns:
            for raw in self.dataset["rule_reasons"].head(300):
                for reason in self._parse_reason_list(raw):
                    top_reasons[reason] = top_reasons.get(reason, 0) + 1

        return {
            "summary": {
                "totalJobs": int(len(self.dataset)),
                "lowRiskJobs": 0,
                "mediumRiskJobs": 0,
                "highRiskJobs": 0,
                "averageConfidence": 0,
            },
            "charts": {
                "riskDistribution": [],
                "topCompanies": [{"name": c, "value": int(n)} for c, n in top_companies],
                "topReasons": [{"reason": r, "value": v} for r, v in sorted(top_reasons.items(), key=lambda x: x[1], reverse=True)[:5]],
            },
            "system": {
                "modelReady": self.model_ready,
                "datasetReady": self.dataset_ready,
                "modelMessage": "Mô hình đã sẵn sàng." if self.model_ready else "Chưa tải được mô hình.",
                "datasetMessage": "Dữ liệu đã sẵn sàng." if self.dataset_ready else "Chưa tải được dữ liệu.",
            },
        }

    # ------------------------------------------------------------------ #
    # Jobs list
    # ------------------------------------------------------------------ #

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
                | df["full_text"].str.lower().str.contains(q, na=False)
            )
            df = df[mask]

        total = int(len(df))
        total_pages = (total + page_size - 1) // page_size if total else 0
        page = min(page, total_pages) if total_pages > 0 else 1
        start = (page - 1) * page_size
        paged_df = df.iloc[start : start + page_size]

        return {
            "items": [self._serialize_job(row) for _, row in paged_df.iterrows()],
            "total": total,
            "page": page,
            "pageSize": page_size,
            "totalPages": total_pages,
            "hasNext": page < total_pages,
            "hasPrevious": page > 1 and total_pages > 0,
        }

    def get_job(self, job_id):
        if not self.dataset_ready:
            return None
        try:
            normalized_id = int(job_id)
        except (TypeError, ValueError):
            return None

        matched = self.dataset[self.dataset["dataset_job_id"] == normalized_id]
        if matched.empty:
            return None
        row = matched.iloc[0]
        return self._serialize_job(row)

    # ------------------------------------------------------------------ #
    # Analysis
    # ------------------------------------------------------------------ #

    def analyze_job(self, payload):
        job          = self._normalize_input(payload)
        heuristic    = self._heuristic_analysis(job)
        blacklist    = self._blacklist_matches(job)
        recommendation = self._personalization_score(job, payload.get("candidateProfile", {}))
        model_result = self._model_predict(job)

        if model_result:
            model_risk  = model_result["probability_fake"] * 100
            risk_score  = round(model_risk * 0.65 + heuristic["riskScore"] * 0.35, 2)
            trust_score = round(100 - risk_score, 2)
            confidence  = round(
                max(model_result["probability_real"], model_result["probability_fake"]) * 0.7
                + heuristic["confidence"] * 0.3,
                3,
            )
        else:
            risk_score  = heuristic["riskScore"]
            trust_score = 100 - risk_score
            confidence  = heuristic["confidence"]

        if blacklist["hasMatch"]:
            risk_score  = min(100, risk_score + 20)
            trust_score = max(0, 100 - risk_score)

        result = {
            "trustScore":   trust_score,
            "riskScore":    risk_score,
            "riskLevel":    self._risk_label_from_score(risk_score),
            "riskLabel":    self._risk_label_vi(risk_score),
            "confidence":   confidence,
            "decision":     (
                "Tin cậy" if risk_score < 40
                else "Cần kiểm tra" if risk_score < 70
                else "Nguy cơ cao"
            ),
            "modelReady":   self.model_ready,
            "modelMessage": (
                "Đã dùng mô hình máy học." if model_result
                else "Đang dùng heuristic vì chưa có mô hình phù hợp."
            ),
        }

        return {
            "job": job,
            "result": result,
            "trustScore": result["trustScore"],
            "riskScore": result["riskScore"],
            "riskLevel": result["riskLevel"],
            "riskLabel": result["riskLabel"],
            "confidence": result["confidence"],
            "decision": result["decision"],
            "modelReady": result["modelReady"],
            "modelMessage": result["modelMessage"],
            "signals":         heuristic["signals"],
            "blacklist":       blacklist,
            "personalization": recommendation,
        }

    def batch_analyze(self, payload):
        jobs         = payload.get("jobs", []) if isinstance(payload, dict) else []
        raw_text     = payload.get("rawText", "") if isinstance(payload, dict) else ""
        parsing_notes = []

        if raw_text:
            parsed_jobs, parsing_notes = self._parse_bulk_jobs(raw_text)
            jobs = jobs + parsed_jobs

        jobs    = jobs[:50]
        results = [self.analyze_job(job) for job in jobs]

        risk_levels = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
        for item in results:
            risk_levels[item["result"]["riskLevel"]] += 1

        avg_trust = (
            round(sum(i["result"]["trustScore"] for i in results) / len(results), 2)
            if results else 0
        )
        return {
            "items": results,
            "summary": {
                "total":           len(results),
                "parsedFromText":  len(jobs),
                "riskLevels":      risk_levels,
                "riskLevelsVi":    {
                    "Thấp": risk_levels["LOW"],
                    "Trung bình": risk_levels["MEDIUM"],
                    "Cao": risk_levels["HIGH"],
                },
                "averageTrustScore": avg_trust,
                "message": "Đã phân tích danh sách tin tuyển dụng.",
            },
            "parsingNotes": parsing_notes,
        }

    # ------------------------------------------------------------------ #
    # Recommendation
    # ------------------------------------------------------------------ #

    def recommend_jobs(self, payload):
        if not self.dataset_ready:
            return {"profile": payload, "message": "Chưa có dữ liệu để gợi ý.", "items": []}

        profile = payload or {}
        target_keywords = self._tokenize(" ".join(profile.get("keywords", [])))
        preferred_levels = {l.lower() for l in profile.get("preferredRisk", ["LOW", "MEDIUM"])}
        items = []

        for _, row in self.dataset.head(500).iterrows():
            text_tokens = self._tokenize(f"{row['job_title']} {row['full_text']} {row['company_name']}")
            overlap = len(target_keywords.intersection(text_tokens)) if target_keywords else 0
            safe_bonus = 20 if preferred_levels else 0
            score = overlap * 15 + safe_bonus
            items.append({
                **self._serialize_job(row),
                "personalizationScore": round(score, 2),
                "matchedKeywords": sorted(target_keywords.intersection(text_tokens))[:6],
            })

        items.sort(key=lambda x: x["personalizationScore"], reverse=True)
        return {"profile": profile, "message": "Đã tạo danh sách gợi ý cá nhân hóa.", "items": items[:8]}

    # ------------------------------------------------------------------ #
    # Blacklist
    # ------------------------------------------------------------------ #

    def get_blacklist(self):
        return self.blacklist

    def check_blacklist(self, job):
        return self._blacklist_matches(self._normalize_input(job))

    def update_blacklist(self, payload):
        self.blacklist = {
            "companies": self._normalize_blacklist_items(payload.get("companies", [])),
            "emails":    self._normalize_blacklist_items(payload.get("emails", []),  item_type="email"),
            "phones":    self._normalize_blacklist_items(payload.get("phones", []),  item_type="phone"),
        }
        BLACKLIST_PATH.write_text(
            json.dumps(self.blacklist, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return self.blacklist

    # ------------------------------------------------------------------ #
    # ML predict
    # ------------------------------------------------------------------ #

    def _model_predict(self, job):
        if not self.model_ready:
            return None
        try:
            full_text = " ".join([
                job["title"], job["companyName"], job["description"],
                job["requirements"], job["benefits"],
            ])
            row = {
                "FULL_TEXT":           full_text,
                "Company Overview":    job["companyName"],
                "Salary":              job["salary"],
                "Company Size":        job["companySize"],
                "Years of Experience": job["experience"],
                "Number Cadidate":     job["candidates"],
                "Job Requirements":    job["requirements"],
                "Job Description":     job["description"],
                "Career Level":        job["careerLevel"],
                "Job Type":            job["jobType"],
            }
            features = self.extractor.extract_all_features(row)
            frame    = pd.DataFrame([{**row, **features}])
            for name in self.feature_names:
                if name not in frame.columns:
                    frame[name] = 0

            x_text      = self.tfidf.transform([full_text])
            x_num       = frame[self.feature_names].fillna(0)
            x_num_scaled = self.scaler.transform(x_num)
            matrix      = hstack([x_text, x_num_scaled])
            probs       = self.model.predict_proba(matrix)[0]
            return {"probability_fake": float(probs[0]), "probability_real": float(probs[1])}
        except Exception:
            return None

    # ------------------------------------------------------------------ #
    # Heuristic
    # ------------------------------------------------------------------ #

    def _heuristic_analysis(self, job):
        signals    = []
        risk_score = 15

        if len(job["description"].split()) < 60:
            risk_score += 15
            signals.append("Mô tả ngắn, thiếu chi tiết công việc.")
        if not job["requirements"]:
            risk_score += 10
            signals.append("Thiếu yêu cầu công việc.")
        if not job["companySize"]:
            risk_score += 5
            signals.append("Thiếu quy mô công ty.")
        if any(kw in job["description"].lower() for kw in
               ["dong phi", "viec nhe luong cao", "tuyen gap", "khong can kinh nghiem"]):
            risk_score += 20
            signals.append("Nội dung chứa từ khóa có nguy cơ lừa đảo.")
        if "gmail.com" in job["email"].lower() or "yahoo.com" in job["email"].lower():
            risk_score += 10
            signals.append("Sử dụng email cá nhân thay vì email doanh nghiệp.")
        if not job["email"]:
            risk_score += 3
            signals.append("Thiếu email liên hệ.")
        if not job["phone"]:
            risk_score += 2
            signals.append("Thiếu số điện thoại liên hệ.")
        if not job["companyName"]:
            risk_score += 15
            signals.append("Thiếu thông tin doanh nghiệp.")
        if not job["address"]:
            risk_score += 10
            signals.append("Không có địa chỉ doanh nghiệp rõ ràng.")
        if not job["careerLevel"]:
            risk_score += 5
            signals.append("Thiếu cấp bậc công việc.")
        if not job["jobType"]:
            risk_score += 5
            signals.append("Thiếu loại hình công việc.")
        if not job["experience"]:
            risk_score += 5
            signals.append("Thiếu yêu cầu kinh nghiệm.")
        if not job["salary"]:
            risk_score += 5
            signals.append("Thiếu thông tin lương.")
        if self._extract_average_salary(job["salary"]) > 50_000_000:
            risk_score += 15
            signals.append("Mức lương cao bất thường so với thị trường.")

        risk_score = min(100, risk_score)
        confidence = round(0.55 + abs(50 - risk_score) / 100, 3)
        return {"riskScore": risk_score, "confidence": min(0.95, confidence), "signals": signals}

    # ------------------------------------------------------------------ #
    # Blacklist matching
    # ------------------------------------------------------------------ #

    def _blacklist_matches(self, job):
        company = job["companyName"].lower()
        email   = job["email"].lower()
        phone   = re.sub(r"\D", "", job["phone"])
        details = []

        for entry in self.blacklist["companies"]:
            if entry.lower() and entry.lower() in company:
                details.append(f"Công ty nằm trong blacklist: {entry}")
        for entry in self.blacklist["emails"]:
            if entry.lower() and entry.lower() in email:
                details.append(f"Email nằm trong blacklist: {entry}")
        for entry in self.blacklist["phones"]:
            clean = re.sub(r"\D", "", entry)
            if clean and clean in phone:
                details.append(f"Số điện thoại nằm trong blacklist: {entry}")

        return {"hasMatch": bool(details), "details": details}

    # ------------------------------------------------------------------ #
    # Normalization & serialization
    # ------------------------------------------------------------------ #

    def _normalize_input(self, payload):
        return {
            "title":       str(payload.get("title",       "")).strip(),
            "companyName": str(payload.get("companyName", "")).strip(),
            "description": str(payload.get("description", "")).strip(),
            "requirements":str(payload.get("requirements","")).strip(),
            "benefits":    str(payload.get("benefits",    "")).strip(),
            "salary":      str(payload.get("salary",      "")).strip(),
            "address":     str(payload.get("address",     "")).strip(),
            "email":       str(payload.get("email",       "")).strip(),
            "phone":       str(payload.get("phone",       "")).strip(),
            "companySize": str(payload.get("companySize", "")).strip(),
            "experience":  str(payload.get("experience",  "")).strip(),
            "candidates":  int(payload.get("candidates",  0) or 0),
            "careerLevel": str(payload.get("careerLevel", "")).strip(),
            "jobType":     str(payload.get("jobType",     "")).strip(),
        }

    def _serialize_job(self, row):
        return {
            "id":                 int(row.get("dataset_job_id", row.name)),
            "jobId":              int(row.get("dataset_job_id", row.name)),
            "urlJob":             str(row.get("URL Job", "") or "").strip(),
            "title":              row["job_title"],
            "jobTitle":           row["job_title"],
            "companyName":        row["company_name"],
            "nameCompany":        row["company_name"],
            "companyOverview":    str(row.get("Company Overview", "") or "").strip(),
            "companySize":        str(row.get("Company Size", "") or "").strip(),
            "companyAddress":     str(row.get("Company Address", "") or "").strip(),
            "description":        str(row.get("Job Description", "") or "").strip(),
            "requirements":       str(row.get("Job Requirements", "") or "").strip(),
            "benefits":           str(row.get("Benefits", "") or "").strip(),
            "jobAddress":         str(row.get("Job Address", "") or "").strip(),
            "location":           row["location"],
            "address":            str(row.get("Job Address", "") or row["location"]).strip(),
            "jobType":            str(row.get("Job Type", "") or "").strip(),
            "gender":             str(row.get("Gender", "") or "").strip(),
            "candidates":         int(row.get("Number Cadidate", 0) or 0),
            "numberCadidate":     int(row.get("Number Cadidate", 0) or 0),
            "careerLevel":        str(row.get("Career Level", "") or "").strip(),
            "experience":         str(row.get("Years of Experience", "") or "").strip(),
            "yearsOfExperience":  str(row.get("Years of Experience", "") or "").strip(),
            "salary":             row.get("Salary", ""),
            "submissionDeadline": str(row.get("Submission Deadline", "") or "").strip(),
            "industry":           str(row.get("Industry", "") or "").strip(),
            "email":              "",
            "phone":              "",
        }

    # ------------------------------------------------------------------ #
    # Derive helpers
    # ------------------------------------------------------------------ #

    def _derive_location(self, row):
        job_address = str(row.get("Job Address", "")).strip()
        company_address = str(row.get("Company Address", "")).strip()
        return job_address or company_address or "Toàn quốc"

    def _build_full_text(self, row):
        return " ".join(
            [
                str(row.get("Job Title", "")).strip(),
                str(row.get("Name Company", "")).strip(),
                str(row.get("Company Overview", "")).strip(),
                str(row.get("Job Description", "")).strip(),
                str(row.get("Job Requirements", "")).strip(),
                str(row.get("Benefits", "")).strip(),
                str(row.get("Industry", "")).strip(),
            ]
        ).strip()

    def _risk_from_row(self, row):
        return self._risk_label_from_score(self._risk_score_from_row(row))

    def _risk_score_from_row(self, row):
        confidence  = float(row.get("confidence",       0) or 0)
        rule_score  = float(row.get("rule_score",       0) or 0)
        reputation  = float(row.get("reputation_score", 0) or 0)
        closed      = 25 if float(row.get("company_closed", 0) or 0) else 0
        return round(min(100, rule_score * 10 + reputation * 35 + (1 - confidence) * 40 + closed), 2)

    def _risk_label_from_score(self, score):
        if score < 35: return "LOW"
        if score < 65: return "MEDIUM"
        return "HIGH"

    def _risk_label_vi(self, score_or_level):
        level = score_or_level if isinstance(score_or_level, str) else self._risk_label_from_score(score_or_level)
        return {"LOW": "Thấp", "MEDIUM": "Trung bình", "HIGH": "Cao"}.get(level, "Chưa xác định")

    def _extract_average_salary(self, salary_text):
        nums = [int(n) for n in re.findall(r"\d+", salary_text.replace(",", ""))]
        return sum(nums) / len(nums) if nums else 0

    def _parse_reason_list(self, raw):
        if not raw: return []
        cleaned = str(raw).strip("[]")
        parts   = [p.strip().strip("'\"") for p in cleaned.split(",")]
        return [p for p in parts if p]

    def _tokenize(self, text):
        return {t for t in re.findall(r"\w+", text.lower()) if len(t) > 2}

    def _personalization_score(self, job, profile):
        profile    = profile or {}
        keywords   = self._tokenize(" ".join(profile.get("keywords", [])))
        job_tokens = self._tokenize(" ".join([job["title"], job["description"], job["requirements"]]))
        overlap    = sorted(keywords.intersection(job_tokens))
        return {
            "fitScore": round(
                min(100, len(overlap) * 20 + (20 if job["jobType"] in profile.get("jobTypes", []) else 0)),
                2,
            ),
            "matchedKeywords": overlap[:6],
        }

    def _normalize_blacklist_items(self, items, item_type="text"):
        normalized, seen = [], set()
        for raw in items:
            value = str(raw).strip()
            if not value: continue
            if item_type == "email":
                key = value = value.lower()
            elif item_type == "phone":
                key = value = re.sub(r"\D", "", value)
            else:
                key   = re.sub(r"\s+", " ", value.lower())
                value = re.sub(r"\s+", " ", value)
            if not key or key in seen: continue
            seen.add(key)
            normalized.append(value)
        return normalized

    def _parse_bulk_jobs(self, raw_text):
        blocks = [b.strip() for b in re.split(r"\n\s*\n+", str(raw_text)) if b.strip()]
        jobs, notes = [], []
        for i, block in enumerate(blocks, start=1):
            parsed = self._parse_job_block(block)
            if parsed:
                jobs.append(parsed)
            else:
                notes.append(f"Khối dữ liệu #{i} chưa đủ rõ để tách tự động.")
        return jobs, notes

    def _parse_job_block(self, block):
        lines = [l.strip(" -\t") for l in block.splitlines() if l.strip()]
        job   = {k: "" for k in [
            "title","companyName","description","requirements","benefits",
            "salary","address","email","phone","companySize","experience",
            "careerLevel","jobType",
        ]}
        job["candidates"] = 0

        key_map = {
            "vi tri":"title","vị trí":"title","chuc danh":"title","chức danh":"title",
            "ten cong ty":"companyName","tên công ty":"companyName",
            "cong ty":"companyName","công ty":"companyName",
            "mo ta":"description","mô tả":"description",
            "yeu cau":"requirements","yêu cầu":"requirements",
            "phuc loi":"benefits","phúc lợi":"benefits",
            "muc luong":"salary","mức lương":"salary","luong":"salary","lương":"salary",
            "dia chi":"address","địa chỉ":"address",
            "email":"email",
            "so dien thoai":"phone","số điện thoại":"phone",
            "dien thoai":"phone","điện thoại":"phone",
        }

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                nkey = re.sub(r"\s+", " ", key.lower()).strip()
                if nkey in key_map:
                    job[key_map[nkey]] = value.strip()
                    continue
            lower_line = line.lower()
            if not job["email"]:
                m = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", line)
                if m: job["email"] = m.group(0)
            if not job["phone"]:
                m = re.search(r"(\+?\d[\d\s().-]{7,}\d)", line)
                if m: job["phone"] = m.group(1)
            if not job["salary"] and re.search(r"\d", line) and any(
                t in lower_line for t in ["lương","luong","triệu","trieu","vnđ","vnd"]
            ):
                job["salary"] = line

        if not job["title"] and lines:
            segs = re.split(r"\s*[|;,-]\s*", lines[0])
            if segs:
                job["title"] = segs[0].strip()
                if len(segs) > 1 and not job["companyName"]:
                    job["companyName"] = segs[1].strip()

        if not job["companyName"]:
            for line in lines[1:3]:
                if "công ty" in line.lower() or "cong ty" in line.lower():
                    job["companyName"] = re.sub(r"(?i)(tên công ty|công ty)\s*:", "", line).strip()
                    break

        if not job["description"]:
            remaining = [
                l for l in lines[1:]
                if not any(t in l.lower() for t in
                           ["công ty","cong ty","lương","luong","email","địa chỉ","dia chi",
                            "số điện thoại","so dien thoai"])
            ]
            job["description"] = " ".join(remaining[:4]).strip()

        if not job["title"] and not job["description"]:
            return None
        return job
