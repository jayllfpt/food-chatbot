import sqlite3
import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Đường dẫn đến file database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'food_chatbot.db')

def get_connection():
    """Tạo và trả về kết nối đến cơ sở dữ liệu SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Để kết quả truy vấn có thể truy cập bằng tên cột
    return conn

def init_database():
    """Khởi tạo cơ sở dữ liệu và các bảng cần thiết nếu chưa tồn tại"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tạo bảng sessions để lưu trữ thông tin phiên
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        last_updated TEXT NOT NULL
    )
    ''')
    
    # Tạo bảng messages để lưu trữ lịch sử tin nhắn
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        message_id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions (session_id)
    )
    ''')
    
    # Tạo bảng user_states để lưu trữ trạng thái của người dùng
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_states (
        user_id TEXT PRIMARY KEY,
        current_state TEXT NOT NULL,
        criteria TEXT,
        location TEXT,
        last_updated TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()

def create_session(user_id: str) -> str:
    """Tạo một phiên mới cho người dùng và trả về session_id"""
    conn = get_connection()
    cursor = conn.cursor()
    
    session_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    cursor.execute(
        "INSERT INTO sessions (session_id, user_id, created_at, last_updated) VALUES (?, ?, ?, ?)",
        (session_id, user_id, now, now)
    )
    
    conn.commit()
    conn.close()
    
    return session_id

def get_active_session(user_id: str) -> Optional[str]:
    """Lấy phiên hoạt động gần nhất của người dùng"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT session_id FROM sessions WHERE user_id = ? ORDER BY last_updated DESC LIMIT 1",
        (user_id,)
    )
    
    result = cursor.fetchone()
    conn.close()
    
    return result['session_id'] if result else None

def add_message(session_id: str, user_id: str, role: str, content: str) -> str:
    """Thêm tin nhắn mới vào lịch sử hội thoại"""
    conn = get_connection()
    cursor = conn.cursor()
    
    message_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    # Thêm tin nhắn vào bảng messages
    cursor.execute(
        "INSERT INTO messages (message_id, session_id, user_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (message_id, session_id, user_id, role, content, now)
    )
    
    # Cập nhật thời gian last_updated của phiên
    cursor.execute(
        "UPDATE sessions SET last_updated = ? WHERE session_id = ?",
        (now, session_id)
    )
    
    conn.commit()
    conn.close()
    
    return message_id

def get_session_messages(session_id: str) -> List[Dict[str, Any]]:
    """Lấy tất cả tin nhắn trong một phiên"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
        (session_id,)
    )
    
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return messages

def get_user_state(user_id: str) -> Optional[Dict[str, Any]]:
    """Lấy trạng thái hiện tại của người dùng"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM user_states WHERE user_id = ?",
        (user_id,)
    )
    
    result = cursor.fetchone()
    conn.close()
    
    return dict(result) if result else None

def set_user_state(user_id: str, state: str, criteria: Optional[List[str]] = None, location: Optional[Tuple[float, float]] = None) -> None:
    """Cập nhật trạng thái của người dùng"""
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    criteria_json = json.dumps(criteria) if criteria else None
    location_json = json.dumps(location) if location else None
    
    # Kiểm tra xem người dùng đã có trong bảng user_states chưa
    cursor.execute(
        "SELECT user_id FROM user_states WHERE user_id = ?",
        (user_id,)
    )
    
    if cursor.fetchone():
        # Cập nhật trạng thái nếu người dùng đã tồn tại
        cursor.execute(
            "UPDATE user_states SET current_state = ?, criteria = ?, location = ?, last_updated = ? WHERE user_id = ?",
            (state, criteria_json, location_json, now, user_id)
        )
    else:
        # Thêm mới nếu người dùng chưa tồn tại
        cursor.execute(
            "INSERT INTO user_states (user_id, current_state, criteria, location, last_updated) VALUES (?, ?, ?, ?, ?)",
            (user_id, state, criteria_json, location_json, now)
        )
    
    conn.commit()
    conn.close()

def clear_user_state(user_id: str) -> None:
    """Xóa trạng thái của người dùng"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "DELETE FROM user_states WHERE user_id = ?",
        (user_id,)
    )
    
    conn.commit()
    conn.close()

 