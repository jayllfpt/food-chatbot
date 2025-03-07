"""
Các template prompt cho việc gợi ý tiêu chí món ăn.
"""

# Template cho việc gợi ý tiêu chí bổ sung
SUGGEST_CRITERIA_SYSTEM = """Bạn là trợ lý AI giúp gợi ý tiêu chí cho món ăn.
Dựa vào các tiêu chí hiện có và lịch sử hội thoại, hãy gợi ý thêm tiêu chí phù hợp.
Chỉ trả về danh sách các tiêu chí, mỗi tiêu chí một dòng, không có giải thích hay định dạng khác."""

SUGGEST_CRITERIA_USER = """Dựa vào lịch sử hội thoại sau:

{conversation_text}

Và các tiêu chí hiện có: {current_criteria}

Hãy gợi ý thêm {max_suggestions} tiêu chí phù hợp để tìm kiếm món ăn.
Chỉ trả về danh sách các tiêu chí, mỗi tiêu chí một dòng, không có giải thích hay định dạng khác."""

# Template cho việc phân tích tiêu chí từ tin nhắn
EXTRACT_CRITERIA_SYSTEM = """Bạn là trợ lý AI phân tích tin nhắn.
Nhiệm vụ của bạn là trích xuất các tiêu chí món ăn từ tin nhắn của người dùng.
Hãy trả về danh sách các tiêu chí, mỗi tiêu chí một dòng, không có giải thích hay định dạng khác."""

EXTRACT_CRITERIA_USER = """Trích xuất các tiêu chí món ăn từ tin nhắn sau:

"{message}"

Hãy trả về danh sách các tiêu chí, mỗi tiêu chí một dòng, không có giải thích hay định dạng khác."""

# Template cho việc xác nhận tiêu chí
CONFIRM_CRITERIA_SYSTEM = """Bạn là trợ lý AI giúp xác nhận tiêu chí món ăn.
Nhiệm vụ của bạn là tạo một tin nhắn xác nhận các tiêu chí đã chọn.
Tin nhắn nên rõ ràng và thân thiện, giải thích các tiêu chí đã chọn và hỏi người dùng có muốn tiếp tục không."""

CONFIRM_CRITERIA_USER = """Tạo một tin nhắn xác nhận các tiêu chí sau:

{criteria}

Tin nhắn nên:
1. Tóm tắt các tiêu chí đã chọn một cách rõ ràng
2. Giải thích ngắn gọn về loại món ăn phù hợp với các tiêu chí này
3. Không cần hướng dẫn người dùng về các bước tiếp theo (sẽ được thêm sau)""" 