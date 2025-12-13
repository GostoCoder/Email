/**
 * Alert - Alerte glassmorphism
 * Utilise le design system Reception
 */

import React from 'react';
import { CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react';

interface AlertProps {
  children: React.ReactNode;
  type?: 'success' | 'error' | 'warning' | 'info';
  className?: string;
  title?: string;
}

export const Alert: React.FC<AlertProps> = ({
  children,
  type = 'info',
  className = '',
  title
}) => {
  const icons = {
    success: <CheckCircle size={24} />,
    error: <XCircle size={24} />,
    warning: <AlertTriangle size={24} />,
    info: <Info size={24} />
  };

  return (
    <div className={`alert alert-${type} ${className}`}>
      <span className="alert-icon">{icons[type]}</span>
      <div>
        {title && <strong>{title}</strong>}
        {children}
      </div>
    </div>
  );
};

export default Alert;
