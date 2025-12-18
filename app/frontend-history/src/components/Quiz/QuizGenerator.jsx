  import { useState } from 'react';
  import { quizService } from '@/services/quizService';
  import toast from 'react-hot-toast';

  const TOPIC_RANGES = {
    1: "Lịch Sử Việt Nam Tập 1: Từ khởi thủy đến thế kỷ X",
    2: "Lịch Sử Việt Nam Tập 2: Từ thế kỷ X đến thế kỷ XIV",
    3: "Lịch Sử Việt Nam Tập 3: Từ thế kỷ XV đến thế kỷ XVI",
    4: "Lịch Sử Việt Nam Tập 4: Từ thế kỷ XVII đến thế kỷ XVIII",
    5: "Lịch Sử Việt Nam Tập 5: Từ năm 1802 đến năm 1858",
    6: "Lịch Sử Việt Nam Tập 6: Từ năm 1859 đến năm 1896",
    7: "Lịch Sử Việt Nam Tập 7: Từ năm 1897 đến năm 1918",
    8: "Lịch Sử Việt Nam Tập 8: Từ năm 1919 đến năm 1930",
    9: "Lịch Sử Việt Nam Tập 9: Từ năm 1930 đến năm 1945",
    10: "Lịch Sử Việt Nam Tập 10: Từ năm 1945 đến năm 1950",
    11: "Lịch Sử Việt Nam Tập 11: Từ năm 1951 đến năm 1954",
    12: "Lịch Sử Việt Nam Tập 12: Từ năm 1954 đến năm 1965",
    13: "Lịch Sử Việt Nam Tập 13: Từ năm 1965 đến năm 1975",
    14: "Lịch Sử Việt Nam Tập 14: Từ năm 1975 đến năm 1986",
    15: "Lịch Sử Việt Nam Tập 15: Từ năm 1986 đến năm 2000"
  };

  const getTopicName = (topicId) => {
    return TOPIC_RANGES[topicId] || `Tập ${topicId}`;
  };

  export default function QuizGenerator() {
    const [selectedTopicIds, setSelectedTopicIds] = useState([1]);
    const [numQuestions, setNumQuestions] = useState(10);
    const [quizData, setQuizData] = useState(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [userAnswers, setUserAnswers] = useState({});
    const [submitted, setSubmitted] = useState(false);
    const [generationProgress, setGenerationProgress] = useState(null);
    const [generatedQuestions, setGeneratedQuestions] = useState([]);

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
      setGeneratedQuestions([]);
      setUserAnswers({});
      setSubmitted(false);
      
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/quiz/generate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
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
                      totalQuestions: data.total_questions,
                      testId: data.test_id
                    });
                    break;
                    
                  case 'progress':
                    // Cập nhật tiến độ khi nhận được từ worker
                    setGenerationProgress(prev => ({
                      ...prev,
                      status: 'progress',
                      message: data.message || `Đã tạo ${data.generated_count}/${data.total_questions} câu hỏi`,
                      generatedCount: data.generated_count,
                      totalQuestions: data.total_questions
                    }));
                    break;
                    
                  // KHÔNG CÒN XỬ LÝ 'question' RIÊNG LẺ NỮA
                  // Vì backend chỉ gửi progress và completed
                  
                  case 'completed':
                    // Nhận toàn bộ câu hỏi khi hoàn thành
                    const finalQuestions = data.questions || [];
                    setQuizData({
                      test_id: data.test_id || currentTestId,
                      questions: finalQuestions
                    });
                    setGeneratedQuestions(finalQuestions);
                    setGenerationProgress(null);
                    toast.success(data.message || 'Tạo đề thi thành công!');
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
        toast.error('Có lỗi xảy ra khi tạo đề thi: ' + error.message);
        console.error('Lỗi chi tiết:', error);
      } finally {
        setIsGenerating(false);
      }
    };

    const handleAnswerSelect = (questionIndex, answer) => {
      setUserAnswers(prev => ({
        ...prev,
        [questionIndex]: answer
      }));
    };

    const handleSubmitQuiz = () => {
      if (!quizData || !quizData.questions) {
        toast.error('Không có dữ liệu đề thi');
        return;
      }
      
      if (Object.keys(userAnswers).length < quizData.questions.length) {
        toast.error('Vui lòng trả lời tất cả các câu hỏi trước khi nộp bài');
        return;
      }
      setSubmitted(true);
      toast.success('Đã nộp bài!');
    };

    const toggleTopic = (topicId) => {
      setSelectedTopicIds(prev => {
        if (prev.includes(topicId)) {
          return prev.filter(id => id !== topicId);
        } else {
          return [...prev, topicId];
        }
      });
    };

    const selectAllTopics = () => {
      setSelectedTopicIds([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]);
    };

    const clearAllTopics = () => {
      setSelectedTopicIds([]);
    };

    // Hàm tính điểm
    const calculateScore = () => {
      if (!quizData || !quizData.questions) return 0;
      
      let correctCount = 0;
      quizData.questions.forEach((question, index) => {
        if (userAnswers[index] === question.correct_answer) {
          correctCount++;
        }
      });
      
      return correctCount;
    };

    return (
      <div className="space-y-6">
        <div className="card">
          <h2 className="text-xl font-bold mb-4">Tạo Đề Thi Lịch Sử</h2>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Chọn chủ đề:
            </label>
            <div className="flex flex-wrap gap-2 mb-2">
              <button
                onClick={selectAllTopics}
                className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
              >
                Chọn tất cả
              </button>
              <button
                onClick={clearAllTopics}
                className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
              >
                Bỏ chọn tất cả
              </button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
              {Object.entries(TOPIC_RANGES).map(([id, name]) => (
                <div key={id} className="flex items-center">
                  <input
                    type="checkbox"
                    id={`topic-${id}`}
                    checked={selectedTopicIds.includes(parseInt(id))}
                    onChange={() => toggleTopic(parseInt(id))}
                    className="mr-2"
                  />
                  <label htmlFor={`topic-${id}`} className="text-sm cursor-pointer truncate">
                    <span className="font-medium">Tập {id}:</span> {name.split(':')[1] ? name.split(':')[1].trim() : name}
                  </label>
                </div>
              ))}
            </div>
            {selectedTopicIds.length === 0 && (
              <p className="text-red-500 text-sm mt-1">Vui lòng chọn ít nhất một chủ đề</p>
            )}
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Số câu hỏi:
            </label>
            <div className="flex flex-wrap gap-2">
              {questionNumbers.map(num => (
                <button
                  key={num}
                  onClick={() => setNumQuestions(num)}
                  className={`px-4 py-2 rounded transition-colors ${
                    numQuestions === num 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {num} câu
                </button>
              ))}
            </div>
          </div>
          
          <button
            onClick={handleGenerateQuiz}
            disabled={isGenerating || selectedTopicIds.length === 0}
            className={`btn-primary w-full mt-4 ${isGenerating ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isGenerating ? 'Đang tạo đề thi...' : 'Tạo Đề Thi'}
          </button>
          
          {generationProgress && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium text-blue-700">
                  {generationProgress.status === 'started' ? 'Bắt đầu' : 
                  generationProgress.status === 'progress' ? 'Đang tạo...' : 
                  generationProgress.status === 'starting' ? 'Đang khởi tạo...' : 'Hoàn thành'}
                </span>
                <span className="text-sm text-blue-600">
                  {generationProgress.generatedCount}/{generationProgress.totalQuestions} câu
                </span>
              </div>
              
              {/* Progress bar */}
              <div className="w-full bg-blue-200 rounded-full h-2.5 mb-2">
                <div 
                  className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                  style={{ 
                    width: `${Math.min(
                      (generationProgress.generatedCount / generationProgress.totalQuestions) * 100,
                      100
                    )}%` 
                  }}
                ></div>
              </div>
              
              <p className="text-sm text-blue-700">
                {generationProgress.message}
                {generationProgress.testId && (
                  <span className="ml-2 text-xs text-blue-500">
                    (Mã đề: {generationProgress.testId})
                  </span>
                )}
              </p>
              
              {isGenerating && (
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

        {quizData && quizData.questions && quizData.questions.length > 0 && (
          <div className="card">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-bold">
                Đề thi: {selectedTopicIds.map(id => `Tập ${id}`).join(', ')} 
                <span className="text-gray-600 font-normal ml-2">({numQuestions} câu)</span>
              </h3>
              {generationProgress?.testId && (
                <span className="text-sm bg-gray-100 px-3 py-1 rounded">
                  Mã đề: {generationProgress.testId}
                </span>
              )}
            </div>

            <div className="space-y-6">
              {quizData.questions.map((question, index) => (
                <div key={index} className="border-b pb-6 last:border-0">
                  <p className="font-medium mb-4">
                    <span className="text-blue-600">Câu {index + 1}:</span> {question.question}
                  </p>
                  
                  <div className="space-y-2 ml-4">
                    {question.options && question.options.map((option, optIndex) => {
                      const optionLetter = String.fromCharCode(65 + optIndex); // A, B, C, D
                      return (
                        <div key={optIndex} className="flex items-start">
                          <input
                            type="radio"
                            id={`q${index}-${optIndex}`}
                            name={`question-${index}`}
                            checked={userAnswers[index] === optionLetter}
                            onChange={() => handleAnswerSelect(index, optionLetter)}
                            className="mr-3 mt-1"
                            disabled={submitted}
                          />
                          <label htmlFor={`q${index}-${optIndex}`} className="cursor-pointer flex-1">
                            <span className="font-medium">{optionLetter}.</span> {option}
                          </label>
                        </div>
                      );
                    })}
                  </div>

                  {submitted && (
                    <div className={`mt-4 p-4 rounded-md ${
                      userAnswers[index] === question.correct_answer 
                        ? 'bg-green-50 border border-green-200' 
                        : 'bg-red-50 border border-red-200'
                    }`}>
                      <div className="flex items-center">
                        <span className="font-medium">
                          Đáp án đúng: <span className="text-green-600">{question.correct_answer}</span>
                        </span>
                        <span className="ml-4">
                          {userAnswers[index] === question.correct_answer ? (
                            <span className="text-green-600 font-bold">✓ Đúng</span>
                          ) : (
                            <span className="text-red-600 font-bold">
                              ✗ Sai {userAnswers[index] && `(Bạn chọn: ${userAnswers[index]})`}
                            </span>
                          )}
                        </span>
                      </div>
                      {question.explanation && (
                        <p className="mt-2 text-sm text-gray-700">
                          <span className="font-medium">Giải thích:</span> {question.explanation}
                        </p>
                      )}
                      {question.context && (
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <p className="text-xs font-bold text-blue-800 uppercase tracking-wider mb-1">
                            Tài liệu tham khảo:
                          </p>
                          <div className="p-2 bg-white/50 rounded border border-blue-100 text-sm text-gray-600 italic leading-relaxed">
                            "{question.context}"
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}

              {!submitted && (
                <div className="flex justify-between items-center mt-8 pt-6 border-t">
                  <div className="text-sm text-gray-600">
                    Đã trả lời: {Object.keys(userAnswers).length}/{quizData.questions.length} câu
                  </div>
                  <button
                    onClick={handleSubmitQuiz}
                    className="btn-primary px-8"
                    disabled={Object.keys(userAnswers).length < quizData.questions.length}
                  >
                    Nộp Bài
                  </button>
                </div>
              )}

              {submitted && (
                <div className="mt-8 p-6 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="text-xl font-bold text-center mb-4">Kết quả bài làm</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-white rounded-lg">
                      <div className="text-3xl font-bold text-blue-600">{calculateScore()}</div>
                      <div className="text-sm text-gray-600">Số câu đúng</div>
                    </div>
                    <div className="text-center p-4 bg-white rounded-lg">
                      <div className="text-3xl font-bold text-gray-800">{quizData.questions.length}</div>
                      <div className="text-sm text-gray-600">Tổng số câu</div>
                    </div>
                    <div className="text-center p-4 bg-white rounded-lg">
                      <div className="text-3xl font-bold text-green-600">
                        {((calculateScore() / quizData.questions.length) * 100).toFixed(1)}%
                      </div>
                      <div className="text-sm text-gray-600">Tỷ lệ đúng</div>
                    </div>
                  </div>
                  <div className="mt-6 text-center">
                    <button
                      onClick={() => {
                        setSubmitted(false);
                        setUserAnswers({});
                      }}
                      className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                      Làm lại
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  }