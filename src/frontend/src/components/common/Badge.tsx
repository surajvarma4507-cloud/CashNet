import React from 'react';

export type BadgeVariant =
  | 'critical'
  | 'high'
  | 'moderate'
  | 'low'
  | 'neutral'
  | 'teal'
  | 'blue'
  | 'amber'
  | 'danger'
  | 'warning'
  | 'info'
  | 'primary'
  | 'success';

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
  icon?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'neutral',
  children,
  className = '',
  icon,
}) => {
  // Normalize alias variants to CSS badge styles
  const normalizedVariant =
    variant === 'danger'
      ? 'critical'
      : variant === 'warning'
      ? 'high'
      : variant === 'info' || variant === 'primary'
      ? 'teal'
      : variant === 'success'
      ? 'low'
      : variant;

  const variantClass = `badge-${normalizedVariant}`;
  return (
    <span className={`badge ${variantClass} ${className}`}>
      {icon && <span className="inline-flex items-center">{icon}</span>}
      <span>{children}</span>
    </span>
  );
};
