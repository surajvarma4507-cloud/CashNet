import React from 'react';
import { AlertOctagon, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { Badge } from './Badge';

interface RiskBadgeProps {
  tier: string;
  probability?: number;
  showIcon?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  tier,
  probability,
  showIcon = true,
}) => {
  const normTier = (tier || 'low').toLowerCase();

  let variant: 'critical' | 'high' | 'moderate' | 'low' = 'low';
  let label = 'Low Risk';
  let icon = <CheckCircle size={12} />;

  if (normTier === 'critical') {
    variant = 'critical';
    label = 'CRITICAL RISK';
    icon = <AlertOctagon size={12} />;
  } else if (normTier === 'high') {
    variant = 'high';
    label = 'HIGH RISK';
    icon = <AlertTriangle size={12} />;
  } else if (normTier === 'moderate') {
    variant = 'moderate';
    label = 'MODERATE RISK';
    icon = <Info size={12} />;
  }

  const probText = probability !== undefined ? ` (${(probability * 100).toFixed(1)}%)` : '';

  return (
    <Badge variant={variant} icon={showIcon ? icon : undefined}>
      {label}{probText}
    </Badge>
  );
};
