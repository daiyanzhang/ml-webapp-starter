import { Row, Col, Card, Statistic, Typography } from 'antd'
import { UserOutlined, TeamOutlined, SettingOutlined, SafetyCertificateOutlined } from '@ant-design/icons'

const { Title } = Typography

const DashboardPage = () => {
  return (
    <div>
      <Title level={2}>仪表板</Title>
      
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="用户总数"
              value={1}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="活跃用户"
              value={1}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="系统状态"
              value="正常"
              prefix={<SafetyCertificateOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="配置项"
              value={5}
              prefix={<SettingOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>
      
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col span={24}>
          <Card title="欢迎使用 Web App Starter" bordered={false}>
            <p>这是一个现代化的前后端分离 Web 应用脚手架。支持热模块替换(HMR)！</p>
            <p>特性包括：</p>
            <ul style={{ marginTop: 16 }}>
              <li>🚀 FastAPI 后端 + React 前端</li>
              <li>📚 自动生成的 API 文档</li>
              <li>🔒 JWT 身份验证</li>
              <li>🎨 Ant Design 组件库</li>
              <li>🐳 Docker 容器化部署</li>
              <li>📊 PostgreSQL 数据库</li>
            </ul>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default DashboardPage