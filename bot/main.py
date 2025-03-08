import os
import logging
import asyncio
import re  # Thêm thư viện re để xử lý regex
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from llm.main import (
    get_model_response, 
    get_model_response_with_history,
    analyze_conversation_history,
    rank_restaurants_by_criteria,
    generate_food_suggestions,
    client
)
from session.main import SessionManager, ConversationState
from criteria.main import CriteriaProcessor
from location.main import LocationService
from fallback.main import FallbackHandler

# Get environment variables (already loaded in main.py)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MODEL_NAME = os.getenv("MODEL_NAME")

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.ERROR
)
logger = logging.getLogger(__name__)

# Define system message for the AI
SYSTEM_MESSAGE = """Bạn là trợ lý AI giúp gợi ý món ăn dựa trên tiêu chí của người dùng.
Hãy trả lời ngắn gọn, thân thiện và chính xác."""

# Hàm xử lý markdown
def remove_markdown(text):
    """
    Loại bỏ các dấu markdown trong văn bản
    
    Args:
        text: Văn bản cần xử lý
        
    Returns:
        Văn bản đã được xử lý
    """
    # Loại bỏ dấu ** (bold)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    
    # Loại bỏ dấu * (italic)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    # Loại bỏ dấu __ (underline)
    text = re.sub(r'__(.*?)__', r'\1', text)
    
    # Loại bỏ dấu ` (code)
    text = re.sub(r'`(.*?)`', r'\1', text)
    
    # Loại bỏ dấu ~~ (strikethrough)
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    
    return text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý lệnh /start."""
    user = update.effective_user
    user_id = str(user.id)
    
    # Khởi tạo phiên mới và đặt trạng thái về IDLE
    SessionManager.reset_state(user_id)
    
    # Lưu tin nhắn vào lịch sử
    SessionManager.add_bot_message(user_id, f"Xin chào {user.first_name}! Tôi là trợ lý AI giúp bạn tìm món ăn phù hợp.")
    
    welcome_message = (
        f"Xin chào {user.first_name}! Tôi là trợ lý AI giúp bạn tìm món ăn phù hợp.\n\n"
        "Bạn có thể hỏi tôi về việc gợi ý món ăn hoặc tìm quán ăn phù hợp với sở thích của bạn."
    )
    
    # Tạo nút gợi ý món ăn
    suggestion_button = KeyboardButton("Gợi ý món ăn")
    reply_markup = ReplyKeyboardMarkup([[suggestion_button]], resize_keyboard=True)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý lệnh /help."""
    user_id = str(update.effective_user.id)
    
    help_message = (
        "Tôi là trợ lý AI giúp bạn tìm món ăn phù hợp. Đây là cách sử dụng:\n\n"
        "1. Hỏi tôi về việc gợi ý món ăn hoặc tìm quán ăn\n"
        "2. Nhập các tiêu chí món ăn (ví dụ: nướng, cay, hải sản...)\n"
        "3. Xác nhận tiêu chí bằng cách nhắn 'xác nhận'\n"
        "4. Chia sẻ vị trí của bạn\n"
        "5. Nhận gợi ý món ăn phù hợp\n\n"
        "Bạn có thể nhắn /reset để bắt đầu lại quá trình tìm kiếm."
    )
    
    # Lưu tin nhắn vào lịch sử
    SessionManager.add_bot_message(user_id, help_message)
    
    await update.message.reply_text(help_message)

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Đặt lại trạng thái hội thoại."""
    user_id = str(update.effective_user.id)
    
    # Đặt lại trạng thái về IDLE
    SessionManager.reset_state(user_id)
    
    reset_message = "Đã đặt lại quá trình tìm kiếm. Bạn có thể hỏi tôi về việc gợi ý món ăn bất cứ lúc nào."
    
    # Lưu tin nhắn vào lịch sử
    SessionManager.add_bot_message(user_id, reset_message)
    
    # Tạo nút gợi ý món ăn
    suggestion_button = KeyboardButton("Gợi ý món ăn")
    reply_markup = ReplyKeyboardMarkup([[suggestion_button]], resize_keyboard=True)
    
    await update.message.reply_text(reset_message, reply_markup=reply_markup)

def is_food_suggestion_request(message: str) -> bool:
    """
    Sử dụng Gemini để xác định xem tin nhắn có phải là yêu cầu gợi ý món ăn không.
    
    Args:
        message: Tin nhắn của người dùng
        
    Returns:
        True nếu là yêu cầu gợi ý món ăn, False nếu không
    """
    try:
        # Xây dựng prompt cho Gemini
        system_message = """Bạn là trợ lý AI phân tích ý định của người dùng.
Nhiệm vụ của bạn là xác định xem tin nhắn của người dùng có phải là yêu cầu gợi ý món ăn hoặc tìm quán ăn không.
Chỉ trả về "yes" nếu người dùng đang hỏi về việc gợi ý món ăn, tìm quán ăn, hoặc muốn biết nên ăn gì.
Trả về "no" cho tất cả các trường hợp khác."""
        
        user_message = f"Tin nhắn của người dùng: '{message}'\nĐây có phải là yêu cầu gợi ý món ăn hoặc tìm quán ăn không? Chỉ trả lời 'yes' hoặc 'no'."
        
        # Gọi Gemini để phân tích
        response = get_model_response(client, system_message, user_message).strip().lower()
        
        # Kiểm tra kết quả
        return "yes" in response
        
    except Exception as e:
        logger.error(f"Lỗi khi gọi Gemini để phân tích ý định: {e}")
        # Fallback: sử dụng phương pháp đơn giản
        food_keywords = ["gợi ý món ăn", "tìm món ăn", "món ăn", "ăn gì", "đề xuất món", "quán ăn", "nhà hàng"]
        return any(keyword in message.lower() for keyword in food_keywords)

async def send_typing_action(update: Update) -> None:
    """
    Hiển thị trạng thái 'đang nhập' để cải thiện trải nghiệm người dùng
    
    Args:
        update: Update từ Telegram
    """
    try:
        await update.effective_chat.send_chat_action(action="typing")
    except Exception as e:
        logger.error(f"Lỗi khi gửi trạng thái đang nhập: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý tin nhắn của người dùng dựa trên trạng thái hội thoại."""
    try:
        # Lấy thông tin người dùng và tin nhắn
        user = update.effective_user
        user_id = str(user.id)
        user_message = update.message.text
        
        # Lưu tin nhắn của người dùng vào lịch sử
        SessionManager.add_user_message(user_id, user_message)
        
        # Lấy trạng thái hiện tại của người dùng
        current_state = SessionManager.get_state(user_id)
        
        # Kiểm tra nếu tin nhắn là "Gợi ý món ăn"
        if user_message == "Gợi ý món ăn":
            # Đặt lại trạng thái về IDLE
            SessionManager.reset_state(user_id)
            
            # Tạo phiên mới
            session_id = SessionManager.get_or_create_session(user_id)
            
            # Thông báo bắt đầu quá trình gợi ý món ăn
            start_message = "Hãy cho tôi biết bạn muốn ăn gì? Bạn có thể nhập các tiêu chí như: nướng, cay, hải sản..."
            
            # Lưu tin nhắn vào lịch sử
            SessionManager.add_bot_message(user_id, start_message)
            
            # Chuyển sang trạng thái thu thập tiêu chí
            SessionManager.set_state(user_id, ConversationState.COLLECTING_CRITERIA)
            
            # Tạo nút hủy
            cancel_button = KeyboardButton("Hủy")
            reply_markup = ReplyKeyboardMarkup([[cancel_button]], resize_keyboard=True)
            
            await update.message.reply_text(start_message, reply_markup=reply_markup)
            return
        
        # Kiểm tra xem người dùng có đang yêu cầu gợi ý món ăn không
        if current_state == ConversationState.IDLE and is_food_suggestion_request(user_message):
            # Đặt lại trạng thái và tạo phiên mới để bắt đầu flow gợi ý món ăn
            SessionManager.reset_state(user_id)
            session_id = SessionManager.get_or_create_session(user_id)
            
            # Trích xuất tiêu chí từ tin nhắn ban đầu
            initial_criteria = CriteriaProcessor.extract_criteria_from_message(user_message)
            
            # Nếu đã có tiêu chí trong tin nhắn ban đầu, chuyển thẳng sang trạng thái xác nhận
            if initial_criteria:
                # Chuyển sang trạng thái xác nhận tiêu chí
                SessionManager.set_state(user_id, ConversationState.CONFIRMING_CRITERIA, initial_criteria)
                
                # Lấy lịch sử hội thoại
                conversation_history = SessionManager.get_formatted_history(user_id)
                
                # Gợi ý thêm tiêu chí nếu cần
                suggested_criteria = []
                if len(initial_criteria) < 3:
                    suggested_criteria = CriteriaProcessor.generate_criteria_suggestions(
                        initial_criteria, 
                        conversation_history,
                        max_suggestions=2
                    )
                
                # Định dạng tiêu chí để xác nhận, kèm theo gợi ý (nhưng không thêm vào danh sách tiêu chí)
                confirmation_message = CriteriaProcessor.format_criteria_for_confirmation(initial_criteria, suggested_criteria)
                
                # Lưu tin nhắn vào lịch sử
                SessionManager.add_bot_message(user_id, confirmation_message)
                
                # Tạo nút xác nhận và hủy
                confirm_button = KeyboardButton("Xác nhận")
                cancel_button = KeyboardButton("Hủy")
                reply_markup = ReplyKeyboardMarkup([[confirm_button, cancel_button]], resize_keyboard=True)
                
                # Xử lý markdown trước khi gửi
                confirmation_message = remove_markdown(confirmation_message)
                
                await update.message.reply_text(confirmation_message, reply_markup=reply_markup)
                return
            else:
                # Nếu không có tiêu chí, chuyển sang trạng thái thu thập tiêu chí
                SessionManager.set_state(user_id, ConversationState.COLLECTING_CRITERIA)
                
                # Tạo thông báo yêu cầu tiêu chí
                criteria_prompt = "Hãy cho tôi biết bạn muốn ăn gì? Bạn có thể nhập các tiêu chí như: nướng, cay, hải sản..."
                
                # Lưu tin nhắn vào lịch sử
                SessionManager.add_bot_message(user_id, criteria_prompt)
                
                # Tạo nút hủy
                cancel_button = KeyboardButton("Hủy")
                reply_markup = ReplyKeyboardMarkup([[cancel_button]], resize_keyboard=True)
                
                await update.message.reply_text(criteria_prompt, reply_markup=reply_markup)
                return
        
        # Kiểm tra nếu người dùng muốn hủy quá trình
        if user_message.lower() == "hủy" and current_state != ConversationState.IDLE:
            # Đặt lại trạng thái về IDLE
            SessionManager.reset_state(user_id)
            
            cancel_message = "Đã hủy quá trình tìm kiếm. Bạn có thể hỏi tôi về việc gợi ý món ăn bất cứ lúc nào."
            
            # Lưu tin nhắn vào lịch sử
            SessionManager.add_bot_message(user_id, cancel_message)
            
            # Tạo nút gợi ý món ăn
            suggestion_button = KeyboardButton("Gợi ý món ăn")
            reply_markup = ReplyKeyboardMarkup([[suggestion_button]], resize_keyboard=True)
            
            await update.message.reply_text(cancel_message, reply_markup=reply_markup)
            return
        
        # Xử lý các trạng thái khác nhau của hội thoại
        if current_state == ConversationState.COLLECTING_CRITERIA:
            # Trích xuất tiêu chí từ tin nhắn
            extracted_criteria = CriteriaProcessor.extract_criteria_from_message(user_message)
            
            # Lấy tiêu chí hiện có (nếu có)
            current_criteria = SessionManager.get_criteria(user_id) or []
            
            # Thêm tiêu chí mới vào danh sách
            updated_criteria = current_criteria + [c for c in extracted_criteria if c not in current_criteria]
            
            # Cập nhật trạng thái với tiêu chí mới
            SessionManager.set_state(user_id, ConversationState.CONFIRMING_CRITERIA, updated_criteria)
            
            # Lấy lịch sử hội thoại
            conversation_history = SessionManager.get_formatted_history(user_id)
            
            # Gợi ý thêm tiêu chí nếu cần
            suggested_criteria = []
            if len(updated_criteria) < 3:
                suggested_criteria = CriteriaProcessor.generate_criteria_suggestions(
                    updated_criteria, 
                    conversation_history,
                    max_suggestions=2
                )
            
            # Định dạng tiêu chí để xác nhận, kèm theo gợi ý (nhưng không thêm vào danh sách tiêu chí)
            confirmation_message = CriteriaProcessor.format_criteria_for_confirmation(updated_criteria, suggested_criteria)
            
            # Lưu tin nhắn vào lịch sử
            SessionManager.add_bot_message(user_id, confirmation_message)
            
            # Tạo nút xác nhận và hủy
            confirm_button = KeyboardButton("Xác nhận")
            cancel_button = KeyboardButton("Hủy")
            reply_markup = ReplyKeyboardMarkup([[confirm_button, cancel_button]], resize_keyboard=True)
            
            # Xử lý markdown trước khi gửi
            confirmation_message = remove_markdown(confirmation_message)
            
            await update.message.reply_text(confirmation_message, reply_markup=reply_markup)
            return
        elif current_state == ConversationState.CONFIRMING_CRITERIA:
            # Lấy tiêu chí hiện có
            current_criteria = SessionManager.get_criteria(user_id) or []
            
            # Kiểm tra xem người dùng có xác nhận không
            if CriteriaProcessor.is_confirmation_message(user_message):
                # Nếu không có tiêu chí nào, yêu cầu người dùng nhập lại
                if not current_criteria:
                    no_criteria_message = "Bạn chưa cung cấp tiêu chí nào. Vui lòng nhập tiêu chí để tôi có thể gợi ý món ăn phù hợp."
                    
                    # Lưu tin nhắn vào lịch sử
                    SessionManager.add_bot_message(user_id, no_criteria_message)
                    
                    # Tạo nút hủy
                    cancel_button = KeyboardButton("Hủy")
                    reply_markup = ReplyKeyboardMarkup([[cancel_button]], resize_keyboard=True)
                    
                    await update.message.reply_text(no_criteria_message, reply_markup=reply_markup)
                    return
                
                # Chuyển sang trạng thái chờ vị trí
                SessionManager.set_state(user_id, ConversationState.WAITING_FOR_LOCATION, current_criteria)
                
                # Tạo nút chia sẻ vị trí và hủy
                location_button = KeyboardButton("Chia sẻ vị trí", request_location=True)
                cancel_button = KeyboardButton("Hủy")
                reply_markup = ReplyKeyboardMarkup([[location_button], [cancel_button]], resize_keyboard=True)
                
                location_message = "Vui lòng chia sẻ vị trí của bạn để tôi có thể tìm quán ăn gần đó."
                
                # Lưu tin nhắn vào lịch sử
                SessionManager.add_bot_message(user_id, location_message)
                
                await update.message.reply_text(location_message, reply_markup=reply_markup)
                return
            else:
                # Nếu không phải xác nhận, xử lý như tin nhắn thông thường
                # Trích xuất tiêu chí từ tin nhắn
                extracted_criteria = CriteriaProcessor.extract_criteria_from_message(user_message)
                
                # Nếu không tìm thấy tiêu chí nào, yêu cầu người dùng nhập lại
                if not extracted_criteria:
                    no_criteria_message = "Tôi không thể xác định tiêu chí từ tin nhắn của bạn. Vui lòng nhập tiêu chí cụ thể (ví dụ: nướng, cay, hải sản...)."
                    
                    # Lưu tin nhắn vào lịch sử
                    SessionManager.add_bot_message(user_id, no_criteria_message)
                    
                    # Tạo nút hủy
                    cancel_button = KeyboardButton("Hủy")
                    reply_markup = ReplyKeyboardMarkup([[cancel_button]], resize_keyboard=True)
                    
                    await update.message.reply_text(no_criteria_message, reply_markup=reply_markup)
                    return
                
                # Thêm tiêu chí mới vào danh sách
                updated_criteria = current_criteria + [c for c in extracted_criteria if c not in current_criteria]
                
                # Cập nhật trạng thái với tiêu chí mới
                SessionManager.set_state(user_id, ConversationState.CONFIRMING_CRITERIA, updated_criteria)
                
                # Lấy lịch sử hội thoại
                conversation_history = SessionManager.get_formatted_history(user_id)
                
                # Gợi ý thêm tiêu chí nếu cần
                suggested_criteria = []
                if len(updated_criteria) < 3:
                    suggested_criteria = CriteriaProcessor.generate_criteria_suggestions(
                        updated_criteria, 
                        conversation_history,
                        max_suggestions=2
                    )
                
                # Định dạng tiêu chí để xác nhận, kèm theo gợi ý (nhưng không thêm vào danh sách tiêu chí)
                confirmation_message = CriteriaProcessor.format_criteria_for_confirmation(updated_criteria, suggested_criteria)
                
                # Lưu tin nhắn vào lịch sử
                SessionManager.add_bot_message(user_id, confirmation_message)
                
                # Tạo nút xác nhận và hủy
                confirm_button = KeyboardButton("Xác nhận")
                cancel_button = KeyboardButton("Hủy")
                reply_markup = ReplyKeyboardMarkup([[confirm_button, cancel_button]], resize_keyboard=True)
                
                # Xử lý markdown trước khi gửi
                confirmation_message = remove_markdown(confirmation_message)
                
                await update.message.reply_text(confirmation_message, reply_markup=reply_markup)
                return
        elif current_state == ConversationState.WAITING_FOR_LOCATION:
            # Kiểm tra xem tin nhắn có chứa vị trí không
            if update.message.location:
                # Lấy vị trí từ tin nhắn
                latitude = update.message.location.latitude
                longitude = update.message.location.longitude
                
                # Lấy tiêu chí hiện có
                current_criteria = SessionManager.get_criteria(user_id) or []
                
                # Chuyển sang trạng thái xử lý
                SessionManager.set_state(user_id, ConversationState.PROCESSING, current_criteria, (latitude, longitude))
                
                # Hiển thị trạng thái "đang nhập" để cải thiện trải nghiệm người dùng
                await send_typing_action(update)
                
                # Thông báo đang xử lý
                processing_message = "Đang tìm kiếm quán ăn phù hợp với tiêu chí của bạn..."
                
                # Lưu tin nhắn vào lịch sử
                SessionManager.add_bot_message(user_id, processing_message)
                
                await update.message.reply_text(processing_message)
                
                # Tìm kiếm quán ăn gần vị trí
                restaurants = LocationService.search_restaurants_by_coordinates(latitude, longitude, current_criteria)
                
                # Nếu tìm thấy quán ăn
                if restaurants:
                    # Xếp hạng quán ăn dựa trên tiêu chí
                    ranked_restaurants = rank_restaurants_by_criteria(restaurants, current_criteria)
                    
                    # Lấy top 3 quán ăn
                    top_restaurants = ranked_restaurants[:3]
                    
                    # Định dạng kết quả
                    result_message = LocationService.format_restaurant_results(top_restaurants, current_criteria)
                    
                    # Lưu tin nhắn vào lịch sử
                    SessionManager.add_bot_message(user_id, result_message)
                    
                    # Tạo nút gợi ý món ăn
                    suggestion_button = KeyboardButton("Gợi ý món ăn")
                    reply_markup = ReplyKeyboardMarkup([[suggestion_button]], resize_keyboard=True)
                    
                    # Xử lý markdown trước khi gửi
                    result_message = remove_markdown(result_message)
                    
                    await update.message.reply_text(result_message, reply_markup=reply_markup)
                else:
                    # Không tìm thấy quán ăn, sử dụng fallback
                    fallback_message = FallbackHandler.handle_no_restaurants(current_criteria)
                    
                    # Lưu tin nhắn vào lịch sử
                    SessionManager.add_bot_message(user_id, fallback_message)
                    
                    # Tạo nút gợi ý món ăn
                    suggestion_button = KeyboardButton("Gợi ý món ăn")
                    reply_markup = ReplyKeyboardMarkup([[suggestion_button]], resize_keyboard=True)
                    
                    # Xử lý markdown trước khi gửi
                    fallback_message = remove_markdown(fallback_message)
                    
                    await update.message.reply_text(fallback_message, reply_markup=reply_markup)
                
                # Đặt lại trạng thái về IDLE sau khi hoàn thành
                SessionManager.reset_state(user_id)
                return
            else:
                # Nếu không có vị trí, yêu cầu người dùng chia sẻ vị trí
                location_reminder = "Vui lòng chia sẻ vị trí của bạn bằng cách nhấn nút 'Chia sẻ vị trí'."
                
                # Lưu tin nhắn vào lịch sử
                SessionManager.add_bot_message(user_id, location_reminder)
                
                # Tạo nút chia sẻ vị trí và hủy
                location_button = KeyboardButton("Chia sẻ vị trí", request_location=True)
                cancel_button = KeyboardButton("Hủy")
                reply_markup = ReplyKeyboardMarkup([[location_button], [cancel_button]], resize_keyboard=True)
                
                await update.message.reply_text(location_reminder, reply_markup=reply_markup)
                return
        else:
            # Nếu không ở trong flow gợi ý món ăn, sử dụng Gemini để trả lời tin nhắn thông thường
            # Hiển thị trạng thái "đang nhập" để cải thiện trải nghiệm người dùng
            await send_typing_action(update)
            
            # Lấy lịch sử hội thoại
            conversation_history = SessionManager.get_formatted_history(user_id)
            
            # Gọi Gemini để trả lời
            response = get_model_response_with_history(client, SYSTEM_MESSAGE, conversation_history, user_message)
            
            # Lưu tin nhắn vào lịch sử
            SessionManager.add_bot_message(user_id, response)
            
            # Tạo nút gợi ý món ăn
            suggestion_button = KeyboardButton("Gợi ý món ăn")
            reply_markup = ReplyKeyboardMarkup([[suggestion_button]], resize_keyboard=True)
            
            # Xử lý markdown trước khi gửi
            response = remove_markdown(response)
            
            await update.message.reply_text(response, reply_markup=reply_markup)
            return
    except Exception as e:
        logger.error(f"Lỗi khi xử lý tin nhắn: {e}")
        await handle_error(update, context, e)

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý khi người dùng chia sẻ vị trí."""
    try:
        # Lấy thông tin người dùng và vị trí
        user = update.effective_user
        user_id = str(user.id)
        location = update.message.location
        
        # Lấy trạng thái hiện tại của người dùng
        current_state = SessionManager.get_state(user_id)
        
        # Chỉ xử lý nếu đang ở trạng thái chờ vị trí
        if current_state == ConversationState.WAITING_FOR_LOCATION:
            # Lấy vị trí từ tin nhắn
            latitude = location.latitude
            longitude = location.longitude
            
            # Lấy tiêu chí hiện có
            current_criteria = SessionManager.get_criteria(user_id) or []
            
            # Chuyển sang trạng thái xử lý
            SessionManager.set_state(user_id, ConversationState.PROCESSING, current_criteria, (latitude, longitude))
            
            # Hiển thị trạng thái "đang nhập" để cải thiện trải nghiệm người dùng
            await send_typing_action(update)
            
            # Thông báo đang xử lý
            processing_message = "Đang tìm kiếm quán ăn phù hợp với tiêu chí của bạn..."
            
            # Lưu tin nhắn vào lịch sử
            SessionManager.add_bot_message(user_id, processing_message)
            
            await update.message.reply_text(processing_message)
            
            # Tìm kiếm quán ăn gần vị trí
            restaurants = LocationService.search_restaurants_by_coordinates(latitude, longitude, current_criteria)
            
            # Nếu tìm thấy quán ăn
            if restaurants:
                # Xếp hạng quán ăn dựa trên tiêu chí
                ranked_restaurants = rank_restaurants_by_criteria(restaurants, current_criteria)
                
                # Lấy top 3 quán ăn
                top_restaurants = ranked_restaurants[:3]
                
                # Định dạng kết quả
                result_message = LocationService.format_restaurant_results(top_restaurants, current_criteria)
                
                # Lưu tin nhắn vào lịch sử
                SessionManager.add_bot_message(user_id, result_message)
                
                # Tạo nút gợi ý món ăn
                suggestion_button = KeyboardButton("Gợi ý món ăn")
                reply_markup = ReplyKeyboardMarkup([[suggestion_button]], resize_keyboard=True)
                
                # Xử lý markdown trước khi gửi
                result_message = remove_markdown(result_message)
                
                await update.message.reply_text(result_message, reply_markup=reply_markup)
            else:
                # Không tìm thấy quán ăn, sử dụng fallback
                fallback_message = FallbackHandler.handle_no_restaurants(current_criteria)
                
                # Lưu tin nhắn vào lịch sử
                SessionManager.add_bot_message(user_id, fallback_message)
                
                # Tạo nút gợi ý món ăn
                suggestion_button = KeyboardButton("Gợi ý món ăn")
                reply_markup = ReplyKeyboardMarkup([[suggestion_button]], resize_keyboard=True)
                
                # Xử lý markdown trước khi gửi
                fallback_message = remove_markdown(fallback_message)
                
                await update.message.reply_text(fallback_message, reply_markup=reply_markup)
            
            # Đặt lại trạng thái về IDLE sau khi hoàn thành
            SessionManager.reset_state(user_id)
    except Exception as e:
        logger.error(f"Lỗi khi xử lý vị trí: {e}")
        await handle_error(update, context, e)

async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception = None) -> None:
    """Xử lý lỗi và gửi thông báo lỗi đến người dùng."""
    try:
        # Lấy thông tin người dùng
        user = update.effective_user
        user_id = str(user.id)
        
        # Sử dụng FallbackHandler để định dạng thông báo lỗi
        error_message = FallbackHandler.format_error_message(error)
        
        # Lưu tin nhắn vào lịch sử
        SessionManager.add_bot_message(user_id, error_message)
        
        # Đặt lại trạng thái về IDLE
        SessionManager.reset_state(user_id)
        
        # Tạo nút gợi ý món ăn
        suggestion_button = KeyboardButton("Gợi ý món ăn")
        reply_markup = ReplyKeyboardMarkup([[suggestion_button]], resize_keyboard=True)
        
        # Xử lý markdown trước khi gửi
        error_message = remove_markdown(error_message)
        
        await update.message.reply_text(error_message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Lỗi khi xử lý lỗi: {e}")

def run_bot() -> None:
    """Khởi động bot."""
    # Tạo ứng dụng
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Thêm các handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Chạy bot cho đến khi người dùng nhấn Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    run_bot()
