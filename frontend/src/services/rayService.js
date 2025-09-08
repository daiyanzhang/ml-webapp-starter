import api from './api'

export const rayService = {
  // 获取Ray集群状态
  async getClusterStatus() {
    const response = await api.get('/ray/cluster/status')
    return response.data
  },

  // 获取可用的任务类型
  async getAvailableJobs() {
    const response = await api.get('/ray/available')
    return response.data
  },

  // 提交Ray任务
  async submitJob(jobType, parameters) {
    const response = await api.post('/ray/submit', {
      job_type: jobType,
      parameters: parameters
    })
    return response.data
  },

  // 测试简单任务
  async testSimpleJob(taskType = 'prime_count') {
    const response = await api.post(`/ray/test/simple?task_type=${taskType}`)
    return response.data
  },

  // 测试数据处理任务
  async testDataProcessing(dataSize = 5000, batchSize = 500) {
    const response = await api.post('/ray/test/data-processing', null, {
      params: {
        data_size: dataSize,
        batch_size: batchSize
      }
    })
    return response.data
  },

  // 测试机器学习任务
  async testMachineLearning(params = {}) {
    const {
      n_samples = 5000,
      n_features = 15,
      n_classes = 3,
      n_models = 3
    } = params

    const response = await api.post('/ray/test/machine-learning', null, {
      params: {
        n_samples,
        n_features,
        n_classes,
        n_models
      }
    })
    return response.data
  },

  // 获取任务历史记录
  async getJobHistory(limit = 50, offset = 0, userId = null) {
    const params = { limit, offset }
    if (userId) {
      params.user_id = userId
    }
    
    const response = await api.get('/ray/jobs', { params })
    return response.data
  },

  // 根据ID获取任务详情
  async getJobById(jobId) {
    const response = await api.get(`/ray/jobs/${jobId}`)
    return response.data
  }
}