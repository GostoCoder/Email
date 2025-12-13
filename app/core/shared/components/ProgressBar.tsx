/**
 * ProgressBar - Barre de progression glassmorphism
 * Utilise le design system Reception
 */

import React from 'react';

interface ProgressBarProps {
  value: number;
  max?: number;
  animated?: boolean;
  className?: string;
  showLabel?: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  animated = false,
  className = '',
  showLabel = false
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div className={className}>
      {showLabel && (
        <div style={{ marginBottom: '0.5rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
          {percentage.toFixed(0)}%
        </div>
      )}
      <div className="progress-container">
        <div 
          className={`progress-bar ${animated ? 'animated' : ''}`} 
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

export default ProgressBar;
