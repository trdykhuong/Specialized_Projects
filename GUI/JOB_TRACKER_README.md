# 📱 Personal Job Tracker & Scam Analyzer

**Hệ thống quản lý và đánh giá độ tin cậy tin tuyển dụng cá nhân**

---

## 🎯 Tổng quan

Một ứng dụng web giúp người tìm việc:
- ✅ Lưu trữ và quản lý các tin tuyển dụng
- 🛡️ Tự động phân tích và cảnh báo rủi ro lừa đảo
- 📊 Theo dõi tiến trình apply job
- 🚫 Quản lý danh sách đen (blacklist)

---

## ✨ Tính năng chính

### 1️⃣ **Lưu trữ tin tuyển dụng**
- Thêm tin bằng cách:
  - Copy/paste nội dung
  - Nhập thông tin thủ công
  - Lưu link gốc
- Thông tin lưu trữ:
  - Vị trí tuyển dụng
  - Tên công ty
  - Mức lương
  - Địa chỉ, email, phone
  - Mô tả công việc
  - Trạng thái (Đang cân nhắc / Đã apply / Phỏng vấn / Offer / Từ chối)

### 2️⃣ **Đánh giá độ tin cậy tự động**
Hệ thống tính **Risk Score (0-100)** dựa trên:

| Tiêu chí | Điểm cộng |
|----------|-----------|
| Lương > 50M cho fresher | +20 |
| Từ khóa nghi ngờ (đóng phí, MLM, đa cấp) | +15/từ |
| Email cá nhân (@gmail, @yahoo) | +10 |
| Thiếu địa chỉ công ty | +15 |
| Thiếu thông tin công ty | +10 |
| Trong blacklist (email, company, phone) | +30 |

**Phân loại:**
- 🟢 **0-30**: Tin cậy
- 🟡 **31-60**: Cần kiểm tra
- 🔴 **61-100**: Nguy cơ cao

### 3️⃣ **Ghi chú & Đánh giá cá nhân**
- Đánh giá sao (1-5 ⭐)
- Viết nhận xét riêng:
  - "HR nói chuyện mập mờ"
  - "Yêu cầu đóng phí 500k"
  - "Công ty uy tín, phỏng vấn chuyên nghiệp"
- Đánh dấu confirmed scam

### 4️⃣ **Theo dõi Application Tracking**
- Timeline apply jobs
- Trạng thái từng bước:
  - Đang cân nhắc
  - Đã apply (lưu ngày apply)
  - Phỏng vấn
  - Nhận offer
  - Từ chối

### 5️⃣ **Phân tích thống kê**
Dashboard hiển thị:
- 📊 Phân bố rủi ro (Low/Medium/High)
- 📈 Trạng thái apply
- 📅 Timeline apply gần đây
- 🎯 Tỷ lệ thành công

### 6️⃣ **Blacklist cá nhân**
Quản lý danh sách đen:
- Email nghi ngờ
- Công ty không tin cậy
- Số điện thoại spam

Hệ thống tự động cảnh báo khi phát hiện thông tin trùng khớp!

---

## 🎨 Giao diện

### **3 chế độ xem:**

1. **List View** (Danh sách)
   - Hiển thị đầy đủ thông tin
   - Risk score và warnings
   - Personal notes
   - Quick actions

2. **Grid View** (Lưới)
   - Compact cards
   - Phù hợp khi có nhiều tin
   - Dễ browse

3. **Stats View** (Thống kê)
   - Biểu đồ phân bố rủi ro
   - Trạng thái apply
   - Timeline apply

---

## 🚀 Cách sử dụng

### **Khởi chạy ứng dụng**

1. Mở file `job_tracker_app.jsx` trong Claude Artifacts
2. Giao diện sẽ tự động hiển thị

### **Thêm tin mới**

1. Click nút **"Thêm tin mới"**
2. Điền thông tin:
   - Vị trí tuyển dụng (bắt buộc)
   - Công ty, lương, địa chỉ
   - Email, phone liên hệ
   - Link tin gốc
3. Chọn trạng thái
4. Click **"Lưu tin"**

→ Hệ thống tự động tính Risk Score và hiển thị warnings!

### **Xem chi tiết & Cập nhật**

1. Click vào bất kỳ tin nào
2. Modal chi tiết hiển thị:
   - Risk analysis đầy đủ
   - Warnings cụ thể
   - Thông tin liên hệ
3. Thêm ghi chú cá nhân:
   - Đánh giá sao
   - Viết nhận xét
4. Cập nhật trạng thái
5. Thêm vào blacklist nếu cần

### **Quản lý Blacklist**

1. Click nút **"Blacklist"**
2. Thêm vào danh sách đen:
   - Email nghi ngờ
   - Công ty không uy tín
   - Số điện thoại spam
3. Xóa khỏi blacklist khi cần

### **Tìm kiếm & Lọc**

- **Search box**: Tìm theo tên công ty, vị trí
- **Filter dropdown**:
  - Tất cả
  - Nguy cơ cao
  - An toàn
  - Đang cân nhắc
  - Đã apply
  - Phỏng vấn
  - Nhận offer

---

## 💾 Lưu trữ dữ liệu

Dữ liệu được lưu **persistent** trong browser storage:
- `jobs-list`: Danh sách tất cả jobs
- `blacklist-data`: Danh sách đen

**Ưu điểm:**
- Tự động lưu mỗi khi có thay đổi
- Không mất dữ liệu khi refresh
- Hoàn toàn private (chỉ lưu local)

**Lưu ý:**
- Dữ liệu chỉ tồn tại trong session artifact hiện tại
- Để backup: Export ra file (tính năng sẽ thêm sau)

---

## 🔍 Ví dụ thực tế

### **Case 1: Tin FAKE rõ ràng**

```
Vị trí: "Cộng tác viên bán hàng online"
Công ty: "Công ty ABC"
Lương: "30-100 triệu"
Mô tả: "Việc nhẹ lương cao, không cần kinh nghiệm"
Email: "recruiter123@gmail.com"
Địa chỉ: (trống)

→ Risk Score: 75/100 🔴
Warnings:
• Lương bất thường cao
• Có từ khóa nghi ngờ: "việc nhẹ lương cao"
• Có từ khóa nghi ngờ: "không cần kinh nghiệm"
• Email cá nhân
• Thiếu địa chỉ công ty
```

### **Case 2: Tin REAL uy tín**

```
Vị trí: "Senior Frontend Developer"
Công ty: "VNG Corporation"
Lương: "25-35 triệu"
Mô tả: "Phát triển web app với React/Next.js..."
Email: "hr@vng.com.vn"
Địa chỉ: "182 Lê Đại Hành, Q3, TPHCM"

→ Risk Score: 5/100 🟢
Tin cậy!
```

---

## 📊 So sánh với các giải pháp khác

| Tính năng | Ứng dụng này | LinkedIn | Job sites | Google Sheets |
|-----------|--------------|----------|-----------|---------------|
| Lưu tin offline | ✅ | ❌ | ❌ | ✅ |
| Auto risk analysis | ✅ | ❌ | ❌ | ❌ |
| Personal notes | ✅ | ✅ | ❌ | ✅ |
| Blacklist management | ✅ | ❌ | ❌ | ❌ |
| Application tracking | ✅ | ✅ | ❌ | ✅ |
| Stats dashboard | ✅ | ⚠️ Limited | ❌ | ⚠️ Manual |
| **Privacy** | ✅ 100% local | ❌ | ❌ | ⚠️ Cloud |

---

## 🎓 Giá trị học thuật

### **Đóng góp:**
1. **Personalization**: Mỗi người có "sổ tay thông minh" riêng
2. **User empowerment**: Người dùng chủ động đánh giá
3. **Learning from experience**: Ghi chú và rating giúp học hỏi
4. **Privacy-first**: Dữ liệu hoàn toàn local

### **Khác biệt với platform lớn:**
- Không phải làm hệ thống cho hàng nghìn người
- Focus vào trải nghiệm cá nhân
- Dễ triển khai, dễ sử dụng
- Có chiều sâu (AI risk scoring)

---

## 🔮 Tính năng tương lai

### **Short-term:**
- [ ] Export data to CSV/JSON
- [ ] Import từ email hoặc link
- [ ] Dark mode
- [ ] Calendar integration (nhắc lịch phỏng vấn)

### **Medium-term:**
- [ ] Tích hợp ML model thật (API backend)
- [ ] Chrome extension (save job từ bất kỳ trang nào)
- [ ] Mobile responsive
- [ ] Chia sẻ blacklist với bạn bè

### **Long-term:**
- [ ] Community-shared blacklist
- [ ] Sentiment analysis cho reviews
- [ ] Salary insights (so sánh mức lương)
- [ ] Job matching recommendations

---

## 💡 Tips sử dụng hiệu quả

1. **Luôn lưu tin ngay khi thấy**
   - Đừng để quên link
   - Ghi ngay impression đầu tiên

2. **Tin vào Risk Score nhưng kết hợp với common sense**
   - Score chỉ là tham khảo
   - Đọc kỹ warnings
   - Thêm personal notes

3. **Cập nhật trạng thái thường xuyên**
   - Giúp theo dõi progress
   - Thống kê chính xác hơn

4. **Sử dụng Blacklist tích cực**
   - Thấy scam → add ngay
   - Giúp cảnh báo cho các tin sau

5. **Review định kỳ**
   - Mỗi tuần xem lại stats
   - Học từ các tin đã apply
   - Adjust chiến lược tìm việc

---

## 🙏 Kết luận

Đây là một **personal tool** thực sự hữu ích cho người tìm việc, đặc biệt trong bối cảnh:
- 📈 Tuyển dụng online tăng mạnh
- ⚠️ Lừa đảo phổ biến
- 😰 Khó quản lý nhiều ứng tuyển

**Không chỉ là anti-scam tool, mà còn là job management system hoàn chỉnh!**

---

**Developed with ❤️ by Claude**
