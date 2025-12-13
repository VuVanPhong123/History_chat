import api from './api';

export const quizService = {
  // Sửa: Thêm tham số topicIds (mảng số)
  async generateQuiz(topic, numQuestions, topicIds = []) {
    const requestBody = {
      topic: topic,
      num_questions: numQuestions,
      topic_ids: topicIds
    };
    
    console.log('[QuizService] Request gửi đến /api/quiz/generate:', requestBody);
    
    try {
      const response = await fetch('/api/quiz/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // Đọc streaming response
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let questions = [];
      let testId = null;
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();
        
        for (const line of lines) {
          if (line.trim()) {
            try {
              const data = JSON.parse(line);
              
              if (data.status === 'started') {
                testId = data.test_id;
              } 
              else if (data.status === 'question' && data.question) {
                questions.push(data.question);
              }
              else if (data.status === 'completed') {
                return {
                  test_id: testId || data.test_id,
                  questions: data.questions || questions
                };
              }
              else if (data.status === 'error') {
                throw new Error(data.message);
              }
              
            } catch (e) {
              console.error('Error parsing stream data:', e);
            }
          }
        }
      }
      
      return {
        test_id: testId,
        questions: questions
      };
      
    } catch (error) {
      console.error('[QuizService] Lỗi khi tạo quiz:', error);
      throw error;
    }
  },

  async getTests(limit = 10, offset = 0) {
    const response = await api.get('/api/quiz/tests', {
      params: { limit, offset },
    });
    return response.data;
  },

  async submitTest(testId, answers) {
    console.log(`[QuizService] Nộp bài test ${testId}`);
    const response = await api.post(`/api/quiz/tests/${testId}/submit`, answers);
    return response.data;
  },
};