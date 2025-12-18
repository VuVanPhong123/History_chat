import Link from 'next/link';
import { useEffect, useState } from 'react';
import { authService } from '@/services/authService';

export default function Header() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const checkAuth = () => {
      setIsAuthenticated(authService.isAuthenticated());
    };
    
    checkAuth();
    // Kiểm tra mỗi 10 giây
    const interval = setInterval(checkAuth, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="bg-white shadow-md">
      <div className="container mx-auto px-4 py-4">
        <div className="flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold text-blue-600">
            History AI
          </Link>
          <div className="flex items-center space-x-4">
            <nav className="flex space-x-4 mr-4">
              <Link href="/" className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md hover:bg-gray-50">
                Chat
              </Link>
              <Link href="/quiz" className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md hover:bg-gray-50">
                Quiz
              </Link>
              {/* <Link href="/history" className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md hover:bg-gray-50">
                Lịch sử
              </Link>
              <Link href="/settings" className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md hover:bg-gray-50">
                Cài đặt
              </Link> */}
            </nav>
            
            {isAuthenticated && (
              <div className="flex items-center text-sm">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                <span className="text-green-600 font-medium">Admin</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}