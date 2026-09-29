import React from 'react';
import { Badge } from './Badge';

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const normalized = (status || '').toLowerCase().replace(/_/g, ' ');

  let variant: 'critical' | 'high' | 'moderate' | 'low' | 'neutral' | 'teal' = 'neutral';
  let label = normalized;

  if (normalized === 'under investigation') {
    variant = 'teal';
    label = 'Under Investigation';
  } else if (normalized === 'registered') {
    variant = 'high';
    label = 'Registered (Pending)';
  } else if (normalized === 'resolved' || normalized === 'closed') {
    variant = 'low';
    label = 'Resolved';
  } else if (normalized === 'active') {
    variant = 'teal';
    label = 'Active';
  } else if (normalized === 'completed') {
    variant = 'low';
    label = 'Completed';
  } else if (normalized === 'pending') {
    variant = 'high';
    label = 'Pending';
  }

  return <Badge variant={variant}>{label}</Badge>;
};
