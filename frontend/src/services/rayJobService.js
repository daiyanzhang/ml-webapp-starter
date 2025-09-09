import apiClient from './api';

class RayJobService {
  /**
   * 提交GitHub Ray作业
   */
  async submitGitHubJob(jobRequest) {
    try {
      const response = await apiClient.post('/ray/submit-github', jobRequest);
      return response.data;
    } catch (error) {
      console.error('Submit GitHub Ray job failed:', error);
      throw new Error(error.response?.data?.detail || 'Failed to submit Ray job');
    }
  }

  /**
   * 获取Ray作业状态
   */
  async getJobStatus(jobId) {
    try {
      const response = await apiClient.get(`/ray/status/${jobId}`);
      return response.data;
    } catch (error) {
      console.error('Get Ray job status failed:', error);
      throw new Error(error.response?.data?.detail || 'Failed to get job status');
    }
  }

  /**
   * 列出Ray作业
   */
  async listJobs(limit = 10) {
    try {
      const response = await apiClient.get('/ray/list', {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      console.error('List Ray jobs failed:', error);
      throw new Error(error.response?.data?.detail || 'Failed to list jobs');
    }
  }

  /**
   * 取消Ray作业
   */
  async cancelJob(jobId) {
    try {
      const response = await apiClient.post(`/ray/cancel/${jobId}`);
      return response.data;
    } catch (error) {
      console.error('Cancel Ray job failed:', error);
      throw new Error(error.response?.data?.detail || 'Failed to cancel job');
    }
  }

  /**
   * 获取作业模板
   */
  async getTemplates() {
    try {
      const response = await apiClient.get('/ray/templates');
      return response.data;
    } catch (error) {
      console.error('Get Ray job templates failed:', error);
      throw new Error(error.response?.data?.detail || 'Failed to get templates');
    }
  }

  /**
   * 验证GitHub仓库
   */
  async validateRepository(repoUrl, branch = 'main', entryPoint = 'main.py') {
    try {
      const response = await apiClient.post('/ray/validate-repo', null, {
        params: {
          repo_url: repoUrl,
          branch,
          entry_point: entryPoint
        }
      });
      return response.data;
    } catch (error) {
      console.error('Validate repository failed:', error);
      throw new Error(error.response?.data?.detail || 'Failed to validate repository');
    }
  }

  /**
   * 获取Ray集群状态
   */
  async getClusterStatus() {
    try {
      const response = await apiClient.get('/ray/cluster/status');
      return response.data;
    } catch (error) {
      console.error('Get Ray cluster status failed:', error);
      throw new Error(error.response?.data?.detail || 'Failed to get cluster status');
    }
  }

  /**
   * 获取示例仓库
   */
  async getExamples() {
    try {
      const response = await apiClient.get('/ray/examples');
      return response.data;
    } catch (error) {
      console.error('Get Ray examples failed:', error);
      throw new Error(error.response?.data?.detail || 'Failed to get examples');
    }
  }
}

export const rayJobService = new RayJobService();