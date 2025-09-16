import {
  DeleteOutlined,
  EyeOutlined,
  FileTextOutlined,
  LinkOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import {
  Button,
  Card,
  Col,
  Form,
  Input,
  message,
  Modal,
  Popconfirm,
  Row,
  Space,
  Statistic,
  Table,
  Tooltip,
  Typography
} from 'antd';
import { useEffect, useState } from 'react';
import notebookService from '../services/notebookService';

const { Title, Text } = Typography;

const NotebooksPage = () => {
  const [notebooks, setNotebooks] = useState([]);
  const [serverStatus, setServerStatus] = useState({});
  const [loading, setLoading] = useState(false);
  const [sessionLoading, setSessionLoading] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [form] = Form.useForm();

  // 检查session状态
  const isSessionRunning = serverStatus.status === 'running';

  // 只加载服务器状态
  const loadServerStatus = async () => {
    setLoading(true);
    try {
      const statusData = await notebookService.getServerStatus();
      setServerStatus(statusData);
    } catch (error) {
      console.error('Failed to load server status:', error);
      message.error('Failed to load server status');
    } finally {
      setLoading(false);
    }
  };

  // 加载notebooks（仅在session运行时）
  const loadNotebooks = async () => {
    if (!isSessionRunning) return;

    setLoading(true);
    try {
      const notebooksData = await notebookService.getNotebooks();
      setNotebooks(notebooksData);
    } catch (error) {
      console.error('Failed to load notebooks:', error);
      message.error('Failed to load notebooks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadServerStatus();
  }, []);

  useEffect(() => {
    if (isSessionRunning) {
      loadNotebooks();
    } else {
      setNotebooks([]);
    }
  }, [isSessionRunning]);

  // 创建 notebook
  const handleCreateNotebook = async (values) => {
    try {
      await notebookService.createNotebook(values.name);
      message.success('Notebook created successfully');
      setCreateModalVisible(false);
      form.resetFields();
      await loadNotebooks();
    } catch (error) {
      console.error('Failed to create notebook:', error);
      message.error('Failed to create notebook');
    }
  };

  // 删除 notebook
  const handleDeleteNotebook = async (path) => {
    try {
      await notebookService.deleteNotebook(path);
      message.success('Notebook deleted successfully');
      await loadNotebooks();
    } catch (error) {
      console.error('Failed to delete notebook:', error);
      message.error('Failed to delete notebook');
    }
  };

  // 打开 notebook
  const handleOpenNotebook = async (path) => {
    try {
      // 通过JupyterHub打开notebook
      const jupyterUrl = `http://localhost:8001/user/admin/notebooks/${path}`;
      window.open(jupyterUrl, '_blank');
      message.success('Opening notebook in JupyterHub');
    } catch (error) {
      console.error('Failed to open notebook:', error);
      message.error('Failed to open notebook');
    }
  };


  // 启动 JupyterHub 会话
  const handleStartSession = async () => {
    try {
      setSessionLoading(true);
      message.loading({ content: 'Starting Jupyter session...', key: 'session' });
      const result = await notebookService.startSession();

      if (result.url) {
        message.success({ content: 'Session started successfully!', key: 'session' });
        // 刷新服务器状态
        await loadServerStatus();
      } else {
        message.info({ content: result.message || 'Session is starting...', key: 'session' });
        // 等待一段时间后刷新状态
        setTimeout(() => {
          loadServerStatus();
        }, 3000);
      }
    } catch (error) {
      console.error('Failed to start session:', error);
      message.error({ content: 'Failed to start Jupyter session', key: 'session' });
    } finally {
      setSessionLoading(false);
    }
  };

  // 停止 JupyterHub 会话
  const handleStopSession = async () => {
    try {
      await notebookService.stopSession();
      message.success('Jupyter session stopped');
      await loadServerStatus(); // 刷新状态
    } catch (error) {
      console.error('Failed to stop session:', error);
      message.error('Failed to stop Jupyter session');
    }
  };

  // 打开 JupyterHub
  const handleOpenJupyterHub = () => {
    notebookService.openJupyterHub();
  };

  // 表格列定义
  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text) => (
        <Space>
          <FileTextOutlined style={{ color: '#1890ff' }} />
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: 'Path',
      dataIndex: 'path',
      key: 'path',
      render: (text) => <Text code>{text}</Text>,
    },
    {
      title: 'Last Modified',
      dataIndex: 'last_modified',
      key: 'last_modified',
      render: (text) => new Date(text).toLocaleString(),
    },
    {
      title: 'Size',
      dataIndex: 'size',
      key: 'size',
      render: (size) => `${(size / 1024).toFixed(1)} KB`,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="Open Notebook">
            <Button
              icon={<EyeOutlined />}
              onClick={() => handleOpenNotebook(record.path)}
            />
          </Tooltip>
          <Popconfirm
            title="Are you sure to delete this notebook?"
            onConfirm={() => handleDeleteNotebook(record.path)}
            okText="Yes"
            cancelText="No"
          >
            <Button icon={<DeleteOutlined />} danger />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>
          <FileTextOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
          Jupyter Notebooks
        </Title>
        <Text type="secondary">
          Create, edit, and run Jupyter notebooks for data analysis and experimentation.
        </Text>
      </div>

      {/* 服务器状态卡片 */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="Jupyter Server Status"
              value={serverStatus.status || 'Not Started'}
              valueStyle={{
                color: serverStatus.status === 'running' ? '#3f8600' : '#cf1322',
              }}
              prefix={serverStatus.status === 'running' ? '🟢' : '🔴'}
            />
          </Card>
        </Col>
        {isSessionRunning && (
          <Col span={8}>
            <Card>
              <Statistic
                title="Total Notebooks"
                value={notebooks.length}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
        )}
      </Row>

      {!isSessionRunning ? (
        // 未启动Session的界面
        <Card>
          <div style={{ textAlign: 'center', padding: '60px 20px' }}>
            <PlayCircleOutlined
              style={{ fontSize: '64px', color: '#1890ff', marginBottom: '24px' }}
            />
            <Title level={3}>No Jupyter Session Running</Title>
            <Text type="secondary" style={{ display: 'block', marginBottom: '32px' }}>
              Start a Jupyter session to create and manage your notebooks.
              Each session runs in an isolated environment for your security and privacy.
            </Text>
            <Button
              type="primary"
              size="large"
              icon={<PlayCircleOutlined />}
              onClick={handleStartSession}
              loading={sessionLoading}
            >
              Start Jupyter Session
            </Button>
          </div>
        </Card>
      ) : (
        // 已启动Session的界面
        <>
          {/* 操作按钮 */}
          <div style={{ marginBottom: '16px' }}>
            <Space>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setCreateModalVisible(true)}
              >
                New Notebook
              </Button>
              <Button icon={<ReloadOutlined />} onClick={loadNotebooks} loading={loading}>
                Refresh
              </Button>
              <Button
                icon={<LinkOutlined />}
                onClick={handleOpenJupyterHub}
              >
                Open JupyterHub
              </Button>
              <Button
                danger
                onClick={handleStopSession}
              >
                Stop Session
              </Button>
            </Space>
          </div>

          {/* Notebooks 表格 */}
          <Card>
            <Table
              columns={columns}
              dataSource={notebooks}
              rowKey="path"
              loading={loading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `Total ${total} notebooks`,
              }}
              locale={{
                emptyText: notebooks.length === 0 && !loading ? 'No notebooks yet. Click "New Notebook" to create one.' : undefined
              }}
            />
          </Card>
        </>
      )}

      {/* 创建 Notebook 模态框 */}
      <Modal
        title="Create New Notebook"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
        }}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateNotebook}
        >
          <Form.Item
            name="name"
            label="Notebook Name"
            rules={[
              { required: true, message: 'Please enter notebook name' },
              { pattern: /^[a-zA-Z0-9_-]+$/, message: 'Only letters, numbers, hyphens, and underscores allowed' }
            ]}
          >
            <Input
              placeholder="my-notebook"
              suffix=".ipynb"
            />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                Create
              </Button>
              <Button onClick={() => setCreateModalVisible(false)}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default NotebooksPage;