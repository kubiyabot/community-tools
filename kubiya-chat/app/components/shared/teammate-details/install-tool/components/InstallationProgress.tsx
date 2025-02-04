import React from 'react';
import { CheckCircle2, XCircle, Loader2, Circle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface InstallationStep {
  id: string;
  status: 'pending' | 'loading' | 'success' | 'error';
  description: string;
  error?: string;
}

interface InstallationProgressProps {
  steps: InstallationStep[];
}

export function InstallationProgress({ steps }: InstallationProgressProps) {
  const totalSteps = steps.length;
  const completedSteps = steps.filter(step => step.status === 'success').length;
  const hasError = steps.some(step => step.status === 'error');
  const isLoading = steps.some(step => step.status === 'loading');
  const progress = Math.round((completedSteps / totalSteps) * 100);

  return (
    <div className="space-y-4">
      {/* Progress bar */}
      <div className="relative h-2 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={cn(
            'absolute left-0 top-0 h-full transition-all duration-500 ease-in-out',
            hasError ? 'bg-red-500' : 
            isLoading ? 'bg-purple-500' : 
            completedSteps === totalSteps ? 'bg-green-500' : 'bg-purple-500'
          )}
          style={{ 
            width: `${progress}%`,
            transition: 'width 0.5s ease-in-out'
          }}
        />
      </div>

      {/* Steps */}
      <div className="space-y-3">
        {steps.map((step, index) => {
          const isPreviousStepFailed = index > 0 && steps[index - 1].status === 'error';
          const isCurrentStep = step.status === 'loading';
          
          return (
            <div 
              key={step.id} 
              className={cn(
                "flex items-start gap-3 p-3 rounded-lg transition-all duration-200",
                step.status === 'pending' && "bg-slate-800/50",
                step.status === 'loading' && "bg-purple-500/10 border border-purple-500/20",
                step.status === 'success' && "bg-green-500/10 border border-green-500/20",
                step.status === 'error' && "bg-red-500/10 border border-red-500/20",
                isPreviousStepFailed && "opacity-50",
                isCurrentStep && "ring-2 ring-purple-500/20"
              )}
            >
              <div className="mt-0.5 flex-shrink-0">
                {step.status === 'pending' && (
                  <Circle className="h-4 w-4 text-slate-500" />
                )}
                {step.status === 'loading' && (
                  <Loader2 className="h-4 w-4 text-purple-400 animate-spin" />
                )}
                {step.status === 'success' && (
                  <CheckCircle2 className="h-4 w-4 text-green-400" />
                )}
                {step.status === 'error' && (
                  <XCircle className="h-4 w-4 text-red-400" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className={cn(
                  "text-sm font-medium",
                  step.status === 'pending' && "text-slate-400",
                  step.status === 'loading' && "text-purple-400",
                  step.status === 'success' && "text-green-400",
                  step.status === 'error' && "text-red-400"
                )}>
                  {step.description}
                </p>
                {step.error && (
                  <p className="mt-1 text-xs text-red-400 bg-red-500/10 p-2 rounded">
                    {step.error}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
} 