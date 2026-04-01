
import requests
import json

API_URL = "http://localhost:5000"

# Test 1: Health check
print("\n" + "="*80)
print("TEST 1: Health Check")
print("="*80)

response = requests.get(f"{API_URL}/health")
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Test 2: Analyze FAKE job
print("\n" + "="*80)
print("TEST 2: Analyze FAKE Job")
print("="*80)

fake_job = {
    "title": "Tuyển nhân viên online",
    "description": "Việc nhẹ lương cao, không cần kinh nghiệm",
    "salary": "50-100 triệu",
    "email": "test@gmail.com"
}

response = requests.post(
    f"{API_URL}/api/analyze-job",
    json=fake_job,
    headers={"Content-Type": "application/json"}
)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Test 3: Analyze REAL job
print("\n" + "="*80)
print("TEST 3: Analyze REAL Job")
print("="*80)

real_job = {
    "title": "Senior Developer",
    "companyName": "VNG Corporation",
    "description": "Develop web applications with React. 3+ years experience required.",
    "salary": "25-35 triệu",
    "email": "hr@vng.com.vn"
}

response = requests.post(
    f"{API_URL}/api/analyze-job",
    json=real_job,
    headers={"Content-Type": "application/json"}
)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

print("\n" + "="*80)
print("✅ All tests complete!")
print("="*80)
