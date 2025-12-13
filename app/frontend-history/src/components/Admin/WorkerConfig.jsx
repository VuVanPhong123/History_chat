import { useState, useEffect } from 'react';
import { adminService } from '@/services/adminService';
import toast from 'react-hot-toast';

export default function WorkerConfig() {
  const [workerStatus, setWorkerStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    fetchWorkerStatus();
  }, []);

  const fetchWorkerStatus = async () => {
    setIsLoading(true);
    try {
      const status = await adminService.getWorkerStatus();
      setWorkerStatus(status);
      setLastUpdated(new Date());
      toast.success('Đã cập nhật trạng thái workers!');
    } catch (error) {
      console.error('Lỗi khi lấy trạng thái workers:', error);
      toast.error('Không thể lấy trạng thái workers');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-xl font-bold">Trạng thái AI Workers</h2>
            <p className="text-sm text-gray-500 mt-1">
              Worker URLs được cấu hình trong file .env của server
            </p>
          </div>
          <button
            onClick={fetchWorkerStatus}
            disabled={isLoading}
            className="btn-secondary text-sm"
          >
            {isLoading ? 'Đang tải...' : 'Làm mới'}
          </button>
        </div>

        {lastUpdated && (
          <p className="text-sm text-gray-500 mb-4">
            Cập nhật lúc: {lastUpdated.toLocaleTimeString()}
          </p>
        )}

        {workerStatus ? (
          <div className="space-y-6">
            <div>
              <h3 className="font-bold mb-2 text-lg">Chat Workers</h3>
              {workerStatus.chat_workers && workerStatus.chat_workers.length > 0 ? (
                <div className="space-y-2">
                  {workerStatus.chat_workers.map((url, index) => (
                    <div key={index} className="flex items-center p-2 bg-gray-50 rounded-md">
                      <div className="w-3 h-3 rounded-full mr-3 bg-green-500"></div>
                      <div className="flex-grow">
                        <p className="font-mono text-sm">{url}</p>
                        <p className="text-xs text-gray-500">Đang hoạt động</p>
                      </div>
                    </div>
                  ))}
                  <p className="text-sm text-gray-500 mt-2">
                    Tổng số: {workerStatus.total_chat_workers || workerStatus.chat_workers.length} workers
                  </p>
                </div>
              ) : (
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
                  <p className="text-yellow-700">⚠️ Không có chat worker nào được cấu hình</p>
                  <p className="text-sm text-yellow-600 mt-1">
                    Vui lòng thêm CHAT_WORKER_URLS vào file .env và khởi động lại server
                  </p>
                </div>
              )}
            </div>

            <div>
              <h3 className="font-bold mb-2 text-lg">Quiz Workers</h3>
              {workerStatus.quiz_workers && workerStatus.quiz_workers.length > 0 ? (
                <div className="space-y-2">
                  {workerStatus.quiz_workers.map((url, index) => (
                    <div key={index} className="flex items-center p-2 bg-gray-50 rounded-md">
                      <div className="w-3 h-3 rounded-full mr-3 bg-green-500"></div>
                      <div className="flex-grow">
                        <p className="font-mono text-sm">{url}</p>
                        <p className="text-xs text-gray-500">Đang hoạt động</p>
                      </div>
                    </div>
                  ))}
                  <p className="text-sm text-gray-500 mt-2">
                    Tổng số: {workerStatus.total_quiz_workers || workerStatus.quiz_workers.length} workers
                  </p>
                </div>
              ) : (
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
                  <p className="text-yellow-700">⚠️ Không có quiz worker nào được cấu hình</p>
                  <p className="text-sm text-yellow-600 mt-1">
                    Vui lòng thêm QUIZ_WORKER_URLS vào file .env và khởi động lại server
                  </p>
                </div>
              )}
            </div>

            {workerStatus.note && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
                <p className="text-sm text-blue-700">{workerStatus.note}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-500">Đang tải thông tin workers...</p>
          </div>
        )}
      </div>

      <div className="card">
        <h3 className="font-bold mb-3">Hướng dẫn cấu hình Workers</h3>
        <div className="space-y-3 text-sm">
          <div className="p-3 bg-gray-50 rounded-md">
            <p className="font-medium">1. Tạo AI Workers (Kaggle/Colab):</p>
            <ul className="list-disc pl-5 mt-1 space-y-1">
              <li>Chat Worker: chạy model Qwen-Chat để trả lời hội thoại</li>
              <li>Quiz Worker: chạy model Qwen-GenQuiz để sinh câu hỏi</li>
            </ul>
          </div>
          
          <div className="p-3 bg-gray-50 rounded-md">
            <p className="font-medium">2. Mở cổng Ngrok:</p>
            <code className="block mt-1 p-2 bg-black text-white rounded">
              ngrok http 8000 --basic-auth="username:password"
            </code>
          </div>
          
          <div className="p-3 bg-gray-50 rounded-md">
            <p className="font-medium">3. Cập nhật file .env trên server:</p>
            <code className="block mt-1 p-2 bg-black text-white rounded">
              CHAT_WORKER_URLS=https://chat-worker-1.ngrok.io<br />
              QUIZ_WORKER_URLS=https://quiz-worker-1.ngrok.io,https://quiz-worker-2.ngrok.io
            </code>
          </div>
        </div>
      </div>
    </div>
  );
}