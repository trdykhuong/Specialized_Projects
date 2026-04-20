"""
ml_pipeline/src/enrich_company_features.py
-------------------------------------------
Script chạy OFFLINE để bổ sung company features vào tập dữ liệu train.

"""

import os
import sys
import time
import json
import argparse
import random
import re
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, BASE_DIR)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    from backend.core.company_lookup import (
        process_company_features,
        analyze_company_reputation,
    )
except Exception:
    process_company_features = None
    analyze_company_reputation = None

# =========================
# ARGS
# =========================

parser = argparse.ArgumentParser()
parser.add_argument("--use-dl",  action="store_true",
                    help="Dùng BERT (company_loolup_DL) cho reputation analysis")
parser.add_argument("--input",   default="data/JOB_DATA_ENHANCED_FEATURES.csv")
parser.add_argument("--output",  default="data/JOB_DATA_WITH_COMPANY.csv")
parser.add_argument("--workers", type=int, default=3,
                    help="Số luồng song song (mặc định: 3). Tối đa nên để 5 để tránh bị ban IP")
parser.add_argument("--delay",   type=float, default=0.3,
                    help="Delay ngẫu nhiên tối đa giữa các request trong mỗi luồng (giây)")
parser.add_argument("--resume",  action="store_true",
                    help="Tiếp tục từ checkpoint nếu pipeline bị ngắt trước đó")
args = parser.parse_args()

if args.use_dl:
    try:
        from backend.core.company_loolup_DL import (
            analyze_company_reputation as analyze_company_reputation_dl,
        )
    except Exception:
        analyze_company_reputation_dl = None
else:
    analyze_company_reputation_dl = None

# =========================
# PATHS
# =========================

input_path      = os.path.join(BASE_DIR, args.input)
output_path     = os.path.join(BASE_DIR, args.output)
checkpoint_path = output_path.replace(".csv", "_checkpoint.json")

os.makedirs(os.path.dirname(output_path), exist_ok=True)

# =========================
# LOAD DATA
# =========================

print(f"[INFO] Đọc dữ liệu: {input_path}")

# Detect encoding để tránh tên công ty bị cắt do đọc sai encoding
try:
    import chardet
    with open(input_path, 'rb') as f:
        detected = chardet.detect(f.read(100_000))
    encoding = detected.get('encoding') or 'utf-8'
    # chardet đôi khi trả về 'windows-1252' hay 'ISO-8859-1' cho file Excel export
    # utf-8-sig xử lý được cả BOM
    if encoding.lower() in ('ascii', 'iso-8859-1'):
        encoding = 'utf-8-sig'
except ImportError:
    encoding = 'utf-8-sig'   # fallback an toàn nhất

print(f"[INFO] Encoding detected: {encoding}")
df = pd.read_csv(input_path, encoding=encoding)
total_rows = len(df)
print(f"[INFO] Tổng số dòng: {total_rows}")

has_name_col = "Name Company" in df.columns
if has_name_col:
    print(f"[INFO] Cột 'Name Company': {df['Name Company'].notna().sum()} giá trị hợp lệ")
else:
    print("[WARN] Không có cột 'Name Company' — sẽ extract từ text")

# =========================
# DEDUP: chỉ xử lý mỗi tên công ty 1 lần
# =========================

_KEY_ABBREV = {
    r'\bctcp\b': 'công ty cổ phần',
    r'\bcty\b':  'công ty',
    r'\bcp\b':   'cổ phần',
    r'\btnhh\b': 'trách nhiệm hữu hạn',
    r'\btm\b':   'thương mại',
    r'\bdv\b':   'dịch vụ',
    r'\bxnk\b':  'xuất nhập khẩu',
    r'\btmcp\b': 'thương mại cổ phần',
}

def _normalize_key(name: str) -> str:
    """
    Chuẩn hoá tên công ty để làm cache key.
    Đảm bảo các biến thể viết tắt của cùng một công ty map về cùng một key.

    VD: "Cty CP ISOFH", "CTCP ISOFH", "Công ty Cổ phần ISOFH"
        → đều ra "công ty cổ phần isofh"
    """
    key = name.lower().strip()
    for pattern, replacement in _KEY_ABBREV.items():
        key = re.sub(pattern, replacement, key)
    key = re.sub(r'\s+', ' ', key).strip()
    return key


def get_company_key(row) -> str:
    """Trả về tên công ty đã chuẩn hoá để làm cache key."""
    name = str(row.get("Name Company", "")).strip() if has_name_col else ""
    if name in ("", "nan", "None"):
        desc = str(row.get("Job Description", ""))[:80]
        return f"__text__{desc}"
    return _normalize_key(name)

unique_keys = {}   # key → (company_name, full_text)
row_to_key  = []   # index dòng → key

for idx, row in df.iterrows():
    key = get_company_key(row)
    row_to_key.append(key)

    if key not in unique_keys:
        company_name = str(row.get("Name Company", "")).strip() if has_name_col else None
        if company_name in ("", "nan", "None"):
            company_name = None

        text_parts = [
            str(row.get("Job Description", "")),
            str(row.get("Company Overview", "")),
        ]
        full_text = " ".join(p for p in text_parts if p not in ("", "nan", "None"))
        unique_keys[key] = (company_name, full_text)

print(f"[INFO] Số công ty duy nhất: {len(unique_keys)} / {total_rows} dòng")
print(f"[INFO] Tiết kiệm: {total_rows - len(unique_keys)} lần gọi API nhờ dedup")

# =========================
# CHECKPOINT: resume nếu bị ngắt
# =========================

results_cache: dict = {}

if args.resume and os.path.exists(checkpoint_path):
    with open(checkpoint_path, "r", encoding="utf-8") as f:
        results_cache = json.load(f)
    print(f"[RESUME] Đã load {len(results_cache)} công ty từ checkpoint")

keys_todo = [k for k in unique_keys if k not in results_cache]
print(f"[INFO] Còn {len(keys_todo)} công ty chưa xử lý")

# =========================
# WORKER FUNCTION
# =========================

print_lock = Lock()
done_count = [0]

def process_one(key: str) -> tuple:
    company_name, full_text = unique_keys[key]

    # Jitter để các luồng không đồng loạt hit server
    time.sleep(random.uniform(0.1, args.delay))

    if process_company_features is None or analyze_company_reputation is None:
        merged = {
            "company_name_is_direct": 1 if company_name else 0,
            "company_found": 0,
            "company_verified": 0,
            "company_active": 0,
            "company_closed": 0,
            "company_unknown": 1,
            "company_age_months": 0,
            "company_match_score": 0,
            "company_is_branch": 0,
            "company_name_source": "Khong co",
            "reputation_found": 0,
            "reputation_negative_hits": 0,
            "reputation_avg_risk": 0,
            "reputation_max_risk": 0,
            "reputation_score": 0,
        }
    else:
        cf  = process_company_features(company_name=company_name, text=full_text)
        rep = analyze_company_reputation(company_name=company_name, text=full_text)
        merged = {**cf, **rep}

    if args.use_dl and analyze_company_reputation_dl is not None:
        rep_dl = analyze_company_reputation_dl(company_name=company_name, text=full_text)
        merged.update({k: v for k, v in rep_dl.items() if k.startswith("dl_")})

    with print_lock:
        done_count[0] += 1
        pct    = done_count[0] / len(keys_todo) * 100
        found  = merged.get("company_found", 0)
        source = merged.get("company_name_source", "?")
        print(f"  [{done_count[0]:4d}/{len(keys_todo)}] {pct:5.1f}%  "
              f"source={source}  found={found}  {key[:50]}")

    return key, merged

# =========================
# CONCURRENT PROCESSING
# =========================

def _save_checkpoint():
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(results_cache, f, ensure_ascii=False)
    print(f"  [CHECKPOINT] Đã lưu {len(results_cache)} / {len(keys_todo)} kết quả")
    print(f"  Chạy lại với --resume để tiếp tục từ chỗ này.")

if keys_todo:
    print(f"\n[START] Xử lý {len(keys_todo)} công ty với {args.workers} luồng song song...\n")

    checkpoint_interval = max(10, len(keys_todo) // 20)

    executor = ThreadPoolExecutor(max_workers=args.workers)
    futures = {executor.submit(process_one, key): key for key in keys_todo}

    try:
        for i, future in enumerate(as_completed(futures), 1):
            try:
                key, features = future.result()
                results_cache[key] = features
            except Exception as e:
                key = futures[future]
                print(f"[ERROR] {key[:50]}: {e}")
                results_cache[key] = {}

            if i % checkpoint_interval == 0:
                _save_checkpoint()

    except KeyboardInterrupt:
        print("\n\n⚠  Bị ngắt bởi người dùng — đang dừng các luồng...")
        # cancel_futures=True: huỷ các task chưa bắt đầu, không chờ task đang chạy
        executor.shutdown(wait=False, cancel_futures=True)
        _save_checkpoint()
        print("Để tiếp tục: python enrich_company_features.py --resume")
        sys.exit(0)
    else:
        executor.shutdown(wait=True)

    # Hoàn tất bình thường — lưu checkpoint cuối
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(results_cache, f, ensure_ascii=False)

else:
    print("[INFO] Tất cả công ty đã có trong cache, bỏ qua bước gọi API")

# Nếu checkpoint đã có đủ kết quả (chạy xong 100% nhưng bị crash sau đó)
# → load lại từ checkpoint và tiếp tục merge & save bình thường
if os.path.exists(checkpoint_path) and not keys_todo:
    pass   # results_cache đã được load từ checkpoint ở trên

# =========================
# MAP KẾT QUẢ VỀ TỪNG DÒNG
# =========================

print("\n[INFO] Ghép kết quả vào từng dòng...")

enriched_rows = []
for idx in range(total_rows):
    key      = row_to_key[idx]
    features = dict(results_cache.get(key, {}))
    enriched_rows.append(features)

enriched_df = pd.DataFrame(enriched_rows)

if "company_name_source" in enriched_df.columns:
    enriched_df["company_name_is_direct"] = (
        enriched_df["company_name_source"] == "direct"
    ).astype(int)
    enriched_df = enriched_df.drop(columns=["company_name_source"])

# =========================
# SAVE
# =========================

df_out = pd.concat([df.reset_index(drop=True), enriched_df.reset_index(drop=True)], axis=1)
df_out.to_csv(output_path, index=False, encoding="utf-8-sig")

if os.path.exists(checkpoint_path):
    os.remove(checkpoint_path)

# =========================
# SUMMARY
# =========================

print("\n" + "=" * 60)
print("HOÀN TẤT")
print("=" * 60)
print(f"Output : {output_path}")
print(f"Số dòng: {len(df_out)}")
if "company_found" in enriched_df.columns:
    found = enriched_df["company_found"].sum()
    print(f"\nThống kê:")
    print(f"  Công ty tìm được    : {found} / {total_rows} ({found/total_rows*100:.1f}%)")
if "company_active" in enriched_df.columns:
    print(f"  Đang hoạt động      : {enriched_df['company_active'].sum()}")
if "company_closed" in enriched_df.columns:
    print(f"  Ngừng hoạt động     : {enriched_df['company_closed'].sum()}")
if "company_name_is_direct" in enriched_df.columns:
    print(f"  Tên từ cột trực tiếp: {enriched_df['company_name_is_direct'].sum()}")
