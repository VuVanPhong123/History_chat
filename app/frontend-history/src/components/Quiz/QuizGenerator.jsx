import { useState } from 'react';
import { quizService } from '@/services/quizService';
import toast from 'react-hot-toast';

// Định nghĩa TOPIC_RANGES từ backend
const TOPIC_RANGES = {
  1: {"name": "Lịch Sử Việt Nam Tập 1: Từ khởi thủy đến thế kỷ X", "start": 0, "end": 1195},
  2: {"name": "Lịch Sử Việt Nam Tập 2: Từ thế kỷ X đến thế kỷ XIV", "start": 1196, "end": 2553},
  3: {"name": "Lịch Sử Việt Nam Tập 3: Từ thế kỷ XV đến thế kỷ XVI", "start": 2554, "end": 4195},
  4: {"name": "Lịch Sử Việt Nam Tập 4: Từ thế kỷ XVII đến thế kỷ XVIII", "start": 4196, "end": 5414},
  5: {"name": "Lịch Sử Việt Nam Tập 5: Từ năm 1802 đến năm 1858", "start": 5415, "end": 7025},
  6: {"name": "Lịch Sử Việt Nam Tập 6: Từ năm 1859 đến năm 1896", "start": 7026, "end": 7911},
  7: {"name": "Lịch Sử Việt Nam Tập 7: Từ năm 1897 đến năm 1918", "start": 7912, "end": 9278},
  8: {"name": "Lịch Sử Việt Nam Tập 8: Từ năm 1919 đến năm 1930", "start": 9279, "end": 10569},
  9: {"name": "Lịch Sử Việt Nam Tập 9: Từ năm 1930 đến năm 1945", "start": 10570, "end": 12201},
  10: {"name": "Lịch Sử Việt Nam Tập 10: Từ năm 1945 đến năm 1950", "start": 12202, "end": 13658},
  11: {"name": "Lịch Sử Việt Nam Tập 11: Từ năm 1951 đến năm 1954", "start": 13659, "end": 14797},
  12: {"name": "Lịch Sử Việt Nam Tập 12: Từ năm 1954 đến năm 1965", "start": 14798, "end": 16041},
  13: {"name": "Lịch Sử Việt Nam Tập 13: Từ năm 1965 đến năm 1975", "start": 16042, "end": 17441},
  14: {"name": "Lịch Sử Việt Nam Tập 14: Từ năm 1975 đến năm 1986", "start": 17442, "end": 18585},
  15: {"name": "Lịch Sử Việt Nam Tập 15: Từ năm 1986 đến năm 2000", "start": 18586, "end": 19508}
};

export default function QuizGenerator() {
  const [selectedTopicIds, setSelectedTopicIds] = useState([1]);
  const [numQuestions, setNumQuestions] = useState(10);
  const [quizData, setQuizData] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [userAnswers, setUserAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(null);

  const questionNumbers = [10, 20, 30, 40];

  const handleGenerateQuiz = async () => {
    setIsGenerating(true);
    setGenerationProgress({
      status: 'starting',
      message: 'Đang bắt đầu tạo đề thi...',
      generatedCount: 0,
      totalQuestions: numQuestions
    });
    setQuizData(null);
    setUserAnswers({});
    setSubmitted(false);
    
    const topicName = selectedTopicIds.map(id => 
      TOPIC_RANGES[id]?.name || `Tập ${id}`
    ).join(' + ');
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/quiz/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topic: topicName,
          num_questions: numQuestions,
          topic_ids: selectedTopicIds
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let questions = [];
      let currentTestId = null;
      
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
              
              switch (data.status) {
                case 'started':
                  currentTestId = data.test_id;
                  setGenerationProgress({
                    status: 'started',
                    message: data.message,
                    generatedCount: 0,
                    totalQuestions: data.total_questions
                  });
                  break;
                  
                case 'progress':
                  setGenerationProgress({
                    status: 'progress',
                    message: data.message,
                    generatedCount: data.generated_count,
                    totalQuestions: data.total_questions,
                    currentWorker: data.current_worker,
                    totalWorkers: data.total_workers
                  });
                  break;
                  
                case 'question':
                  questions.push(data.question);
                  setGenerationProgress(prev => ({
                    ...prev,
                    generatedCount: questions.length,
                    message: `Đã tạo ${questions.length}/${numQuestions} câu hỏi`
                  }));
                  break;
                  
                case 'completed':
                  setQuizData({
                    test_id: data.test_id,
                    questions: data.questions || questions
                  });
                  setGenerationProgress(null);
                  toast.success('Tạo đề thi thành công!');
                  break;
                  
                case 'error':
                  toast.error('Có lỗi xảy ra: ' + data.message);
                  setGenerationProgress(null);
                  setIsGenerating(false);
                  return;
              }
              
            } catch (e) {
              console.error('Error parsing stream data:', e);
            }
          }
        }
      }
      
    } catch (error) {
      toast.error('Có lỗi xảy ra khi tạo đề thi');
      console.error('Lỗi chi tiết:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  // ... (giữ nguyên các hàm handleAnswerSelect, handleSubmitQuiz, etc.)

  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Tạo Đề Thi Lịch Sử</h2>
        
        {/* ... (giữ nguyên phần chọn topic và số câu) */}
        
        <button
          onClick={handleGenerateQuiz}
          disabled={isGenerating || selectedTopicIds.length === 0}
          className="btn-primary w-full mt-4"
        >
          {isGenerating ? 'Đang tạo đề thi...' : 'Tạo Đề Thi'}
        </button>
        
        {/* Hiển thị tiến trình */}
        {generationProgress && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
            <div className="flex justify-between items-center mb-2">
              <span className="font-medium text-blue-700">
                {generationProgress.status === 'started' ? '🚀 Bắt đầu' : 
                 generationProgress.status === 'progress' ? '⚡ Đang tạo' : '✅ Hoàn thành'}
              </span>
              <span className="text-sm text-blue-600">
                {generationProgress.generatedCount}/{generationProgress.totalQuestions} câu
              </span>
            </div>
            
            <div className="w-full bg-blue-200 rounded-full h-2.5 mb-2">
              <div 
                className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                style={{ 
                  width: `${(generationProgress.generatedCount / generationProgress.totalQuestions) * 100}%` 
                }}
              ></div>
            </div>
            
            <p className="text-sm text-blue-700">
              {generationProgress.message}
              {generationProgress.currentWorker && (
                <span className="ml-2 text-blue-600">
                  (Worker {generationProgress.currentWorker}/{generationProgress.totalWorkers})
                </span>
              )}
            </p>
            
            {generationProgress.status === 'progress' && (
              <div className="mt-2 flex space-x-1">
                {[...Array(3)].map((_, i) => (
                  <div 
                    key={i}
                    className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"
                    style={{ animationDelay: `${i * 0.1}s` }}
                  ></div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {quizData && (
        <div className="card">
          <h3 className="text-lg font-bold mb-4">
            Đề thi: {selectedTopicIds.map(id => `Tập ${id}`).join(', ')} 
            ({numQuestions} câu)
          </h3>

          <div className="space-y-6">
            {quizData.questions.map((question, index) => (
              <div key={index} className="border-b pb-4 last:border-0">
                <p className="font-medium mb-3">
                  Câu {index + 1}: {question.question}
                </p>
                
                <div className="space-y-2 ml-4">
                  {question.options.map((option) => (
                    <div key={option} className="flex items-center">
                      <input
                        type="radio"
                        id={`q${index}-${option}`}
                        name={`question-${index}`}
                        checked={userAnswers[index] === option.charAt(0)}
                        onChange={() => handleAnswerSelect(index, option.charAt(0))}
                        className="mr-2"
                        disabled={submitted}
                      />
                      <label htmlFor={`q${index}-${option}`} className="cursor-pointer">
                        {option}
                      </label>
                    </div>
                  ))}
                </div>

                {submitted && (
                  <div className="mt-3 p-3 bg-gray-50 rounded-md">
                    <p className="font-medium">
                      Đáp án đúng: {question.correct_answer}
                      {userAnswers[index] === question.correct_answer ? (
                        <span className="text-green-600 ml-2">✓ Đúng</span>
                      ) : (
                        <span className="text-red-600 ml-2">✗ Sai</span>
                      )}
                    </p>
                    <p className="text-sm mt-2 text-gray-600">
                      <span className="font-medium">Giải thích:</span> {question.explanation}
                    </p>
                  </div>
                )}
              </div>
            ))}

            {!submitted && (
              <button
                onClick={handleSubmitQuiz}
                className="btn-primary w-full mt-4"
              >
                Nộp Bài
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}