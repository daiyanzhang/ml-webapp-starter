import api from './api'

export const userService = {
  // 获取用户列表
  async getUsers(params = {}) {
    const response = await api.get('/users/', { params })
    return response.data
  },

  // 创建用户
  async createUser(userData) {
    const response = await api.post('/users/', userData)
    return response.data
  },

  // 获取用户详情
  async getUser(userId) {
    const response = await api.get(`/users/${userId}`)
    return response.data
  },

  // 更新用户
  async updateUser(userId, userData) {
    const response = await api.put(`/users/${userId}`, userData)
    return response.data
  },
}