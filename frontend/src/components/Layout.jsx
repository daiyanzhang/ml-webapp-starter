import { useState } from 'react'
import { Layout, Menu, Button, Dropdown, Avatar, Space } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DashboardOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  CodeOutlined,
  BookOutlined,
  ApiOutlined,
  BranchesOutlined,
  NodeIndexOutlined,
  ThunderboltOutlined,
  RocketOutlined,
} from '@ant-design/icons'

import useAuthStore from '../store/useAuthStore'

const { Header, Sider, Content } = Layout

const AppLayout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  
  const { user, clearAuth } = useAuthStore()

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/users',
      icon: <UserOutlined />,
      label: '用户管理',
    },
    {
      key: '/workflows',
      icon: <NodeIndexOutlined />,
      label: '工作流管理',
    },
    {
      key: '/ray-jobs',
      icon: <ThunderboltOutlined />,
      label: 'Ray分布式计算',
    },
    {
      key: '/notebooks',
      icon: <RocketOutlined />,
      label: 'Jupyter Notebooks',
    },
    {
      key: 'developer',
      icon: <CodeOutlined />,
      label: '开发者工具',
      children: [
        {
          key: 'storybook',
          icon: <BookOutlined />,
          label: 'Storybook',
        },
        {
          key: 'api-docs',
          icon: <ApiOutlined />,
          label: 'API文档',
        },
        {
          key: 'temporal-ui',
          icon: <BranchesOutlined />,
          label: 'Temporal工作流',
        },
        {
          key: 'ray-dashboard',
          icon: <ThunderboltOutlined />,
          label: 'Ray Dashboard',
        },
        {
          key: 'jupyter-lab',
          icon: <RocketOutlined />,
          label: 'Jupyter Lab',
        },
      ],
    },
  ]

  const handleMenuClick = ({ key }) => {
    // 处理开发者工具的外部链接
    if (key === 'storybook') {
      window.open('http://localhost:6006', '_blank')
      return
    }
    if (key === 'api-docs') {
      window.open('http://localhost:8000/docs', '_blank')
      return
    }
    if (key === 'temporal-ui') {
      window.open('http://localhost:8080', '_blank')
      return
    }
    if (key === 'ray-dashboard') {
      window.open('http://localhost:8265', '_blank')
      return
    }
    if (key === 'jupyter-lab') {
      window.open('http://localhost:8888?token=webapp-starter-token', '_blank')
      return
    }
    
    // 普通页面导航
    navigate(key)
  }

  const handleLogout = () => {
    clearAuth()
    navigate('/login')
  }

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <Layout className="full-height">
      <Sider trigger={null} collapsible collapsed={collapsed}>
        <div className="logo" style={{ 
          height: 32, 
          background: 'rgba(255, 255, 255, 0.2)', 
          margin: 16, 
          borderRadius: 6,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontWeight: 'bold'
        }}>
          {collapsed ? 'WS' : 'Web Starter'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        <Header style={{ 
          padding: 0, 
          background: '#fff',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{
              fontSize: '16px',
              width: 64,
              height: 64,
            }}
          />
          <Space style={{ marginRight: 24 }}>
            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
            >
              <Space style={{ cursor: 'pointer' }}>
                <Avatar icon={<UserOutlined />} />
                <span>{user?.full_name || user?.username}</span>
              </Space>
            </Dropdown>
          </Space>
        </Header>
        <Content style={{ margin: 24, padding: 24, background: '#fff', borderRadius: 8 }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  )
}

export default AppLayout