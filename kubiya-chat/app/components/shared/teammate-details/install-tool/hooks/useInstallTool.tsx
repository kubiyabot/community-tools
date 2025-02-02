import * as React from 'react';
import { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import type { FormState, CommunityTool, CategoryInfo } from '../types';
import { RetryQueue } from '../utils/RetryQueue';
import { createSourceInfo } from '../utils/sourceInfo';
import { discoverTools } from '../utils/discovery';
import type { TeammateDetails } from '@/app/types/teammate';
import { TOOL_CATEGORIES } from '@/app/constants/tools';
import { CategoriesSidebar } from '../components/CategoriesSidebar';
import { CommunityToolsSkeleton } from '../components/CommunityToolsSkeleton';
import { ErrorMessage } from '../components/ErrorMessage';
import { ToolsLayout } from '../components/ToolsLayout';
import type { CommunityTool as BaseCommunityTool } from '@/app/types/tools';

// Convert TOOL_CATEGORIES from Record to Array
const toolCategoriesArray = Object.entries(TOOL_CATEGORIES).map(([key, category]) => ({
  ...category,
  id: key
}));

interface UseInstallToolProps {
  onInstall: (data: any) => void;
  teammate: TeammateDetails;
}

export function useInstallTool({ onInstall, teammate }: UseInstallToolProps) {
  const [formState, setFormState] = useState<FormState>({
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
      error: null
    }
  });

  const [currentStep, setCurrentStep] = useState('source');
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [selectedTool, setSelectedTool] = useState<CommunityTool | null>(null);
  const [failedIcons, setFailedIcons] = useState<Set<string>>(new Set());
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set());
  const [retryQueue] = useState(() => new RetryQueue());

  const methods = useForm({
    defaultValues: {
      name: "",
      url: "",
      runner: teammate?.runners?.[0] || "kubiya-hosted",
      dynamic_config: "",
    }
  });

  const handleRefresh = useCallback(async () => {
    try {
      setFormState(prev => ({
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
      setFormState(prev => ({
        ...prev,
        communityTools: {
          isLoading: false,
          error: null,
          data
        }
      }));
    } catch (error) {
      console.error('Error refreshing tools:', error);
      setFormState(prev => ({
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

  const handleToolSelect = useCallback((tool: Partial<CommunityTool>) => {
    // If tool metadata isn't loaded yet, load it
    if (!tool.tools?.length && tool.loadingState !== 'loading') {
      discoverTools(tool as CommunityTool)
        .then(data => {
          setSelectedTool({
            ...tool,
            loadingState: 'success',
            tools: data?.tools || [],
            isDiscovering: false,
            path: tool.path || '',
            description: tool.description || '',
            tools_count: data?.tools?.length || 0,
            name: tool.name || ''
          } as CommunityTool);
        })
        .catch(error => {
          setSelectedTool({
            ...tool,
            loadingState: 'error',
            tools: [],
            error: error instanceof Error ? error.message : 'Failed to load metadata',
            isDiscovering: false,
            path: tool.path || '',
            description: tool.description || '',
            tools_count: 0,
            name: tool.name || ''
          } as CommunityTool);
        });
    } else {
      setSelectedTool({
        ...tool,
        loadingState: tool.loadingState || 'success',
        tools: tool.tools || [],
        isDiscovering: false,
        path: tool.path || '',
        description: tool.description || '',
        tools_count: tool.tools?.length || 0,
        name: tool.name || ''
      } as CommunityTool);
    }
  }, []);

  const handleIconError = useCallback((url: string) => {
    setFailedIcons(prev => new Set(prev).add(url));
  }, []);

  const handleCommunityToolSelect = useCallback(async (tool: CommunityTool) => {
    setSelectedTool({
      ...tool,
      loadingState: 'loading',
      tools: tool.tools || []  // Ensure tools is always an array
    });
    
    if (!tool.tools) {
      try {
        const data = await discoverTools({
          ...tool,
          tools: [] as any[],
          loadingState: 'loading' as const
        });
        if (data && (Array.isArray(data.tools) || Array.isArray(data))) {
          setFormState(prev => ({
            ...prev,
            preview: {
              ...prev.preview,
              data: {
                tools: Array.isArray(data.tools) ? data.tools : Array.isArray(data) ? data : [],
                source: createSourceInfo(tool, Array.isArray(data.tools) ? data.tools : Array.isArray(data) ? data : []),
                errors: []
              }
            }
          }));
        }
      } catch (error) {
        setFormState(prev => ({
          ...prev,
          preview: {
            ...prev.preview,
            error: error instanceof Error ? error.message : 'Failed to discover tools'
          }
        }));
      }
    }
  }, []);

  const handleSubmit = useCallback(async () => {
    try {
      setFormState(prev => ({
        ...prev,
        installation: {
          isLoading: true,
          error: null
        }
      }));

      await onInstall(methods.getValues());
    } catch (error) {
      setFormState(prev => ({
        ...prev,
        installation: {
          isLoading: false,
          error: error instanceof Error ? error.message : 'Failed to install tools'
        }
      }));
    }
  }, [methods, onInstall]);

  const goToNextStep = useCallback(() => {
    const steps = ['source', 'preview', 'configure'];
    const currentIndex = steps.indexOf(currentStep);
    if (currentIndex < steps.length - 1) {
      setCurrentStep(steps[currentIndex + 1]);
    }
  }, [currentStep]);

  const goToPreviousStep = useCallback(() => {
    const steps = ['source', 'preview', 'configure'];
    const currentIndex = steps.indexOf(currentStep);
    if (currentIndex > 0) {
      setCurrentStep(steps[currentIndex - 1]);
    }
  }, [currentStep]);

  const canProceed = useCallback(() => {
    switch (currentStep) {
      case 'source': {
        // For community tools
        const hasValidCommunityTool = selectedTool && selectedTool.tools && selectedTool.tools.length > 0;
        
        // For custom source
        const customUrl = methods.getValues('url');
        const isValidUrl = customUrl ? /^https?:\/\/.+/.test(customUrl) : false;
        
        // Can proceed if either condition is met
        return hasValidCommunityTool || isValidUrl;
      }
      case 'preview':
        return formState.preview.data !== null;
      case 'configure':
        return true;
      default:
        return false;
    }
  }, [currentStep, selectedTool, methods, formState.preview.data]);

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
        return (
          <div className="space-y-8">
            <CategoriesSidebar 
              categories={TOOL_CATEGORIES}
              tools={formState.communityTools.data as BaseCommunityTool[]}
              activeCategory={activeCategory}
              onCategorySelect={setActiveCategory}
            />
            {formState.communityTools.isLoading ? (
              <CommunityToolsSkeleton />
            ) : (
              <ToolsLayout 
                tools={formState.communityTools.data}
                categories={toolCategoriesArray}
                selectedTool={selectedTool}
                onToolSelect={handleToolSelect}
                failedIcons={failedIcons}
                onIconError={handleIconError}
                expandedTools={expandedTools}
                setExpandedTools={setExpandedTools}
                handleRefresh={handleRefresh}
              />
            )}
          </div>
        );
      case 'preview':
        return null;
      case 'configure':
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
    setActiveCategory
  ]);

  return {
    formState,
    selectedCommunityTool: selectedTool,
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
    canProceed: canProceed(),
    renderStepContent
  };
} 