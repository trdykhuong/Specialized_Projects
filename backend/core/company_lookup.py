import re
import time
import random
from datetime import datetime
from ddgs import DDGS
from thefuzz import fuzz
import requests
from bs4 import BeautifulSoup

# =========================
# CONFIG
# =========================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

HEADERS = {
    "User-Agent": random.choice(USER_AGENTS),
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
    "Connection": "keep-alive"
}

# =========================
# UTILS
# =========================

def normalize_text(text: str) -> str:
    return text.lower().strip()


# Bảng expand viết tắt phổ biến trong tên công ty Việt Nam
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
    """Expand viết tắt thường gặp để tăng độ khớp fuzzy với tên đầy đủ trên masothue."""
    result = name.lower()
    for pattern, replacement in _ABBR_MAP.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def normalize_company_name(name: str) -> str:
    """
    Chuẩn hoá tên công ty trước khi search hoặc so sánh:
    - Loại bỏ \\r\\n ở giữa tên (CSV đôi khi chứa newline ẩn)
    - Xoá nội dung trong ngoặc đơn: "(VPBank)" → ""  tránh DuckDuckGo dùng () làm group operator
    - Strip khoảng trắng dư
    """
    name = re.sub(r'[\r\n]+', ' ', name)        # newline ẩn ở giữa tên
    name = re.sub(r'\s*\(.*?\)\s*', ' ', name)  # nội dung trong ngoặc
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def fuzzy_score(a: str, b: str) -> float:
    """So sánh fuzzy, tự động expand viết tắt của cả hai vế."""
    a = expand_abbreviations(normalize_text(a))
    b = expand_abbreviations(normalize_text(b))
    return max(
        fuzz.token_set_ratio(a, b),
        fuzz.partial_ratio(a, b),
        fuzz.ratio(a, b)
    ) / 100.0


def normalize_tax_code(mst: str) -> str:
    """Lấy MST gốc (10 số)"""
    return mst.split('-')[0] if mst else None


# =========================
# EXTRACT INFO (dùng cho runtime khi không có tên công ty)
# =========================

def extract_company_name_from_text(text: str):
    """
    Trích xuất tên công ty từ mô tả bài đăng (dùng khi người dùng gửi text).
    Chỉ dùng khi KHÔNG có tên công ty rõ ràng (luồng runtime/API).
    """
    # Tiền tố nhận diện — mở rộng thêm ngân hàng, văn phòng đại diện
    PREFIX = (
        r'(?:công ty(?:\s+(?:cổ phần|tnhh|cp|trách nhiệm hữu hạn))?'
        r'|cty(?:\s+cp)?|ctcp|tập đoàn|ngân hàng(?:\s+tmcp)?'
        r'|chi nhánh|văn phòng đại diện)'
    )

    # Boundary dừng — thêm dấu chấm cuối câu và từ "việc làm", "tuyển dụng"
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
    raw = re.sub(r'\s*[:\-–]\s*$', '', raw)   # trailing colon/dash
    raw = re.sub(r'\s*\(.*?\)\s*$', '', raw)  # trailing parentheses
    raw = re.sub(r',\s*$', '', raw)            # trailing comma
    raw = re.sub(r'[\r\n]+', ' ', raw)         # newline ẩn
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
    Trích tên công ty ra khỏi title masothue.
    Format A: "Công ty CP ISOFH - Mã số thuế 0107..."  → lấy phần trước ' - '
    Format B: "0107... - Công ty CP ISOFH"              → lấy phần sau  ' - '
    """
    if ' - ' not in title:
        return title.strip()
    parts = title.split(' - ', 1)
    left, right = parts[0].strip(), parts[1].strip()
    if re.fullmatch(r'[\d\s]+', left):   # phần trái là số MST → tên ở phải
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
    """Mở rộng viết tắt phổ biến để tăng khả năng match với masothue."""
    result = name.lower()
    for pattern, replacement in _ABBREV_MAP.items():
        result = re.sub(pattern, replacement, result)
    return result


def _extract_unique_keyword(company_name: str) -> str:
    """
    Trích từ khoá đặc trưng của công ty (bỏ các tiền tố chung).
    Dùng làm fallback query khi search với tên đầy đủ không ra kết quả.

    VD: "công ty tnhh tm xnk nguồn sống việt" → "nguồn sống việt"
        "công ty tnhh phần mềm acazia"         → "acazia"
        "công ty cổ phần đầu tư dv tm agv v"   → "agv"  (xử lý cả tên bị cắt)
    """
    name = company_name.strip().lower()
    name = re.sub(r'\(.*?\)', '', name).strip()    # bỏ ngoặc đơn VD: (vpbank)

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
    # Bỏ ký tự đơn lẻ ở cuối — artifact của tên bị cắt ở byte boundary
    keyword = re.sub(r'\s+\b[a-zA-ZÀ-ỹ]\b$', '', keyword).strip()
    return keyword


def find_mst_by_name_search(company_name: str):
    """
    Tìm MST trên masothue.com theo tên công ty.
    Chiến lược 3 bước (ưu tiên giảm dần):
      1. Tên đã expand viết tắt → query đầy đủ nhất
      2. Unique keyword          → fallback khi tên quá dài/bị cắt/viết tắt lạ
      3. Bỏ site: filter         → fallback cuối nếu DuckDuckGo không index được
    """
    expanded = _expand_abbreviations(company_name)
    keyword  = _extract_unique_keyword(company_name)

    queries = [expanded]
    if keyword and keyword != expanded:
        queries.append(keyword)

    for query_term in queries:
        # Bỏ ngoặc đơn khỏi query — DuckDuckGo hiểu "(vpbank)" là group
        clean_q = re.sub(r'\(.*?\)', '', query_term).strip()

        result = _search_masothue(f'site:masothue.com {clean_q}', company_name)
        if result:
            return result

        # Fallback: bỏ site: nếu DuckDuckGo không có kết quả
        result = _search_masothue(f'masothue.com {clean_q}', company_name)
        if result:
            return result

    return None


def _search_masothue(query: str, original_name: str):
    """Thực hiện một lần search DuckDuckGo và trả về best match."""
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
        print(f"[Search Error] '{query}': {e}")
        return None


# =========================
# CRAWL DATA (WITH CACHE)
# =========================

cache = {}

def get_real_company_details(mst: str):
    if mst in cache:
        return cache[mst]

    result = {
        "status": "Không rõ",
        "founded_year": datetime.now().year,
        "founded_month": datetime.now().month,
        "verified": 0
    }

    url = f"https://masothue.com/Search/?q={mst}"

    try:
        time.sleep(random.uniform(0.5, 1.5))

        response = requests.get(url, headers=HEADERS, timeout=10)

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
        print(f"[Crawl Error] MST {mst}: {e}")

    cache[mst] = result
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
        company_extracted    : 1 nếu có tên hoặc MST
        company_found        : 1 nếu tìm được MST trên masothue.com
        company_verified     : 1 nếu crawl thành công
        company_active       : 1 nếu đang hoạt động
        company_closed       : 1 nếu đã ngừng hoạt động
        company_unknown      : 1 nếu không rõ trạng thái
        company_age_months   : số tháng tuổi của công ty
        company_match_score  : độ tin cậy khi match tên → MST (0.0–1.0)
        company_is_branch    : 1 nếu là chi nhánh (MST có dấu -)
    """
    now = datetime.now()

    # --- Bước 1: xác định tên công ty ---
    resolved_name, name_source = _resolve_company_name(company_name, text)

    # --- Bước 2: tìm tax code ---
    # Ưu tiên extract MST từ text (nếu có), vì MST cho kết quả chính xác nhất
    tax_code = None
    if text:
        tax_code = extract_tax_code(text)

    # --- Bước 3: resolve MST ---
    target_mst = None
    match_score = 0.0
    is_branch = 1 if tax_code and '-' in tax_code else 0

    if tax_code:
        # Có MST trực tiếp trong text → dùng luôn, độ tin cậy tuyệt đối
        target_mst = normalize_tax_code(tax_code)
        match_score = 1.0
    elif resolved_name:
        # Không có MST → search theo tên công ty
        search_result = find_mst_by_name_search(resolved_name)
        if search_result:
            target_mst = search_result["mst"]
            match_score = search_result["confidence"]

    # --- Bước 4: build feature dict ---
    features = {
        "company_name_source":  name_source,
        "company_extracted":    1 if (resolved_name or tax_code) else 0,
        "company_found":        1 if target_mst else 0,
        "company_verified":     0,
        "company_active":       0,
        "company_closed":       0,
        "company_unknown":      1,
        "company_age_months":   0,
        "company_match_score":  match_score,
        "company_is_branch":    is_branch,
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

    features["company_verified"] = details["verified"]

    age_months = (now.year - details["founded_year"]) * 12 + (now.month - details["founded_month"])
    features["company_age_months"] = max(age_months, 0)

    return features


# =========================
# REPUTATION ANALYSIS
# =========================

reputation_cache = {}

SEVERE_KEYWORDS = ['lừa đảo', 'chiếm đoạt', 'công an', 'tố cáo', 'đường dây']
WARNING_KEYWORDS = ['phốt', 'quỵt lương', 'nợ lương', 'đa cấp', 'bắt đóng cọc', 'bóc lột', 'tránh xa']


def keyword_risk_score(text: str) -> float:
    """Tính điểm risk dựa trên keyword"""
    score = 0.0
    for word in SEVERE_KEYWORDS:
        if word in text:
            score += 2.0
    for word in WARNING_KEYWORDS:
        if word in text:
            score += 1.0
    return score


def analyze_company_reputation(
    company_name: str | None = None,
    text: str | None = None
):
    """
    Phân tích dư luận về công ty dựa trên keyword.

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
        reputation_found          : 1 nếu tìm được kết quả
        reputation_negative_hits  : số kết quả có dấu hiệu tiêu cực
        reputation_avg_risk       : điểm risk trung bình
        reputation_max_risk       : điểm risk cao nhất
        reputation_score          : điểm tổng hợp (0.0–1.0)
    """
    # Resolve tên công ty
    resolved_name, _ = _resolve_company_name(company_name, text)

    empty_result = {
        "reputation_found": 0,
        "reputation_negative_hits": 0,
        "reputation_avg_risk": 0.0,
        "reputation_max_risk": 0.0,
        "reputation_score": 0.0
    }

    if not resolved_name:
        return empty_result

    clean_name = normalize_text(resolved_name)

    if clean_name in reputation_cache:
        return reputation_cache[clean_name]

    query = f'"{resolved_name}" lừa đảo OR phốt OR quỵt lương OR đa cấp'

    risk_scores = []
    negative_hits = 0

    try:
        time.sleep(random.uniform(0.5, 1.0))

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=10))

            for res in results:
                text_content = normalize_text(
                    res.get('title', '') + " " + res.get('body', '')
                )
                score = keyword_risk_score(text_content)
                if score > 0:
                    negative_hits += 1
                risk_scores.append(score)

    except Exception as e:
        print(f"[Reputation Error] {resolved_name}: {e}")

    if not risk_scores:
        reputation_cache[clean_name] = empty_result
        return empty_result

    avg_risk = sum(risk_scores) / len(risk_scores)
    max_risk = max(risk_scores)
    final_score = min((avg_risk + max_risk) / 6.0, 1.0)

    features = {
        "reputation_found": 1,
        "reputation_negative_hits": negative_hits,
        "reputation_avg_risk": round(avg_risk, 2),
        "reputation_max_risk": round(max_risk, 2),
        "reputation_score": round(final_score, 2)
    }

    reputation_cache[clean_name] = features
    return features