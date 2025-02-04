import * as React from 'react';
import { useState, useCallback, useMemo, useEffect } from 'react';
import { useForm, UseFormReturn } from 'react-hook-form';
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
import { toast } from '@/app/components/ui/use-toast';
import * as z from 'zod';
import type { FormValues } from '../schema';

// Convert TOOL_CATEGORIES from Record to Array
const toolCategoriesArray = Object.entries(TOOL_CATEGORIES).map(([key, category]) => ({
  ...category,
  id: key
}));

// At the top of the file, add this type
type ExtendedCommunityTool = CommunityTool & {
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
  const [selectedTool, setSelectedTool] = useState<CommunityTool | null>(null);
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
      setFormState((prev: InstallToolFormState) => ({
        ...prev,
        communityTools: {
          ...prev.communityTools,
          isLoading: true,
          error: null
        }
      }));

      // Clear cache and fetch fresh data
      const response = await fetch('/api/sources/community/list', {
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to refresh tools');
      }

      const data = await response.json();
      setFormState((prev: InstallToolFormState) => ({
        ...prev,
        communityTools: {
          isLoading: false,
          error: null,
          data
        }
      }));
    } catch (error) {
      console.error('Error refreshing tools:', error);
      setFormState((prev: InstallToolFormState) => ({
        ...prev,
        communityTools: {
          ...prev.communityTools,
          isLoading: false,
          error: error instanceof Error ? error.message : 'Failed to refresh tools'
        }
      }));
    }
  }, []);

  // Add initial fetch on mount
  React.useEffect(() => {
    handleRefresh();
  }, [handleRefresh]);

  const handleToolSelect = useCallback((tool: CommunityTool) => {
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

  const handleCommunityToolSelect = useCallback((tool: CommunityTool) => {
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
    setFormState((prev: InstallToolFormState) => ({
      ...prev,
      installation: {
        ...prev.installation,
        isLoading: true,
        error: null,
        isComplete: false
      }
    }));

    try {
      await onInstall(data as FormValues, updateStepStatus);
      setFormState((prev: InstallToolFormState) => ({
        ...prev,
        installation: {
          ...prev.installation,
          isLoading: false,
          isComplete: true
        }
      }));
    } catch (error) {
      setFormState((prev: InstallToolFormState) => ({
        ...prev,
        installation: {
          ...prev.installation,
          isLoading: false,
          error: error instanceof Error ? error.message : 'Installation failed',
          isComplete: false
        }
      }));
    }
  }, [onInstall, updateStepStatus]);

  // Add cleanup on dialog close
  useEffect(() => {
    if (!formState.isOpen) {
      resetInstallation();
    }
  }, [formState.isOpen, resetInstallation]);

  const goToNextStep = useCallback(() => {
    setCurrentStep(prev => {
      switch(prev) {
        case 'source': return 'select';
        case 'select': return 'preview';
        case 'preview': return 'configure';
        case 'configure': return 'installing';
        default: return prev;
      }
    });
  }, []);

  const goToPreviousStep = useCallback(() => {
    setCurrentStep(prev => {
      switch(prev) {
        case 'select': return 'source';
        case 'preview': return 'select';
        case 'configure': return 'preview';
        case 'installing': return 'configure';
        default: return prev;
      }
    });
  }, []);

  const calculateCanProceed = useCallback((): boolean => {
    switch (currentStep) {
      case 'source':
        return Boolean(selectedTool !== null && 
          (!selectedTool.runner || teammate?.runners?.includes(selectedTool.runner)));
      case 'select':
        return Boolean(selectedTool);
      case 'preview':
        return Boolean(selectedTool);
      case 'configure':
        return true;
      default:
        return false;
    }
  }, [currentStep, selectedTool, teammate?.runners]);

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
      case 'source':
        return null;
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
      case 'preview':
        return (
          <div className="p-6">
            <PreviewStep selectedTool={selectedTool} />
          </div>
        );
      case 'configure':
        return null;
      case 'installing':
        return null;
      default:
        return null;
    }
  }, [
    currentStep,
    formState,
    activeCategory,
    handleRefresh,
    selectedTool,
    handleToolSelect,
    failedIcons,
    expandedTools,
    setExpandedTools,
    setActiveCategory,
    teammate
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