import * as React from 'react';
import { ArrowLeft, Check, ChevronRight, Loader2 } from 'lucide-react';
import { Button } from '@/app/components/ui/button';
import { styles } from '../styles';
import type { FormState } from '../types';
import type { UseFormReturn } from 'react-hook-form';

interface DialogFooterProps {
  currentStep: string;
  onClose: () => void;
  formState: FormState;
  methods: UseFormReturn<any>;
  onBack?: () => void;
  onNext?: () => void;
  onSubmit?: () => void;
  canProceed: boolean;
}

export function DialogFooter({ 
  currentStep, 
  onClose, 
  formState, 
  methods,
  onBack,
  onNext,
  onSubmit,
  canProceed 
}: DialogFooterProps) {
  return (
    <div className="p-6 border-t border-slate-800 bg-slate-900">
      <div className="flex justify-between w-full">
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={onClose}
            className="bg-slate-900 text-slate-400 border-slate-700 hover:bg-slate-800 hover:text-slate-300"
          >
            Cancel
          </Button>
          {currentStep !== 'source' && (
            <Button
              variant="outline"
              onClick={onBack}
              className="bg-slate-900 text-slate-400 border-slate-700 hover:bg-slate-800 hover:text-slate-300"
            >
              Back
            </Button>
          )}
        </div>
        <div className="flex gap-3">
          {currentStep === 'configure' ? (
            <Button
              onClick={onSubmit}
              disabled={!canProceed || formState.installation.isLoading}
              className="bg-purple-600 text-white hover:bg-purple-700 disabled:bg-purple-600/50"
            >
              {formState.installation.isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Installing...
                </>
              ) : (
                'Install'
              )}
            </Button>
          ) : (
            <Button
              onClick={onNext}
              disabled={!canProceed}
              className="bg-purple-600 text-white hover:bg-purple-700 disabled:bg-purple-600/50"
            >
              <span className="flex items-center">
                Continue
                <ChevronRight className="h-4 w-4 ml-2" />
              </span>
            </Button>
          )}
        </div>
      </div>
    </div>
  );
} 