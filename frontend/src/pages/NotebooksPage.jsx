import {
  DeleteOutlined,
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
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [form] = Form.useForm();

  // 加载数据
  const loadData = async () => {
    setLoading(true);
    try {
      const [notebooksData, statusData] = await Promise.all([
        notebookService.getNotebooks(),
        notebookService.getServerStatus()
      ]);
      setNotebooks(notebooksData);
      setServerStatus(statusData);
    } catch (error) {
      console.error('Failed to load data:', error);
      message.error('Failed to load notebooks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // 创建 notebook
  const handleCreateNotebook = async (values) => {
    try {
      await notebookService.createNotebook(values.name);
      message.success('Notebook created successfully');
      setCreateModalVisible(false);
      form.resetFields();
      await loadData();
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
      await loadData();
    } catch (error) {
      console.error('Failed to delete notebook:', error);
      message.error('Failed to delete notebook');
    }
  };

  // 执行 notebook
  const handleExecuteNotebook = async (path) => {
    try {
      message.loading({ content: 'Executing notebook...', key: 'execute' });
      await notebookService.executeNotebook(path);
      message.success({ content: 'Notebook executed successfully', key: 'execute' });
    } catch (error) {
      console.error('Failed to execute notebook:', error);
      message.error({ content: 'Failed to execute notebook', key: 'execute' });
    }
  };


  // 在 Jupyter 中打开
  const handleOpenInJupyter = (record) => {
    const url = notebookService.getJupyterUrl(record.path, record.full_path);
    window.open(url, '_blank');
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
          <Tooltip title="Open in Jupyter">
            <Button
              type="primary"
              icon={<LinkOutlined />}
              onClick={() => handleOpenInJupyter(record)}
            />
          </Tooltip>
          <Tooltip title="Execute Notebook">
            <Button
              icon={<PlayCircleOutlined />}
              onClick={() => handleExecuteNotebook(record.path)}
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

      {/* 状态卡片 */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Jupyter Server"
              value={serverStatus.status || 'Unknown'}
              valueStyle={{
                color: serverStatus.status === 'running' ? '#3f8600' : '#cf1322',
              }}
              prefix={serverStatus.status === 'running' ? '🟢' : '🔴'}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Notebooks"
              value={notebooks.length}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
      </Row>

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
          <Button icon={<ReloadOutlined />} onClick={loadData} loading={loading}>
            Refresh
          </Button>
          <Button
            icon={<LinkOutlined />}
            onClick={() => window.open(notebookService.getJupyterUrl(), '_blank')}
          >
            Open Jupyter Lab
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
        />
      </Card>

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