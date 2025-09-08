import { Card as AntCard } from 'antd'

const Card = ({ 
  title,
  children,
  bordered = true,
  hoverable = false,
  loading = false,
  size = 'default',
  extra,
  ...props
}) => {
  return (
    <AntCard
      title={title}
      bordered={bordered}
      hoverable={hoverable}
      loading={loading}
      size={size}
      extra={extra}
      {...props}
    >
      {children}
    </AntCard>
  )
}

export default Card