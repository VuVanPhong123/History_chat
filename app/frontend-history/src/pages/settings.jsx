import { useEffect, useState } from 'react';
import { authService } from '@/services/authService';
import LoginForm from '@/components/Admin/LoginForm';
import WorkerConfig from '@/components/Admin/WorkerConfig';
import { useRouter } from 'next/router';

export default function SettingsPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Kiểm tra xem có token không
    const checkAuth = () => {
      const authStatus = authService.isAuthenticated();
      setIsAuthenticated(authStatus);
      setIsLoading(false);
    };
    
    checkAuth();
    
    // Check auth mỗi 30 giây
    const interval = setInterval(checkAuth, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    authService.logout();
    setIsAuthenticated(false);
    // Không reload để giữ state các trang khác
    router.push('/settings');
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-3 text-gray-600">Đang kiểm tra đăng nhập...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Cài đặt Admin</h1>
          <p className="text-gray-600 mt-1">Quản lý trạng thái hệ thống</p>
        </div>
        {isAuthenticated && (
          <button 
            onClick={handleLogout}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Đăng xuất
          </button>
        )}
      </div>

      {!isAuthenticated ? (
        <>
          <div className="card mb-6">
            <h2 className="text-xl font-bold mb-4">Đăng nhập để xem trạng thái hệ thống</h2>
            <p className="text-gray-600 mb-4">
              Chỉ admin mới có thể xem thông tin cấu hình workers và trạng thái server.
            </p>
            <LoginForm />
          </div>
        </>
      ) : (
        <>
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">Thông báo bảo mật</h3>
                <div className="mt-2 text-sm text-blue-700">
                  <ul className="list-disc pl-5 space-y-1">
                    <li>Token admin có hiệu lực trong 5 phút</li>
                    <li>Tự động đăng xuất sau khi token hết hạn</li>
                    <li>Worker URLs được cấu hình trong file .env trên server</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
          
          <WorkerConfig />
          
          <div className="mt-6 card">
            <h3 className="font-bold mb-3">Thông tin server</h3>
            <div className="space-y-2 text-sm">
              <p>Frontend URL: <code className="bg-gray-100 px-2 py-1 rounded">{process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}</code></p>
              <p>API Base URL: <code className="bg-gray-100 px-2 py-1 rounded">{process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}</code></p>
              <p>Môi trường: <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">Development</span></p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}