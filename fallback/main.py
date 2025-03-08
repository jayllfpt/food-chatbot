import logging
from typing import List, Dict, Any, Optional
from llm.main import generate_food_suggestions, get_model_response, client
from prompts.recommendation import SUGGEST_FOODS_SYSTEM, SUGGEST_FOODS_USER

# Cấu hình logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FallbackHandler:
    """Xử lý các trường hợp đặc biệt khi không tìm thấy quán ăn hoặc xảy ra lỗi"""
    
    @staticmethod
    def handle_no_restaurants(criteria: List[str]) -> str:
        """
        Xử lý trường hợp không tìm thấy quán ăn
        
        Args:
            criteria: Danh sách tiêu chí
            
        Returns:
            Chuỗi văn bản chứa gợi ý món ăn
        """
        try:
            # Tạo thông báo
            message = (
                f"Tôi không thể tìm thấy quán ăn nào gần vị trí của bạn dựa trên tiêu chí ({', '.join(criteria)}).\n\n"
                "Tuy nhiên, tôi có thể gợi ý một số món ăn phù hợp với tiêu chí của bạn:\n\n"
            )
            
            # Gọi Gemini để gợi ý món ăn dựa trên tiêu chí
            food_suggestions = generate_food_suggestions(criteria, count=3)
            
            # Kết hợp thông báo và gợi ý
            message += food_suggestions
            message += "\n\nBạn có thể hỏi tôi về việc gợi ý món ăn bất cứ lúc nào."
            
            return message
            
        except Exception as e:
            logger.error(f"Lỗi khi xử lý trường hợp không tìm thấy quán ăn: {e}")
            return FallbackHandler.get_generic_food_suggestions()
    
    @staticmethod
    def handle_no_location() -> str:
        """
        Xử lý trường hợp người dùng không chia sẻ vị trí
        
        Returns:
            Chuỗi văn bản chứa thông báo
        """
        return (
            "Để tôi có thể gợi ý quán ăn gần bạn, vui lòng chia sẻ vị trí của bạn.\n\n"
            "Bạn có thể sử dụng nút 'Chia sẻ vị trí' bên dưới hoặc nhập địa chỉ của bạn."
        )
    
    @staticmethod
    def handle_no_criteria() -> str:
        """
        Xử lý trường hợp người dùng không cung cấp tiêu chí
        
        Returns:
            Chuỗi văn bản chứa thông báo
        """
        return (
            "Để tôi có thể gợi ý món ăn phù hợp, vui lòng cho tôi biết bạn thích ăn món gì?\n\n"
            "Bạn có thể nhập tiêu chí như 'khô', 'nước', 'chiên', 'nướng', 'xào', 'cay', 'ngọt', 'mặn', 'chua', "
            "'rau', 'thịt', 'hải sản', 'chay', 'nóng', 'lạnh', v.v."
        )
    
    @staticmethod
    def handle_api_error() -> str:
        """
        Xử lý trường hợp lỗi API
        
        Returns:
            Chuỗi văn bản chứa thông báo
        """
        return (
            "Xin lỗi, tôi đang gặp sự cố khi kết nối với máy chủ. Vui lòng thử lại sau.\n\n"
            "Trong khi chờ đợi, bạn có thể thử lại với các tiêu chí khác hoặc chia sẻ vị trí khác."
        )
    
    @staticmethod
    def get_generic_food_suggestions() -> str:
        """
        Trả về gợi ý món ăn chung khi không có tiêu chí cụ thể
        
        Returns:
            Chuỗi văn bản chứa gợi ý món ăn
        """
        try:
            # Xây dựng prompt cho Gemini
            system_message = """Bạn là trợ lý AI giúp gợi ý món ăn.
Hãy gợi ý 3 món ăn phổ biến và được nhiều người yêu thích.
Đối với mỗi món, hãy cung cấp tên món và mô tả ngắn gọn."""
            
            user_message = "Gợi ý 3 món ăn phổ biến và được nhiều người yêu thích ở Việt Nam."
            
            # Gọi Gemini để gợi ý
            response = get_model_response(client, system_message, user_message)
            
            # Tạo thông báo
            message = (
                "Tôi không thể xác định tiêu chí cụ thể, nhưng đây là một số món ăn phổ biến mà bạn có thể thích:\n\n"
                f"{response}\n\n"
                "Bạn có thể cho tôi biết bạn thích ăn món gì để tôi có thể gợi ý chính xác hơn."
            )
            
            return message
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy gợi ý món ăn chung: {e}")
            return (
                "Tôi không thể đưa ra gợi ý cụ thể lúc này. Vui lòng cho tôi biết bạn thích ăn món gì "
                "để tôi có thể gợi ý phù hợp hơn."
            )
    
    @staticmethod
    def format_error_message(error: Exception) -> str:
        """
        Định dạng thông báo lỗi thân thiện với người dùng
        
        Args:
            error: Lỗi xảy ra
            
        Returns:
            Chuỗi văn bản chứa thông báo lỗi
        """
        # Phân loại lỗi và trả về thông báo phù hợp
        error_str = str(error).lower()
        
        if "timeout" in error_str or "connection" in error_str:
            return FallbackHandler.handle_api_error()
        elif "location" in error_str:
            return FallbackHandler.handle_no_location()
        elif "criteria" in error_str:
            return FallbackHandler.handle_no_criteria()
        else:
            return (
                "Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại sau.\n\n"
                "Bạn có thể thử lại với các tiêu chí khác hoặc chia sẻ vị trí khác."
            ) 