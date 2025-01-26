import { Button } from '../../ui/button';
import { cn } from '../../../lib/utils';
import { Check, ChevronRight } from 'lucide-react';
import { Step, StepIndicatorProps } from '../types';

const STEPS: { key: Step; label: string }[] = [
  { key: 'provider', label: 'Provider' },
  { key: 'event', label: 'Event' },
  { key: 'event_example', label: 'Example' },
  { key: 'prompt', label: 'Prompt' },
  { key: 'webhook', label: 'Webhook' }
];

export function StepIndicator({
  currentStep,
  canNavigateToStep,
  onStepClick
}: StepIndicatorProps) {
  const getStepState = (step: Step) => {
    const stepIndex = STEPS.findIndex(s => s.key === step);
    const currentIndex = STEPS.findIndex(s => s.key === currentStep);

    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'current';
    return 'upcoming';
  };

  return (
    <div className="flex items-center gap-2">
      {STEPS.map((step, index) => {
        const state = getStepState(step.key);
        const canNavigate = canNavigateToStep(step.key);

        return (
          <div key={step.key} className="flex items-center">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => canNavigate && onStepClick(step.key)}
              disabled={!canNavigate}
              className={cn(
                "h-8 gap-2 transition-all",
                state === 'completed'
                  ? "text-emerald-400 hover:text-emerald-500"
                  : state === 'current'
                  ? "text-slate-200 bg-emerald-500/10 hover:bg-emerald-500/20"
                  : "text-slate-400 hover:text-slate-300",
                !canNavigate && "opacity-50 cursor-not-allowed"
              )}
            >
              {state === 'completed' ? (
                <Check className="h-4 w-4" />
              ) : (
                <div className={cn(
                  "h-4 w-4 rounded-full border",
                  state === 'current'
                    ? "border-emerald-500 bg-emerald-500/20"
                    : "border-slate-600 bg-slate-800"
                )} />
              )}
              {step.label}
            </Button>
            {index < STEPS.length - 1 && (
              <ChevronRight className={cn(
                "h-4 w-4 mx-1",
                state === 'completed' ? "text-emerald-400" : "text-slate-600"
              )} />
            )}
          </div>
        );
      })}
    </div>
  );
} 