/**
 * Spinner - Indicateur de chargement glassmorphism
 * Utilise le design system Reception
 */

import React from 'react';

interface SpinnerProps {
  size?: 'small' | 'medium' | 'large';
  className?: string;
  label?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({
  size = 'medium',
  className = '',
  label
}) => {
  const sizeClass = size === 'small' ? 'spinner-small' : size === 'large' ? 'spinner-large' : 'spinner';

  return (
    <div className={`loading ${className}`}>
      <div className={sizeClass}></div>
      {label && <p style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>{label}</p>}
    </div>
  );
};

export default Spinner;
