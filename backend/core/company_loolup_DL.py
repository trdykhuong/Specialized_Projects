import re
import time
import random
import logging
import torch
import torch.nn.functional as F
from datetime import datetime
from ddgs import DDGS
from thefuzz import fuzz
import requests
from bs4 import BeautifulSoup
from transformers import pipeline

# =========================
# CONFIG
# =========================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

CACHE_TTL = 86400

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================
# HEADERS
# =========================

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Connection": "keep-alive"
    }

# =========================
# CACHE
# =========================

def set_cache(cache, key, value):
    cache[key] = {
        "data": value,
        "time": time.time()
    }

def get_cache(cache, key):
    item = cache.get(key)
    if not item:
        return None
    if time.time() - item["time"] > CACHE_TTL:
        return None
    return item["data"]

# =========================
# UTILS
# =========================

def normalize_text(text: str) -> str:
    return text.lower().strip()

_ABBR_MAP = {
    r'\bdv\b':   'dịch vụ',
    r'\btm\b':   'thương mại',
    r'\bxnk\b':  'xuất nhập khẩu',
    r'\bxk\b':   'xuất khẩu',
    r'\bnk\b':   'nhập khẩu',
    r'\bsx\b':   'sản xuất',
    r'\bxd\b':   'xây dựng',
    r'\bth\b':   'tổng hợp',
    r'\bdt\b':   'đầu tư',
    r'\bptnt\b': 'phát triển nông thôn',
    r'\btmcp\b': 'thương mại cổ phần',
    r'\btnhh\b': 'trách nhiệm hữu hạn',
    r'\bctcp\b': 'cổ phần',
    r'\bcp\b':   'cổ phần',
}

def expand_abbreviations(name: str) -> str:
    result = name.lower()
    for pattern, replacement in _ABBR_MAP.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result

def normalize_company_name(name: str) -> str:
    name = re.sub(r'[\r\n]+', ' ', name)
    name = re.sub(r'\s*\(.*?\)\s*', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def fuzzy_score(a: str, b: str) -> float:
    a = expand_abbreviations(normalize_text(a))
    b = expand_abbreviations(normalize_text(b))
    return max(
        fuzz.token_set_ratio(a, b),
        fuzz.partial_ratio(a, b),
        fuzz.ratio(a, b)
    ) / 100.0

def normalize_tax_code(mst: str) -> str:
    return mst.split('-')[0] if mst else None

def split_text(text, chunk_size=300):
    """Chunk theo câu cho BERT"""
    sentences = re.split(r'[.!?]', text)
    chunks = []
    current = ""
    for s in sentences:
        if len(current) + len(s) < chunk_size:
            current += " " + s
        else:
            chunks.append(current.strip())
            current = s
    if current:
        chunks.append(current.strip())
    return chunks

# =========================
# EXTRACT INFO (dùng cho runtime khi không có tên công ty)
# =========================

def extract_company_name_from_text(text: str):
    """
    Trích xuất tên công ty từ mô tả bài đăng (dùng khi người dùng gửi text).
    Chỉ dùng khi KHÔNG có tên công ty rõ ràng (luồng runtime/API).
    """
    PREFIX = (
        r'(?:công ty(?:\s+(?:cổ phần|tnhh|cp|trách nhiệm hữu hạn))?' 
        r'|cty(?:\s+cp)?|ctcp|tập đoàn|ngân hàng(?:\s+tmcp)?' 
        r'|chi nhánh|văn phòng đại diện)'
    )
    STOP = (
        r'(?=\n|\r|;|\||@|\d{9,}'
        r'|(?i:trân trọng|kính gửi|địa chỉ|website|hotline'
        r'|liên hệ|điện thoại|việc làm|tuyển dụng|mô tả công việc))'
    )
    pattern = rf'(?i){PREFIX}\s+(.+?){STOP}'
    match = re.search(pattern, text)
    if not match:
        return None

    raw = match.group(1).strip()
    raw = re.sub(r'\s*[:\-–]\s*$', '', raw)
    raw = re.sub(r'\s*\(.*?\)\s*$', '', raw)
    raw = re.sub(r',\s*$', '', raw)
    raw = re.sub(r'[\r\n]+', ' ', raw)
    raw = re.sub(r'\s+', ' ', raw).strip()

    if len(raw) > 120:
        cut = re.search(r'(?<=.{60})[,\-–]', raw)
        if cut:
            raw = raw[:cut.start()].strip()

    return "Công ty " + raw if raw else None


def extract_tax_code(text: str):
    match = re.search(
        r'(?i)(?:mst|mã số thuế)[\s:]*([0-9]{10}(?:-[0-9]{3})?)',
        text
    )
    return match.group(1) if match else None

# =========================
# SEARCH MST
# =========================

def _extract_name_from_title(title: str) -> str:
    """
    Trích phần tên công ty ra khỏi title masothue.

    masothue trả title theo 2 format:
      Format A: "Công ty CP Công nghệ ISOFH - Mã số thuế 0107869256"
                → tên ở TRƯỚC dấu ' - '
      Format B: "0107869256 - Công ty CP Công nghệ ISOFH"
                → tên ở SAU dấu ' - ' (bug cũ: lấy nhầm phần số MST)
    """
    if ' - ' not in title:
        return title.strip()

    parts = title.split(' - ', 1)
    left, right = parts[0].strip(), parts[1].strip()

    if re.fullmatch(r'[\d\s]+', left):
        return right

    return left


_ABBREV_MAP = {
    r'\btnhh\b':  'trách nhiệm hữu hạn',
    r'\bcp\b':    'cổ phần',
    r'\bctcp\b':  'công ty cổ phần',
    r'\bcty\b':   'công ty',
    r'\bdv\b':    'dịch vụ',
    r'\btm\b':    'thương mại',
    r'\bxnk\b':   'xuất nhập khẩu',
    r'\btmcp\b':  'thương mại cổ phần',
    r'\bvt\b':    'vận tải',
    r'\bxd\b':    'xây dựng',
    r'\bsx\b':    'sản xuất',
    r'\bđt\b':    'đầu tư',
    r'\bqc\b':    'quảng cáo',
    r'\bbđs\b':   'bất động sản',
    r'\bcntt\b':  'công nghệ thông tin',
}

_GENERIC_PREFIXES = [
    'công ty', 'cty', 'ctcp', 'tnhh', 'cổ phần', r'\bcp\b',
    'thương mại', 'dịch vụ', r'\btm\b', r'\bdv\b', 'xnk', 'xuất nhập khẩu',
    'đầu tư', 'xây dựng', 'sản xuất', 'phần mềm', 'công nghệ',
    'giải pháp', 'tư vấn', 'ngân hàng', 'tmcp', r'\bvà\b',
]


def _expand_abbreviations(name: str) -> str:
    result = name.lower()
    for pattern, replacement in _ABBREV_MAP.items():
        result = re.sub(pattern, replacement, result)
    return result


def _extract_unique_keyword(company_name: str) -> str:
    """
    Trích từ khoá đặc trưng — dùng làm fallback query khi tên đầy đủ không tìm được.
    VD: "công ty tnhh phần mềm acazia" → "acazia"
        "công ty cổ phần đầu tư dv tm agv v" → "agv"  (xử lý tên bị cắt)
    """
    name = company_name.strip().lower()
    name = re.sub(r'\(.*?\)', '', name).strip()

    changed = True
    while changed:
        changed = False
        for p in _GENERIC_PREFIXES:
            new = re.sub(rf'^{p}\s*', '', name, flags=re.I).strip()
            if new != name:
                name = new
                changed = True

    words = name.split()
    keyword = ' '.join(words[-3:]) if len(words) >= 3 else name
    keyword = re.sub(r'\s+\b[a-zA-ZÀ-ỹ]\b$', '', keyword).strip()
    return keyword


def find_mst_by_name_search(company_name: str):
    """
    Tìm MST trên masothue.com theo tên công ty.
    Chiến lược 3 bước:
      1. Tên đã expand viết tắt   → query đầy đủ nhất
      2. Unique keyword            → fallback khi tên bị cắt/viết tắt lạ
      3. Bỏ site: filter          → fallback cuối nếu DDG không index được
    """
    expanded = _expand_abbreviations(company_name)
    keyword  = _extract_unique_keyword(company_name)

    queries = [expanded]
    if keyword and keyword != expanded:
        queries.append(keyword)

    for query_term in queries:
        clean_q = re.sub(r'\(.*?\)', '', query_term).strip()

        result = _search_masothue(f'site:masothue.com {clean_q}', company_name)
        if result:
            return result

        result = _search_masothue(f'masothue.com {clean_q}', company_name)
        if result:
            return result

    return None


def _search_masothue(query: str, original_name: str):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))

        if not results:
            return None

        best_match = None
        best_score = 0.0

        for res in results:
            title = res.get('title', '')
            body  = res.get('body',  '')
            href  = res.get('href',  '')

            title_name = _extract_name_from_title(title)
            score = fuzzy_score(original_name, title_name)
            mst_match = re.search(r'\b([0-9]{10})\b', f"{href} {title} {body}")

            if mst_match and score >= best_score:
                best_score = score
                best_match = {
                    "mst":        mst_match.group(1),
                    "confidence": score
                }

        return best_match

    except Exception as e:
        logger.error(f"[Search Error] '{query}': {e}")
        return None

# =========================
# CRAWL
# =========================

company_cache = {}

def get_real_company_details(mst: str):
    cached = get_cache(company_cache, mst)
    if cached:
        return cached

    result = {
        "status": "Không rõ",
        "founded_year": datetime.now().year,
        "founded_month": datetime.now().month,
        "verified": 0
    }

    url = f"https://masothue.com/Search/?q={mst}"

    try:
        time.sleep(random.uniform(0.5, 1.5))
        response = requests.get(url, headers=get_headers(), timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Lấy trạng thái qua id='tax-status-html'
            # (masothue hiển thị: "Tình trạng" với value trong <a> bên trong td)
            status_td = soup.find('td', id='tax-status-html')
            if status_td:
                result["status"] = status_td.get_text(strip=True)

            # Lấy ngày hoạt động qua icon fa-calendar
            # (masothue dùng "Ngày hoạt động", định dạng YYYY-MM-DD)
            cal_icon = soup.find('i', class_='fa-calendar')
            if cal_icon:
                label_td = cal_icon.find_parent('td')
                value_td = label_td.find_next_sibling('td') if label_td else None
                if value_td:
                    date_text = value_td.get_text(strip=True)
                    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_text)
                    if m:
                        result["founded_year"]  = int(m.group(1))
                        result["founded_month"] = int(m.group(2))

            result["verified"] = 1

    except Exception as e:
        logger.error(f"[Crawl Error] MST {mst}: {e}")

    set_cache(company_cache, mst, result)
    return result

# =========================
# CORE: RESOLVE COMPANY NAME
# =========================

def _resolve_company_name(company_name: str | None, text: str | None):
    """
    Trả về (company_name_final, source) với source là:
      - 'direct'    : tên công ty được cung cấp thẳng (từ CSV hoặc frontend)
      - 'extracted' : tên được extract từ text mô tả
      - 'none'      : không tìm được tên công ty
    """
    if company_name and company_name.strip():
        return company_name.strip(), 'direct'

    if text:
        extracted = extract_company_name_from_text(text)
        if extracted:
            return extracted, 'extracted'

    return None, 'none'

# =========================
# LOAD BERT MODEL
# =========================

device = 0 if torch.cuda.is_available() else -1

sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment",
    device=device
)

tokenizer = sentiment_analyzer.tokenizer
model = sentiment_analyzer.model
device = model.device

# =========================
# BATCH INFERENCE
# =========================

def batch_ml_risk_score(texts: list[str]) -> list[float]:
    inputs = tokenizer(
        texts,
        truncation=True,
        max_length=512,
        padding=True,
        return_tensors="pt"
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    probs = F.softmax(outputs.logits, dim=1).detach().cpu().numpy()

    scores = []
    for prob in probs:
        n = len(prob)
        risk = sum((n - 1 - i) / (n - 1) * prob[i] for i in range(n))
        scores.append(float(risk))

    return scores

# =========================
# MAIN FEATURE FUNCTION (Dual-mode)
# =========================

def process_company_features(
    company_name: str | None = None,
    text: str | None = None
):
    """
    Trích xuất features xác minh công ty qua MST.

    Sử dụng:
    --------
    - Luồng TRAIN (từ CSV):
        process_company_features(company_name=row['Name Company'])

    - Luồng RUNTIME (từ mô tả người dùng gửi lên):
        process_company_features(text=job_description)

    - Kết hợp (có cả hai — ưu tiên company_name):
        process_company_features(company_name=name, text=description)

    Tham số:
    --------
    company_name : str | None
        Tên công ty được cung cấp trực tiếp (ưu tiên cao hơn).
    text : str | None
        Mô tả bài đăng để fallback extract tên + tax code.

    Trả về:
    -------
    dict với các features:
        company_name_source  : 'direct' | 'extracted' | 'none'
        company_found        : 1 nếu tìm được MST trên masothue.com
        company_match_score  : độ tin cậy khi match tên → MST (0.0–1.0)
        company_is_branch    : 1 nếu là chi nhánh (MST có dấu -)
        company_active       : 1 nếu đang hoạt động
        company_closed       : 1 nếu đã ngừng hoạt động
        company_unknown      : 1 nếu không rõ trạng thái
        company_age_months   : số tháng tuổi của công ty
    """
    now = datetime.now()

    # --- Bước 1: xác định tên công ty ---
    resolved_name, name_source = _resolve_company_name(company_name, text)

    # --- Bước 2: tìm tax code (từ text nếu có) ---
    tax_code = None
    if text:
        tax_code = extract_tax_code(text)

    # --- Bước 3: resolve MST ---
    target_mst = None
    match_score = 0.0
    is_branch = 1 if tax_code and '-' in tax_code else 0

    if tax_code:
        target_mst = normalize_tax_code(tax_code)
        match_score = 1.0
    elif resolved_name:
        search_result = find_mst_by_name_search(resolved_name)
        if search_result:
            target_mst = search_result["mst"]
            match_score = search_result["confidence"]

    # --- Bước 4: build feature dict ---
    features = {
        "company_name_source":  name_source,
        "company_found":        1 if target_mst else 0,
        "company_match_score":  match_score,
        "company_is_branch":    is_branch,
        "company_active":       0,
        "company_closed":       0,
        "company_unknown":      1,
        "company_age_months":   0,
    }

    if not target_mst:
        return features

    # --- Bước 5: crawl chi tiết công ty ---
    details = get_real_company_details(target_mst)
    status = details["status"].lower()

    if "đang hoạt động" in status:
        features["company_active"] = 1
        features["company_unknown"] = 0
    elif "ngừng hoạt động" in status:
        features["company_closed"] = 1
        features["company_unknown"] = 0

    age = (now.year - details["founded_year"]) * 12 + (now.month - details["founded_month"])
    features["company_age_months"] = max(age, 0)

    return features


# =========================
# REPUTATION (DL version)
# =========================

reputation_cache = {}

def analyze_company_reputation(
    company_name: str | None = None,
    text: str | None = None
):
    """
    Phân tích dư luận về công ty dùng BERT sentiment analysis.

    Sử dụng:
    --------
    - Luồng TRAIN (từ CSV):
        analyze_company_reputation(company_name=row['Name Company'])

    - Luồng RUNTIME (từ mô tả người dùng gửi lên):
        analyze_company_reputation(text=job_description)

    - Kết hợp:
        analyze_company_reputation(company_name=name, text=description)

    Trả về:
    -------
    dict với các features:
        dl_rep_score      : điểm tổng hợp (0.0–1.0)
        dl_rep_avg        : điểm risk trung bình
        dl_rep_max        : điểm risk cao nhất
        dl_rep_high_ratio : tỷ lệ kết quả có điểm > 0.7
    """
    # Resolve tên công ty
    resolved_name, _ = _resolve_company_name(company_name, text)

    empty_result = {
        "dl_rep_score": 0.0,
        "dl_rep_avg": 0.0,
        "dl_rep_max": 0.0,
        "dl_rep_high_ratio": 0.0
    }

    if not resolved_name:
        return empty_result

    clean_name = normalize_text(resolved_name)

    cached = get_cache(reputation_cache, clean_name)
    if cached:
        return cached

    query = f'"{resolved_name}" (lừa đảo OR phốt OR review OR quỵt lương) -tuyển dụng -jobs'

    risk_scores = []

    try:
        time.sleep(random.uniform(0.5, 1.2))

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=10))

            for res in results:
                text_content = f"{res.get('title', '')}. {res.get('body', '')}"
                chunks = split_text(text_content)[:3]

                if chunks and any(c.strip() for c in chunks):
                    scores = batch_ml_risk_score(chunks)
                    if scores:
                        risk_scores.append(max(scores))

    except Exception as e:
        logger.error(f"[Reputation Error] {resolved_name}: {e}")

    if not risk_scores:
        set_cache(reputation_cache, clean_name, empty_result)
        return empty_result

    doc_count = len(risk_scores)
    avg = sum(risk_scores) / doc_count
    max_r = max(risk_scores)
    high_ratio = sum(1 for x in risk_scores if x > 0.7) / doc_count
    final = avg * 0.5 + max_r * 0.3 + high_ratio * 0.2

    result = {
        "dl_rep_score": round(final, 3),
        "dl_rep_avg": round(avg, 3),
        "dl_rep_max": round(max_r, 3),
        "dl_rep_high_ratio": round(high_ratio, 3)
    }

    set_cache(reputation_cache, clean_name, result)
    return result