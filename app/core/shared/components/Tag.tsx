/**
 * Tag - Pill/Tag glassmorphism
 * Utilise le design system Reception
 */

import React from 'react';

interface TagProps {
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
}

export const Tag: React.FC<TagProps> = ({ children, onClick, className = '' }) => {
  return (
    <span 
      className={`tag-pill ${className}`}
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      {children}
    </span>
  );
};

export default Tag;
