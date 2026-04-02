#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TEST EXAMPLES - Ví dụ test API với các trường hợp khác nhau
"""

import requests
import json

# API endpoint
API_URL = "http://localhost:5000"

# ============================================================================
# TEST CASES
# ============================================================================

# Case 1: TIN FAKE RÕ RÀNG
fake_job_1 = {
    "job_title": "Tuyển nhân viên làm việc tại nhà - Lương cao",
    "company_overview": "",
    "job_description": "Công việc nhẹ nhàng, không cần kinh nghiệm. Thu nhập không giới hạn!!!",
    "job_requirements": "Không yêu cầu",
    "benefits": "Lương thưởng cao",
    "salary": "30-100 triệu",
    "company_size": "",
    "years_of_experience": "Không yêu cầu",
    "number_candidates": 50
}

# Case 2: TIN REAL RÕ RÀNG
real_job_1 = {
    "job_title": "Software Engineer - Backend",
    "company_overview": "Công ty công nghệ hàng đầu Việt Nam, chuyên về fintech. Có văn phòng tại TPHCM và Hà Nội với hơn 500 nhân viên.",
    "job_description": """
    Chúng tôi đang tìm kiếm Backend Developer có kinh nghiệm để tham gia phát triển hệ thống thanh toán.
    
    Trách nhiệm:
    - Thiết kế và phát triển API RESTful
    - Tối ưu performance database
    - Code review và mentor junior developers
    - Viết unit tests và integration tests
    """,
    "job_requirements": """
    - Tốt nghiệp Đại học chuyên ngành CNTT hoặc tương đương
    - 3+ năm kinh nghiệm với Python/Django hoặc Java/Spring
    - Thành thạo SQL, NoSQL databases
    - Hiểu biết về microservices architecture
    - Có kinh nghiệm với Docker, Kubernetes là một lợi thế
    """,
    "benefits": """
    - Lương cạnh tranh, thỏa thuận theo năng lực
    - Thưởng hiệu suất 2 lần/năm
    - Bảo hiểm sức khỏe cao cấp
    - 14 ngày nghỉ phép năm
    - Đào tạo và phát triển kỹ năng
    - Du lịch team building hàng năm
    """,
    "salary": "25-35 triệu",
    "company_size": "500-999",
    "years_of_experience": "3-5 năm",
    "number_candidates": 2
}

# Case 3: TIN HƠI NGHI NGỜ (Borderline)
suspicious_job_1 = {
    "job_title": "Cộng tác viên bán hàng online",
    "company_overview": "Công ty thương mại điện tử mới thành lập",
    "job_description": "Bán hàng qua mạng xã hội, làm việc online từ xa. Hoa hồng hấp dẫn!",
    "job_requirements": "Nhiệt tình, năng động",
    "benefits": "Hoa hồng cao",
    "salary": "10-20 triệu",
    "company_size": "10-24",
    "years_of_experience": "Không yêu cầu",
    "number_candidates": 30
}

# Case 4: TIN REAL NHƯNG THIẾU THÔNG TIN
incomplete_job_1 = {
    "job_title": "Marketing Executive",
    "company_overview": "Công ty TNHH ABC, lĩnh vực FMCG",
    "job_description": "Thực hiện các hoạt động marketing, quản lý social media",
    "job_requirements": "Tốt nghiệp Đại học, am hiểu marketing",
    "benefits": "Thỏa thuận",
    "salary": "Thỏa thuận",
    "company_size": "100-499",
    "years_of_experience": "1-2 năm",
    "number_candidates": 1
}

# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_health_check():
    """Test health check endpoint"""
    print("\n" + "="*80)
    print("TEST 1: Health Check")
    print("="*80)
    
    response = requests.get(f"{API_URL}/health")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_single_prediction(job_data, description):
    """Test single prediction"""
    print("\n" + "="*80)
    print(f"TEST: {description}")
    print("="*80)
    
    print(f"\nInput:")
    print(f"  Title: {job_data['job_title']}")
    print(f"  Salary: {job_data['salary']}")
    print(f"  Company Size: {job_data['company_size']}")
    print(f"  Experience: {job_data['years_of_experience']}")
    
    response = requests.post(
        f"{API_URL}/predict",
        json=job_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n{'─'*80}")
        print("KẾT QUẢ DỰ ĐOÁN")
        print(f"{'─'*80}")
        
        print(f"\n🎯 Kết luận: {'REAL ✓' if result['is_real'] else 'FAKE ✗'}")
        print(f"📊 Confidence: {result['confidence']*100:.1f}%")
        print(f"📈 Probability REAL: {result['probability_real']*100:.1f}%")
        print(f"📉 Probability FAKE: {result['probability_fake']*100:.1f}%")
        print(f"⚠️  Risk Level: {result['risk_level']}")
        
        if result['warnings']:
            print(f"\n⚠️  WARNINGS:")
            for warning in result['warnings']:
                print(f"  - {warning}")
        
        print(f"\n📋 Analysis:")
        print(f"  Text Quality: {result['analysis']['text_quality']['professional_level']}")
        print(f"  Text Length: {result['analysis']['text_quality']['length']} words")
        print(f"  Salary Avg: {result['analysis']['salary_info']['average']:,} VND")
        print(f"  Company Size: {result['analysis']['company_info']['size']} người")
        print(f"  Scam Keywords: {result['analysis']['keywords']['scam_count']}")
        print(f"  Positive Keywords: {result['analysis']['keywords']['positive_count']}")
        
        return True
    else:
        print(f"\n✗ Error: {response.text}")
        return False

def test_batch_prediction():
    """Test batch prediction"""
    print("\n" + "="*80)
    print("TEST: Batch Prediction")
    print("="*80)
    
    batch_data = {
        "jobs": [fake_job_1, real_job_1, suspicious_job_1],
        "use_ensemble": False
    }
    
    response = requests.post(
        f"{API_URL}/batch_predict",
        json=batch_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n📊 SUMMARY:")
        print(f"  Total jobs: {result['summary']['total']}")
        print(f"  Real jobs: {result['summary']['real_count']} ✓")
        print(f"  Fake jobs: {result['summary']['fake_count']} ✗")
        print(f"  High risk: {result['summary']['high_risk_count']} ⚠️")
        
        print(f"\n📋 DETAILS:")
        for i, job_result in enumerate(result['results'], 1):
            status = "REAL ✓" if job_result['is_real'] else "FAKE ✗"
            print(f"  Job {i}: {status} (Confidence: {job_result['confidence']*100:.1f}%, Risk: {job_result['risk_level']})")
        
        return True
    else:
        print(f"\n✗ Error: {response.text}")
        return False

def run_all_tests():
    """Chạy tất cả tests"""
    print("\n" + "="*80)
    print("API TESTING - Job Posting Authenticity Checker")
    print("="*80)
    
    print(f"\nAPI URL: {API_URL}")
    print(f"\nĐảm bảo API server đang chạy (python 4_api_demo.py)")
    
    input("\nNhấn Enter để bắt đầu test...")
    
    # Test 1: Health check
    try:
        if not test_health_check():
            print("\n✗ Health check failed! Server có đang chạy không?")
            return
    except Exception as e:
        print(f"\n✗ Không thể kết nối tới server: {e}")
        print("\nVui lòng chạy: python 4_api_demo.py")
        return
    
    # Test 2-5: Single predictions
    test_cases = [
        (fake_job_1, "Tin FAKE rõ ràng"),
        (real_job_1, "Tin REAL uy tín"),
        (suspicious_job_1, "Tin nghi ngờ"),
        (incomplete_job_1, "Tin thiếu thông tin")
    ]
    
    for job_data, description in test_cases:
        test_single_prediction(job_data, description)
        input("\nNhấn Enter để tiếp tục...")
    
    # Test 6: Batch prediction
    test_batch_prediction()
    
    print("\n" + "="*80)
    print("✓ HOÀN THÀNH TẤT CẢ TESTS")
    print("="*80)

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠ Tests bị ngắt bởi người dùng")
    except Exception as e:
        print(f"\n\n✗ Lỗi: {e}")
        import traceback
        traceback.print_exc()
