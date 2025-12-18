import api from './api';

export const chatService = {
  async sendMessage(message, sessionId = null, onChunkReceived = null) {
    // Chuẩn bị request body đúng format
    const requestBody = {
      message: message,
      session_id: sessionId // Có thể là null hoặc số
    };
    
    // LOG request trước khi gửi
    console.log('[ChatService] Request gửi đến /api/chat:', {
      url: '/api/chat',
      method: 'POST',
      body: requestBody
    });
    
    try {
      // 1. Sử dụng Fetch API thay vì axios để xử lý stream dễ dàng hơn
      const baseURL = api.defaults.baseURL || ''; // Lấy baseURL từ axios config
      const response = await fetch(`${baseURL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // 2. Xử lý stream response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullMessage = '';
      let finalSessionId = null;
      
      console.log('[ChatService] Bắt đầu nhận stream response...');
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        // Giải mã dữ liệu nhận được
        const chunkStr = decoder.decode(value);
        
        // Tách các dòng NDJSON
        const lines = chunkStr.split('\n').filter(line => line.trim() !== '');
        
        for (const line of lines) {
          try {
            const parsed = JSON.parse(line);
            console.log('[ChatService] Chunk nhận được:', parsed);
            
            // 3. Xử lý từng loại chunk
            if (parsed.chunk !== undefined) {
              // Đây là một phần của câu trả lời đang streaming
              fullMessage += parsed.chunk;
              finalSessionId = parsed.session_id;
              
              // Gọi callback nếu được cung cấp (để cập nhật UI real-time)
              if (onChunkReceived && typeof onChunkReceived === 'function') {
                onChunkReceived(parsed.chunk, parsed.session_id);
              }
            }
            else if (parsed.status === 'completed' && parsed.message !== undefined) {
              // Đây là thông báo hoàn tất (end of stream)
              console.log('[ChatService] Stream hoàn tất:', parsed);
              return {
                session_id: parsed.session_id,
                message: parsed.message,
                status: 'completed'
              };
            }
            else if (parsed.status === 'error') {
              // Server báo lỗi
              console.error('[ChatService] Lỗi từ server:', parsed);
              throw new Error(parsed.message || 'Lỗi từ server');
            }
          } catch (parseError) {
            console.error('[ChatService] Lỗi parse JSON:', parseError, 'Dữ liệu:', line);
          }
        }
      }
      
      // 4. Trả về kết quả cuối cùng (phòng trường hợp không có chunk "completed")
      console.log('[ChatService] Stream kết thúc, tổng hợp response');
      return {
        session_id: finalSessionId,
        message: fullMessage,
        status: 'completed'
      };
      
    } catch (error) {
      // LOG lỗi chi tiết
      console.error('[ChatService] Lỗi khi gửi message:', {
        message: error.message,
        stack: error.stack
      });
      throw error;
    }
  },

  async getSessions() {
    console.log('[ChatService] Lấy danh sách sessions');
    const response = await api.get('/api/chat/sessions');
    return response.data;
  },

  async getSessionMessages(sessionId, limit = 50) {
    console.log(`[ChatService] Lấy tin nhắn session ${sessionId}`);
    const response = await api.get(`/api/chat/sessions/${sessionId}/messages`, {
      params: { limit },
    });
    return response.data;
  },
};