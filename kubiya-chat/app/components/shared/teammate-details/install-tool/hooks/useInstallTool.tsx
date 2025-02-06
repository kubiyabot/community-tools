import * as React from 'react';
import { useState, useCallback, useMemo, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import type { 
  InstallToolFormState,
  CommunityTool, 
  CategoryInfo, 
  InstallationStep,
  UseInstallToolProps,
  UseInstallToolReturn
} from '../types';
import { RetryQueue } from '../utils/RetryQueue';
import { createSourceInfo } from '../utils/sourceInfo';
import { discoverTools } from '../utils/discovery';
import type { TeammateDetails } from '../../../../../types/teammate';
import { TOOL_CATEGORIES } from '../../../../../constants/tools';
import { CategoriesSidebar } from '../components/CategoriesSidebar';
import { CommunityToolsSkeleton } from '../components/CommunityToolsSkeleton';
import { ErrorMessage } from '../components/ErrorMessage';
import { ToolsLayout } from '../components/ToolsLayout';
import { PreviewStep } from '../components/PreviewStep';
import { zodResolver } from "@hookform/resolvers/zod";
import { sourceFormSchema } from '../schema';
import * as z from 'zod';
import type { FormValues } from '../schema';
import type { CommunityTool as CommunityToolType } from '@/app/types/tool';
import { Loader2, CheckCircle, XCircle, Circle, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/app/components/ui/alert';

// Convert TOOL_CATEGORIES from Record to Array
const toolCategoriesArray = Object.entries(TOOL_CATEGORIES).map(([key, category]) => ({
  ...category,
  id: key
}));

// At the top of the file, add this type
type ExtendedCommunityTool = CommunityToolType & {
  runner: string;
};

// Define the form data type based on the schema
type FormData = z.infer<typeof sourceFormSchema>;

// Add to the initial state
const initialState: InstallToolFormState = {
  isOpen: false,
  communityTools: {
    isLoading: false,
    error: null,
    data: []
  },
  preview: {
    isLoading: false,
    error: null,
    data: null
  },
  installation: {
    isLoading: false,
    error: null,
    data: null,
    isComplete: false
  }
};

export function useInstallTool({ onInstall, teammate, onClose }: UseInstallToolProps): UseInstallToolReturn {
  const [formState, setFormState] = useState<InstallToolFormState>(initialState);

  const [currentStep, setCurrentStep] = useState('select');
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [selectedTool, setSelectedTool] = useState<CommunityToolType | null>(null);
  const [failedIcons, setFailedIcons] = useState<Set<string>>(new Set());
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set());
  const [selectedTools, setSelectedTools] = useState<Set<string>>(new Set());
  const [steps, setSteps] = useState<InstallationStep[]>([
    {
      id: 'validate',
      status: 'pending',
      description: 'Validating configuration and inputs'
    },
    {
      id: 'prepare',
      status: 'pending',
      description: 'Preparing installation'
    },
    {
      id: 'install',
      status: 'pending',
      description: 'Installing tool'
    },
    {
      id: 'configure',
      status: 'pending',
      description: 'Configuring tool'
    }
  ]);

  const methods = useForm<FormData>({
    resolver: zodResolver(sourceFormSchema),
    defaultValues: {
      name: '',
      url: '',
      runner: teammate?.runners?.[0] || 'kubiya-hosted',
      dynamic_config: {}
    },
    mode: "onChange"
  });

  // Update form values when selectedTool changes
  React.useEffect(() => {
    if (selectedTool) {
      methods.setValue('name', selectedTool.name, { shouldValidate: true });
      methods.setValue('url', selectedTool.path, { shouldValidate: true });
      // Set runner value from teammate context
      methods.setValue('runner', teammate?.runners?.[0] || 'kubiya-hosted', { shouldValidate: true });
    }
  }, [selectedTool, methods, teammate]);

  const handleRefresh = useCallback(async () => {
    try {
      const currentUrl = methods.getValues('url');
      const currentRunner = methods.getValues('runner') || 'automatic';
      
      // Check if we have a URL to refresh
      if (!currentUrl) {
        return null;
      }
      
      const response = await fetch(`/api/v1/sources/load?url=${encodeURIComponent(currentUrl)}&runner=${encodeURIComponent(currentRunner)}`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to refresh tools');
      }

      return data;
    } catch (error) {
      console.error('Error refreshing tools:', error);
      throw new Error(error instanceof Error ? error.message : 'Failed to refresh tools');
    }
  }, [methods]);

  // Add initial fetch on mount
  React.useEffect(() => {
    handleRefresh();
  }, [handleRefresh]);

  const handleToolSelect = useCallback((tool: CommunityToolType) => {
    setSelectedTool(tool);
    // Set the name if not already set
    if (!methods.getValues('name')) {
      methods.setValue('name', tool.name);
    }
    // Don't set the URL here - let the ConfigureStep form handle it
  }, [methods]);

  const handleIconError = useCallback((url: string) => {
    setFailedIcons(prev => new Set(prev).add(url));
  }, []);

  const handleCommunityToolSelect = useCallback((tool: CommunityToolType) => {
    setSelectedTool(tool);
  }, []);

  const updateStepStatus = useCallback((
    stepId: string, 
    status: 'pending' | 'loading' | 'success' | 'error',
    error?: string
  ) => {
    setSteps(prev => prev.map(step =>
      step.id === stepId ? { ...step, status, error } : step
    ));
  }, []);

  // Reset installation state when step changes
  useEffect(() => {
    setFormState((prev: InstallToolFormState) => ({
      ...prev,
      installation: {
        isLoading: false,
        error: null,
        data: null,
        isComplete: false
      }
    }));
  }, [currentStep]);

  // Add reset function
  const resetInstallation = useCallback(() => {
    setFormState((prev: InstallToolFormState) => ({
      ...prev,
      installation: {
        isLoading: false,
        error: null,
        data: null,
        isComplete: false
      }
    }));
  }, []);

  // Update handleSubmit to properly set completion status
  const handleSubmit = useCallback(async (data: { name: string; url: string; runner?: string; dynamic_config?: any }) => {
    try {
      // Set initial loading state
      setCurrentStep('installing');
      setFormState((prev: InstallToolFormState) => ({
        ...prev,
        installation: {
          ...prev.installation,
          isLoading: true,
          error: null,
          isComplete: false,
          data: {
            steps: steps
          }
        }
      }));

      // Reset all steps to pending
      setSteps(steps.map(step => ({ ...step, status: 'pending', error: undefined })));

      // Start the installation
      updateStepStatus('validate', 'loading');
      
      try {
        await onInstall(data as FormValues, updateStepStatus);
        
        // Update final state on success
        setFormState((prev: InstallToolFormState) => ({
          ...prev,
          installation: {
            ...prev.installation,
            isLoading: false,
            error: null,
            isComplete: true
          }
        }));

        // Mark all steps as complete
        setSteps(prev => prev.map(step => ({ ...step, status: 'success' })));
      } catch (error) {
        console.error('Installation error:', error);
        let errorMessage = 'Installation failed';
        
        if (error instanceof Error) {
          errorMessage = error.message;
        } else if (error && typeof error === 'object' && 'message' in error) {
          errorMessage = String(error.message);
        }

        throw new Error(errorMessage);
      }
    } catch (error) {
      console.error('Installation error:', error);
      
      // Update error state
      setFormState((prev: InstallToolFormState) => ({
        ...prev,
        installation: {
          ...prev.installation,
          isLoading: false,
          error: error instanceof Error ? error.message : 'Installation failed',
          isComplete: false
        }
      }));

      // Mark current step as failed and go back to configure step
      setSteps(prev => prev.map(step => 
        step.status === 'loading' 
          ? { ...step, status: 'error', error: error instanceof Error ? error.message : 'Installation failed' }
          : step
      ));
      setCurrentStep('configure');
    }
  }, [onInstall, updateStepStatus, steps]);

  // Add cleanup on dialog close
  useEffect(() => {
    if (!formState.isOpen) {
      resetInstallation();
    }
  }, [formState.isOpen, resetInstallation]);

  const goToNextStep = useCallback(() => {
    setCurrentStep(prev => {
      switch(prev) {
        case 'select':
          if (selectedTool) {
            return 'configure';
          }
          return prev;
        case 'configure':
          if (methods.formState.isValid && (formState.preview.data?.tools?.length > 0 || (selectedTool?.tools && selectedTool.tools.length > 0))) {
            return 'install';
          }
          return prev;
        default:
          return prev;
      }
    });
  }, [selectedTool, methods.formState.isValid, formState.preview.data?.tools?.length]);

  const goToPreviousStep = useCallback(() => {
    setCurrentStep(prev => {
      switch(prev) {
        case 'configure': return 'select';
        case 'install': return 'configure';
        default: return prev;
      }
    });
  }, []);

  const calculateCanProceed = useCallback((): boolean => {
    switch (currentStep) {
      case 'select':
        return !!selectedTool;
      case 'configure':
        // For custom source, check if we have valid preview data with tools
        if (formState.preview.data?.tools) {
          return formState.preview.data.tools.length > 0 && methods.formState.isValid;
        }
        // For community tools, check if we have tools in the selected tool
        if (selectedTool?.tools) {
          return selectedTool.tools.length > 0 && methods.formState.isValid;
        }
        return false;
      case 'install':
        return !formState.installation.isLoading;
      default:
        return false;
    }
  }, [currentStep, selectedTool, methods.formState.isValid, formState.installation.isLoading, formState.preview.data]);

  // Calculate canProceed value whenever dependencies change
  const canProceed = useMemo(() => calculateCanProceed(), [calculateCanProceed]);

  const renderStepContent = useCallback(() => {
    if (formState.communityTools.error) {
      return (
        <ErrorMessage 
          message={formState.communityTools.error} 
          onRetry={handleRefresh}
        />
      );
    }

    switch (currentStep) {
      case 'select':
        return (
          <div className="space-y-8">
            <CategoriesSidebar 
              categories={TOOL_CATEGORIES}
              tools={formState.communityTools.data}
              activeCategory={activeCategory}
              onCategorySelect={setActiveCategory}
            />
            {formState.communityTools.isLoading ? (
              <CommunityToolsSkeleton />
            ) : (
              <ToolsLayout 
                tools={formState.communityTools.data}
                categories={toolCategoriesArray}
                activeCategory={activeCategory}
                onCategorySelect={setActiveCategory}
                selectedTool={selectedTool}
                onToolSelect={handleToolSelect}
                failedIcons={failedIcons}
                onIconError={handleIconError}
                expandedTools={expandedTools}
                setExpandedTools={setExpandedTools}
                handleRefresh={handleRefresh}
                runners={teammate?.runners || ['kubiya-hosted']}
              />
            )}
          </div>
        );
      case 'configure':
        return null; // This is handled by CustomSourceTab
      case 'install':
        return (
          <div className="p-6">
            <PreviewStep 
              selectedTool={selectedTool || {
                name: methods.getValues('name'),
                description: 'Custom source',
                tools: formState.preview.data?.tools || [],
                type: 'custom'
              }} 
              isLoading={formState.installation.isLoading}
            />
          </div>
        );
      default:
        return null;
    }
  }, [
    formState.communityTools.error,
    formState.communityTools.isLoading,
    formState.communityTools.data,
    formState.installation.isLoading,
    formState.preview.data,
    currentStep,
    activeCategory,
    selectedTool,
    handleRefresh,
    handleToolSelect,
    failedIcons,
    handleIconError,
    expandedTools,
    setExpandedTools,
    teammate?.runners,
    methods,
    setActiveCategory
  ]);

  const startInstallation = useCallback(() => {
    setFormState((prev: InstallToolFormState) => ({
      ...prev,
      installation: {
        ...prev.installation,
        isLoading: true,
        error: null,
        isComplete: false,
        data: {
          steps: steps
        }
      }
    }));
    setSteps(steps.map(step => ({ ...step, status: 'pending', error: undefined })));
  }, [steps]);

  const cancelInstallation = useCallback(() => {
    setFormState((prev: InstallToolFormState) => ({
      ...prev,
      installation: {
        ...prev.installation,
        isLoading: false,
        error: null,
        data: null,
        isComplete: false
      }
    }));
    setSteps(steps.map(step => ({ ...step, status: 'pending', error: undefined })));
  }, [steps]);

  return {
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
    teammate,
    setState: setFormState,
    steps,
    setSteps,
    isLoading: formState.installation.isLoading,
    installationSteps: steps,
    startInstallation,
    cancelInstallation,
    updateStepStatus,
    isInstallationComplete: formState.installation.isComplete,
    resetInstallation
  } satisfies UseInstallToolReturn;
} 