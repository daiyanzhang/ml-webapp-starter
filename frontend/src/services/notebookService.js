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



  // 获取 JupyterHub 服务器状态
  async getServerStatus() {
    const response = await api.get('/notebooks/server/status');
    return response.data;
  },

  // 启动 JupyterHub 会话
  async startSession() {
    const response = await api.post('/notebooks/session/start');
    return response.data;
  },

  // 停止 JupyterHub 会话
  async stopSession() {
    const response = await api.delete('/notebooks/session/stop');
    return response.data;
  },

  // 获取 JupyterHub URL
  async getJupyterUrl() {
    const response = await api.get('/notebooks/session/url');
    return response.data.url;
  },

  // 直接打开 JupyterHub (用于新标签页)
  openJupyterHub() {
    // 直接打开 JupyterHub 主页
    window.open('http://localhost:8001', '_blank');
  }
};

export default notebookService;