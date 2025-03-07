import json
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from database.main import (
    get_active_session,
    create_session,
    add_message,
    get_session_messages,
    get_user_state,
    set_user_state,
    clear_user_state
)

# Định nghĩa các trạng thái hội thoại
class ConversationState(str, Enum):
    IDLE = "IDLE"  # Trạng thái ban đầu
    COLLECTING_CRITERIA = "COLLECTING_CRITERIA"  # Đang thu thập tiêu chí món ăn
    CONFIRMING_CRITERIA = "CONFIRMING_CRITERIA"  # Đang xác nhận tiêu chí
    WAITING_FOR_LOCATION = "WAITING_FOR_LOCATION"  # Đang chờ vị trí
    PROCESSING = "PROCESSING"  # Đang xử lý yêu cầu
    SUGGESTING = "SUGGESTING"  # Đang đưa ra gợi ý

class SessionManager:
    """Quản lý phiên hội thoại và trạng thái của người dùng"""
    
    @staticmethod
    def get_or_create_session(user_id: str) -> str:
        """Lấy phiên hiện tại hoặc tạo phiên mới nếu chưa có"""
        session_id = get_active_session(user_id)
        if not session_id:
            session_id = create_session(user_id)
        return session_id
    
    @staticmethod
    def add_user_message(user_id: str, content: str) -> None:
        """Thêm tin nhắn của người dùng vào lịch sử hội thoại"""
        session_id = SessionManager.get_or_create_session(user_id)
        add_message(session_id, user_id, "user", content)
    
    @staticmethod
    def add_bot_message(user_id: str, content: str) -> None:
        """Thêm tin nhắn của bot vào lịch sử hội thoại"""
        session_id = SessionManager.get_or_create_session(user_id)
        add_message(session_id, user_id, "bot", content)
    
    @staticmethod
    def get_conversation_history(user_id: str) -> List[Dict[str, Any]]:
        """Lấy lịch sử hội thoại của người dùng"""
        session_id = SessionManager.get_or_create_session(user_id)
        return get_session_messages(session_id)
    
    @staticmethod
    def get_formatted_history(user_id: str) -> List[Dict[str, str]]:
        """Lấy lịch sử hội thoại định dạng phù hợp cho LLM"""
        history = SessionManager.get_conversation_history(user_id)
        formatted_history = []
        
        for message in history:
            role = "user" if message["role"] == "user" else "assistant"
            formatted_history.append({
                "role": role,
                "content": message["content"]
            })
        
        return formatted_history
    
    @staticmethod
    def get_state(user_id: str) -> ConversationState:
        """Lấy trạng thái hiện tại của người dùng"""
        state_data = get_user_state(user_id)
        if not state_data:
            # Nếu chưa có trạng thái, thiết lập trạng thái mặc định là IDLE
            SessionManager.set_state(user_id, ConversationState.IDLE)
            return ConversationState.IDLE
        
        return ConversationState(state_data["current_state"])
    
    @staticmethod
    def set_state(user_id: str, state: ConversationState, criteria: Optional[List[str]] = None, location: Optional[Tuple[float, float]] = None) -> None:
        """Cập nhật trạng thái của người dùng"""
        set_user_state(user_id, state.value, criteria, location)
    
    @staticmethod
    def get_criteria(user_id: str) -> Optional[List[str]]:
        """Lấy tiêu chí món ăn của người dùng"""
        state_data = get_user_state(user_id)
        if not state_data or not state_data["criteria"]:
            return None
        
        return json.loads(state_data["criteria"])
    
    @staticmethod
    def get_location(user_id: str) -> Optional[Tuple[float, float]]:
        """Lấy vị trí của người dùng"""
        state_data = get_user_state(user_id)
        if not state_data or not state_data["location"]:
            return None
        
        return tuple(json.loads(state_data["location"]))
    
    @staticmethod
    def reset_state(user_id: str) -> None:
        """Đặt lại trạng thái của người dùng về IDLE"""
        SessionManager.set_state(user_id, ConversationState.IDLE)
    
    @staticmethod
    def clear_state(user_id: str) -> None:
        """Xóa hoàn toàn trạng thái của người dùng"""
        clear_user_state(user_id) 