/**
 * GlassCard - Carte avec effet glassmorphism
 * Utilise le design system Reception avec glassmorphism
 */

import React from 'react';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  glow?: boolean;
  gradient?: boolean;
  onClick?: () => void;
}

export const GlassCard: React.FC<GlassCardProps> = ({ 
  children, 
  className = '', 
  hover = true,
  glow = false,
  gradient = false,
  onClick 
}) => {
  const baseClass = glow ? 'card-glow' : gradient ? 'gradient-tinted' : 'card';
  const hoverClass = hover ? '' : 'no-hover';
  
  return (
    <div 
      className={`${baseClass} ${hoverClass} ${className}`}
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      {children}
    </div>
  );
};

export default GlassCard;
