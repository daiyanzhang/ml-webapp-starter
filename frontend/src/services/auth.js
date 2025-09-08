import api from './api'

export const authService = {
  // 用户登录
  async login(credentials) {
    const formData = new URLSearchParams()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)
    
    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return response.data
  },

  // 获取当前用户信息
  async getCurrentUser() {
    const response = await api.get('/users/me')
    return response.data
  },

  // 更新用户信息
  async updateProfile(userData) {
    const response = await api.put('/users/me', userData)
    return response.data
  },
}