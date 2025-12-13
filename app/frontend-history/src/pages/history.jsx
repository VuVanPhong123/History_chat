import { useState, useEffect } from 'react';
import { chatService } from '@/services/chatService';
import { quizService } from '@/services/quizService';

export default function HistoryPage() {
  const [activeTab, setActiveTab] = useState('chat');
  const [chatSessions, setChatSessions] = useState([]);
  const [quizTests, setQuizTests] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      if (activeTab === 'chat') {
        const sessions = await chatService.getSessions();
        setChatSessions(sessions);
      } else {
        const tests = await quizService.getTests();
        setQuizTests(tests);
      }
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Lịch sử</h1>

      <div className="mb-6">
        <div className="flex border-b">
          <button
            className={`px-4 py-2 font-medium ${
              activeTab === 'chat'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-500'
            }`}
            onClick={() => setActiveTab('chat')}
          >
            Cuộc trò chuyện
          </button>
          <button
            className={`px-4 py-2 font-medium ${
              activeTab === 'quiz'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-500'
            }`}
            onClick={() => setActiveTab('quiz')}
          >
            Bài kiểm tra
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-8">
          <p>Đang tải dữ liệu...</p>
        </div>
      ) : activeTab === 'chat' ? (
        <div className="space-y-4">
          {chatSessions.length === 0 ? (
            <p className="text-gray-500">Chưa có cuộc trò chuyện nào</p>
          ) : (
            chatSessions.map((session) => (
              <div key={session.id} className="card hover:shadow-lg transition-shadow">
                <h3 className="font-bold mb-2">{session.title}</h3>
                <p className="text-sm text-gray-600 mb-2">
                  {session.last_message?.substring(0, 100)}...
                </p>
                <p className="text-xs text-gray-500">
                  {new Date(session.created_at).toLocaleDateString()}
                </p>
              </div>
            ))
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {quizTests.length === 0 ? (
            <p className="text-gray-500">Chưa có bài kiểm tra nào</p>
          ) : (
            quizTests.map((test) => (
              <div key={test.id} className="card hover:shadow-lg transition-shadow">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-bold mb-1">{test.topic}</h3>
                    <p className="text-sm text-gray-600">
                      {test.total_questions} câu hỏi
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-lg">
                      {test.score !== null ? `${test.score}/${test.total_questions}` : 'Chưa nộp'}
                    </p>
                    {test.score !== null && (
                      <p className="text-sm text-gray-600">
                        {((test.score / test.total_questions) * 100).toFixed(1)}%
                      </p>
                    )}
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  {new Date(test.created_at).toLocaleDateString()}
                </p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}