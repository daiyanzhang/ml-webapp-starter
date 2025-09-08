import Button from './Button'
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons'

export default {
  title: 'Components/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: '基于 Ant Design Button 封装的通用按钮组件，支持多种类型和状态。'
      }
    }
  },
  tags: ['autodocs'],
  argTypes: {
    type: {
      control: { type: 'select' },
      options: ['default', 'primary', 'dashed', 'text', 'link']
    },
    size: {
      control: { type: 'select' },
      options: ['small', 'middle', 'large']
    },
    loading: {
      control: { type: 'boolean' }
    },
    disabled: {
      control: { type: 'boolean' }
    }
  }
}

export const Default = {
  args: {
    children: '默认按钮'
  }
}

export const Primary = {
  args: {
    type: 'primary',
    children: '主要按钮'
  }
}

export const WithIcon = {
  args: {
    type: 'primary',
    icon: <PlusOutlined />,
    children: '添加'
  }
}

export const Loading = {
  args: {
    type: 'primary',
    loading: true,
    children: '加载中'
  }
}

export const Disabled = {
  args: {
    disabled: true,
    children: '禁用状态'
  }
}

export const AllSizes = () => (
  <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
    <Button size="small">小按钮</Button>
    <Button size="middle">中等按钮</Button>
    <Button size="large">大按钮</Button>
  </div>
)

export const AllTypes = () => (
  <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
    <Button type="default">默认</Button>
    <Button type="primary">主要</Button>
    <Button type="dashed">虚线</Button>
    <Button type="text">文本</Button>
    <Button type="link">链接</Button>
  </div>
)