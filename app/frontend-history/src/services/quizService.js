import api from './api';

export const quizService = {
  /**
   * Tạo đề thi mới với cơ chế stream tiến độ.
   * @param {number} numQuestions - Số lượng câu hỏi (10, 20, 30, 40).
   * @param {Array} topicIds - Danh sách ID chủ đề (1-15).
   * @param {Function} onProgress - Callback xử lý tiến độ gửi về UI.
   */
  async generateQuiz(numQuestions, topicIds = [], onProgress = null) {
    try {
      const response = await fetch('/api/quiz/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          num_questions: numQuestions,
          topic_ids: topicIds
        })
      });

      if (!response.ok) throw new Error(`Lỗi server: ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Giữ lại dòng dang dở trong buffer

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            
            // Gửi mọi trạng thái nhận được về cho UI xử lý
            if (onProgress) {
              onProgress({
                status: data.status,
                current: data.generated_count || 0,
                total: data.total_questions || numQuestions,
                message: data.message,
                testId: data.test_id,
                questions: data.questions || []
              });
            }

            // Trả về kết quả cuối cùng khi hoàn tất
            if (data.status === 'completed') {
              return {
                test_id: data.test_id,
                questions: data.questions
              };
            }
          } catch (e) {
            console.error("[QuizService] Lỗi xử lý dòng dữ liệu:", e);
          }
        }
      }
    } catch (error) {
      console.error("[QuizService] Lỗi tạo đề thi:", error);
      throw error;
    }
  },

  async getTests(limit = 10, offset = 0) {
    const response = await api.get('/api/quiz/tests', { params: { limit, offset } });
    return response.data;
  },

  async submitTest(testId, answers) {
    const response = await api.post(`/api/quiz/tests/${testId}/submit`, answers);
    return response.data;
  },
};