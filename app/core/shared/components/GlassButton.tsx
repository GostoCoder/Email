/**
 * GlassButton - Bouton avec effet glassmorphism
 * Utilise le design system Reception avec gradients et animations
 */

import React from 'react';

interface GlassButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'danger' | 'brand';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
  icon?: React.ReactNode;
}

export const GlassButton: React.FC<GlassButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  className = '',
  type = 'button',
  icon
}) => {
  const variantClass = variant === 'brand' ? 'brand-button' : `btn btn-${variant}`;
  const sizeClass = size === 'small' ? 'btn-small' : size === 'large' ? 'btn-large' : '';
  
  return (
    <button
      type={type}
      className={`${variantClass} ${sizeClass} ${className}`}
      onClick={onClick}
      disabled={disabled}
    >
      {icon && <span>{icon}</span>}
      {children}
    </button>
  );
};

export default GlassButton;
