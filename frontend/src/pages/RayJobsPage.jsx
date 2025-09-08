import { useState, useEffect } from 'react';
import { 
  Card, 
  Button, 
  Form, 
  Input, 
  Select, 
  Space, 
  message,
  Tabs,
  Statistic,
  Row,
  Col,
  Typography,
  Alert,
  Collapse,
  Badge,
  Spin,
  Table,
  Tag,
  Tooltip,
  Modal
} from 'antd';
import { 
  PlayCircleOutlined, 
  ReloadOutlined,
  ThunderboltOutlined,
  ClusterOutlined,
  ExperimentOutlined,
  BarChartOutlined,
  RobotOutlined,
  InfoCircleOutlined,
  HistoryOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { rayService } from '../services/rayService';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { Panel } = Collapse;
const { TabPane } = Tabs;

const RayJobsPage = () => {
  const [clusterStatus, setClusterStatus] = useState(null);
  const [availableJobs, setAvailableJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [lastResult, setLastResult] = useState(null);
  const [jobHistory, setJobHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);
  const [jobDetailModal, setJobDetailModal] = useState(false);
  const [pollingJobs, setPollingJobs] = useState(new Set());
  const [form] = Form.useForm();

  // 获取集群状态
  const fetchClusterStatus = async () => {
    try {
      const status = await rayService.getClusterStatus();
      setClusterStatus(status);
    } catch (error) {
      message.error('获取集群状态失败: ' + error.message);
      setClusterStatus({ status: 'error', error: error.message });
    }
  };

  // 获取可用任务
  const fetchAvailableJobs = async () => {
    try {
      const jobs = await rayService.getAvailableJobs();
      setAvailableJobs(jobs);
    } catch (error) {
      message.error('获取可用任务失败: ' + error.message);
    }
  };

  // 获取任务历史
  const fetchJobHistory = async () => {
    setHistoryLoading(true);
    try {
      const jobs = await rayService.getJobHistory(50, 0);
      setJobHistory(jobs);
    } catch (error) {
      message.error('获取任务历史失败: ' + error.message);
    } finally {
      setHistoryLoading(false);
    }
  };

  // 轮询任务状态
  const startJobStatusPolling = (jobId) => {
    setPollingJobs(prev => {
      if (prev.has(jobId)) return prev; // 已在轮询中
      const newSet = new Set(prev);
      newSet.add(jobId);
      return newSet;
    });
    
    const pollInterval = setInterval(async () => {
      try {
        const job = await rayService.getJobById(jobId);
        
        if (job.status === 'completed') {
          message.success(`任务完成: ${jobId}`);
          clearInterval(pollInterval);
          setPollingJobs(prev => {
            const newSet = new Set(prev);
            newSet.delete(jobId);
            return newSet;
          });
          fetchJobHistory(); // 刷新历史记录
        } else if (job.status === 'failed') {
          message.error(`任务失败: ${jobId} - ${job.error_message}`);
          clearInterval(pollInterval);
          setPollingJobs(prev => {
            const newSet = new Set(prev);
            newSet.delete(jobId);
            return newSet;
          });
          fetchJobHistory(); // 刷新历史记录
        } else if (job.status === 'running') {
          // 任务正在运行，继续轮询
          console.log(`任务运行中: ${jobId}`);
        }
      } catch (error) {
        console.error(`轮询任务状态失败: ${jobId}`, error);
        // 如果连续失败多次，停止轮询
      }
    }, 3000); // 每3秒轮询一次
    
    // 设置最大轮询时间（10分钟）
    setTimeout(() => {
      clearInterval(pollInterval);
      setPollingJobs(prev => {
        const newSet = new Set(prev);
        newSet.delete(jobId);
        return newSet;
      });
    }, 10 * 60 * 1000);
  };

  // 查看任务详情
  const handleViewJobDetail = async (jobId) => {
    try {
      const job = await rayService.getJobById(jobId);
      setSelectedJob(job);
      setJobDetailModal(true);
    } catch (error) {
      message.error('获取任务详情失败: ' + error.message);
    }
  };

  // 提交任务
  const handleSubmitJob = async (values) => {
    setSubmitting(true);
    try {
      const result = await rayService.submitJob(values.jobType, values.parameters || {});
      setLastResult(result);
      
      if (result.status === 'submitted') {
        message.success(`任务已提交: ${result.job_id}，正在执行中...`);
        // 开始轮询任务状态
        startJobStatusPolling(result.job_id);
      } else if (result.status === 'failed') {
        message.error(`任务提交失败: ${result.error}`);
      }
      
      // 刷新任务历史
      fetchJobHistory();
    } catch (error) {
      message.error('提交任务失败: ' + error.message);
    } finally {
      setSubmitting(false);
    }
  };

  // 快速测试任务
  const handleQuickTest = async (testType) => {
    setSubmitting(true);
    try {
      let result;
      
      switch (testType) {
        case 'simple':
          result = await rayService.testSimpleJob('prime_count');
          break;
        case 'data_processing':
          result = await rayService.testDataProcessing(3000, 300);
          break;
        case 'machine_learning':
          result = await rayService.testMachineLearning({
            n_samples: 2000,
            n_features: 10,
            n_classes: 3,
            n_models: 2
          });
          break;
        default:
          throw new Error('未知的测试类型');
      }
      
      setLastResult(result);
      
      if (result.status === 'submitted') {
        message.success(`测试任务已提交: ${result.job_id}，正在执行中...`);
        // 开始轮询任务状态
        startJobStatusPolling(result.job_id);
      } else if (result.status === 'failed') {
        message.error(`测试任务提交失败: ${result.error}`);
      }
      
      // 刷新任务历史
      fetchJobHistory();
    } catch (error) {
      message.error('快速测试失败: ' + error.message);
    } finally {
      setSubmitting(false);
    }
  };

  // 渲染集群状态
  const renderClusterStatus = () => {
    if (!clusterStatus) return null;

    const isConnected = clusterStatus.status === 'connected';
    
    return (
      <Card 
        title={
          <Space>
            <ClusterOutlined />
            Ray集群状态
            <Badge 
              status={isConnected ? 'success' : 'error'} 
              text={isConnected ? '已连接' : '断开连接'} 
            />
          </Space>
        }
        extra={
          <Button 
            icon={<ReloadOutlined />} 
            onClick={fetchClusterStatus}
            loading={loading}
          >
            刷新
          </Button>
        }
      >
        {isConnected ? (
          <Row gutter={16}>
            <Col span={6}>
              <Statistic 
                title="节点数" 
                value={clusterStatus.nodes} 
                prefix={<ClusterOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic 
                title="CPU核心" 
                value={clusterStatus.cluster_resources?.CPU || 0} 
                precision={0}
              />
            </Col>
            <Col span={6}>
              <Statistic 
                title="内存 (GB)" 
                value={(clusterStatus.cluster_resources?.memory || 0) / (1024 * 1024 * 1024)} 
                precision={1}
              />
            </Col>
            <Col span={6}>
              <Statistic 
                title="Ray版本" 
                value={clusterStatus.ray_version} 
                formatter={(value) => <Text code>{value}</Text>}
              />
            </Col>
          </Row>
        ) : (
          <Alert
            type="error"
            message="集群连接失败"
            description={clusterStatus.error || '无法连接到Ray集群'}
            showIcon
          />
        )}
      </Card>
    );
  };

  // 渲染任务结果
  const renderJobResult = () => {
    if (!lastResult) return null;

    const isSuccess = lastResult.status === 'completed';
    
    return (
      <Card 
        title={
          <Space>
            <ThunderboltOutlined />
            任务执行结果
            <Badge 
              status={isSuccess ? 'success' : 'error'} 
              text={isSuccess ? '执行成功' : '执行失败'} 
            />
          </Space>
        }
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Row gutter={16}>
            <Col span={8}>
              <Text strong>任务ID: </Text>
              <Text code>{lastResult.job_id}</Text>
            </Col>
            <Col span={8}>
              <Text strong>状态: </Text>
              <Badge 
                status={isSuccess ? 'success' : 'error'} 
                text={lastResult.status} 
              />
            </Col>
            <Col span={8}>
              <Text strong>提交时间: </Text>
              <Text>{new Date(lastResult.submitted_at).toLocaleString()}</Text>
            </Col>
          </Row>
          
          {isSuccess && lastResult.result && (
            <Collapse>
              <Panel header="执行结果详情" key="1">
                <pre style={{
                  backgroundColor: '#f5f5f5',
                  padding: '12px',
                  borderRadius: '4px',
                  maxHeight: '400px',
                  overflow: 'auto'
                }}>
                  {JSON.stringify(lastResult.result, null, 2)}
                </pre>
              </Panel>
            </Collapse>
          )}
          
          {!isSuccess && lastResult.error && (
            <Alert
              type="error"
              message="执行错误"
              description={lastResult.error}
              showIcon
            />
          )}
        </Space>
      </Card>
    );
  };

  // 渲染任务表单
  const renderJobForm = () => {
    return (
      <Card title={
        <Space>
          <RobotOutlined />
          提交Ray任务
        </Space>
      }>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmitJob}
        >
          <Form.Item
            name="jobType"
            label="任务类型"
            rules={[{ required: true, message: '请选择任务类型' }]}
          >
            <Select placeholder="选择任务类型" style={{ width: '100%' }}>
              {availableJobs.map(job => (
                <Option key={job.job_type} value={job.job_type}>
                  <Space>
                    <Text strong>{job.name}</Text>
                    <Text type="secondary">- {job.description}</Text>
                  </Space>
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="parameters"
            label="任务参数 (JSON格式)"
            extra='例如: {"data_size": 10000, "batch_size": 1000}'
          >
            <Input.TextArea 
              rows={4} 
              placeholder='{"param1": "value1", "param2": "value2"}'
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button 
                type="primary" 
                htmlType="submit" 
                loading={submitting}
                icon={<PlayCircleOutlined />}
              >
                提交任务
              </Button>
              
              <Button onClick={() => form.resetFields()}>
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    );
  };

  // 渲染快速测试
  const renderQuickTests = () => {
    return (
      <Card title={
        <Space>
          <ExperimentOutlined />
          快速测试
        </Space>
      }>
        <Row gutter={16}>
          <Col span={8}>
            <Card size="small" hoverable>
              <Space direction="vertical" align="center" style={{ width: '100%' }}>
                <BarChartOutlined style={{ fontSize: 24, color: '#1890ff' }} />
                <Text strong>简单计算</Text>
                <Text type="secondary">素数计算测试</Text>
                <Button 
                  type="primary"
                  size="small"
                  loading={submitting}
                  onClick={() => handleQuickTest('simple')}
                >
                  运行测试
                </Button>
              </Space>
            </Card>
          </Col>
          
          <Col span={8}>
            <Card size="small" hoverable>
              <Space direction="vertical" align="center" style={{ width: '100%' }}>
                <ThunderboltOutlined style={{ fontSize: 24, color: '#52c41a' }} />
                <Text strong>数据处理</Text>
                <Text type="secondary">批量数据分析</Text>
                <Button 
                  type="primary"
                  size="small" 
                  loading={submitting}
                  onClick={() => handleQuickTest('data_processing')}
                >
                  运行测试
                </Button>
              </Space>
            </Card>
          </Col>
          
          <Col span={8}>
            <Card size="small" hoverable>
              <Space direction="vertical" align="center" style={{ width: '100%' }}>
                <RobotOutlined style={{ fontSize: 24, color: '#fa8c16' }} />
                <Text strong>机器学习</Text>
                <Text type="secondary">模型并行训练</Text>
                <Button 
                  type="primary"
                  size="small"
                  loading={submitting}
                  onClick={() => handleQuickTest('machine_learning')}
                >
                  运行测试
                </Button>
              </Space>
            </Card>
          </Col>
        </Row>
      </Card>
    );
  };

  // 获取任务状态标签
  const getStatusTag = (status, jobId) => {
    const statusConfig = {
      'completed': { color: 'green', text: '已完成' },
      'failed': { color: 'red', text: '失败' },
      'running': { color: 'blue', text: '运行中' },
      'submitted': { color: 'orange', text: '已提交' }
    };
    
    const config = statusConfig[status] || { color: 'default', text: status };
    const isPolling = pollingJobs.has(jobId);
    
    return (
      <Space>
        <Tag color={config.color}>{config.text}</Tag>
        {isPolling && <Spin size="small" />}
      </Space>
    );
  };

  // 获取任务类型显示名称
  const getJobTypeName = (jobType) => {
    const typeNames = {
      'simple_job': '简单计算',
      'data_processing': '数据处理',
      'machine_learning': '机器学习'
    };
    return typeNames[jobType] || jobType;
  };

  // 渲染任务历史表格
  const renderJobHistory = () => {
    const columns = [
      {
        title: '任务ID',
        dataIndex: 'job_id',
        key: 'job_id',
        render: (text) => <Text code>{text}</Text>,
        ellipsis: true,
      },
      {
        title: '任务类型',
        dataIndex: 'job_type',
        key: 'job_type',
        render: (text) => getJobTypeName(text),
        width: 120,
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        render: (status, record) => getStatusTag(status, record.job_id),
        width: 120,
      },
      {
        title: '执行时间',
        dataIndex: 'execution_time',
        key: 'execution_time',
        render: (time) => time ? `${time.toFixed(2)}s` : '-',
        width: 100,
      },
      {
        title: '创建时间',
        dataIndex: 'created_at',
        key: 'created_at',
        render: (time) => time ? new Date(time).toLocaleString() : '-',
        width: 160,
      },
      {
        title: '操作',
        key: 'action',
        render: (_, record) => (
          <Space size="middle">
            <Tooltip title="查看详情">
              <Button 
                type="link" 
                icon={<EyeOutlined />} 
                onClick={() => handleViewJobDetail(record.job_id)}
              />
            </Tooltip>
          </Space>
        ),
        width: 80,
      },
    ];

    return (
      <Card 
        title={
          <Space>
            <HistoryOutlined />
            任务历史
          </Space>
        }
        extra={
          <Button 
            icon={<ReloadOutlined />} 
            onClick={fetchJobHistory}
            loading={historyLoading}
          >
            刷新
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={jobHistory}
          rowKey="id"
          loading={historyLoading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Card>
    );
  };

  // 渲染任务详情模态框
  const renderJobDetailModal = () => {
    if (!selectedJob) return null;

    const isSuccess = selectedJob.status === 'completed';
    
    return (
      <Modal
        title={
          <Space>
            <InfoCircleOutlined />
            任务详情: {selectedJob.job_id}
          </Space>
        }
        open={jobDetailModal}
        onCancel={() => setJobDetailModal(false)}
        footer={[
          <Button key="close" onClick={() => setJobDetailModal(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Row gutter={16}>
            <Col span={8}>
              <Text strong>任务类型: </Text>
              <Text>{getJobTypeName(selectedJob.job_type)}</Text>
            </Col>
            <Col span={8}>
              <Text strong>状态: </Text>
              {getStatusTag(selectedJob.status)}
            </Col>
            <Col span={8}>
              <Text strong>执行时间: </Text>
              <Text>{selectedJob.execution_time ? `${selectedJob.execution_time.toFixed(2)}s` : '-'}</Text>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Text strong>创建时间: </Text>
              <Text>{selectedJob.created_at ? new Date(selectedJob.created_at).toLocaleString() : '-'}</Text>
            </Col>
            <Col span={12}>
              <Text strong>完成时间: </Text>
              <Text>{selectedJob.completed_at ? new Date(selectedJob.completed_at).toLocaleString() : '-'}</Text>
            </Col>
          </Row>

          {selectedJob.parameters && (
            <div>
              <Text strong>任务参数:</Text>
              <pre style={{
                backgroundColor: '#f5f5f5',
                padding: '12px',
                borderRadius: '4px',
                marginTop: '8px',
                maxHeight: '200px',
                overflow: 'auto'
              }}>
                {JSON.stringify(selectedJob.parameters, null, 2)}
              </pre>
            </div>
          )}

          {isSuccess && selectedJob.result && (
            <div>
              <Text strong>执行结果:</Text>
              <pre style={{
                backgroundColor: '#f5f5f5',
                padding: '12px',
                borderRadius: '4px',
                marginTop: '8px',
                maxHeight: '300px',
                overflow: 'auto'
              }}>
                {JSON.stringify(selectedJob.result, null, 2)}
              </pre>
            </div>
          )}

          {!isSuccess && selectedJob.error_message && (
            <Alert
              type="error"
              message="执行错误"
              description={selectedJob.error_message}
              showIcon
            />
          )}
        </Space>
      </Modal>
    );
  };

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchClusterStatus(),
      fetchAvailableJobs(),
      fetchJobHistory()
    ]).finally(() => {
      setLoading(false);
    });
  }, []);

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={2}>
            <Space>
              <ThunderboltOutlined />
              Ray分布式计算
            </Space>
          </Title>
          <Paragraph>
            Ray是一个开源的分布式计算框架，支持并行计算、机器学习和分布式应用。
            通过这个界面，你可以提交各种类型的Ray任务并查看执行结果。
          </Paragraph>
        </div>

        {loading ? (
          <Card>
            <Spin size="large" style={{ display: 'block', textAlign: 'center', padding: '50px' }} />
          </Card>
        ) : (
          <Tabs defaultActiveKey="1">
            <TabPane 
              tab={
                <span>
                  <InfoCircleOutlined />
                  集群状态
                </span>
              } 
              key="1"
            >
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                {renderClusterStatus()}
                {renderQuickTests()}
              </Space>
            </TabPane>
            
            <TabPane 
              tab={
                <span>
                  <PlayCircleOutlined />
                  任务提交
                </span>
              } 
              key="2"
            >
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                {renderJobForm()}
                {renderJobResult()}
              </Space>
            </TabPane>
            
            <TabPane 
              tab={
                <span>
                  <HistoryOutlined />
                  任务历史
                </span>
              } 
              key="3"
            >
              {renderJobHistory()}
            </TabPane>
          </Tabs>
        )}
        
        {renderJobDetailModal()}
      </Space>
    </div>
  );
};

export default RayJobsPage;