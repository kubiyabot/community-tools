import { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { sourceFormSchema } from './schema';
import type { 
  UseInstallToolProps, 
  UseInstallToolReturn, 
  InstallToolFormState,
  CommunityTool,
  InstallationStep,
  Step,
  FormValues
} from './types';

const STEPS: Step[] = [
  {
    id: 'select',
    title: 'Select Tool',
    description: 'Choose a tool from the community or provide your own',
    icon: 'search'
  },
  {
    id: 'preview',
    title: 'Preview Tool',
    description: 'Review the selected tool details',
    icon: 'eye'
  },
  {
    id: 'configure',
    title: 'Configure Tool',
    description: 'Configure the selected tool settings',
    icon: 'settings'
  },
  {
    id: 'install',
    title: 'Installation',
    description: 'Review and complete installation',
    icon: 'download'
  }
];

const initialSteps: InstallationStep[] = [
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
];

export function useInstallTool({ onInstall, teammate }: UseInstallToolProps): UseInstallToolReturn {
  const [formState, setState] = useState<InstallToolFormState>({
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
  });

  const [currentStep, setCurrentStep] = useState<string>('select');
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [selectedTool, setSelectedTool] = useState<CommunityTool | null>(null);
  const [failedIcons] = useState<Set<string>>(new Set());
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set());
  const [selectedTools, setSelectedTools] = useState<Set<string>>(new Set());
  const [steps, setSteps] = useState<InstallationStep[]>(initialSteps);
  const [isLoading, setIsLoading] = useState(false);

  const methods = useForm<FormValues>({
    resolver: zodResolver(sourceFormSchema),
    defaultValues: {
      name: "",
      url: "",
      runner: "automatic",
      dynamic_config: {} as Record<string, unknown>
    },
    mode: "onChange",
  });

  const handleToolSelect = useCallback((tool: CommunityTool) => {
    setSelectedTool(tool);
    setSelectedTools(new Set([tool.name]));
    methods.setValue('name', tool.name);
    methods.setValue('url', tool.path);
    methods.setValue('runner', tool.runner || 'automatic');
  }, [methods]);

  const handleIconError = useCallback((url: string) => {
    failedIcons.add(url);
  }, [failedIcons]);

  const handleCommunityToolSelect = useCallback((tool: CommunityTool) => {
    handleToolSelect(tool);
  }, [handleToolSelect]);

  const handleRefresh = useCallback(async () => {
    // Implement refresh logic if needed
  }, []);

  const handleSubmit = useCallback(async (data: FormValues) => {
    if (!selectedTool) return;
    
    setIsLoading(true);
    setState(prev => ({
      ...prev,
      installation: {
        ...prev.installation,
        isLoading: true,
        error: null
      }
    }));

    try {
      setSteps(initialSteps);
      const submitData: FormValues = {
        ...data,
        dynamic_config: data.dynamic_config || {},
        runner: data.runner || 'automatic'
      };
      await onInstall(submitData, updateStepStatus);
      // After successful installation, wait a bit before closing
      await new Promise(resolve => setTimeout(resolve, 2000));
    } catch (error) {
      setState(prev => ({
        ...prev,
        installation: {
          ...prev.installation,
          error: error instanceof Error ? error.message : 'Installation failed'
        }
      }));
    } finally {
      setIsLoading(false);
      setState(prev => ({
        ...prev,
        installation: {
          ...prev.installation,
          isLoading: false
        }
      }));
    }
  }, [onInstall, selectedTool, setSteps, setState]);

  const calculateCanProceed = useCallback(() => {
    switch (currentStep) {
      case 'select':
        return !!selectedTool;
      case 'preview':
        return !!selectedTool;
      case 'configure':
        return methods.formState.isValid;
      case 'install':
        return !isLoading;
      default:
        return false;
    }
  }, [currentStep, selectedTool, methods.formState.isValid, isLoading]);

  const canProceed = calculateCanProceed();

  const goToNextStep = useCallback(() => {
    const currentIndex = STEPS.findIndex(step => step.id === currentStep);
    if (currentIndex < STEPS.length - 1 && canProceed) {
      setCurrentStep(STEPS[currentIndex + 1].id);
    }
  }, [currentStep, canProceed]);

  const goToPreviousStep = useCallback(() => {
    const currentIndex = STEPS.findIndex(step => step.id === currentStep);
    if (currentIndex > 0) {
      setCurrentStep(STEPS[currentIndex - 1].id);
    }
  }, [currentStep]);

  const getCurrentStep = useCallback(() => {
    return STEPS.find(step => step.id === currentStep) || null;
  }, [currentStep]);

  const startInstallation = useCallback(() => {
    setState(prev => ({
      ...prev,
      installation: {
        ...prev.installation,
        isLoading: true,
        error: null,
        data: {
          steps: initialSteps
        }
      }
    }));
    setSteps(initialSteps);
  }, []);

  const cancelInstallation = useCallback(() => {
    setState(prev => ({
      ...prev,
      installation: {
        ...prev.installation,
        isLoading: false,
        error: null,
        data: null
      }
    }));
    setSteps(initialSteps);
  }, []);

  const updateStepStatus = useCallback((
    stepId: string,
    status: 'pending' | 'loading' | 'success' | 'error',
    error?: string
  ) => {
    setSteps(prev => prev.map(step => {
      if (step.id === stepId) {
        return { ...step, status, error };
      }
      if (status === 'error' && prev.findIndex(s => s.id === stepId) < prev.findIndex(s => s.id === step.id)) {
        return { ...step, status: 'pending', error: undefined };
      }
      return step;
    }));
  }, []);

  const renderStepContent = useCallback((): JSX.Element | null => {
    switch (currentStep) {
      case 'select':
        return null;
      case 'preview':
        return null;
      case 'configure':
        return null;
      case 'install':
        return null;
      default:
        return null;
    }
  }, [currentStep]);

  const getNextStep = (currentStep: string): string => {
    const currentIndex = STEPS.findIndex(step => step.id === currentStep);
    return currentIndex < STEPS.length - 1 ? STEPS[currentIndex + 1].id : currentStep;
  };

  const getPreviousStep = (currentStep: string): string => {
    const currentIndex = STEPS.findIndex(step => step.id === currentStep);
    return currentIndex > 0 ? STEPS[currentIndex - 1].id : currentStep;
  };

  const resetInstallation = useCallback(() => {
    setState(prev => ({
      ...prev,
      installation: {
        isLoading: false,
        error: null,
        data: null,
        isComplete: false
      }
    }));
  }, []);

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
    setState,
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