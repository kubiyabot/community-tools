import * as React from 'react';
import { ArrowLeft, Check, ChevronRight, Loader2, XCircle, RefreshCcw, Settings2, ChevronDown, ChevronUp, CheckCircle2 } from 'lucide-react';
import { Button } from '@/app/components/ui/button';
import { styles } from '../styles';
import type {  InstallationStep } from '../types';
import type { UseFormReturn } from 'react-hook-form';
import { motion } from 'framer-motion';
import type { InstallToolFormState } from '../types';
import type { FormValues } from '../schema';

export interface DialogFooterProps {
  currentStep: string;
  onClose: () => void;
  formState: InstallToolFormState;
  methods: UseFormReturn<FormValues>;
  onBack?: () => void;
  onNext?: () => void;
  onSubmit: (data: { name: string; url: string; runner: string; dynamic_config?: any }) => Promise<void>;
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
  const [isCollapsed, setIsCollapsed] = React.useState(false);

  const handleSubmit = async () => {
    try {
      // Get form data first to check values
      const formData = methods.getValues();
      
      // Validate source ID/name first
      if (!formData.name?.trim()) {
        methods.setError('name', { 
          type: 'required',
          message: 'Source name is required' 
        });
        return;
      }

      // Validate and format URL
      const url = formData.url?.trim();
      if (!url) {
        methods.setError('url', { 
          type: 'required',
          message: 'Source URL is required' 
        });
        return;
      }

      // Ensure URL is properly formatted
      let fullUrl = url;
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        fullUrl = `https://github.com/${url}`;
      }

      try {
        new URL(fullUrl);
      } catch {
        methods.setError('url', {
          type: 'invalid',
          message: 'Invalid URL format'
        });
        return;
      }

      // Now trigger full form validation
      const isValid = await methods.trigger();
      if (!isValid) {
        return;
      }

      // Clean up and prepare the data
      const cleanData = {
        name: formData.name.trim(),
        url: fullUrl,
        runner: formData.runner?.trim() || 'automatic',
        // Handle dynamic_config properly
        dynamic_config: formData.dynamic_config 
          ? (typeof formData.dynamic_config === 'string' 
              ? JSON.parse(formData.dynamic_config) 
              : formData.dynamic_config)
          : undefined
      };

      await onSubmit(cleanData);
    } catch (error) {
      console.error('Installation failed:', error);
      methods.setError('root', {
        type: 'submit',
        message: error instanceof Error ? error.message : 'Installation failed'
      });
    }
  };

  // Add installation state checks for the footer buttons
  const isInstalling = formState.installation?.isLoading;
  const hasError = formState.installation?.error;
  const isSuccess = formState.installation?.data?.success;

  const getButtonConfig = () => {
    switch (currentStep) {
      case 'source':
        return {
          text: 'Review Tools',
          icon: <ChevronRight className="ml-2 h-4 w-4" />,
          action: onNext,
          showLoading: false
        };
      case 'preview':
        return {
          text: 'Configure Installation',
          icon: <ChevronRight className="ml-2 h-4 w-4" />,
          action: onNext,
          showLoading: false
        };
      case 'configure':
        if (isInstalling) {
          return {
            text: 'Installing...',
            icon: <Loader2 className="mr-2 h-4 w-4 animate-spin" />,
            action: () => {},
            showLoading: true
          };
        }
        if (isSuccess) {
          return {
            text: 'Installed',
            icon: <CheckCircle2 className="mr-2 h-4 w-4" />,
            action: () => {},
            showLoading: false
          };
        }
        return {
          text: 'Install',
          icon: <Check className="ml-2 h-4 w-4" />,
          action: handleSubmit,
          showLoading: false
        };
      default:
        return {
          text: 'Next',
          icon: <ChevronRight className="ml-2 h-4 w-4" />,
          action: onNext,
          showLoading: false
        };
    }
  };

  // Reset collapsed state when step changes
  React.useEffect(() => {
    setIsCollapsed(false);
  }, [currentStep]);

  // Reset collapsed state when installation starts
  React.useEffect(() => {
    if (isInstalling) {
      setIsCollapsed(false);
    }
  }, [isInstalling]);

  const buttonConfig = getButtonConfig();

  return (
    <div className="border-t border-slate-800 bg-slate-900">
      {hasError && !isCollapsed && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="overflow-hidden"
        >
          <div className="px-6 py-4 bg-red-950/30 border-b border-red-500/20">
            <div className="flex items-start gap-4">
              <div className="p-2 rounded-full bg-red-500/10">
                <XCircle className="h-5 w-5 text-red-400" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-medium text-red-400">Installation Failed</h3>
                <p className="mt-1 text-sm text-slate-400">
                  Previous installation attempt failed. Please review the error and try again.
                </p>
                <div className="mt-2 text-sm text-red-400 bg-red-950/50 p-2 rounded border border-red-500/20">
                  {hasError}
                </div>
                <div className="mt-4 flex items-center gap-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleSubmit}
                    className="bg-red-950/30 border-red-500/30 text-red-400 hover:bg-red-950/50 hover:border-red-500/50 hover:text-red-300"
                  >
                    <RefreshCcw className="mr-2 h-4 w-4" />
                    Retry Installation
                  </Button>
                  <button 
                    onClick={onBack}
                    className="text-sm text-slate-400 hover:text-slate-300 flex items-center gap-2"
                  >
                    <Settings2 className="h-4 w-4" />
                    Review Configuration
                  </button>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}
      
      <div className="relative">
        <button
          onClick={() => setIsCollapsed(prev => !prev)}
          className="absolute -top-3 left-1/2 transform -translate-x-1/2 p-1 rounded-full bg-slate-800 border border-slate-700 text-slate-400 hover:text-slate-300 hover:bg-slate-700 transition-colors group"
          title={isCollapsed ? "Show Footer" : "Hide Footer"}
        >
          <motion.div
            initial={false}
            animate={{ rotate: isCollapsed ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown className="h-4 w-4 group-hover:scale-110 transition-transform" />
          </motion.div>
        </button>

        {!isCollapsed && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="p-6">
              <div className="flex justify-between w-full">
                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    onClick={onClose}
                    disabled={isInstalling}
                    className="bg-slate-900 text-slate-400 border-slate-700 hover:bg-slate-800 hover:text-slate-300 disabled:opacity-50"
                  >
                    Cancel
                  </Button>
                  {currentStep !== 'source' && (
                    <Button
                      variant="outline"
                      onClick={onBack}
                      disabled={isInstalling}
                      className="bg-slate-900 text-slate-400 border-slate-700 hover:bg-slate-800 hover:text-slate-300 disabled:opacity-50"
                    >
                      Back
                    </Button>
                  )}
                </div>
                <div className="flex gap-3 items-center">
                  {isInstalling && (
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20">
                      <Loader2 className="h-4 w-4 text-purple-400 animate-spin" />
                      <span className="text-sm text-purple-400">
                        Installing...
                      </span>
                    </div>
                  )}
                  <Button
                    onClick={buttonConfig.action}
                    disabled={!canProceed || isInstalling || isSuccess}
                    className={`${
                      isInstalling && currentStep === 'configure'
                        ? 'bg-purple-600 hover:bg-purple-700'
                        : 'bg-purple-600 hover:bg-purple-700'
                    } text-white disabled:opacity-50 min-w-[120px]`}
                  >
                    <span className="flex items-center">
                      {buttonConfig.text}
                      {buttonConfig.icon}
                    </span>
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {isCollapsed && isInstalling && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="p-3 flex justify-center"
          >
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20">
              <Loader2 className="h-4 w-4 text-purple-400 animate-spin" />
              <span className="text-sm text-purple-400">
                Installing...
              </span>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
} 