import api from './api';

const notebookService = {
  // 获取所有 notebooks
  async getNotebooks() {
    const response = await api.get('/notebooks/');
    return response.data;
  },

  // 创建新 notebook
  async createNotebook(name, content = null) {
    const response = await api.post('/notebooks/', {
      name,
      content
    });
    return response.data;
  },

  // 获取指定 notebook 内容
  async getNotebook(path) {
    const response = await api.get(`/notebooks/${path}`);
    return response.data;
  },

  // 更新 notebook 内容
  async updateNotebook(path, content) {
    const response = await api.put(`/notebooks/${path}`, {
      content
    });
    return response.data;
  },

  // 删除 notebook
  async deleteNotebook(path) {
    const response = await api.delete(`/notebooks/${path}`);
    return response.data;
  },

  // 执行 notebook
  async executeNotebook(path) {
    const response = await api.post(`/notebooks/${path}/execute`);
    return response.data;
  },

  // 在Ray集群上执行 notebook
  async executeNotebookOnRay(path) {
    const response = await api.post(`/notebooks/${path}/execute-on-ray`);
    return response.data;
  },

  // 获取Ray任务列表
  async getRayJobs() {
    const response = await api.get('/notebooks/ray/jobs');
    return response.data;
  },

  // 获取Ray任务状态
  async getRayJobStatus(jobId) {
    const response = await api.get(`/notebooks/ray/jobs/${jobId}`);
    return response.data;
  },

  // 取消Ray任务
  async cancelRayJob(jobId) {
    const response = await api.delete(`/notebooks/ray/jobs/${jobId}`);
    return response.data;
  },

  // 获取Ray集群状态
  async getRayClusterStatus() {
    const response = await api.get('/notebooks/ray/cluster/status');
    return response.data;
  },

  // 获取 Jupyter 服务器状态
  async getServerStatus() {
    const response = await api.get('/notebooks/server/status');
    return response.data;
  },

  // 生成 Jupyter URL
  getJupyterUrl(path = '') {
    const baseUrl = 'http://localhost:8888';
    const token = 'webapp-starter-token';
    
    if (path) {
      return `${baseUrl}/notebooks/${path}?token=${token}`;
    }
    return `${baseUrl}/tree?token=${token}`;
  }
};

export default notebookService;