import logging
from typing import List, Dict, Any, Optional
from llm.main import get_model_response, client
from prompts.criteria import (
    SUGGEST_CRITERIA_SYSTEM,
    SUGGEST_CRITERIA_USER,
    EXTRACT_CRITERIA_SYSTEM,
    EXTRACT_CRITERIA_USER,
    CONFIRM_CRITERIA_SYSTEM,
    CONFIRM_CRITERIA_USER
)

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Danh sách các tiêu chí phổ biến
COMMON_CRITERIA = [
    "khô", "nước", "chiên", "nướng", "xào", "hấp", "luộc", "cay", "ngọt", "mặn", "chua",
    "rau", "thịt", "hải sản", "chay", "nóng", "lạnh", "ăn nhanh", "ăn chậm", "sang trọng",
    "bình dân", "Việt Nam", "Trung Quốc", "Nhật Bản", "Hàn Quốc", "Thái Lan", "Ý", "Pháp"
]

class CriteriaProcessor:
    """Xử lý tiêu chí món ăn"""
    
    @staticmethod
    def extract_criteria_from_message(message: str) -> List[str]:
        """
        Trích xuất tiêu chí từ tin nhắn của người dùng
        
        Args:
            message: Tin nhắn của người dùng
            
        Returns:
            Danh sách các tiêu chí
        """
        try:
            # Sử dụng Gemini để trích xuất tiêu chí
            user_message = EXTRACT_CRITERIA_USER.format(message=message)
            response = get_model_response(client, EXTRACT_CRITERIA_SYSTEM, user_message)
            
            # Xử lý kết quả
            extracted_criteria = [line.strip() for line in response.strip().split('\n') if line.strip()]
            
            # Nếu không tìm thấy tiêu chí nào, sử dụng phương pháp đơn giản
            if not extracted_criteria:
                return CriteriaProcessor._extract_criteria_simple(message)
            
            return extracted_criteria
        except Exception as e:
            logger.error(f"Lỗi khi trích xuất tiêu chí: {e}")
            # Fallback: sử dụng phương pháp đơn giản
            return CriteriaProcessor._extract_criteria_simple(message)
    
    @staticmethod
    def _extract_criteria_simple(message: str) -> List[str]:
        """
        Phương pháp đơn giản để trích xuất tiêu chí từ tin nhắn
        
        Args:
            message: Tin nhắn của người dùng
            
        Returns:
            Danh sách các tiêu chí
        """
        # Chuyển đổi tin nhắn thành chữ thường để dễ so sánh
        message_lower = message.lower()
        
        # Tìm kiếm các tiêu chí phổ biến trong tin nhắn
        found_criteria = []
        for criterion in COMMON_CRITERIA:
            if criterion.lower() in message_lower:
                found_criteria.append(criterion)
        
        # Nếu không tìm thấy tiêu chí nào, thêm toàn bộ tin nhắn làm một tiêu chí
        if not found_criteria and message.strip():
            found_criteria = [message.strip()]
        
        return found_criteria
    
    @staticmethod
    def suggest_additional_criteria(current_criteria: List[str], max_suggestions: int = 2) -> List[str]:
        """
        Gợi ý thêm tiêu chí dựa trên các tiêu chí hiện có
        
        Args:
            current_criteria: Danh sách tiêu chí hiện có
            max_suggestions: Số lượng gợi ý tối đa
            
        Returns:
            Danh sách các tiêu chí được gợi ý thêm
        """
        # Nếu không có tiêu chí nào, gợi ý một số tiêu chí phổ biến
        if not current_criteria:
            return COMMON_CRITERIA[:max_suggestions]
        
        # Loại bỏ các tiêu chí đã có
        available_criteria = [c for c in COMMON_CRITERIA if c not in current_criteria]
        
        # Trả về số lượng gợi ý tối đa
        return available_criteria[:max_suggestions]
    
    @staticmethod
    def generate_criteria_suggestions(current_criteria: List[str], conversation_history: List[Dict[str, str]], max_suggestions: int = 2) -> List[str]:
        """
        Sử dụng Gemini để gợi ý thêm tiêu chí dựa trên lịch sử hội thoại
        
        Args:
            current_criteria: Danh sách tiêu chí hiện có
            conversation_history: Lịch sử hội thoại
            max_suggestions: Số lượng gợi ý tối đa
            
        Returns:
            Danh sách các tiêu chí được gợi ý thêm
        """
        try:
            # Chuyển đổi lịch sử hội thoại thành văn bản
            conversation_text = ""
            for message in conversation_history:
                role = "User" if message["role"] == "user" else "Bot"
                conversation_text += f"{role}: {message['content']}\n\n"
            
            # Chuẩn bị thông tin tiêu chí hiện có
            current_criteria_text = ', '.join(current_criteria) if current_criteria else 'Chưa có tiêu chí nào'
            
            # Sử dụng template để tạo prompt
            user_message = SUGGEST_CRITERIA_USER.format(
                conversation_text=conversation_text,
                current_criteria=current_criteria_text,
                max_suggestions=max_suggestions
            )
            
            # Gọi Gemini để gợi ý
            response = get_model_response(client, SUGGEST_CRITERIA_SYSTEM, user_message)
            
            # Xử lý kết quả
            suggested_criteria = [line.strip() for line in response.strip().split('\n') if line.strip()]
            
            # Giới hạn số lượng gợi ý
            return suggested_criteria[:max_suggestions]
            
        except Exception as e:
            logger.error(f"Lỗi khi gọi Gemini để gợi ý tiêu chí: {e}")
            # Fallback: sử dụng phương pháp đơn giản
            return CriteriaProcessor.suggest_additional_criteria(current_criteria, max_suggestions)
    
    @staticmethod
    def format_criteria_for_confirmation(criteria: List[str]) -> str:
        """
        Định dạng danh sách tiêu chí để xác nhận
        
        Args:
            criteria: Danh sách tiêu chí
            
        Returns:
            Chuỗi văn bản đã định dạng
        """
        try:
            # Nếu không có tiêu chí nào
            if not criteria:
                return "Bạn chưa cung cấp tiêu chí nào. Vui lòng nhập tiêu chí để tôi có thể gợi ý món ăn phù hợp."
            
            # Sử dụng template để tạo prompt
            user_message = CONFIRM_CRITERIA_USER.format(criteria=', '.join(criteria))
            
            # Gọi Gemini để định dạng
            response = get_model_response(client, CONFIRM_CRITERIA_SYSTEM, user_message)
            
            return response
            
        except Exception as e:
            logger.error(f"Lỗi khi định dạng tiêu chí: {e}")
            # Fallback: sử dụng phương pháp đơn giản
            criteria_text = ", ".join(criteria)
            return f"Tiêu chí bạn đã chọn: {criteria_text}\nBạn có muốn thêm tiêu chí nào khác không? Nếu không, hãy gõ 'xác nhận' để tiếp tục."
    
    @staticmethod
    def is_confirmation_message(message: str) -> bool:
        """
        Kiểm tra xem tin nhắn có phải là xác nhận không
        
        Args:
            message: Tin nhắn của người dùng
            
        Returns:
            True nếu là xác nhận, False nếu không
        """
        confirmation_keywords = ["xác nhận", "đồng ý", "ok", "được", "tiếp tục", "yes", "có"]
        message_lower = message.lower()
        
        for keyword in confirmation_keywords:
            if keyword in message_lower:
                return True
        
        return False 