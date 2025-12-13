import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
});

api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('admin_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      console.error('Network error:', error.message);
      if (typeof window !== 'undefined') {
        alert('Không thể kết nối đến server. Vui lòng kiểm tra kết nối mạng và thử lại.');
      }
    }
    
    if (error.response && error.response.status === 401) {
      console.log('Token hết hạn hoặc không hợp lệ');
      if (typeof window !== 'undefined') {
        localStorage.removeItem('admin_token');
        if (window.location.pathname === '/settings') {
          window.location.reload(); 
        }
      }
    }
    
    if (error.response && error.response.status === 503) {
      console.error('Service Unavailable:', error.response.data);
      if (typeof window !== 'undefined') {
        alert('Server đang bảo trì hoặc không có worker nào khả dụng. Vui lòng thử lại sau.');
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;