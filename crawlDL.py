import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def init_driver():
    """Khởi tạo Chrome driver"""
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--start-maximized')
    # Bỏ comment dòng dưới nếu muốn chạy ẩn
    # options.add_argument('--headless')
    
    driver = webdriver.Chrome(options=options)
    return driver

def scrape_job_detail(driver, job_url):
    """Cào thông tin chi tiết từ trang job"""
    try:
        driver.get(job_url)
        wait = WebDriverWait(driver, 10)
        
        # Đợi trang load
        time.sleep(2)
        
        job_data = {}
        
        # Lấy tên công ty
        try:
            company_name = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "company-name-label"))
            ).text.strip()
            job_data['company_name'] = company_name
        except:
            job_data['company_name'] = "N/A"
        
        # Lấy vị trí/chức danh
        try:
            job_title = driver.find_element(By.CLASS_NAME, "job-detail__info--title").text.strip()
            job_data['job_title'] = job_title
        except:
            job_data['job_title'] = "N/A"
        
        # Lấy các thông tin chi tiết
        try:
            detail_elements = driver.find_elements(By.CLASS_NAME, "job-detail__information-detail")
            details = []
            for element in detail_elements:
                detail_text = element.text.strip()
                if detail_text:
                    details.append(detail_text)
            job_data['details'] = " | ".join(details) if details else "N/A"
        except:
            job_data['details'] = "N/A"
        
        return job_data
        
    except Exception as e:
        print(f"Lỗi khi cào chi tiết job: {e}")
        return None

def scrape_topcv_it_jobs(url, max_jobs=10):
    """Hàm chính để cào dữ liệu từ TopCV"""
    driver = init_driver()
    all_jobs_data = []
    
    try:
        print(f"Đang truy cập: {url}")
        driver.get(url)
        
        # Đợi trang load
        wait = WebDriverWait(driver, 15)
        time.sleep(3)
        
        # Tìm danh sách công việc
        try:
            job_list = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "job-list-2"))
            )
            print("Đã tìm thấy danh sách công việc")
        except TimeoutException:
            print("Không tìm thấy danh sách công việc")
            return all_jobs_data
        
        # Tìm các job items
        job_items = driver.find_elements(By.CSS_SELECTOR, ".job-item-2.job-item-default")
        print(f"Tìm thấy {len(job_items)} công việc")
        
        # Giới hạn số lượng job cào
        jobs_to_scrape = min(len(job_items), max_jobs)
        
        for i in range(jobs_to_scrape):
            try:
                # Refresh lại danh sách job items sau mỗi lần quay lại
                job_items = driver.find_elements(By.CSS_SELECTOR, ".job-item-2.job-item-default")
                job_item = job_items[i]
                
                # Tìm button hoặc link để vào chi tiết
                try:
                    # Thử tìm button với data-job-id
                    button = job_item.find_element(By.CSS_SELECTOR, "button[data-job-id]")
                    job_id = button.get_attribute("data-job-id")
                    
                    # Click vào button
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(2)
                    
                    # Lấy URL hiện tại
                    current_url = driver.current_url
                    
                except NoSuchElementException:
                    # Nếu không có button, thử tìm link
                    try:
                        link = job_item.find_element(By.CSS_SELECTOR, "a[href*='job']")
                        current_url = link.get_attribute("href")
                        driver.get(current_url)
                        time.sleep(2)
                    except:
                        print(f"Không tìm thấy link cho job {i+1}")
                        continue
                
                print(f"Đang cào job {i+1}/{jobs_to_scrape}: {current_url}")
                
                # Cào thông tin chi tiết
                job_data = scrape_job_detail(driver, current_url)
                
                if job_data:
                    all_jobs_data.append(job_data)
                    print(f"  ✓ Đã cào: {job_data.get('job_title', 'N/A')} - {job_data.get('company_name', 'N/A')}")
                
                # Quay lại trang danh sách
                driver.back()
                time.sleep(2)
                
            except Exception as e:
                print(f"Lỗi khi xử lý job {i+1}: {e}")
                # Thử quay lại trang danh sách
                try:
                    driver.get(url)
                    time.sleep(2)
                except:
                    pass
                continue
        
    except Exception as e:
        print(f"Lỗi chung: {e}")
    
    finally:
        driver.quit()
    
    return all_jobs_data

def save_to_csv(jobs_data, filename="topcv_it_jobs.csv"):
    """Lưu dữ liệu vào file CSV"""
    if not jobs_data:
        print("Không có dữ liệu để lưu")
        return
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['company_name', 'job_title', 'details']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for job in jobs_data:
            writer.writerow(job)
    
    print(f"\n✓ Đã lưu {len(jobs_data)} công việc vào file {filename}")

# Sử dụng
if __name__ == "__main__":
    # URL trang tìm kiếm việc làm IT trên TopCV
    url = "https://www.topcv.vn/viec-lam-it"
    
    # Cào dữ liệu (giới hạn 10 jobs để test)
    print("Bắt đầu cào dữ liệu từ TopCV...")
    jobs_data = scrape_topcv_it_jobs(url, max_jobs=10)
    
    # Lưu vào CSV
    if jobs_data:
        save_to_csv(jobs_data, "topcv_it_jobs.csv")
        print(f"\nHoàn thành! Đã cào được {len(jobs_data)} công việc.")
    else:
        print("\nKhông cào được dữ liệu nào.")