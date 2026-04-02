# Thuyết Minh Ngắn Về Nguyên Lý Hoạt Động Hệ Thống

Hệ thống của em được xây dựng nhằm hỗ trợ quản lý và đánh giá độ tin cậy của tin tuyển dụng theo hướng cá nhân hóa, có ứng dụng Machine Learning. Quy trình hoạt động gồm 3 lớp chính là dữ liệu, mô hình đánh giá và giao diện người dùng.

Đầu tiên, ở lớp dữ liệu, hệ thống sử dụng tập dữ liệu tuyển dụng đã được tiền xử lý, gán nhãn và trích xuất đặc trưng. Các đặc trưng bao gồm đặc trưng văn bản như độ dài mô tả, mật độ từ khóa nghi ngờ, đặc trưng về lương, yêu cầu công việc, thông tin công ty và điểm uy tín doanh nghiệp.

Tiếp theo, ở lớp mô hình, backend Flask sẽ nạp sẵn mô hình đã huấn luyện, bộ TF-IDF, bộ chuẩn hóa dữ liệu và danh sách đặc trưng. Khi người dùng nhập một tin tuyển dụng mới, hệ thống sẽ chuẩn hóa dữ liệu đầu vào, ghép các trường thành văn bản tổng hợp, trích xuất đặc trưng thủ công, rồi đưa qua mô hình Machine Learning để dự đoán xác suất tin thật hoặc tin có rủi ro.

Điểm đặc biệt là hệ thống không chỉ dùng mô hình học máy đơn thuần mà còn kết hợp thêm heuristic rules và blacklist. Heuristic giúp phát hiện nhanh các dấu hiệu như mô tả quá ngắn, dùng email cá nhân, mức lương bất thường hoặc thiếu thông tin doanh nghiệp. Nếu tin tuyển dụng trùng với blacklist về công ty, email hoặc số điện thoại thì hệ thống sẽ tăng mức cảnh báo.

Sau đó, hệ thống tổng hợp các nguồn tín hiệu này để đưa ra Trust Score, Risk Score, mức rủi ro và kết luận gợi ý như tin cậy, cần kiểm tra hay nguy cơ cao. Bên cạnh đó, hệ thống còn có cơ chế cá nhân hóa, tức là so khớp hồ sơ và từ khóa quan tâm của ứng viên với các tin tuyển dụng đã được đánh giá để đề xuất những công việc vừa phù hợp vừa an toàn hơn.

Cuối cùng, toàn bộ kết quả được hiển thị trên giao diện React dưới dạng dashboard trực quan, danh sách tin tuyển dụng, trang phân tích chi tiết, trang quản lý blacklist và trang gợi ý cá nhân hóa. Nhờ đó, hệ thống không chỉ hỗ trợ phát hiện rủi ro mà còn hỗ trợ ra quyết định cho người dùng một cách trực quan và thực tiễn.
