import React, { useState, useEffect } from 'react';
import { Card } from '../components/Card/Card';
import { Button } from '../components/Button/Button';
import useAuthStore from '../store/useAuthStore';

const WorkflowManagementPage = () => {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { user } = useAuthStore();
  const [newWorkflow, setNewWorkflow] = useState({
    action: '',
    workflow_id: ''
  });

  // 获取工作流列表
  const fetchWorkflows = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/workflows/list?limit=20', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setWorkflows(data);
      } else {
        setError('获取工作流列表失败');
      }
    } catch (err) {
      setError('网络错误，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 启动新工作流
  const startWorkflow = async () => {
    if (!newWorkflow.action) {
      setError('请填写操作类型');
      return;
    }


    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/workflows/start', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          action: newWorkflow.action,
          workflow_id: newWorkflow.workflow_id || undefined
        })
      });

      if (response.ok) {
        setError('');
        setNewWorkflow({ action: '', workflow_id: '' });
        // 刷新工作流列表
        fetchWorkflows();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || '启动工作流失败');
      }
    } catch (err) {
      setError('网络错误，请稍后重试');
    }
  };

  // 取消工作流
  const cancelWorkflow = async (workflowId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/v1/workflows/${workflowId}/cancel`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        fetchWorkflows(); // 刷新列表
      } else {
        setError('取消工作流失败');
      }
    } catch (err) {
      setError('网络错误，请稍后重试');
    }
  };

  // 格式化时间
  const formatTime = (timeStr) => {
    if (!timeStr) return '-';
    return new Date(timeStr).toLocaleString('zh-CN');
  };

  // 获取状态标签颜色
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return '#10B981'; // 绿色
      case 'running':
        return '#3B82F6'; // 蓝色
      case 'failed':
        return '#EF4444'; // 红色
      case 'cancelled':
        return '#6B7280'; // 灰色
      default:
        return '#8B5CF6'; // 紫色
    }
  };

  useEffect(() => {
    fetchWorkflows();
  }, []);

  return (
    <div className="workflow-management-page" style={{ padding: '2rem' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <h1 style={{ 
          fontSize: '2rem', 
          fontWeight: 'bold', 
          marginBottom: '2rem',
          color: '#1F2937'
        }}>
          工作流管理
        </h1>

        {/* 启动新工作流 */}
        <Card style={{ marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem' }}>
            启动新工作流
          </h2>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '1rem',
            marginBottom: '1rem'
          }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                当前用户
              </label>
              <input
                type="text"
                value={user?.username || '未登录'}
                disabled
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #D1D5DB',
                  borderRadius: '0.375rem',
                  backgroundColor: '#F9FAFB',
                  color: '#6B7280',
                  outline: 'none'
                }}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                操作类型 *
              </label>
              <input
                type="text"
                value={newWorkflow.action}
                onChange={(e) => setNewWorkflow({...newWorkflow, action: e.target.value})}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #D1D5DB',
                  borderRadius: '0.375rem',
                  outline: 'none'
                }}
                placeholder="例如: process_data"
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                工作流ID (可选)
              </label>
              <input
                type="text"
                value={newWorkflow.workflow_id}
                onChange={(e) => setNewWorkflow({...newWorkflow, workflow_id: e.target.value})}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #D1D5DB',
                  borderRadius: '0.375rem',
                  outline: 'none'
                }}
                placeholder="留空自动生成"
              />
            </div>
          </div>
          <Button onClick={startWorkflow}>
            启动工作流
          </Button>
        </Card>

        {/* 错误信息 */}
        {error && (
          <div style={{
            backgroundColor: '#FEE2E2',
            border: '1px solid #FECACA',
            color: '#991B1B',
            padding: '1rem',
            borderRadius: '0.375rem',
            marginBottom: '1rem'
          }}>
            {error}
          </div>
        )}

        {/* 工作流列表 */}
        <Card>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '1rem'
          }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '600' }}>
              工作流列表
            </h2>
            <Button onClick={fetchWorkflows} disabled={loading}>
              {loading ? '刷新中...' : '刷新'}
            </Button>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#6B7280' }}>
              加载中...
            </div>
          ) : workflows.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#6B7280' }}>
              暂无工作流
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #E5E7EB' }}>
                    <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: '600' }}>
                      工作流ID
                    </th>
                    <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: '600' }}>
                      状态
                    </th>
                    <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: '600' }}>
                      开始时间
                    </th>
                    <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: '600' }}>
                      结束时间
                    </th>
                    <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: '600' }}>
                      结果
                    </th>
                    <th style={{ padding: '0.75rem', textAlign: 'center', fontWeight: '600' }}>
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {workflows.map((workflow, index) => (
                    <tr 
                      key={workflow.workflow_id} 
                      style={{ 
                        borderBottom: index < workflows.length - 1 ? '1px solid #F3F4F6' : 'none'
                      }}
                    >
                      <td style={{ padding: '0.75rem' }}>
                        <span style={{ 
                          fontFamily: 'monospace',
                          fontSize: '0.875rem',
                          color: '#4B5563'
                        }}>
                          {workflow.workflow_id}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        <span style={{
                          backgroundColor: getStatusColor(workflow.status) + '20',
                          color: getStatusColor(workflow.status),
                          padding: '0.25rem 0.5rem',
                          borderRadius: '0.25rem',
                          fontSize: '0.75rem',
                          fontWeight: '500',
                          textTransform: 'uppercase'
                        }}>
                          {workflow.status}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem', fontSize: '0.875rem', color: '#6B7280' }}>
                        {formatTime(workflow.start_time)}
                      </td>
                      <td style={{ padding: '0.75rem', fontSize: '0.875rem', color: '#6B7280' }}>
                        {formatTime(workflow.end_time)}
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        {workflow.result ? (
                          <details style={{ cursor: 'pointer' }}>
                            <summary style={{ color: '#3B82F6', fontSize: '0.875rem' }}>
                              查看结果
                            </summary>
                            <pre style={{
                              backgroundColor: '#F9FAFB',
                              padding: '0.5rem',
                              borderRadius: '0.25rem',
                              fontSize: '0.75rem',
                              marginTop: '0.5rem',
                              overflow: 'auto',
                              maxWidth: '300px'
                            }}>
                              {JSON.stringify(workflow.result, null, 2)}
                            </pre>
                          </details>
                        ) : (
                          <span style={{ color: '#9CA3AF', fontSize: '0.875rem' }}>-</span>
                        )}
                      </td>
                      <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                          <a
                            href={workflow.temporal_ui_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              color: '#3B82F6',
                              textDecoration: 'none',
                              fontSize: '0.875rem',
                              padding: '0.25rem 0.5rem',
                              borderRadius: '0.25rem',
                              border: '1px solid #3B82F6',
                              transition: 'all 0.2s'
                            }}
                            onMouseOver={(e) => {
                              e.target.style.backgroundColor = '#3B82F6';
                              e.target.style.color = 'white';
                            }}
                            onMouseOut={(e) => {
                              e.target.style.backgroundColor = 'transparent';
                              e.target.style.color = '#3B82F6';
                            }}
                          >
                            详情
                          </a>
                          {workflow.status === 'running' && (
                            <button
                              onClick={() => cancelWorkflow(workflow.workflow_id)}
                              style={{
                                color: '#EF4444',
                                backgroundColor: 'transparent',
                                border: '1px solid #EF4444',
                                borderRadius: '0.25rem',
                                padding: '0.25rem 0.5rem',
                                fontSize: '0.875rem',
                                cursor: 'pointer',
                                transition: 'all 0.2s'
                              }}
                              onMouseOver={(e) => {
                                e.target.style.backgroundColor = '#EF4444';
                                e.target.style.color = 'white';
                              }}
                              onMouseOut={(e) => {
                                e.target.style.backgroundColor = 'transparent';
                                e.target.style.color = '#EF4444';
                              }}
                            >
                              取消
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default WorkflowManagementPage;