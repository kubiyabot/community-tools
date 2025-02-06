import * as React from 'react';
import { useCallback, useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { sourceFormSchema } from './schema';
import type { TeammateDetails } from '@/app/types/teammate';
import { useCommunityTools } from '@/app/hooks/useCommunityTools';
import { useVirtualizer, VirtualItem, Virtualizer } from '@tanstack/react-virtual';
import { Loader2, Search, AlertCircle, CheckCircle2, Info, Settings, Download } from 'lucide-react';
import { Input } from '@/app/components/ui/input';
import { debounce } from 'lodash';
import {
  Dialog,
  DialogContent,
  DialogHeader as BaseDialogHeader,
  DialogTitle,
  DialogDescription
} from '@/app/components/ui/dialog';
import { Form, FormField, FormItem, FormLabel, FormControl, FormDescription, FormMessage } from '@/app/components/ui/form';
import { ToolCard } from './components/ToolCard';
import { cn } from '@/lib/utils';
import { Alert, AlertDescription, AlertTitle } from '@/app/components/ui/alert';
import { Button } from '@/app/components/ui/button';
import { InstallationProgress } from './components/InstallationProgress';
import type { InstallationStep, InstallToolFormState, FormValues } from './types';
import type { ExtendedCommunityTool } from './types';
import { useInstallTool } from './hooks/useInstallTool';
import type { Step, UseInstallToolReturn } from './types';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/app/components/ui/tooltip';
import { Textarea } from '@/app/components/ui/textarea';
import { useInstallToolContext, InstallToolProvider } from './context';
import { FormProvider } from 'react-hook-form';
import { ScrollArea } from '@/app/components/ui/scroll-area';
import { StepIndicator } from './components/StepIndicator';
import { StepContent } from './components/StepContent';
import { DialogFooter as BaseDialogFooter } from '@/app/components/ui/dialog';
import { DialogFooter } from './components/DialogFooter';
import { SelectStep } from './components/SelectStep';
import { PreviewStep } from './components/PreviewStep';

interface InstallToolFormProps {
  isOpen: boolean;
  onClose: () => void;
  onInstall: (values: FormValues, updateProgress: (stepId: string, status: 'pending' | 'loading' | 'success' | 'error', error?: string) => void) => Promise<void>;
  teammate: TeammateDetails;
  initialValues?: Partial<FormValues>;
}

interface InstallToolFormContentProps {
  onClose: () => void;
  onInstall: (values: FormValues, updateProgress: (stepId: string, status: 'pending' | 'loading' | 'success' | 'error', error?: string) => void) => Promise<void>;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
  installationSteps: InstallationStep[];
  setInstallationSteps: React.Dispatch<React.SetStateAction<InstallationStep[]>>;
  methods: ReturnType<typeof useForm<FormValues>>;
  transformedTools: ExtendedCommunityTool[];
  rowVirtualizer: Virtualizer<HTMLDivElement, Element>;
  parentRef: React.RefObject<HTMLDivElement>;
  handleSearch: (value: string) => void;
  communityToolsLoading: boolean;
  communityToolsError: unknown;
  filteredTools: ExtendedCommunityTool[];
}

function InstallToolFormContent({
  onClose,
  onInstall,
  isLoading,
  setIsLoading,
  error,
  setError,
  installationSteps,
  setInstallationSteps,
  methods,
  transformedTools,
  rowVirtualizer,
  parentRef,
  handleSearch,
  communityToolsLoading,
  communityToolsError,
  filteredTools
}: InstallToolFormContentProps) {
  const { startInstallation, cancelInstallation } = useInstallToolContext();

  const updateStepStatus = React.useCallback((
    stepId: string,
    status: 'pending' | 'loading' | 'success' | 'error',
    error?: string
  ) => {
    setInstallationSteps(prev => prev.map(step => {
      if (step.id === stepId) {
        return { ...step, status, error };
      }
      if (status === 'error' && prev.findIndex(s => s.id === stepId) < prev.findIndex(s => s.id === step.id)) {
        return { ...step, status: 'pending', error: undefined };
      }
      return step;
    }));
  }, [setInstallationSteps]);

  const handleSubmit = async (values: FormValues) => {
    setIsLoading(true);
    setError(null);
    startInstallation();

    try {
      setInstallationSteps(prev => prev.map(step => ({
        ...step,
        status: 'pending',
        error: undefined
      })));

      updateStepStatus('validate', 'loading');
      if (!values.name || !values.url) {
        const error = !values.name ? 'Name is required' : 'URL is required';
        updateStepStatus('validate', 'error', error);
        throw new Error(error);
      }
      updateStepStatus('validate', 'success');

      updateStepStatus('prepare', 'loading');
      await new Promise(resolve => setTimeout(resolve, 500));
      updateStepStatus('prepare', 'success');

      updateStepStatus('install', 'loading');
      await onInstall(values, (stepId, status, error) => {
        if (stepId === 'install') {
          updateStepStatus('install', status, error);
          if (status === 'success') {
            updateStepStatus('configure', 'loading');
          }
        } else if (stepId === 'configure') {
          updateStepStatus('configure', status, error);
        }
      });

      setInstallationSteps(prev => prev.map(step => ({
        ...step,
        status: 'success'
      })));

      await new Promise(resolve => setTimeout(resolve, 2000));
      onClose();
    } catch (err: any) {
      const apiError = err?.message || 'Failed to install tool';
      setError(apiError);
      
      const currentStep = installationSteps.find(step => step.status === 'loading');
      if (currentStep) {
        updateStepStatus(currentStep.id, 'error', apiError);
      }
    } finally {
      setIsLoading(false);
      cancelInstallation();
    }
  };

  return (
    <DialogContent className="max-w-3xl h-[600px] flex flex-col">
      <BaseDialogHeader className="p-6 pb-0">
        <DialogTitle>Install Tool</DialogTitle>
        <DialogDescription>
          Choose from community tools or install from a custom source
        </DialogDescription>
      </BaseDialogHeader>

      <div className="flex-1 min-h-0 flex gap-6 overflow-hidden">
        {/* Community Tools Section */}
        <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
          <div className="mb-4 relative">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
              <Search className="h-4 w-4 text-slate-400" />
            </div>
            <Input
              placeholder="Search tools..."
              onChange={(e) => handleSearch(e.target.value)}
              className="bg-slate-800/50 pl-10"
            />
          </div>

          <ScrollArea className="flex-1 w-full">
            {communityToolsLoading ? (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="h-6 w-6 animate-spin text-purple-400" />
              </div>
            ) : communityToolsError ? (
              <div className="flex flex-col items-center justify-center h-full gap-4">
                <AlertCircle className="h-8 w-8 text-red-400" />
                <div className="text-center">
                  <p className="text-sm font-medium text-red-400">Failed to load tools</p>
                  <p className="text-xs text-red-300 mt-1">{String(communityToolsError)}</p>
                </div>
              </div>
            ) : filteredTools.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full gap-4">
                <Search className="h-8 w-8 text-slate-400" />
                <p className="text-sm text-slate-400">No tools found</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4 p-2">
                {filteredTools.map((tool) => (
                  <ToolCard
                    key={tool.name}
                    tool={tool}
                    onSelect={() => {
                      methods.setValue('name', tool.name);
                      methods.setValue('url', tool.path);
                    }}
                  />
                ))}
              </div>
            )}
          </ScrollArea>
        </div>

        {/* Form Section */}
        <div className="w-80 border-l border-slate-700 pl-6 overflow-y-auto">
          <FormProvider {...methods}>
            <Form {...methods}>
              <form onSubmit={methods.handleSubmit(handleSubmit)} className="space-y-6">
                {/* Installation Progress */}
                {(isLoading || installationSteps.some(step => step.status !== 'pending')) && (
                  <div className="py-4 bg-slate-900/50 rounded-lg border border-slate-800 p-4">
                    <h3 className="text-sm font-medium text-slate-200 mb-4">Installation Progress</h3>
                    <InstallationProgress steps={installationSteps} />
                  </div>
                )}

                {/* Show error if any */}
                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                {/* Form Fields */}
                <FormField
                  control={methods.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Name</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="my-awesome-tool" />
                      </FormControl>
                      <FormDescription>
                        A unique name for this tool
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={methods.control}
                  name="url"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Source URL</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="https://github.com/org/repo" />
                      </FormControl>
                      <FormDescription>
                        URL to the Git repository containing the tool
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={methods.control}
                  name="dynamic_config"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Dynamic Configuration (Optional)</FormLabel>
                      <FormControl>
                        <Textarea
                          {...field}
                          placeholder="{}"
                          className="font-mono"
                        />
                      </FormControl>
                      <FormDescription>
                        JSON configuration for the tool
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="flex items-center justify-end gap-2 pt-6">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={onClose}
                    disabled={isLoading}
                  >
                    Cancel
                  </Button>
                  <Button 
                    type="submit"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Installing...
                      </>
                    ) : (
                      'Install Tool'
                    )}
                  </Button>
                </div>
              </form>
            </Form>
          </FormProvider>
        </div>
      </div>
    </DialogContent>
  );
}

const STEPS: Step[] = [
  {
    id: 'select',
    title: 'Select Tool',
    description: 'Choose a tool from the community or provide your own',
    icon: <Search className="h-4 w-4" />
  },
  {
    id: 'configure',
    title: 'Configure',
    description: 'Configure tool settings',
    icon: <Settings className="h-4 w-4" />
  },
  {
    id: 'install',
    title: 'Install',
    description: 'Review and install',
    icon: <Download className="h-4 w-4" />
  }
];

interface CustomDialogHeaderProps {
  onClose?: () => void;
}

function CustomDialogHeader({ onClose }: CustomDialogHeaderProps) {
  return (
    <BaseDialogHeader className="p-6 pb-0">
      <DialogTitle>Install Tool</DialogTitle>
      <DialogDescription>
        Choose from community tools or install from a custom source
      </DialogDescription>
    </BaseDialogHeader>
  );
}

interface CustomDialogFooterProps {
  currentStep: string;
  onClose: () => void;
  formState: InstallToolFormState;
  methods: ReturnType<typeof useForm<FormValues>>;
  onBack?: () => void;
  onNext?: () => void;
  onSubmit: (data: FormValues) => Promise<void>;
  canProceed: boolean;
}

function CustomDialogFooter({
  currentStep,
  onClose,
  formState,
  methods,
  onBack,
  onNext,
  onSubmit,
  canProceed
}: CustomDialogFooterProps) {
  const handleSubmit = async () => {
    const values = methods.getValues();
    await onSubmit(values);
  };

  const isConfigureStep = currentStep === 'configure';

  return (
    <div className="border-t border-slate-700 p-6">
      <div className="flex justify-between">
        <Button
          type="button"
          variant="outline"
          onClick={onClose}
          disabled={formState.installation.isLoading}
        >
          Cancel
        </Button>
        <div className="flex gap-2">
          {onBack && (
            <Button
              type="button"
              variant="outline"
              onClick={onBack}
              disabled={formState.installation.isLoading}
            >
              Back
            </Button>
          )}
          {isConfigureStep ? (
            <Button
              type="button"
              onClick={handleSubmit}
              disabled={!canProceed || formState.installation.isLoading}
            >
              {formState.installation.isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Installing...
                </>
              ) : (
                'Install Tool'
              )}
            </Button>
          ) : (
            <Button
              type="button"
              onClick={onNext}
              disabled={!canProceed || formState.installation.isLoading}
            >
              Next
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

export function InstallToolForm({ isOpen, onClose, onInstall, teammate }: InstallToolFormProps) {
  const hookValues = useInstallTool({ onInstall, teammate });
  const {
    formState,
    methods,
    currentStep,
    activeCategory,
    setActiveCategory,
    selectedTool,
    handleToolSelect,
    failedIcons,
    handleIconError,
    expandedTools,
    setExpandedTools,
    handleCommunityToolSelect,
    handleRefresh,
    handleSubmit,
    goToNextStep,
    goToPreviousStep,
    selectedTools,
    setSelectedTools,
    canProceed,
    renderStepContent,
    teammate: teammateState,
    setState,
    steps,
    setSteps,
    isLoading
  } = hookValues;

  // Reset form when dialog opens/closes
  useEffect(() => {
    if (!isOpen) {
      methods.reset();
      setState((prev: InstallToolFormState) => ({
        ...prev,
        installation: {
          isLoading: false,
          error: null,
          data: null,
          isComplete: false
        },
        communityTools: {
          isLoading: false,
          error: null,
          data: []
        },
        preview: {
          isLoading: false,
          error: null,
          data: null
        }
      }));
    }
  }, [isOpen, methods, setState]);

  // Prevent dialog from closing during installation
  const handleClose = useCallback(() => {
    if (!formState.installation.isLoading) {
      setState((prev: InstallToolFormState) => ({
        ...prev,
        isOpen: false,
        installation: {
          isLoading: false,
          error: null,
          data: null,
          isComplete: false
        },
        communityTools: {
          isLoading: false,
          error: null,
          data: []
        },
        preview: {
          isLoading: false,
          error: null,
          data: null
        }
      }));
      onClose();
    }
  }, [formState.installation.isLoading, setState, onClose]);

  // Show installation view when installing or when there are steps
  const showInstallationView = formState.installation.isLoading || 
    (formState.installation.data?.steps && formState.installation.data.steps.length > 0);

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl h-[500px] flex flex-col p-0 bg-slate-900 border border-slate-800">
        {showInstallationView ? (
          <div className="flex-1 flex flex-col">
            <CustomDialogHeader />
            <div className="flex-1 p-6 overflow-auto">
              <InstallationProgress 
                steps={formState.installation.data?.steps || []} 
              />
            </div>
          </div>
        ) : (
          <InstallToolProvider
            teammate={teammate}
            value={hookValues}
          >
            <FormProvider {...methods}>
              <CustomDialogHeader />
              
              <div className="flex-1 flex flex-col min-h-0">
                <StepIndicator steps={STEPS} currentStep={currentStep} />
                
                <ScrollArea className="flex-1">
                  <div className="p-6">
                    <StepContent />
                  </div>
                </ScrollArea>

                <CustomDialogFooter 
                  currentStep={currentStep}
                  onClose={handleClose}
                  formState={formState}
                  methods={methods}
                  onBack={goToPreviousStep}
                  onNext={goToNextStep}
                  onSubmit={handleSubmit}
                  canProceed={canProceed && !formState.installation.isLoading}
                />
              </div>
            </FormProvider>
          </InstallToolProvider>
        )}
      </DialogContent>
    </Dialog>
  );
} 