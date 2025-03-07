# Kế hoạch phát triển Food Chatbot dựa trên yêu cầu

Sau khi đọc tài liệu yêu cầu và so sánh với codebase hiện tại, tôi đã xác định các công việc cần thực hiện để hoàn thiện ứng dụng Food Chatbot. Dưới đây là kế hoạch chi tiết:

## 1. Phân tích hiện trạng

**Đã hoàn thành:**
- Cấu trúc cơ bản của Telegram bot
- Tích hợp với Gemini API
- Xử lý các lệnh cơ bản (/start, /help)
- Cấu trúc thư mục và tổ chức code

**Còn thiếu:**
- Luồng hội thoại để thu thập tiêu chí món ăn
- Tích hợp OpenStreetMap API
- Cơ sở dữ liệu SQLite để lưu trữ lịch sử
- Xử lý vị trí người dùng
- Phân tích và gợi ý món ăn dựa trên tiêu chí

## 2. Kế hoạch phát triển

### Giai đoạn 1: Cấu trúc dữ liệu và cơ sở dữ liệu
1. **Tạo module database**
   - Tạo thư mục `database/`
   - Tạo file `database/main.py` để quản lý kết nối và truy vấn SQLite
   - Thiết kế schema cho bảng lưu trữ user_id, session_id, message_history

2. **Tạo module quản lý phiên (session)**
   - Tạo thư mục `session/`
   - Tạo file `session/main.py` để quản lý trạng thái hội thoại của người dùng
   - Xây dựng các hàm lưu trữ và truy xuất lịch sử tin nhắn

### Giai đoạn 2: Tích hợp OpenStreetMap API
1. **Tạo module location**
   - Tạo thư mục `location/`
   - Tạo file `location/main.py` để xử lý vị trí và tìm kiếm quán ăn
   - Xây dựng các hàm gọi API OpenStreetMap và xử lý kết quả

2. **Cập nhật requirements.txt**
   - Thêm thư viện `requests` để gọi API
   - Thêm thư viện `geopy` để tính toán khoảng cách

### Giai đoạn 3: Xây dựng luồng hội thoại
1. **Cập nhật bot/main.py**
   - Thêm các trạng thái hội thoại (COLLECTING_CRITERIA, WAITING_FOR_LOCATION, etc.)
   - Xây dựng hàm xử lý tin nhắn dựa trên trạng thái hiện tại của người dùng
   - Thêm hàm xử lý vị trí được chia sẻ từ người dùng

2. **Tạo module xử lý tiêu chí**
   - Tạo thư mục `criteria/`
   - Tạo file `criteria/main.py` để quản lý và xử lý tiêu chí món ăn
   - Xây dựng hàm phân tích và gợi ý tiêu chí bổ sung

### Giai đoạn 4: Tích hợp Gemini cho gợi ý món ăn
1. **Cập nhật llm/main.py**
   - Thêm hàm phân tích lịch sử tin nhắn
   - Thêm hàm gợi ý tiêu chí bổ sung
   - Thêm hàm xử lý danh sách quán ăn và đưa ra gợi ý cuối cùng

2. **Tạo các prompt template**
   - Tạo thư mục `prompts/`
   - Tạo các template cho việc gợi ý tiêu chí
   - Tạo các template cho việc phân tích quán ăn và đưa ra gợi ý

### Giai đoạn 5: Xử lý trường hợp đặc biệt và hoàn thiện
1. **Xử lý trường hợp không tìm thấy quán ăn**
   - Thêm logic fallback khi không có kết quả từ OpenStreetMap
   - Sử dụng Gemini để gợi ý món ăn dựa trên tiêu chí mà không cần vị trí

2. **Cải thiện trải nghiệm người dùng**
   - Thêm thông báo "Đang xử lý..." khi bot đang tìm kiếm
   - Định dạng kết quả gợi ý để dễ đọc

3. **Xử lý lỗi và ngoại lệ**
   - Thêm xử lý lỗi khi gọi API
   - Thêm xử lý lỗi khi người dùng không cung cấp đủ thông tin

## 3. Cấu trúc thư mục cuối cùng

```
food-chatbot/
├── main.py                  # Entry point
├── .env                     # Environment variables
├── requirements.txt         # Dependencies
├── README.md                # Documentation
├── bot/
│   └── main.py              # Telegram bot implementation
├── llm/
│   └── main.py              # Gemini integration
├── database/
│   └── main.py              # SQLite database management
├── session/
│   └── main.py              # User session management
├── location/
│   └── main.py              # OpenStreetMap API integration
├── criteria/
│   └── main.py              # Food criteria processing
└── prompts/
    ├── criteria.py          # Prompts for criteria suggestion
    └── recommendation.py    # Prompts for food recommendation
```

## 4. Ước tính thời gian

1. **Giai đoạn 1**: 1-2 ngày
2. **Giai đoạn 2**: 1-2 ngày
3. **Giai đoạn 3**: 2-3 ngày
4. **Giai đoạn 4**: 2-3 ngày
5. **Giai đoạn 5**: 1-2 ngày

**Tổng thời gian dự kiến**: 7-12 ngày làm việc

## 5. Các thách thức tiềm ẩn

1. **Xử lý ngôn ngữ tự nhiên**: Cần đảm bảo Gemini hiểu đúng tiêu chí người dùng nhập bằng tiếng Việt
2. **Độ chính xác của OpenStreetMap**: Dữ liệu quán ăn có thể không đầy đủ hoặc chính xác
3. **Quản lý trạng thái hội thoại**: Cần xử lý các trường hợp người dùng thoát giữa chừng hoặc thay đổi yêu cầu
4. **Hiệu suất**: Cần tối ưu thời gian phản hồi khi gọi nhiều API khác nhau

## 6. Đề xuất cải tiến (nếu có thời gian)

1. **Thêm chức năng lưu món ăn yêu thích**
2. **Thêm chức năng đánh giá gợi ý**
3. **Tích hợp với Google Maps để hiển thị bản đồ**
4. **Thêm chức năng tìm kiếm theo loại ẩm thực cụ thể**
5. **Thêm chức năng gợi ý dựa trên lịch sử tìm kiếm trước đó**

Đây là kế hoạch tổng thể để phát triển Food Chatbot theo yêu cầu. Mỗi giai đoạn có thể được triển khai tuần tự hoặc song song tùy thuộc vào nguồn lực và thời gian có sẵn.
