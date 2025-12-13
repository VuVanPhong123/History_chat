import api from './api';

export const chatService = {
  async sendMessage(message, sessionId = null) {
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
      const response = await api.post('/api/chat', requestBody);
      
      // LOG response nhận được
      console.log('[ChatService] Response từ backend:', response.data);
      
      return response.data;
    } catch (error) {
      // LOG lỗi chi tiết
      console.error('[ChatService] Lỗi khi gửi message:', {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message
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