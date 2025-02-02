import * as React from 'react';
import { cn } from '@/lib/utils';
import type { Step } from '../types';

interface StepIndicatorProps {
  steps: Step[];
  currentStep: string;
}

export function StepIndicator({ steps, currentStep }: StepIndicatorProps) {
  return (
    <div className="mb-6 px-6">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => (
          <React.Fragment key={step.id}>
            <div className="flex items-center">
              <div 
                className={cn(
                  "flex items-center justify-center w-10 h-10 rounded-full border-2",
                  currentStep === step.id 
                    ? "bg-purple-500/10 border-purple-500 text-purple-400"
                    : index < steps.findIndex(s => s.id === currentStep)
                      ? "bg-emerald-500/10 border-emerald-500 text-emerald-400"
                      : "bg-slate-800/50 border-slate-700 text-slate-400"
                )}
              >
                {step.icon}
              </div>
              <div className="ml-3">
                <p className={cn(
                  "text-sm font-medium",
                  currentStep === step.id 
                    ? "text-purple-400"
                    : index < steps.findIndex(s => s.id === currentStep)
                      ? "text-emerald-400"
                      : "text-slate-400"
                )}>
                  {step.title}
                </p>
                <p className="text-xs text-slate-500">{step.description}</p>
              </div>
            </div>
            {index < steps.length - 1 && (
              <div className="flex-1 mx-4">
                <div className={cn(
                  "h-0.5 w-full",
                  index < steps.findIndex(s => s.id === currentStep)
                    ? "bg-emerald-500/30"
                    : "bg-slate-700"
                )} />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
} 