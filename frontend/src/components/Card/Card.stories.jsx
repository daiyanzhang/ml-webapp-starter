import Card from './Card'
import Button from '../Button/Button'
import { MoreOutlined } from '@ant-design/icons'

export default {
  title: 'Components/Card',
  component: Card,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: '基于 Ant Design Card 封装的通用卡片组件，用于展示信息内容。'
      }
    }
  },
  tags: ['autodocs'],
}

export const Basic = {
  args: {
    title: '卡片标题',
    children: '这是卡片的内容区域，可以放置任何内容。'
  }
}

export const WithExtra = {
  args: {
    title: '带操作的卡片',
    extra: <Button type="link">更多</Button>,
    children: '这个卡片在标题右侧有额外的操作按钮。'
  }
}

export const Hoverable = {
  args: {
    hoverable: true,
    children: '这个卡片有悬停效果，鼠标悬停时会有阴影变化。'
  }
}

export const Loading = {
  args: {
    loading: true,
    title: '加载中的卡片'
  }
}

export const NoBorder = {
  args: {
    bordered: false,
    title: '无边框卡片',
    children: '这个卡片没有边框。'
  }
}

export const Small = {
  args: {
    size: 'small',
    title: '小尺寸卡片',
    children: '这是一个小尺寸的卡片。'
  }
}

export const WithActions = () => (
  <Card 
    title="用户信息" 
    extra={<MoreOutlined />}
    style={{ width: 300 }}
    actions={[
      <Button key="edit">编辑</Button>,
      <Button key="delete" type="text">删除</Button>
    ]}
  >
    <p>姓名：张三</p>
    <p>邮箱：zhangsan@example.com</p>
    <p>状态：活跃</p>
  </Card>
)