import { useState } from 'react'
import { Form, Input, Button, Card, Typography, message, Row, Col } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'

import { authService } from '../services/auth'
import useAuthStore from '../store/useAuthStore'

const { Title } = Typography

const LoginPage = () => {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()

  const loginMutation = useMutation({
    mutationFn: authService.login,
    onSuccess: async (tokenData) => {
      try {
        // 先保存token
        setAuth(tokenData.access_token, null)
        
        // 然后获取用户信息
        const user = await authService.getCurrentUser()
        setAuth(tokenData.access_token, user)
        message.success('登录成功')
        navigate('/')
      } catch (error) {
        message.error('获取用户信息失败')
        console.error('获取用户信息错误:', error)
      }
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || '登录失败')
    },
  })

  const handleSubmit = (values) => {
    loginMutation.mutate(values)
  }

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Row justify="center" style={{ width: '100%' }}>
        <Col xs={20} sm={16} md={12} lg={8} xl={6}>
          <Card style={{ borderRadius: 12, boxShadow: '0 8px 32px rgba(0,0,0,0.1)' }}>
            <div className="text-center mb-16">
              <Title level={2} style={{ color: '#1890ff', marginBottom: 8 }}>
                Web App Starter
              </Title>
              <Typography.Text type="secondary">
                请登录您的账户
              </Typography.Text>
            </div>
            
            <Form
              name="login"
              onFinish={handleSubmit}
              autoComplete="off"
              size="large"
            >
              <Form.Item
                name="username"
                rules={[
                  { required: true, message: '请输入用户名' },
                ]}
              >
                <Input
                  prefix={<UserOutlined />}
                  placeholder="用户名"
                />
              </Form.Item>

              <Form.Item
                name="password"
                rules={[
                  { required: true, message: '请输入密码' },
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="密码"
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  className="full-width"
                  loading={loginMutation.isPending}
                  style={{ height: 48 }}
                >
                  登录
                </Button>
              </Form.Item>
            </Form>
            
            <div className="text-center">
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                默认管理员账户: admin / admin123
              </Typography.Text>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default LoginPage