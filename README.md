# Selenium — chọn số bài cần thu thập

Sửa lỗi driver không khớp: bộ khởi động bỏ qua chromedriver cũ trên PATH và tự chọn driver cho Chrome cài đặt, dùng cache riêng `driver-cache`. Tệp mở công cụ cập nhật Selenium trước khi chạy. Cần Internet; không cần hạ phiên bản Chrome hoặc xóa driver của chương trình khác. Lỗi chi tiết được lưu ở `data/startup-error.txt`.

Cách mở nhanh: bấm đúp **MO_CONG_CU.cmd**. Lần đầu tạo môi trường Python riêng trong `.venv` và cài Selenium; cần Internet. Không đóng cửa sổ khởi chạy trong lúc dùng. Bản mới đã tạo mã nguồn nhưng chưa chạy kiểm chứng trong phiên hiện tại do lỗi môi trường thực thi; cần chạy thử trước khi dùng với dữ liệu thật.

Đây là chương trình riêng, không phải cập nhật của tiện ích. Cần Python và Google Chrome. Trong thư mục này, chạy `python -m pip install -r requirements.txt`, rồi `python app.py`. Selenium Manager có thể cần Internet để tải driver tương thích lần đầu. Mở giao diện ở http://127.0.0.1:8767/ nếu trình duyệt không tự mở.

Chương trình mở Chrome với hồ sơ riêng `chrome-profile`; bạn tự đăng nhập, không cung cấp mật khẩu cho chương trình. Không dùng hồ sơ Chrome thường của bạn. Giữ hồ sơ này riêng tư vì trình duyệt có thể lưu phiên đăng nhập; không chia sẻ thư mục đó.

Vào nhóm/trang, chọn thứ tự bài mới nhất nếu Facebook hỗ trợ. Nhập **Số bài muốn quét** (số nguyên từ 1–500, mặc định 20), rồi bấm **Bắt đầu quét**. Ô nhập bị khóa trong lúc chạy; dừng phiên trước khi thay đổi số bài cho lượt tiếp theo. Công cụ xử lý tối đa số permalink đã chọn theo thứ tự Facebook hiển thị. Số thực tế có thể ít hơn nếu không tìm được đủ bài. Bài ghim, bài đề xuất và cách sắp xếp của Facebook có thể khiến thứ tự này khác thứ tự thời gian; chương trình không bảo đảm lấy đúng các bài mới nhất.

Công cụ cuộn bảng tin để tìm link, mở từng bài ở tab riêng, ghi nhận nội dung văn bản, mở phản hồi và cuộn vùng bình luận. Giới hạn tìm link là giá trị lớn hơn giữa 60 và 3 lần số bài đã chọn; giới hạn 3 phút/bài và 10.000 mẫu toàn bộ. Dừng hoạt động khi xác minh/hạn chế. Không CAPTCHA bypass, không proxy, không tắt dấu hiệu WebDriver. Tất cả nhãn để trống.

`data/progress.json` tự lưu nguyên tử sau mỗi lượt đọc và mỗi bài. Lần mở lại nhập tiến độ đã lưu; mẫu cùng mã bài và mã bình luận được cập nhật nếu văn bản dài hơn. Với cùng URL nguồn, bài có lý do `no_progress` được bỏ qua lần chạy tiếp theo; lý do đó không chứng minh đầy đủ. Muốn quét lại từ đầu, giữ bản sao dữ liệu rồi đổi tên progress.json khi chương trình đã tắt. Không cần xóa dữ liệu. JSON tương thích trang gán nhãn `../index.html`.

Lý do kết thúc bài: `no_progress` = không có tiến triển qua 5 lượt; `time_limit` = hết 3 phút; `unrecognized_scope` / `unrecognized_scroll` = không nhận diện cấu trúc; `user_stop` = người dùng dừng; `dataset_limit` = đạt giới hạn. Không biến bất kỳ lý do nào thành tuyên bố đã lấy hết.

Giao diện có Bắt đầu/Dừng/Tải JSON. Không thao tác cửa sổ đang thu thập trong lúc chạy; chuyển hoặc đóng tab có thể làm phiên dừng. Khi Dừng, chờ thao tác hiện tại kết thúc (tải trang có timeout tối đa 35 giây). Dữ liệu đã lưu vẫn giữ. Không được dùng hai bản app.py cùng lúc: cổng 8767 và hồ sơ Chrome sẽ xung đột.

Phạm vi kiểm chứng được báo trong hội thoại; Facebook thật có thể thay DOM và đòi điều chỉnh nhận diện. Không bảo đảm thu thập hết hay tránh bị hạn chế tài khoản/IP. Bản này chưa đọc ảnh/sticker và chưa tự xác nhận người viết là sinh viên PTIT.

[Tài liệu Selenium Chrome](https://www.selenium.dev/documentation/webdriver/browsers/chrome/).
