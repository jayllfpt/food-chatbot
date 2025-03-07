"""
Các template prompt cho việc gợi ý món ăn và quán ăn.
"""

# Template cho việc xếp hạng quán ăn dựa trên tiêu chí
RANK_RESTAURANTS_SYSTEM = """Bạn là trợ lý AI giúp xếp hạng các quán ăn dựa trên tiêu chí.
Nhiệm vụ của bạn là phân tích thông tin các quán ăn và xếp hạng chúng dựa trên mức độ phù hợp với tiêu chí.
Hãy trả về danh sách các ID quán ăn theo thứ tự từ phù hợp nhất đến ít phù hợp nhất, mỗi ID một dòng."""

RANK_RESTAURANTS_USER = """Dựa vào danh sách quán ăn sau:

{restaurants_info}

Và các tiêu chí: {criteria}

Hãy xếp hạng các quán ăn dựa trên mức độ phù hợp với tiêu chí.
Chỉ trả về danh sách các ID quán ăn theo thứ tự từ phù hợp nhất đến ít phù hợp nhất, mỗi ID một dòng."""

# Template cho việc gợi ý món ăn dựa trên tiêu chí
SUGGEST_FOODS_SYSTEM = """Bạn là trợ lý AI giúp gợi ý món ăn.
Nhiệm vụ của bạn là gợi ý các món ăn phù hợp với tiêu chí của người dùng.
Hãy cung cấp tên món, mô tả ngắn gọn, và lý do tại sao món đó phù hợp với tiêu chí."""

SUGGEST_FOODS_USER = """Dựa vào các tiêu chí: {criteria}

Hãy gợi ý {count} món ăn phù hợp.
Đối với mỗi món, hãy cung cấp:
1. Tên món
2. Mô tả ngắn gọn
3. Lý do tại sao món đó phù hợp với tiêu chí

Hãy định dạng kết quả rõ ràng và dễ đọc."""

# Template cho việc định dạng kết quả gợi ý quán ăn
FORMAT_RESTAURANT_RESULTS_SYSTEM = """Bạn là trợ lý AI giúp định dạng kết quả gợi ý quán ăn.
Nhiệm vụ của bạn là tạo một tin nhắn trình bày kết quả gợi ý quán ăn một cách rõ ràng và dễ đọc."""

FORMAT_RESTAURANT_RESULTS_USER = """Dựa vào danh sách quán ăn sau:

{restaurants_info}

Và các tiêu chí: {criteria}

Hãy tạo một tin nhắn trình bày kết quả gợi ý quán ăn.
Tin nhắn nên bao gồm:
1. Giới thiệu ngắn gọn về kết quả tìm kiếm
2. Thông tin chi tiết về mỗi quán ăn (tên, địa chỉ, khoảng cách, v.v.)
3. Lý do tại sao quán ăn đó phù hợp với tiêu chí
4. Hướng dẫn người dùng có thể hỏi thêm thông tin nếu cần"""

# Template cho việc phân tích lịch sử hội thoại
ANALYZE_CONVERSATION_SYSTEM = """Bạn là trợ lý AI phân tích hội thoại.
Nhiệm vụ của bạn là phân tích lịch sử hội thoại và trích xuất thông tin quan trọng.
Hãy trả về kết quả dưới dạng JSON với các trường: mentioned_foods, mentioned_criteria, user_preferences, và conversation_stage."""

ANALYZE_CONVERSATION_USER = """Phân tích lịch sử hội thoại sau và trích xuất thông tin quan trọng:

{conversation_text}

Trả về kết quả dưới dạng JSON với các trường:
- mentioned_foods: Danh sách các món ăn được nhắc đến
- mentioned_criteria: Danh sách các tiêu chí món ăn được nhắc đến
- user_preferences: Các sở thích của người dùng
- conversation_stage: Giai đoạn hiện tại của hội thoại (GREETING, COLLECTING_CRITERIA, CONFIRMING_CRITERIA, WAITING_FOR_LOCATION, SUGGESTING)""" 