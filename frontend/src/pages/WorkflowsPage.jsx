import { useState, useEffect } from 'react'
import { 
  Card, 
  Button, 
  Table, 
  Modal, 
  Form, 
  Input, 
  Select, 
  Space, 
  Tag, 
  message,
  Popconfirm,
  Tooltip,
  Typography 
} from 'antd'
import { 
  PlusOutlined, 
  ReloadOutlined, 
  PlayCircleOutlined, 
  StopOutlined,
  EyeOutlined,
  DeleteOutlined 
} from '@ant-design/icons'
import { workflowService } from '../services/workflowService'
import useAuthStore from '../store/useAuthStore'

const { Title } = Typography
const { Option } = Select

const WorkflowsPage = () => {
  const { user } = useAuthStore()
  const [workflows, setWorkflows] = useState([])
  const [loading, setLoading] = useState(false)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedWorkflow, setSelectedWorkflow] = useState(null)
  const [form] = Form.useForm()

  // 获取工作流列表
  const fetchWorkflows = async () => {
    setLoading(true)
    try {
      const data = await workflowService.getWorkflows()
      setWorkflows(data)
    } catch (error) {
      message.error('获取工作流列表失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  // 启动工作流
  const handleStartWorkflow = async (values) => {
    if (!user) {
      message.error('请先登录')
      return
    }
    
    try {
      // 移除user_id，使用后端自动获取当前用户
      const { user_id, ...workflowData } = values
      const response = await workflowService.startWorkflow(workflowData)
      message.success(`工作流已启动: ${response.workflow_id}`)
      setCreateModalVisible(false)
      form.resetFields()
      fetchWorkflows()
    } catch (error) {
      message.error('启动工作流失败: ' + error.message)
    }
  }

  // 查看工作流详情
  const handleViewDetails = async (workflowId) => {
    try {
      const data = await workflowService.getWorkflowStatus(workflowId)
      setSelectedWorkflow(data)
      setDetailModalVisible(true)
    } catch (error) {
      message.error('获取工作流详情失败: ' + error.message)
    }
  }

  // 取消工作流
  const handleCancelWorkflow = async (workflowId) => {
    try {
      await workflowService.cancelWorkflow(workflowId)
      message.success('工作流已取消')
      fetchWorkflows()
    } catch (error) {
      message.error('取消工作流失败: ' + error.message)
    }
  }

  // 状态标签渲染
  const renderStatusTag = (status) => {
    const statusConfig = {
      'running': { color: 'blue', text: '运行中' },
      'completed': { color: 'green', text: '已完成' },
      'failed': { color: 'red', text: '失败' },
      'canceled': { color: 'orange', text: '已取消' },
      'started': { color: 'cyan', text: '已启动' }
    }

    const config = statusConfig[status] || { color: 'default', text: status }
    return <Tag color={config.color}>{config.text}</Tag>
  }

  // 表格列定义
  const columns = [
    {
      title: '工作流ID',
      dataIndex: 'workflow_id',
      key: 'workflow_id',
      width: 200,
      render: (text) => (
        <Tooltip title={text}>
          <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>
            {text?.substring(0, 20)}...
          </span>
        </Tooltip>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: renderStatusTag
    },
    {
      title: '开始时间',
      dataIndex: 'start_time',
      key: 'start_time',
      width: 180,
      render: (text) => text ? new Date(text).toLocaleString('zh-CN') : '-'
    },
    {
      title: '结束时间',
      dataIndex: 'end_time', 
      key: 'end_time',
      width: 180,
      render: (text) => text ? new Date(text).toLocaleString('zh-CN') : '-'
    },
    {
      title: '结果',
      dataIndex: 'result',
      key: 'result',
      width: 150,
      render: (result) => result ? (
        <Tooltip title="点击查看详细结果">
          <Button type="link" size="small" onClick={() => {
            Modal.info({
              title: '工作流结果',
              content: (
                <pre style={{
                  backgroundColor: '#f5f5f5',
                  padding: '12px',
                  borderRadius: '4px',
                  maxHeight: '400px',
                  overflow: 'auto'
                }}>
                  {JSON.stringify(result, null, 2)}
                </pre>
              ),
              width: 600
            })
          }}>
            查看结果
          </Button>
        </Tooltip>
      ) : '-'
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space>
          {record.temporal_ui_url && (
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => window.open(record.temporal_ui_url, '_blank')}
            >
              Temporal详情
            </Button>
          )}
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetails(record.workflow_id)}
          >
            详情
          </Button>
          {record.status === 'running' && (
            <Popconfirm
              title="确定要取消这个工作流吗？"
              onConfirm={() => handleCancelWorkflow(record.workflow_id)}
            >
              <Button
                type="link"
                size="small"
                danger
                icon={<StopOutlined />}
              >
                取消
              </Button>
            </Popconfirm>
          )}
        </Space>
      )
    }
  ]

  useEffect(() => {
    fetchWorkflows()
  }, [])

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2}>工作流管理</Title>
        <Space>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={fetchWorkflows}
          >
            刷新
          </Button>
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            启动工作流
          </Button>
        </Space>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={workflows}
          loading={loading}
          rowKey="workflow_id"
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 条`
          }}
        />
      </Card>

      {/* 创建工作流模态框 */}
      <Modal
        title="启动新工作流"
        visible={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false)
          form.resetFields()
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleStartWorkflow}
          initialValues={{ action: 'process_data' }}
        >
          <Form.Item
            label="当前用户"
          >
            <Input 
              value={user?.username || '未登录'}
              disabled
              style={{ backgroundColor: '#f5f5f5', color: '#666' }}
            />
          </Form.Item>

          <Form.Item
            name="action"
            label="操作类型"
            rules={[{ required: true, message: '请选择操作类型' }]}
          >
            <Select placeholder="请选择操作类型">
              <Option value="process_data">数据处理</Option>
              <Option value="send_email">发送邮件</Option>
              <Option value="backup_data">数据备份</Option>
              <Option value="generate_report">生成报告</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="workflow_id"
            label="自定义工作流ID（可选）"
          >
            <Input placeholder="留空则自动生成" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" icon={<PlayCircleOutlined />}>
                启动工作流
              </Button>
              <Button onClick={() => {
                setCreateModalVisible(false)
                form.resetFields()
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 工作流详情模态框 */}
      <Modal
        title="工作流详情"
        visible={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          selectedWorkflow?.temporal_ui_url && (
            <Button 
              key="temporal" 
              type="primary"
              icon={<EyeOutlined />}
              onClick={() => window.open(selectedWorkflow.temporal_ui_url, '_blank')}
            >
              在Temporal UI中查看
            </Button>
          ),
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {selectedWorkflow && (
          <div>
            <Card size="small" style={{ marginBottom: 16 }}>
              <p><strong>工作流ID:</strong> 
                <span style={{ fontFamily: 'monospace', marginLeft: 8 }}>
                  {selectedWorkflow.workflow_id}
                </span>
              </p>
              <p><strong>状态:</strong> {renderStatusTag(selectedWorkflow.status)}</p>
              {selectedWorkflow.start_time && (
                <p><strong>开始时间:</strong> {new Date(selectedWorkflow.start_time).toLocaleString('zh-CN')}</p>
              )}
              {selectedWorkflow.end_time && (
                <p><strong>结束时间:</strong> {new Date(selectedWorkflow.end_time).toLocaleString('zh-CN')}</p>
              )}
              {selectedWorkflow.error && (
                <p><strong>错误信息:</strong> <span style={{ color: '#ff4d4f' }}>{selectedWorkflow.error}</span></p>
              )}
            </Card>
            
            {selectedWorkflow.result && (
              <Card size="small" title="执行结果">
                <pre style={{ 
                  backgroundColor: '#f5f5f5', 
                  padding: 12, 
                  borderRadius: 4,
                  maxHeight: 300,
                  overflow: 'auto'
                }}>
                  {JSON.stringify(selectedWorkflow.result, null, 2)}
                </pre>
              </Card>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default WorkflowsPage