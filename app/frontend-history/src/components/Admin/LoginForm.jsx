import { useState, useEffect } from 'react';
import { authService } from '@/services/authService';
import toast from 'react-hot-toast';
import { useRouter } from 'next/router';

export default function LoginForm() {
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [remainingTime, setRemainingTime] = useState(0);
  const router = useRouter();

  useEffect(() => {
    const updateRemainingTime = () => {
      const time = authService.getRemainingTime();
      setRemainingTime(time);
    };

    updateRemainingTime();
    const interval = setInterval(updateRemainingTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await authService.login(password);
      toast.success('Đăng nhập thành công! Token có hiệu lực 5 phút');
      router.push('/settings');
    } catch (error) {
      toast.error('Sai mật khẩu!');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto">
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Đăng nhập Admin</h2>
        
        {remainingTime > 0 ? (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md">
            <p className="text-green-700">
              ✅ Đã đăng nhập. Thời gian còn lại: {Math.floor(remainingTime / 60)}:{String(remainingTime % 60).padStart(2, '0')}
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block mb-2 font-medium">Mật khẩu Admin:</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field"
                placeholder="Nhập mật khẩu từ file .env..."
                required
              />
              <p className="text-sm text-gray-500 mt-1">
                Mật khẩu được cấu hình trong biến ADMIN_PASSWORD trên server
              </p>
            </div>
            <button
              type="submit"
              disabled={isLoading || !password}
              className="btn-primary w-full"
            >
              {isLoading ? 'Đang đăng nhập...' : 'Đăng nhập (5 phút)'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}