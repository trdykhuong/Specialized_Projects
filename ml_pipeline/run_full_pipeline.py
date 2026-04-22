#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MASTER PIPELINE - Chạy toàn bộ quy trình từ đầu đến cuối
"""

import os
import sys
import time
from datetime import datetime

def print_header(text):
    """In header đẹp"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80 + "\n")

def print_step(step_num, total_steps, description):
    """In bước hiện tại"""
    print(f"\n{'─'*80}")
    print(f"BƯỚC {step_num}/{total_steps}: {description}")
    print(f"{'─'*80}\n")

def run_script(script_name, description):
    """Chạy một script Python"""
    print(f"▶ Đang chạy {script_name}...")
    start_time = time.time()
    
    # Chạy script
    exit_code = os.system(f"python {script_name}")
    
    elapsed = time.time() - start_time
    
    if exit_code == 0:
        print(f"✓ Hoàn thành trong {elapsed:.1f}s")
        return True
    else:
        print(f"✗ Lỗi khi chạy {script_name}")
        return False

def check_file_exists(filepath):
    """Kiểm tra file có tồn tại không"""
    exists = os.path.exists(filepath)
    status = "✓" if exists else "✗"
    print(f"  {status} {filepath}")
    return exists

def main():
    """Chạy toàn bộ pipeline"""
    
    print_header("HỆ THỐNG PHÂN LOẠI TIN TUYỂN DỤNG - FULL PIPELINE")
    
    print(f"Thời gian bắt đầu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    total_start = time.time()
    
    # ========================================================================
    # BƯỚC 1: Kiểm tra prerequisites
    # ========================================================================
    print_step(1, 6, "Kiểm tra prerequisites")
    
    print("Kiểm tra input files:")
    if not check_file_exists("../data/JOB_DATA_FINAL.csv"):
        print("\n⚠ Thiếu file data/JOB_DATA_FINAL.csv!")
        print("Vui lòng chuẩn bị file dữ liệu gốc.")
        return
    
    print("\nKiểm tra scripts:")
    scripts = [
        "src/1_preprocessing.py",
        "src/advanced_features.py", 
        "src/improved_labeling.py",
        "src/ensemble_training.py"
    ]
    
    for script in scripts:
        if not check_file_exists(script):
            print(f"\n⚠ Thiếu script {script}!")
            return
    
    print("\n✓ Tất cả prerequisites đã sẵn sàng!")
    
    # ========================================================================
    # BƯỚC 2: Preprocessing
    # ========================================================================
    print_step(2, 6, "Preprocessing - Làm sạch và tách từ")
    
    if not run_script("src/1_preprocessing.py", "Preprocessing"):
        print("\n✗ Pipeline dừng do lỗi ở bước preprocessing")
        return
    
    # Kiểm tra output
    print("\nKiểm tra output:")
    if not check_file_exists("../data/JOB_DATA_PREPROCESSED.csv"):
        print("✗ Không tìm thấy output file!")
        return
    
    # ========================================================================
    # BƯỚC 3: Advanced Feature Extraction
    # ========================================================================
    print_step(3, 6, "Feature Engineering - Trích xuất 30+ features")
    
    if not run_script("src/advanced_features.py", "Feature extraction"):
        print("\n✗ Pipeline dừng do lỗi ở bước feature extraction")
        return
    
    # Kiểm tra output
    print("\nKiểm tra output:")
    if not check_file_exists("../data/JOB_DATA_ENHANCED_FEATURES.csv"):
        print("✗ Không tìm thấy output file!")
        return
    
    # ========================================================================
    # BƯỚC 4: Improved Labeling
    # ========================================================================
    print_step(4, 6, "Labeling - Multi-method ensemble với confidence scoring")
    
    if not run_script("src/improved_labeling.py", "Labeling"):
        print("\n✗ Pipeline dừng do lỗi ở bước labeling")
        return
    
    # Kiểm tra outputs
    print("\nKiểm tra outputs:")
    outputs = [
        "../data/JOB_DATA_IMPROVED_LABELS.csv",
        "../data/JOB_DATA_HIGH_CONFIDENCE.csv"
    ]
    
    for output in outputs:
        if not check_file_exists(output):
            print(f"✗ Không tìm thấy {output}!")
            return
    
    # ========================================================================
    # BƯỚC 5: Train Ensemble Models
    # ========================================================================
    print_step(5, 6, "Training - Ensemble models với cross-validation")
    
    if not run_script("src/ensemble_training.py", "Model training"):
        print("\n✗ Pipeline dừng do lỗi ở bước training")
        return
    
    # Kiểm tra outputs
    print("\nKiểm tra outputs:")
    model_files = [
        "../models/best_model.pkl",
        "../models/voting_ensemble.pkl",
        "../models/tfidf_vectorizer.pkl",
        "../models/scaler.pkl",
        "model_comparison.png"
    ]
    
    for model_file in model_files:
        if not check_file_exists(model_file):
            print(f"⚠ Không tìm thấy {model_file}")
    
    # ========================================================================
    # BƯỚC 6: Tổng kết
    # ========================================================================
    print_step(6, 6, "Hoàn thành!")
    
    total_elapsed = time.time() - total_start
    
    print(f"✓ Pipeline hoàn thành trong {total_elapsed/60:.1f} phút")
    print(f"✓ Thời gian kết thúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "="*80)
    print("KẾT QUẢ")
    print("="*80)
    
    print("\nData files được tạo:")
    data_files = [
        "../data/JOB_DATA_PREPROCESSED.csv",
        "../data/JOB_DATA_ENHANCED_FEATURES.csv",
        "../data/JOB_DATA_IMPROVED_LABELS.csv",
        "../data/JOB_DATA_HIGH_CONFIDENCE.csv"
    ]
    
    for df in data_files:
        if os.path.exists(df):
            size = os.path.getsize(df) / 1024 / 1024  # MB
            print(f"  ✓ {df} ({size:.2f} MB)")
    
    print("\nModel files được tạo:")
    for mf in model_files:
        if os.path.exists(mf):
            if mf.endswith('.pkl'):
                size = os.path.getsize(mf) / 1024 / 1024  # MB
                print(f"  ✓ {mf} ({size:.2f} MB)")
            else:
                print(f"  ✓ {mf}")
    
    print("\n" + "="*80)
    print("BƯỚC TIẾP THEO")
    print("="*80)
    print("""
1. Xem kết quả trong file: model_comparison.png
2. Review các metrics trong console output
3. (Optional) Start API server: python api_demo.py
4. (Optional) Test API với curl hoặc Postman
    """)
    
    print("\n🎉 Chúc mừng! Hệ thống đã sẵn sàng sử dụng!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Pipeline bị ngắt bởi người dùng")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Lỗi không mong muốn: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
