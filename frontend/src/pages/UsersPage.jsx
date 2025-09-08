import { useState } from 'react'
import { 
  Table, 
  Button, 
  Space, 
  Typography, 
  Modal, 
  Form, 
  Input, 
  Switch, 
  message,
  Popconfirm,
  Tag
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { userService } from '../services/user'
import useAuthStore from '../store/useAuthStore'

const { Title } = Typography

const UsersPage = () => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingUser, setEditingUser] = useState(null)
  const [form] = Form.useForm()
  const queryClient = useQueryClient()
  const { user: currentUser } = useAuthStore()

  // 获取用户列表
  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: userService.getUsers,
  })
  
  // 创建用户
  const createUserMutation = useMutation({
    mutationFn: userService.createUser,
    onSuccess: () => {
      message.success('用户创建成功')
      setIsModalOpen(false)
      form.resetFields()
      queryClient.invalidateQueries(['users'])
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '创建失败')
    },
  })

  // 更新用户
  const updateUserMutation = useMutation({
    mutationFn: ({ userId, ...userData }) => 
      userService.updateUser(userId, userData),
    onSuccess: () => {
      message.success('用户更新成功')
      setIsModalOpen(false)
      setEditingUser(null)
      form.resetFields()
      queryClient.invalidateQueries(['users'])
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '更新失败')
    },
  })

  const handleAddUser = () => {
    setEditingUser(null)
    setIsModalOpen(true)
    form.resetFields()
  }

  const handleEditUser = (user) => {
    setEditingUser(user)
    setIsModalOpen(true)
    form.setFieldsValue({
      ...user,
      password: '' // 不显示原密码
    })
  }

  const handleSubmit = (values) => {
    // 如果密码为空且是编辑模式，删除密码字段
    if (!values.password && editingUser) {
      delete values.password
    }

    if (editingUser) {
      updateUserMutation.mutate({
        userId: editingUser.id,
        ...values,
      })
    } else {
      createUserMutation.mutate(values)
    }
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '全名',
      dataIndex: 'full_name',
      key: 'full_name',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? '活跃' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '超级用户',
      dataIndex: 'is_superuser',
      key: 'is_superuser',
      render: (isSuperuser) => (
        <Tag color={isSuperuser ? 'blue' : 'default'}>
          {isSuperuser ? '是' : '否'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button 
            type="primary" 
            size="small" 
            icon={<EditOutlined />}
            onClick={() => handleEditUser(record)}
          >
            编辑
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>用户管理</Title>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={handleAddUser}
        >
          添加用户
        </Button>
      </div>
      
      <Table
        columns={columns}
        dataSource={users}
        rowKey="id"
        loading={isLoading}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`,
        }}
      />

      <Modal
        title={editingUser ? '编辑用户' : '添加用户'}
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false)
          setEditingUser(null)
          form.resetFields()
        }}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            is_active: true,
            is_superuser: false,
          }}
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="full_name"
            label="全名"
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="password"
            label="密码"
            rules={editingUser ? [] : [{ required: true, message: '请输入密码' }]}
          >
            <Input.Password placeholder={editingUser ? '留空则不修改密码' : '请输入密码'} />
          </Form.Item>
          
          <Form.Item
            name="is_active"
            label="状态"
            valuePropName="checked"
          >
            <Switch checkedChildren="活跃" unCheckedChildren="禁用" />
          </Form.Item>
          
          <Form.Item
            name="is_superuser"
            label="超级用户"
            valuePropName="checked"
          >
            <Switch checkedChildren="是" unCheckedChildren="否" />
          </Form.Item>
          
          <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
            <Space>
              <Button onClick={() => {
                setIsModalOpen(false)
                setEditingUser(null)
                form.resetFields()
              }}>
                取消
              </Button>
              <Button 
                type="primary" 
                htmlType="submit"
                loading={createUserMutation.isPending || updateUserMutation.isPending}
              >
                {editingUser ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default UsersPage