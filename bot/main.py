import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from llm.main import get_model_response, client
from session.main import SessionManager, ConversationState
from criteria.main import CriteriaProcessor
from location.main import LocationService

# Get environment variables (already loaded in main.py)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MODEL_NAME = os.getenv("MODEL_NAME")

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define system message for the AI
SYSTEM_MESSAGE = """Bạn là trợ lý AI giúp gợi ý món ăn dựa trên tiêu chí của người dùng.
Hãy trả lời ngắn gọn, thân thiện và chính xác."""

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
    
    await update.message.reply_text(welcome_message)

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
    
    await update.message.reply_text(reset_message)

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý tin nhắn của người dùng dựa trên trạng thái hội thoại."""
    user = update.effective_user
    user_id = str(user.id)
    user_message = update.message.text
    
    # Lưu tin nhắn của người dùng vào lịch sử
    SessionManager.add_user_message(user_id, user_message)
    
    # Lấy trạng thái hiện tại của người dùng
    current_state = SessionManager.get_state(user_id)
    
    try:
        # Kiểm tra xem người dùng có đang yêu cầu gợi ý món ăn không
        if current_state == ConversationState.IDLE and is_food_suggestion_request(user_message):
            # Chuyển sang trạng thái thu thập tiêu chí
            SessionManager.set_state(user_id, ConversationState.COLLECTING_CRITERIA)
            
            criteria_prompt = (
                "Bạn muốn ăn món gì? Bạn có thể nhập tiêu chí như 'khô', 'nước', 'chiên', 'nướng', 'xào' "
                "hoặc bất kỳ tiêu chí nào khác. Bạn có thể nhập nhiều tiêu chí cùng lúc."
            )
            
            # Lưu tin nhắn vào lịch sử
            SessionManager.add_bot_message(user_id, criteria_prompt)
            
            await update.message.reply_text(criteria_prompt)
            return
        
        # Xử lý trạng thái thu thập tiêu chí
        elif current_state == ConversationState.COLLECTING_CRITERIA:
            # Trích xuất tiêu chí từ tin nhắn
            extracted_criteria = CriteriaProcessor.extract_criteria_from_message(user_message)
            
            # Nếu không tìm thấy tiêu chí nào trong tin nhắn, thử phân tích bằng Gemini
            if not extracted_criteria:
                # Thêm tiêu chí tùy chỉnh (coi toàn bộ tin nhắn là một tiêu chí)
                extracted_criteria = [user_message.strip()]
            
            # Lấy tiêu chí hiện có (nếu có)
            current_criteria = SessionManager.get_criteria(user_id) or []
            
            # Thêm tiêu chí mới vào danh sách
            updated_criteria = current_criteria + [c for c in extracted_criteria if c not in current_criteria]
            
            # Cập nhật trạng thái với tiêu chí mới
            SessionManager.set_state(user_id, ConversationState.CONFIRMING_CRITERIA, updated_criteria)
            
            # Định dạng tiêu chí để xác nhận
            confirmation_message = CriteriaProcessor.format_criteria_for_confirmation(updated_criteria)
            
            # Lưu tin nhắn vào lịch sử
            SessionManager.add_bot_message(user_id, confirmation_message)
            
            await update.message.reply_text(confirmation_message)
            return
        
        # Xử lý trạng thái xác nhận tiêu chí
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
                    
                    await update.message.reply_text(no_criteria_message)
                    return
                
                # Chuyển sang trạng thái chờ vị trí
                SessionManager.set_state(user_id, ConversationState.WAITING_FOR_LOCATION, current_criteria)
                
                # Tạo nút chia sẻ vị trí
                location_button = KeyboardButton("Chia sẻ vị trí", request_location=True)
                reply_markup = ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True)
                
                location_request_message = "Tuyệt vời! Bây giờ, vui lòng chia sẻ vị trí của bạn để tôi có thể tìm các quán ăn gần đó."
                
                # Lưu tin nhắn vào lịch sử
                SessionManager.add_bot_message(user_id, location_request_message)
                
                await update.message.reply_text(location_request_message, reply_markup=reply_markup)
                return
            else:
                # Người dùng không xác nhận, tiếp tục thu thập tiêu chí
                # Trích xuất tiêu chí từ tin nhắn
                extracted_criteria = CriteriaProcessor.extract_criteria_from_message(user_message)
                
                # Nếu không tìm thấy tiêu chí nào trong tin nhắn, thử phân tích bằng Gemini
                if not extracted_criteria:
                    # Thêm tiêu chí tùy chỉnh (coi toàn bộ tin nhắn là một tiêu chí)
                    extracted_criteria = [user_message.strip()]
                
                # Thêm tiêu chí mới vào danh sách
                updated_criteria = current_criteria + [c for c in extracted_criteria if c not in current_criteria]
                
                # Cập nhật trạng thái với tiêu chí mới
                SessionManager.set_state(user_id, ConversationState.CONFIRMING_CRITERIA, updated_criteria)
                
                # Định dạng tiêu chí để xác nhận
                confirmation_message = CriteriaProcessor.format_criteria_for_confirmation(updated_criteria)
                
                # Lưu tin nhắn vào lịch sử
                SessionManager.add_bot_message(user_id, confirmation_message)
                
                await update.message.reply_text(confirmation_message)
                return
        
        # Xử lý trạng thái mặc định (IDLE)
        else:
            # Gọi Gemini để trả lời tin nhắn thông thường
            response = get_model_response(client, SYSTEM_MESSAGE, user_message)
            
            # Lưu tin nhắn vào lịch sử
            SessionManager.add_bot_message(user_id, response)
            
            await update.message.reply_text(response)
            return
            
    except Exception as e:
        logger.error(f"Lỗi khi xử lý tin nhắn: {e}")
        error_message = "Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại sau."
        
        # Lưu tin nhắn vào lịch sử
        SessionManager.add_bot_message(user_id, error_message)
        
        await update.message.reply_text(error_message)

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý vị trí được chia sẻ từ người dùng."""
    user = update.effective_user
    user_id = str(user.id)
    location = update.message.location
    
    # Lấy trạng thái hiện tại của người dùng
    current_state = SessionManager.get_state(user_id)
    
    try:
        # Kiểm tra xem người dùng có đang ở trạng thái chờ vị trí không
        if current_state == ConversationState.WAITING_FOR_LOCATION:
            # Lấy tiêu chí hiện có
            current_criteria = SessionManager.get_criteria(user_id) or []
            
            # Lưu vị trí vào trạng thái
            SessionManager.set_state(user_id, ConversationState.PROCESSING, current_criteria, (location.latitude, location.longitude))
            
            # Thông báo đang xử lý
            processing_message = "Đang tìm kiếm quán ăn gần bạn dựa trên tiêu chí đã chọn. Vui lòng đợi trong giây lát..."
            
            # Lưu tin nhắn vào lịch sử
            SessionManager.add_bot_message(user_id, processing_message)
            
            await update.message.reply_text(processing_message)
            
            # Tìm kiếm quán ăn gần vị trí
            restaurants = LocationService.search_restaurants_by_coordinates(location.latitude, location.longitude)
            
            # Chuyển sang trạng thái gợi ý
            SessionManager.set_state(user_id, ConversationState.SUGGESTING, current_criteria, (location.latitude, location.longitude))
            
            if restaurants:
                # Lấy top 3 quán ăn
                top_restaurants = LocationService.get_top_restaurants(restaurants)
                
                # Định dạng kết quả
                result_message = f"Dựa trên tiêu chí của bạn ({', '.join(current_criteria)}), đây là top 3 quán ăn gần bạn:\n\n"
                
                for i, restaurant in enumerate(top_restaurants, 1):
                    result_message += f"#{i}: {LocationService.format_restaurant_info(restaurant)}\n\n"
                
                result_message += "Bạn có thể hỏi tôi về việc gợi ý món ăn bất cứ lúc nào."
                
                # Lưu tin nhắn vào lịch sử
                SessionManager.add_bot_message(user_id, result_message)
                
                await update.message.reply_text(result_message)
            else:
                # Không tìm thấy quán ăn, sử dụng fallback
                fallback_message = (
                    f"Tôi không thể tìm thấy quán ăn nào gần vị trí của bạn dựa trên tiêu chí ({', '.join(current_criteria)}).\n\n"
                    "Tuy nhiên, tôi có thể gợi ý một số món ăn phù hợp với tiêu chí của bạn:\n\n"
                )
                
                # Gọi Gemini để gợi ý món ăn dựa trên tiêu chí
                system_message = """Bạn là trợ lý AI giúp gợi ý món ăn.
Hãy gợi ý 3 món ăn phù hợp với tiêu chí của người dùng.
Đối với mỗi món, hãy cung cấp tên món và mô tả ngắn gọn."""
                
                user_message = f"Gợi ý 3 món ăn phù hợp với các tiêu chí sau: {', '.join(current_criteria)}"
                
                food_suggestions = get_model_response(client, system_message, user_message)
                
                fallback_message += food_suggestions
                fallback_message += "\n\nBạn có thể hỏi tôi về việc gợi ý món ăn bất cứ lúc nào."
                
                # Lưu tin nhắn vào lịch sử
                SessionManager.add_bot_message(user_id, fallback_message)
                
                await update.message.reply_text(fallback_message)
            
            # Đặt lại trạng thái về IDLE
            SessionManager.reset_state(user_id)
            return
        else:
            # Người dùng chia sẻ vị trí khi không ở trạng thái chờ vị trí
            location_message = "Cảm ơn bạn đã chia sẻ vị trí. Nếu bạn muốn tìm món ăn, hãy hỏi tôi về việc gợi ý món ăn."
            
            # Lưu tin nhắn vào lịch sử
            SessionManager.add_bot_message(user_id, location_message)
            
            await update.message.reply_text(location_message)
            return
            
    except Exception as e:
        logger.error(f"Lỗi khi xử lý vị trí: {e}")
        error_message = "Xin lỗi, đã xảy ra lỗi khi xử lý vị trí của bạn. Vui lòng thử lại sau."
        
        # Lưu tin nhắn vào lịch sử
        SessionManager.add_bot_message(user_id, error_message)
        
        await update.message.reply_text(error_message)

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
