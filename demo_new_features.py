#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Demo - Hiển thị cách các features mới hoạt động
"""

import pandas as pd
import sys
sys.path.insert(0, '.')

from ml_pipeline.src.advanced_features import AdvancedFeatureExtractor
from ml_pipeline.src.improved_labeling import ImprovedLabeling

def demo_feature_extraction():
    """Demo feature extraction với các features mới"""
    print("\n" + "="*80)
    print("DEMO 1: FEATURE EXTRACTION - CÁC FEATURES MỚI")
    print("="*80)
    
    extractor = AdvancedFeatureExtractor()
    
    # Ví dụ 1: Part-time + Lương cao + Entry level
    fake_example_1 = {
        'FULL_TEXT': 'Sale mua bán hàng trực tuyến',
        'Salary': '20,000,000 - 30,000,000',
        'Company Size': '5-10',
        'Company Overview': 'Công ty nhỏ',
        'Job Description': 'Bán hàng online',
        'Job Requirements': 'Có máy tính',
        'Years of Experience': 'Không yêu cầu',
        'Number Cadidate': 50,
        'Benefits': 'Hoa hồng cao',
        'Job Type': 'Part time',
        'Career Level': 'Nhân viên'
    }
    
    # Ví dụ 2: Quản lý + Không cần KN
    fake_example_2 = {
        'FULL_TEXT': 'Quản lý dự án',
        'Salary': '30,000,000 - 40,000,000',
        'Company Size': '10-50',
        'Company Overview': 'Công ty cấp 2',
        'Job Description': 'Quản lý nhân sự',
        'Job Requirements': 'Kỹ năng quản lý tốt',
        'Years of Experience': 'Không yêu cầu',
        'Number Cadidate': 1,
        'Benefits': 'Thưởng, du lịch',
        'Job Type': 'Full time',
        'Career Level': 'Trưởng phòng'
    }
    
    # Ví dụ 3: Hợp lệ - Full-time + Manager + Kinh nghiệm cao
    real_example = {
        'FULL_TEXT': 'Senior Manager tuyển dụng',
        'Salary': '50,000,000 - 70,000,000',
        'Company Size': '100-499',
        'Company Overview': 'Công ty lớn chuyên nghiệp',
        'Job Description': 'Quản lý cấp cao',
        'Job Requirements': 'MBA, 10+ năm KN',
        'Years of Experience': '5-10 năm',
        'Number Cadidate': 1,
        'Benefits': 'Bảo hiểm y tế, du lịch, công ty xe',
        'Job Type': 'Full time',
        'Career Level': 'Trưởng phòng'
    }
    
    examples = [
        ("FAKE #1: Part-time + Lương cao + Entry level", fake_example_1),
        ("FAKE #2: Quản lý + Không cần kinh nghiệm", fake_example_2),
        ("REAL: Full-time Manager + Kinh nghiệm cao", real_example)
    ]
    
    for title, example in examples:
        print(f"\n\n{'─'*80}")
        print(f"📋 {title}")
        print(f"{'─'*80}")
        
        features = extractor.extract_all_features(example)
        
        # Hiển thị các features liên quan
        print(f"\nCareer Level & Job Type Features:")
        print(f"  • is_management_level: {features.get('is_management_level', 0)}")
        print(f"  • is_entry_level: {features.get('is_entry_level', 0)}")
        print(f"  • is_part_time: {features.get('is_part_time', 0)}")
        print(f"  • is_full_time: {features.get('is_full_time', 0)}")
        print(f"  • is_freelance: {features.get('is_freelance', 0)}")
        
        print(f"\nOther Important Features:")
        print(f"  • experience_years: {features.get('experience_years', 0)}")
        print(f"  • salary_avg: {features.get('salary_avg', 0):,.0f}")
        print(f"  • salary_suspiciously_high: {features.get('salary_suspiciously_high', 0)}")
        print(f"  • no_experience_required: {features.get('no_experience_required', 0)}")

def demo_scoring():
    """Demo scoring với các rules mới"""
    print("\n\n" + "="*80)
    print("DEMO 2: SCORING - TÍNH ĐIỂM THỂ HIỆN MỨC ĐỘ GIẢ")
    print("="*80)
    
    labeler = ImprovedLabeling()
    extractor = AdvancedFeatureExtractor()
    
    # Các ví dụ
    examples = [
        {
            "name": "CASE 1: Part-time + Lương cao (20M) + Entry level",
            "data": {
                'FULL_TEXT': 'Sale làm việc online',
                'Salary': '20,000,000',
                'Company Size': '5',
                'Company Overview': 'Công ty nhỏ',
                'Job Description': 'Bán hàng',
                'Job Requirements': 'Không yêu cầu',
                'Years of Experience': 'Không yêu cầu',
                'Number Cadidate': 50,
                'Benefits': 'Hoa hồng',
                'Job Type': 'Part time',
                'Career Level': 'Nhân viên'
            }
        },
        {
            "name": "CASE 2: Quản lý + Không cần kinh nghiệm",
            "data": {
                'FULL_TEXT': 'Quản lý dự án',
                'Salary': '30,000,000',
                'Company Size': '10',
                'Company Overview': 'Công ty nhỏ',
                'Job Description': 'Quản lý',
                'Job Requirements': 'Không yêu cầu',
                'Years of Experience': 'Không yêu cầu',
                'Number Cadidate': 1,
                'Benefits': 'Thưởng',
                'Job Type': 'Full time',
                'Career Level': 'Trưởng phòng'
            }
        },
        {
            "name": "CASE 3: Full-time Manager + 5-10 năm KN + Lương cao",
            "data": {
                'FULL_TEXT': 'Senior Manager dự án',
                'Salary': '50,000,000',
                'Company Size': '200',
                'Company Overview': 'Công ty lớn uy tín',
                'Job Description': 'Quản lý cấp cao',
                'Job Requirements': 'MBA, 10+ năm',
                'Years of Experience': '5-10 năm',
                'Number Cadidate': 1,
                'Benefits': 'Đầy đủ',
                'Job Type': 'Full time',
                'Career Level': 'Trưởng phòng'
            }
        }
    ]
    
    for example in examples:
        print(f"\n\n{'─'*80}")
        print(f"📋 {example['name']}")
        print(f"{'─'*80}")
        
        # Extract features
        features = extractor.extract_all_features(example['data'])
        
        # Calculate scoring
        score, reasons = labeler.rule_based_score(features)
        
        print(f"\n🎲 ĐIỂM NGHI NGỜ: {score:.1f}/10.0")
        
        if score < 4:
            print(f"   ✅ REAL (Có vẻ hợp lý)")
        elif score < 6:
            print(f"   ⚠️  UNCERTAIN (Cần xem xét)")
        else:
            print(f"   ❌ FAKE (Rất nghi ngờ)")
        
        print(f"\nLý do nghi ngờ:")
        if reasons:
            for i, reason in enumerate(reasons, 1):
                print(f"  {i}. {reason}")
        else:
            print(f"  Không có dấu hiệu nghi ngờ")
        
        # Hiển thị features liên quan
        print(f"\nFeatures liên quan đến Career Level / Experience / Job Type:")
        print(f"  • is_management_level: {features.get('is_management_level', 0)}")
        print(f"  • is_entry_level: {features.get('is_entry_level', 0)}")
        print(f"  • is_part_time: {features.get('is_part_time', 0)}")
        print(f"  • experience_years: {features.get('experience_years', 0)}")
        print(f"  • no_experience_required: {features.get('no_experience_required', 0)}")

if __name__ == "__main__":
    print("\n🚀 DEMO: HỆ THỐNG PHÁT HIỆN TIN GIẢ - CÁC FEATURES MỚI")
    print("="*80)
    
    try:
        demo_feature_extraction()
        demo_scoring()
        
        print("\n\n" + "="*80)
        print("✅ DEMO HOÀN THÀNH")
        print("="*80)
        print("\n💡 Bước tiếp theo:")
        print("  1. Chạy full pipeline: python run_full_pipeline.py")
        print("  2. Xem file tóm tắt: CAREER_LEVEL_UPDATES.md")
        print("  3. Kiểm tra chi tiết: test_new_career_rules.py")
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
