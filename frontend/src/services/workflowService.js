import api from './api'

export const workflowService = {
  // 启动工作流
  async startWorkflow(data) {
    const response = await api.post('/workflows/start', data)
    return response.data
  },

  // 获取工作流状态
  async getWorkflowStatus(workflowId) {
    const response = await api.get(`/workflows/${workflowId}/status`)
    return response.data
  },

  // 取消工作流
  async cancelWorkflow(workflowId) {
    const response = await api.post(`/workflows/${workflowId}/cancel`)
    return response.data
  },

  // 获取工作流列表
  async getWorkflows(params = {}) {
    const { limit = 20, offset = 0 } = params
    const response = await api.get(`/workflows/list?limit=${limit}&offset=${offset}`)
    return response.data
  }
}