import os
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash")

# Initialize OpenAI client
client = OpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

def get_model_response(client, system_message, user_message):
    """
    Get response from the model using the provided client and messages.
    
    Args:
        client: OpenAI client instance
        system_message (str): System message to set model behavior
        user_message (str): User's input message
    
    Returns:
        str: Model's response content
    """
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Error getting model response: {e}")
        return "Xin lỗi, tôi đang gặp sự cố khi xử lý yêu cầu của bạn. Vui lòng thử lại sau."

def get_model_response_with_history(client, system_message, conversation_history, user_message):
    """
    Get response from the model using the provided client, conversation history, and messages.
    
    Args:
        client: OpenAI client instance
        system_message (str): System message to set model behavior
        conversation_history (List[Dict]): List of previous messages
        user_message (str): User's input message
    
    Returns:
        str: Model's response content
    """
    try:
        # Prepare messages with conversation history
        messages = [{"role": "system", "content": system_message}]
        
        # Add conversation history
        for message in conversation_history:
            messages.append(message)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Get completion
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Error getting model response with history: {e}")
        return "Xin lỗi, tôi đang gặp sự cố khi xử lý yêu cầu của bạn. Vui lòng thử lại sau."

def analyze_conversation_history(conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Phân tích lịch sử hội thoại để xác định thông tin quan trọng.
    
    Args:
        conversation_history: Lịch sử hội thoại
        
    Returns:
        Dict chứa thông tin phân tích
    """
    try:
        # Xây dựng prompt cho Gemini
        system_message = """Bạn là trợ lý AI phân tích hội thoại.
Nhiệm vụ của bạn là phân tích lịch sử hội thoại và trích xuất thông tin quan trọng.
Hãy trả về kết quả dưới dạng JSON với các trường: mentioned_foods, mentioned_criteria, user_preferences, và conversation_stage."""
        
        # Chuyển đổi lịch sử hội thoại thành văn bản
        conversation_text = ""
        for message in conversation_history:
            role = "User" if message["role"] == "user" else "Bot"
            conversation_text += f"{role}: {message['content']}\n\n"
        
        user_message = f"""Phân tích lịch sử hội thoại sau và trích xuất thông tin quan trọng:

{conversation_text}

Trả về kết quả dưới dạng JSON với các trường:
- mentioned_foods: Danh sách các món ăn được nhắc đến
- mentioned_criteria: Danh sách các tiêu chí món ăn được nhắc đến
- user_preferences: Các sở thích của người dùng
- conversation_stage: Giai đoạn hiện tại của hội thoại (GREETING, COLLECTING_CRITERIA, CONFIRMING_CRITERIA, WAITING_FOR_LOCATION, SUGGESTING)"""
        
        # Gọi Gemini để phân tích
        response = get_model_response(client, system_message, user_message)
        
        # Xử lý kết quả (giả định kết quả là JSON)
        # Trong thực tế, bạn nên thêm xử lý lỗi và parsing JSON ở đây
        import json
        try:
            analysis = json.loads(response)
            return analysis
        except json.JSONDecodeError:
            logger.error(f"Error parsing JSON response: {response}")
            return {
                "mentioned_foods": [],
                "mentioned_criteria": [],
                "user_preferences": {},
                "conversation_stage": "UNKNOWN"
            }
            
    except Exception as e:
        logger.error(f"Error analyzing conversation history: {e}")
        return {
            "mentioned_foods": [],
            "mentioned_criteria": [],
            "user_preferences": {},
            "conversation_stage": "UNKNOWN"
        }

def suggest_additional_criteria(current_criteria: List[str], conversation_history: List[Dict[str, str]], max_suggestions: int = 2) -> List[str]:
    """
    Sử dụng Gemini để gợi ý thêm tiêu chí dựa trên lịch sử hội thoại và tiêu chí hiện có.
    
    Args:
        current_criteria: Danh sách tiêu chí hiện có
        conversation_history: Lịch sử hội thoại
        max_suggestions: Số lượng gợi ý tối đa
        
    Returns:
        Danh sách các tiêu chí được gợi ý thêm
    """
    try:
        # Xây dựng prompt cho Gemini
        system_message = """Bạn là trợ lý AI giúp gợi ý tiêu chí cho món ăn.
Dựa vào các tiêu chí hiện có và lịch sử hội thoại, hãy gợi ý thêm tiêu chí phù hợp.
Chỉ trả về danh sách các tiêu chí, mỗi tiêu chí một dòng, không có giải thích hay định dạng khác."""
        
        # Chuyển đổi lịch sử hội thoại thành văn bản
        conversation_text = ""
        for message in conversation_history:
            role = "User" if message["role"] == "user" else "Bot"
            conversation_text += f"{role}: {message['content']}\n\n"
        
        user_message = f"""Dựa vào lịch sử hội thoại sau:

{conversation_text}

Và các tiêu chí hiện có: {', '.join(current_criteria) if current_criteria else 'Chưa có tiêu chí nào'}

Hãy gợi ý thêm {max_suggestions} tiêu chí phù hợp để tìm kiếm món ăn.
Chỉ trả về danh sách các tiêu chí, mỗi tiêu chí một dòng, không có giải thích hay định dạng khác."""
        
        # Gọi Gemini để gợi ý
        response = get_model_response(client, system_message, user_message)
        
        # Xử lý kết quả
        suggested_criteria = [line.strip() for line in response.strip().split('\n') if line.strip()]
        
        # Giới hạn số lượng gợi ý
        return suggested_criteria[:max_suggestions]
        
    except Exception as e:
        logger.error(f"Error suggesting additional criteria: {e}")
        return []

def rank_restaurants_by_criteria(restaurants: List[Dict[str, Any]], criteria: List[str]) -> List[Dict[str, Any]]:
    """
    Sử dụng Gemini để xếp hạng các quán ăn dựa trên tiêu chí.
    
    Args:
        restaurants: Danh sách quán ăn
        criteria: Danh sách tiêu chí
        
    Returns:
        Danh sách quán ăn đã được xếp hạng
    """
    if not restaurants or len(restaurants) <= 1:
        return restaurants
    
    try:
        # Xây dựng prompt cho Gemini
        system_message = """Bạn là trợ lý AI giúp xếp hạng các quán ăn dựa trên tiêu chí.
Nhiệm vụ của bạn là phân tích thông tin các quán ăn và xếp hạng chúng dựa trên mức độ phù hợp với tiêu chí.
Hãy trả về danh sách các ID quán ăn theo thứ tự từ phù hợp nhất đến ít phù hợp nhất, mỗi ID một dòng."""
        
        # Chuẩn bị thông tin quán ăn
        restaurants_info = ""
        for i, restaurant in enumerate(restaurants):
            restaurants_info += f"ID: {i}\n"
            restaurants_info += f"Tên: {restaurant.get('name', 'Không có tên')}\n"
            restaurants_info += f"Loại: {restaurant.get('type', 'Không xác định')}\n"
            restaurants_info += f"Ẩm thực: {restaurant.get('cuisine', 'Không xác định')}\n"
            restaurants_info += f"Địa chỉ: {restaurant.get('address', 'Không có địa chỉ')}\n"
            restaurants_info += f"Khoảng cách: {restaurant.get('distance', 'Không xác định')} mét\n"
            if restaurant.get('opening_hours'):
                restaurants_info += f"Giờ mở cửa: {restaurant['opening_hours']}\n"
            restaurants_info += "\n"
        
        user_message = f"""Dựa vào danh sách quán ăn sau:

{restaurants_info}

Và các tiêu chí: {', '.join(criteria)}

Hãy xếp hạng các quán ăn dựa trên mức độ phù hợp với tiêu chí.
Chỉ trả về danh sách các ID quán ăn theo thứ tự từ phù hợp nhất đến ít phù hợp nhất, mỗi ID một dòng."""
        
        # Gọi Gemini để xếp hạng
        response = get_model_response(client, system_message, user_message)
        
        # Xử lý kết quả
        ranked_ids = []
        for line in response.strip().split('\n'):
            try:
                # Trích xuất ID từ mỗi dòng
                id_str = line.strip()
                # Loại bỏ các ký tự không phải số
                id_str = ''.join(c for c in id_str if c.isdigit())
                if id_str:
                    ranked_ids.append(int(id_str))
            except ValueError:
                continue
        
        # Lọc các ID hợp lệ
        valid_ids = [i for i in ranked_ids if 0 <= i < len(restaurants)]
        
        # Thêm các ID còn lại nếu có
        for i in range(len(restaurants)):
            if i not in valid_ids:
                valid_ids.append(i)
        
        # Xếp hạng quán ăn theo thứ tự ID
        ranked_restaurants = [restaurants[i] for i in valid_ids]
        
        return ranked_restaurants
        
    except Exception as e:
        logger.error(f"Error ranking restaurants: {e}")
        return restaurants

def generate_food_suggestions(criteria: List[str], count: int = 3) -> str:
    """
    Sử dụng Gemini để gợi ý món ăn dựa trên tiêu chí.
    
    Args:
        criteria: Danh sách tiêu chí
        count: Số lượng món ăn cần gợi ý
        
    Returns:
        Chuỗi văn bản chứa gợi ý món ăn
    """
    try:
        # Xây dựng prompt cho Gemini
        system_message = """Bạn là trợ lý AI giúp gợi ý món ăn.
Nhiệm vụ của bạn là gợi ý các món ăn phù hợp với tiêu chí của người dùng.
Hãy cung cấp tên món, mô tả ngắn gọn, và lý do tại sao món đó phù hợp với tiêu chí."""
        
        user_message = f"""Dựa vào các tiêu chí: {', '.join(criteria)}

Hãy gợi ý {count} món ăn phù hợp.
Đối với mỗi món, hãy cung cấp:
1. Tên món
2. Mô tả ngắn gọn
3. Lý do tại sao món đó phù hợp với tiêu chí

Hãy định dạng kết quả rõ ràng và dễ đọc."""
        
        # Gọi Gemini để gợi ý
        response = get_model_response(client, system_message, user_message)
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating food suggestions: {e}")
        return "Xin lỗi, tôi không thể gợi ý món ăn lúc này. Vui lòng thử lại sau."

