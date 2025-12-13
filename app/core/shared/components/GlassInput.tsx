/**
 * GlassInput - Input avec effet glassmorphism
 * Utilise le design system Reception
 */

import React from 'react';

interface GlassInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url';
  disabled?: boolean;
  className?: string;
  label?: string;
  error?: string;
  required?: boolean;
}

export const GlassInput: React.FC<GlassInputProps> = ({
  value,
  onChange,
  placeholder,
  type = 'text',
  disabled = false,
  className = '',
  label,
  error,
  required = false
}) => {
  return (
    <div className={`form-group ${className}`}>
      {label && (
        <label>
          {label}
          {required && <span style={{ color: 'var(--error-color)' }}> *</span>}
        </label>
      )}
      <input
        type={type}
        className="input-glass"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
      />
      {error && (
        <small style={{ color: 'var(--error-color)', marginTop: '0.25rem', display: 'block' }}>
          {error}
        </small>
      )}
    </div>
  );
};

export default GlassInput;
