import api from './api';

export const authService = {
  async login(password) {
    const formData = new FormData();
    formData.append('username', 'admin');
    formData.append('password', password);
    
    try {
      const response = await api.post('/api/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      
      if (response.data.access_token) {
        localStorage.setItem('admin_token', response.data.access_token);
        localStorage.setItem('login_time', Date.now());
      }
      
      return response.data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  },

  isAuthenticated() {
    if (typeof window === 'undefined') return false;
    
    const token = localStorage.getItem('admin_token');
    if (!token) return false;
    
    const loginTime = localStorage.getItem('login_time');
    if (loginTime) {
      const elapsed = Date.now() - parseInt(loginTime);
      if (elapsed > 300000) { // 5 phút
        this.logout();
        return false;
      }
    }
    
    return true;
  },

  getRemainingTime() {
    if (typeof window === 'undefined') return 0;
    
    const loginTime = localStorage.getItem('login_time');
    if (!loginTime) return 0;
    
    const elapsed = Date.now() - parseInt(loginTime);
    const remaining = Math.max(0, 300000 - elapsed); 
    return Math.floor(remaining / 1000); 
  },

  // Đăng xuất
  logout() {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('login_time');
  },
};