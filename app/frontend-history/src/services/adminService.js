import api from './api';

export const adminService = {
  // Lấy trạng thái workers
  async getWorkerStatus() {
    const response = await api.get('/api/admin/status');
    return response.data;
  },
};