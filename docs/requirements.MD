## 1. Yêu Cầu Chức Năng (Functional Requirements)

### 1.1. Tương Tác với Người Dùng qua Telegram Bot
- **Lệnh /start:**
  - Khi người dùng gửi lệnh **/start**, bot sẽ gửi lời chào và giới thiệu sơ qua về chức năng của bot.
- **Yêu Cầu Gợi Ý Món Ăn:**
  - Người dùng gửi tin nhắn “gợi ý món ăn”.
  - Bot khởi động luồng thu thập tiêu chí, yêu cầu người dùng tự định nghĩa các tiêu chí phân loại món ăn.
    - Ví dụ: “Bạn muốn ăn món gì? Bạn có thể nhập tiêu chí như ‘khô’, ‘nước’, ‘chiên’, ‘nướng’, ‘xào’ hoặc bất kỳ tiêu chí nào khác.”

### 1.2. Thu Thập và Xác Nhận Tiêu Chí
- **Thu Thập Tiêu Chí:**
  - Người dùng tự nhập tiêu chí phân loại món ăn.
  - Nếu thông tin không đủ, hệ thống sẽ tự động sử dụng Gemini-2.0-Flash để gợi ý thêm tối đa 2 tiêu chí.
- **Xác Nhận Tiêu Chí:**
  - Bot gửi lại các tiêu chí được gợi ý để người dùng xác nhận trước khi tiếp tục.

### 1.3. Yêu Cầu Chia Sẻ Vị Trí
- **Chia Sẻ Vị Trí:**
  - Sau khi hoàn thành quá trình thu thập tiêu chí, bot yêu cầu người dùng chia sẻ vị trí hiện tại (sử dụng tính năng chia sẻ vị trí có sẵn của Telegram).

### 1.4. Tích Hợp OpenStreetMap API
- **Truy Vấn API:**
  - Sau khi nhận được vị trí (latitude, longitude), hệ thống sẽ sử dụng Python để truy vấn OpenStreetMap API nhằm lấy danh sách các quán ăn gần vị trí của người dùng.
  
### 1.5. Xử Lý và Đưa Ra Gợi Ý Qua Gemini-2.0-Flash
- **Phân Tích Lịch Sử Tin Nhắn:**
  - Gemini-2.0-Flash nhận vào lịch sử tin nhắn (session) của người dùng để phân tích và xác định xem cần hỏi thêm thông tin gì hay tự động gợi ý thêm tiêu chí.
- **Tạo Gợi Ý Món Ăn:**
  - Gemini-2.0-Flash xử lý danh sách quán ăn từ OpenStreetMap cùng với các tiêu chí (cả do người dùng nhập và do hệ thống gợi ý) để đưa ra gợi ý cuối cùng.
  - Kết quả cuối cùng là top 3 quán ăn được xếp hạng dựa trên mức độ phù hợp.
- **Lưu Trữ Kết Quả:**
  - Kết quả xử lý của Gemini (gợi ý cuối cùng) được lưu vào lịch sử tin nhắn của phiên làm việc.

### 1.6. Xử Lý Trường Hợp Không Tìm Thấy Quán Ăn Phù Hợp
- **Fallback:**
  - Nếu không có quán ăn phù hợp từ OpenStreetMap, bot sẽ phản hồi: “Tôi không thể search được, nhưng có thể gợi ý các món sau …”
  - Gợi ý dựa trên các tiêu chí đã có (được Gemini xử lý) sẽ được đưa ra cho người dùng.

### 1.7. Lưu Trữ Lịch Sử Tương Tác
- **SQLite Database:**
  - Lưu trữ thông tin gồm:
    - User ID
    - Session ID
    - Message history (toàn bộ các tin nhắn trao đổi giữa bot và người dùng, bao gồm các tiêu chí, gợi ý do Gemini tạo ra, kết quả cuối cùng)
  - Không cần lưu trữ thông tin chi tiết như tên, vị trí hay thông tin cá nhân khác ngoài các dữ liệu cần thiết cho phiên tương tác.

### 1.8. Giao Diện Trả Kết Quả
- **Định Dạng Kết Quả:**
  - Kết quả gợi ý (top 3 quán ăn) sẽ được gửi về cho người dùng dưới dạng tin nhắn văn bản.
  - Nội dung tin nhắn có thể bao gồm: tên quán, địa chỉ, khoảng cách từ vị trí hiện tại, và các thông tin bổ sung nếu có.

---

## 2. Yêu Cầu Phi Chức Năng (Non-functional Requirements)

### 2.1. Công Nghệ và Kiến Trúc
- **Ngôn ngữ lập trình:** Python.
- **API tích hợp:** Sử dụng duy nhất OpenStreetMap API cho việc tìm kiếm quán ăn.
- **Module Gemini-2.0-Flash:** Triển khai dưới dạng một service riêng biệt (microservice) để xử lý phân tích tin nhắn và tạo gợi ý.
- **Cơ sở dữ liệu:** SQLite để lưu trữ lịch sử tương tác (user id, session, message history).

### 2.2. Hiệu Suất và Độ Tin Cậy
- **Tốc độ phản hồi:** Tối ưu hóa thời gian phản hồi của bot khi thực hiện các truy vấn API và xử lý dữ liệu.
- **Xử lý lỗi:** 
  - Xử lý lỗi khi người dùng không cung cấp đủ tiêu chí hoặc vị trí.
  - Xử lý lỗi kết nối với OpenStreetMap API.
  - Đưa ra thông báo lỗi rõ ràng khi có sự cố xảy ra.

### 2.3. Bảo Mật
- **Dữ liệu người dùng:** Bảo vệ thông tin người dùng, chỉ lưu trữ các dữ liệu tối thiểu (user id, session, message history) và không lưu trữ thông tin cá nhân nhạy cảm.
- **Giao tiếp API:** Đảm bảo các kết nối tới OpenStreetMap API được bảo mật.

### 2.4. Khả Năng Mở Rộng và Bảo Trì
- **Triển khai trên localhost:** Giai đoạn đầu chỉ cần chạy trên môi trường localhost để kiểm tra và phát triển.
- **Modular hóa:** Cấu trúc ứng dụng được chia thành các module riêng biệt: Telegram bot, OpenStreetMap integration, Gemini-2.0-Flash service, và SQLite storage.
- **Mở rộng tương lai:** Mặc dù hiện tại không có kế hoạch chuyển sang môi trường production, cấu trúc hệ thống cần được thiết kế có khả năng mở rộng nếu cần trong tương lai.

### 2.5. Trải Nghiệm Người Dùng
- **Giao diện đơn giản:** Hiện tại, giao diện trả kết quả là văn bản thuần, không cần rich media hay inline buttons.
- **Luồng hội thoại tự nhiên:** Bot cần tạo ra các câu trả lời tự động linh hoạt dựa trên lịch sử tin nhắn, và đảm bảo giao tiếp thân thiện với người dùng.

---

## 3. Luồng Xử Lý Tổng Quát

1. **User gửi lệnh /start:**  
   - Bot trả lời lời chào và giới thiệu chức năng.

2. **User gửi “gợi ý món ăn”:**  
   - Bot bắt đầu thu thập tiêu chí bằng cách yêu cầu người dùng nhập phân loại món ăn (ví dụ: “khô”, “nước”, “chiên”, “nướng”, “xào” hoặc tiêu chí tự định nghĩa).

3. **Nếu tiêu chí không đủ:**  
   - Gemini-2.0-Flash (service riêng) tự động gợi ý thêm tối đa 2 tiêu chí và yêu cầu người dùng xác nhận.

4. **Sau khi có tiêu chí hợp lệ:**  
   - Bot yêu cầu người dùng chia sẻ vị trí qua Telegram.
   
5. **Sau khi nhận được vị trí:**  
   - Hệ thống sử dụng OpenStreetMap API để lấy danh sách các quán ăn gần vị trí.

6. **Gemini-2.0-Flash xử lý dữ liệu:**  
   - Phân tích lịch sử tin nhắn cùng với danh sách quán ăn và tiêu chí.
   - Generate gợi ý cuối cùng (top 3 quán ăn) dựa trên sự phù hợp.
   - Lưu kết quả vào lịch sử chat.

7. **Bot gửi kết quả gợi ý về cho người dùng:**  
   - Kết quả được gửi dưới dạng văn bản, bao gồm thông tin chi tiết của các quán ăn (tên, địa chỉ, khoảng cách, …).

8. **Xử lý trường hợp không tìm thấy quán ăn phù hợp:**  
   - Nếu OpenStreetMap API không trả về kết quả phù hợp, bot sẽ gửi thông báo “Tôi không thể search được, nhưng có thể gợi ý các món sau …”