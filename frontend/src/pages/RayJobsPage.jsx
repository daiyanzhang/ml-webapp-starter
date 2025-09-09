import { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Select,
  Table,
  Space,
  Tag,
  Modal,
  Alert,
  Tabs,
  Descriptions,
  message,
  Row,
  Col,
  Statistic,
  InputNumber
} from 'antd';
import {
  PlayCircleOutlined,
  GithubOutlined,
  StopOutlined,
  ReloadOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { rayJobService } from '../services/rayJobService';

const { TextArea } = Input;

const RayJobsPage = () => {
  const [form] = Form.useForm();
  const [jobs, setJobs] = useState([]);
  const [templates, setTemplates] = useState({});
  const [clusterStatus, setClusterStatus] = useState({});
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);

  useEffect(() => {
    loadJobs();
    loadTemplates();
    loadClusterStatus();
    
    // 定期刷新作业状态
    const interval = setInterval(loadJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadJobs = async () => {
    try {
      setLoading(true);
      const response = await rayJobService.listJobs();
      setJobs(response);
    } catch (error) {
      console.error('Failed to load jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await rayJobService.getTemplates();
      setTemplates(response);
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const loadClusterStatus = async () => {
    try {
      const response = await rayJobService.getClusterStatus();
      setClusterStatus(response);
    } catch (error) {
      console.error('Failed to load cluster status:', error);
    }
  };

  const handleSubmitJob = async (values) => {
    setSubmitting(true);
    try {
      const response = await rayJobService.submitGitHubJob(values);
      if (response.success) {
        message.success(`Job ${response.job_id} submitted successfully!`);
        form.resetFields();
        setValidationResult(null);
        await loadJobs();
      }
    } catch (error) {
      message.error(`Failed to submit job: ${error.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleValidateRepo = async () => {
    const repoUrl = form.getFieldValue('github_repo');
    const branch = form.getFieldValue('branch') || 'main';
    const entryPoint = form.getFieldValue('entry_point') || 'main.py';
    
    if (!repoUrl) {
      message.warning('Please enter GitHub repository URL');
      return;
    }

    setValidating(true);
    try {
      const result = await rayJobService.validateRepository(repoUrl, branch, entryPoint);
      setValidationResult(result);
      
      if (result.success) {
        message.success('Repository validation passed!');
      } else {
        message.error('Repository validation failed');
      }
    } catch (error) {
      message.error(`Validation failed: ${error.message}`);
      setValidationResult({ success: false, error: error.message });
    } finally {
      setValidating(false);
    }
  };

  const handleCancelJob = async (jobId) => {
    try {
      await rayJobService.cancelJob(jobId);
      message.success(`Job ${jobId} cancelled successfully`);
      await loadJobs();
    } catch (error) {
      message.error(`Failed to cancel job: ${error.message}`);
    }
  };

  const showJobDetail = (job) => {
    setSelectedJob(job);
    setDetailModalVisible(true);
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending': 'orange',
      'running': 'blue', 
      'completed': 'green',
      'failed': 'red',
      'cancelled': 'default'
    };
    return colors[status] || 'default';
  };

  const getStatusIcon = (status) => {
    const icons = {
      'pending': <ClockCircleOutlined />,
      'running': <PlayCircleOutlined spin />,
      'completed': <CheckCircleOutlined />,
      'failed': <ExclamationCircleOutlined />,
      'cancelled': <StopOutlined />
    };
    return icons[status] || <ClockCircleOutlined />;
  };

  const columns = [
    {
      title: 'Job ID',
      dataIndex: 'job_id',
      key: 'job_id',
      render: (text) => <code>{text.slice(-8)}</code>
    },
    {
      title: 'Repository',
      dataIndex: 'github_repo',
      key: 'github_repo',
      render: (text, record) => (
        <div>
          <div><GithubOutlined /> {text}</div>
          <small style={{ color: '#666' }}>
            {record.branch} / {record.entry_point}
          </small>
        </div>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={getStatusColor(status)} icon={getStatusIcon(status)}>
          {status.toUpperCase()}
        </Tag>
      )
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => new Date(text).toLocaleString()
    },
    {
      title: 'Duration',
      key: 'duration',
      render: (_, record) => {
        if (record.started_at && record.completed_at) {
          const duration = Math.round(
            (new Date(record.completed_at) - new Date(record.started_at)) / 1000
          );
          return `${duration}s`;
        }
        return record.started_at ? 'Running...' : '-';
      }
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => showJobDetail(record)}
            size="small"
          >
            Detail
          </Button>
          {record.status === 'running' && (
            <Button
              type="text"
              danger
              icon={<StopOutlined />}
              onClick={() => handleCancelJob(record.job_id)}
              size="small"
            >
              Cancel
            </Button>
          )}
        </Space>
      )
    }
  ];

  const renderValidationResult = () => {
    if (!validationResult) return null;

    if (validationResult.success) {
      const { validation } = validationResult;
      return (
        <Alert
          type="success"
          message="Repository Validation Passed"
          description={
            <div>
              <p><strong>Entry point:</strong> {validation.info.entry_point_exists ? '✅ Found' : '❌ Missing'}</p>
              <p><strong>Dependencies:</strong> {validation.info.has_requirements ? '✅ requirements.txt found' : '⚠️ No requirements.txt'}</p>
              <p><strong>Size:</strong> {validation.info.size_mb}MB ({validation.info.file_count} files)</p>
              {validation.warnings.length > 0 && (
                <p><strong>Warnings:</strong> {validation.warnings.join(', ')}</p>
              )}
            </div>
          }
          style={{ marginBottom: 16 }}
        />
      );
    } else {
      return (
        <Alert
          type="error"
          message="Repository Validation Failed"
          description={validationResult.error}
          style={{ marginBottom: 16 }}
        />
      );
    }
  };

  const submitJobForm = (
    <Card title="Submit Ray Job from GitHub" extra={
      <Button icon={<ReloadOutlined />} onClick={loadTemplates}>
        Refresh Templates
      </Button>
    }>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmitJob}
        initialValues={{
          template_type: 'custom',
          branch: 'main',
          entry_point: 'main.py',
          job_config: {
            memory: 1024,
            cpu: 1.0,
            gpu: 0,
            timeout: 3600,
            retry: 3
          }
        }}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="template_type"
              label="Template Type"
              tooltip="Choose the type of Ray job template"
            >
              <Select 
                options={Object.entries(templates.templates || {}).map(([key, template]) => ({
                  value: key,
                  label: `${template.name} - ${template.description}`
                }))}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="github_repo"
              label="GitHub Repository"
              rules={[{ required: true, message: 'Please enter GitHub repository' }]}
              tooltip="Format: username/repository or full GitHub URL"
            >
              <Input
                prefix={<GithubOutlined />}
                placeholder="username/repository-name"
                addonAfter={
                  <Button
                    type="link"
                    size="small"
                    loading={validating}
                    onClick={handleValidateRepo}
                  >
                    Validate
                  </Button>
                }
              />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="branch"
              label="Branch"
              tooltip="Git branch to use"
            >
              <Input placeholder="main" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="entry_point"
              label="Entry Point"
              tooltip="Python file to execute (e.g., main.py, src/main.py, jobs/data_processor.py)"
            >
              <Input placeholder="main.py" />
            </Form.Item>
          </Col>
        </Row>

        {renderValidationResult()}

        <Card title="Job Configuration" size="small" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name={['job_config', 'memory']} label="Memory (MB)">
                <InputNumber min={512} max={32768} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name={['job_config', 'cpu']} label="CPU Cores">
                <InputNumber min={0.5} max={32} step={0.5} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name={['job_config', 'gpu']} label="GPU Count">
                <InputNumber min={0} max={8} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name={['job_config', 'timeout']} label="Timeout (s)">
                <InputNumber min={60} max={86400} />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Form.Item
          name="config"
          label="Job Parameters (JSON)"
          tooltip="Additional parameters to pass to your code"
        >
          <TextArea
            rows={4}
            placeholder='{"input_data": "path/to/data.csv", "output_path": "results/"}'
          />
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={submitting}
            size="large"
            icon={<PlayCircleOutlined />}
          >
            Submit Ray Job
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );

  const jobManagementPanel = (
    <Card
      title="Ray Jobs"
      extra={
        <Button icon={<ReloadOutlined />} onClick={loadJobs}>
          Refresh
        </Button>
      }
    >
      <Table
        columns={columns}
        dataSource={jobs}
        rowKey="job_id"
        loading={loading}
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total, range) =>
            `${range[0]}-${range[1]} of ${total} jobs`
        }}
      />
    </Card>
  );

  const tabItems = [
    {
      key: 'submit',
      label: 'Submit Job',
      children: submitJobForm
    },
    {
      key: 'manage',
      label: 'Job Management',
      children: jobManagementPanel
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Row gutter={24} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Ray Cluster Status"
              value={clusterStatus.status || 'Unknown'}
              valueStyle={{ color: clusterStatus.status === 'connected' ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Cluster Nodes"
              value={clusterStatus.nodes || 0}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Active Jobs"
              value={jobs.filter(job => job.status === 'running').length}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Jobs"
              value={jobs.length}
            />
          </Card>
        </Col>
      </Row>

      <Tabs 
        defaultActiveKey="submit" 
        size="large"
        items={tabItems}
      />

      {/* Job Detail Modal */}
      <Modal
        title={`Job Detail: ${selectedJob?.job_id?.slice(-8)}`}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedJob && (
          <div>
            <Descriptions column={2} bordered>
              <Descriptions.Item label="Job ID">{selectedJob.job_id}</Descriptions.Item>
              <Descriptions.Item label="Status">
                <Tag color={getStatusColor(selectedJob.status)} icon={getStatusIcon(selectedJob.status)}>
                  {selectedJob.status.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Repository">{selectedJob.github_repo}</Descriptions.Item>
              <Descriptions.Item label="Branch">{selectedJob.branch}</Descriptions.Item>
              <Descriptions.Item label="Entry Point">{selectedJob.entry_point}</Descriptions.Item>
              <Descriptions.Item label="Created">{new Date(selectedJob.created_at).toLocaleString()}</Descriptions.Item>
              {selectedJob.started_at && (
                <Descriptions.Item label="Started">{new Date(selectedJob.started_at).toLocaleString()}</Descriptions.Item>
              )}
              {selectedJob.completed_at && (
                <Descriptions.Item label="Completed">{new Date(selectedJob.completed_at).toLocaleString()}</Descriptions.Item>
              )}
            </Descriptions>

            {selectedJob.result && (
              <Card title="Result" style={{ marginTop: 16 }}>
                <pre style={{ background: '#f5f5f5', padding: 16, borderRadius: 4, overflow: 'auto' }}>
                  {JSON.stringify(selectedJob.result, null, 2)}
                </pre>
              </Card>
            )}

            {selectedJob.error && (
              <Alert
                type="error"
                message="Job Error"
                description={selectedJob.error}
                style={{ marginTop: 16 }}
              />
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default RayJobsPage;