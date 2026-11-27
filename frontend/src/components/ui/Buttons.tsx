import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  size?: 'md' | 'sm';
  icon?: ReactNode;
  loading?: boolean;
}

export function PrimaryButton({
  children,
  size = 'md',
  icon,
  loading = false,
  disabled,
  className = '',
  type = 'button',
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={`dc-btn dc-btn-primary ${size === 'sm' ? 'dc-btn-sm' : ''} ${className}`}
      {...rest}
    >
      {icon}
      <span>{loading ? 'Đang xử lý...' : children}</span>
    </button>
  );
}

export function SecondaryButton({
  children,
  size = 'md',
  icon,
  loading = false,
  disabled,
  className = '',
  variant = 'default',
  type = 'button',
  ...rest
}: ButtonProps & { variant?: 'default' | 'blue' | 'danger' }) {
  const variantClass =
    variant === 'blue'
      ? 'dc-btn-outline-blue'
      : variant === 'danger'
        ? 'dc-btn-danger'
        : 'dc-btn-secondary';

  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={`dc-btn ${variantClass} ${size === 'sm' ? 'dc-btn-sm' : ''} ${className}`}
      {...rest}
    >
      {icon}
      <span>{loading ? 'Đang xử lý...' : children}</span>
    </button>
  );
}
