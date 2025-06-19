import google.generativeai as genai
import os
from database.storage import DatabaseManager

class GeminiChatbot:
    def __init__(self):
        # Configure the Gemini API
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

        # Initialize the model
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.db_manager = DatabaseManager()
        
        # System prompt for the chatbot
        self.system_prompt = """Bạn là một AI Chatbot chuyên nghiệp tập trung vào việc cung cấp câu trả lời chính xác, ngắn gọn theo định dạng hỏi đáp. 
Duy trì bối cảnh cuộc trò chuyện. Tránh phản ứng sáng tạo hoặc cảm xúc. Ưu tiên sự rõ ràng, liên quan và tính chuyên nghiệp. 
Phát hiện và sử dụng ngôn ngữ ưa thích của người dùng."""
    
    def generate_response(self, user_input: str, chat_history) -> str:
        """Generate response using Gemini with chat history context"""
        try: 
            # Format the prompt with history
            history_context = chat_history if chat_history else ""
            
            full_prompt = f"""{self.system_prompt}
Đây là nội dung tóm tắt của lịch sử nhắn tin trước đó: {history_context}.
bạn nên để ý đến nó và sử dụng nếu cần thiết để trả lời câu hỏi sau từ người dùng: {user_input}
Xác định ngôn ngữ người dùng muốn sử dụng bằng cách làm theo các bước sau:
1. Đọc kỹ câu hỏi hoặc tin nhắn người dùng vừa gửi.
2. Kiểm tra ngôn ngữ chính được sử dụng trong nội dung đó.
3. Nếu có từ khóa hoặc cú pháp đặc trưng của một ngôn ngữ (ví dụ: "bạn", "là gì" → tiếng Việt; "what is", "how to" → tiếng Anh), thì chọn ngôn ngữ tương ứng.
4. Sử dụng ngôn ngữ đó để trả lời. 
Hãy trả lời một cách chính xác, có chú ý đến lịch sử trò chuyện."""

            # Generate response
            response = self.model.generate_content(full_prompt)
            return response.text
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "Xin lỗi, nhưng tôi gặp phải lỗi trong khi xử lý yêu cầu của bạn. Hãy thử lại."
    
    def get_welcome_message(self) -> str:
        """Get welcome message for new chat"""
        return "Xin chào! Tôi là trợ lý AI của bạn. Tôi có thể giúp bạn hôm nay?"
