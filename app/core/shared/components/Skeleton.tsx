/**
 * Skeleton - Loader de skeleton glassmorphism
 * Utilise le design system Reception
 */

import React from 'react';

interface SkeletonProps {
  variant?: 'circle' | 'line' | 'card';
  width?: string;
  height?: string;
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  variant = 'line',
  width,
  height,
  className = ''
}) => {
  const variantClass = variant === 'circle' ? 'skeleton-circle' : 
                       variant === 'card' ? 'skeleton-card' : 'skeleton-line';

  const style: React.CSSProperties = {};
  if (width) style.width = width;
  if (height) style.height = height;

  if (variant === 'card') {
    return (
      <div className={`skeleton-card ${className}`}>
        <div className="skeleton skeleton-circle"></div>
        <div className="skeleton skeleton-line"></div>
        <div className="skeleton skeleton-line short"></div>
      </div>
    );
  }

  return (
    <div className={`skeleton ${variantClass} ${className}`} style={style}></div>
  );
};

export default Skeleton;
