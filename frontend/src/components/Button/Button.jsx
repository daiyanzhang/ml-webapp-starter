import { Button as AntButton } from 'antd'

const Button = ({ 
  children, 
  type = 'default', 
  size = 'middle',
  loading = false,
  disabled = false,
  onClick,
  ...props 
}) => {
  return (
    <AntButton
      type={type}
      size={size}
      loading={loading}
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      {children}
    </AntButton>
  )
}

export default Button