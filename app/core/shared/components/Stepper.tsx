/**
 * Stepper - Indicateur d'étapes glassmorphism
 * Utilise le design system Reception
 */

import React from 'react';

interface Step {
  id: string;
  label: string;
}

interface StepperProps {
  steps: Step[];
  currentStep: number;
  className?: string;
}

export const Stepper: React.FC<StepperProps> = ({ steps, currentStep, className = '' }) => {
  return (
    <div className={`stepper ${className}`}>
      {steps.map((step, index) => {
        const isActive = index === currentStep;
        const isCompleted = index < currentStep;
        const stepClass = isActive ? 'active' : isCompleted ? 'completed' : '';

        return (
          <div key={step.id} className={`step ${stepClass}`}>
            <div className="step-circle">
              {isCompleted ? '✓' : index + 1}
            </div>
            <div className="step-label">{step.label}</div>
          </div>
        );
      })}
    </div>
  );
};

export default Stepper;
