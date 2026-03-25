#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script kiểm tra các rules mới liên quan đến Career Level, Years of Experience, Job Type
"""

import pandas as pd
import sys

def display_career_rules_examples():
    """Hiển thị ví dụ về các rules mới"""
    
    print("="*80)
    print("CÁC RULES MỚI ĐỂ PHÁT HIỆN TIN GIẢ DỰA VÀO CAREER LEVEL, JOB TYPE, EXPERIENCE")
    print("="*80)
    
    rules = [
        {
            "rule_num": 11,
            "name": "Part-time + Lương caoĐiểm: +1.5",
            "description": "Part-time job được đề cập có lương > 15M/tháng",
            "example": "Part-time mà lương 20-30 triệu/tháng = nghi ngờ cao"
        },
        {
            "rule_num": 12,
            "name": "Part-time + Vị trí quản lý",
            "points": "+1.5",
            "description": "Job type là Part-time nhưng Career Level là quản lý/manager",
            "example": "Tuyển Part-time cho vị trí Trưởng phòng = không hợp lý"
        },
        {
            "rule_num": 13,
            "name": "Quản lý + Không cần KN",
            "points": "+2.0",
            "description": "Career Level quản lý nhưng không yêu cầu kinh nghiệm",
            "example": "Tuyển Trưởng phòng mà không cần kinh nghiệm = rất nghi ngờ"
        },
        {
            "rule_num": 14,
            "name": "Quản lý + KN < 3 năm",
            "points": "+1.5",
            "description": "Vị trí quản lý nhưng chỉ yêu cầu < 3 năm kinh nghiệm",
            "example": "Tuyển Manager chỉ yêu cầu 1-2 năm = không hợp lý"
        },
        {
            "rule_num": 15,
            "name": "Entry level + Lương cao",
            "points": "+1.5",
            "description": "Entry level position nhưng lương > 20M",
            "example": "Tuyển Fresher mà lương 25-30 triệu = nghi ngờ"
        },
        {
            "rule_num": 16,
            "name": "Entry level + KN cao",
            "points": "+1.0",
            "description": "Entry level nhưng yêu cầu KN >= 5 năm",
            "example": "Tuyển Junior Developer yêu cầu 5+ năm kinh nghiệm = mâu thuẫn"
        },
        {
            "rule_num": 17,
            "name": "Thiếu Career Level",
            "points": "+0.5",
            "description": "Không có thông tin hoặc Career Level không rõ",
            "example": "Job listing không ghi Career Level = thiếu thông tin uy tín"
        },
        {
            "rule_num": 18,
            "name": "Thiếu Job Type",
            "points": "+0.5",
            "description": "Không rõ loại công việc (Full-time, Part-time, Freelance)",
            "example": "Không ghi thông tin loại công việc (Toàn thời gian, Bán thời gian) = không rõ"
        }
    ]
    
    for rule in rules:
        print(f"\n📌 RULE {rule['rule_num']}: {rule['name']}")
        print(f"   Điểm: {rule.get('points', '(see description)')}")
        print(f"   Mô tả: {rule['description']}")
        print(f"   Ví dụ: {rule['example']}")
    
    print("\n" + "="*80)
    print("GHI CHU:")
    print("  - Mâu thuẫn giữa Career Level / Years of Experience / Job Type là dấu hiệu fake")
    print("  - Part-time không nên có yêu cầu quản lý")
    print("  - Quản lý thường cần > 5 năm kinh nghiệm")
    print("  - Entry level không nên có lương cao")
    print("="*80)

def analyze_data_with_new_rules():
    """Phân tích dữ liệu với các rules mới"""
    
    print("\n\n" + "="*80)
    print("PHÂN TÍCH DỮ LIỆU - TÌMCÁC TRƯỜNG HỢP MÂUTATHUẪN")
    print("="*80)
    
    try:
        df = pd.read_csv("data/JOB_DATA_FINAL.csv")
        print(f"\nĐã load {len(df)} job listings\n")
        
        # Phân tích Career Level
        print("📊 PHÂN BỐ CAREER LEVEL:")
        print(df['Career Level'].value_counts().head(10))
        
        # Phân tích Job Type
        print("\n\n📊 PHÂN BỐ JOB TYPE:")
        print(df['Job Type'].value_counts())
        
        # Phân tích Years of Experience
        print("\n\n📊 PHÂN BỐ YEARS OF EXPERIENCE:")
        print(df['Years of Experience'].value_counts().head(10))
        
        # Tìm cases mâu thuẫn
        print("\n\n" + "="*80)
        print("🔍 CÁC TRƯỜNG HỢP MÂUTATHUẪN:")
        print("="*80)
        
        # Case 1: Part-time + Manager level
        pt_manager = df[(df['Job Type'].str.lower().str.contains('part', na=False)) & 
                        (df['Career Level'].str.lower().str.contains('quản lý|manager|lead|director', na=False))]
        print(f"\n1. Part-time + Vị trí quản lý: {len(pt_manager)} cases")
        if len(pt_manager) > 0:
            for idx, row in pt_manager.head(3).iterrows():
                print(f"   - {row['Job Title']} | {row['Job Type']} | {row['Career Level']}")
        
        # Case 2: Manager level + no experience required
        manager_no_exp = df[(df['Career Level'].str.lower().str.contains('quản lý|manager|director|supervisor', na=False)) &
                           (df['Years of Experience'].str.lower().str.contains('không|0', na=False))]
        print(f"\n2. Vị trí quản lý + Không cần kinh nghiệm: {len(manager_no_exp)} cases")
        if len(manager_no_exp) > 0:
            for idx, row in manager_no_exp.head(3).iterrows():
                print(f"   - {row['Job Title']} | {row['Career Level']} | {row['Years of Experience']}")
        
        # Case 3: Entry level + high salary
        entry_high_salary = df[df['Career Level'].str.lower().str.contains('nhân viên|entry|junior|fresher', na=False)]
        print(f"\n3. Entry level positions: {len(entry_high_salary)} cases")
        print(f"   Trung bình mức lương: {entry_high_salary['Salary'].head()}")
        
        # Case 4: Jobs missing Career Level or Job Type
        missing_career = df[df['Career Level'].isna() | (df['Career Level'].str.strip() == '')]
        missing_job_type = df[df['Job Type'].isna() | (df['Job Type'].str.strip() == '')]
        
        print(f"\n4. Thiếu Career Level: {len(missing_career)} cases")
        print(f"5. Thiếu Job Type: {len(missing_job_type)} cases")
        
    except Exception as e:
        print(f"❌ Lỗi khi đọc dữ liệu: {e}")
        print("   Chạy pipeline để tạo dữ liệu trước: python run_full_pipeline.py")

if __name__ == "__main__":
    display_career_rules_examples()
    analyze_data_with_new_rules()
    
    print("\n\n✅ Để chạy full pipeline với các rules mới:")
    print("   python run_full_pipeline.py")
