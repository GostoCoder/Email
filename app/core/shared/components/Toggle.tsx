/**
 * Toggle - Switch glassmorphism
 * Utilise le design system Reception
 */

import React from 'react';

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
}

export const Toggle: React.FC<ToggleProps> = ({
  checked,
  onChange,
  label,
  disabled = false
}) => {
  const id = React.useId();

  return (
    <div className="toggle-wrapper">
      <input
        type="checkbox"
        id={id}
        className="toggle-input"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        disabled={disabled}
      />
      <label htmlFor={id} className="toggle-label"></label>
      {label && <span>{label}</span>}
    </div>
  );
};

export default Toggle;
