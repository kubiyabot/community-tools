import * as React from 'react';
import { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import type { FormState, CommunityTool, CategoryInfo } from '../types';
import { RetryQueue } from '../utils/RetryQueue';
import { createSourceInfo } from '../utils/sourceInfo';
import { discoverTools } from '../utils/discovery';
import type { TeammateDetails } from '../../../../../types/teammate';
import { TOOL_CATEGORIES } from '../../../../../constants/tools';
import { CategoriesSidebar } from '../components/CategoriesSidebar';
import { CommunityToolsSkeleton } from '../components/CommunityToolsSkeleton';
import { ErrorMessage } from '../components/ErrorMessage';
import { ToolsLayout } from '../components/ToolsLayout';
import type { CommunityTool as BaseCommunityTool } from '../../../../../types/tools';

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
  const [selectedTools, setSelectedTools] = useState<Set<string>>(new Set());

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
    if (!tool.name) return; // Add validation for required fields
    setSelectedTool(tool as CommunityTool);
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
    
    try {
      // If tools are already loaded, use them directly
      if (tool.tools?.length > 0) {
        setFormState(prev => ({
          ...prev,
          preview: {
            ...prev.preview,
            data: {
              tools: tool.tools,
              source: createSourceInfo(tool, tool.tools),
              errors: []
            }
          }
        }));
        return;
      }

      // Otherwise, discover tools
      const data = await discoverTools({
        ...tool,
        tools: [] as any[],
        loadingState: 'loading' as const
      });

      if (data && (Array.isArray(data.tools) || Array.isArray(data))) {
        const toolsArray = Array.isArray(data.tools) ? data.tools : Array.isArray(data) ? data : [];
        setFormState(prev => ({
          ...prev,
          preview: {
            ...prev.preview,
            data: {
              tools: toolsArray,
              source: createSourceInfo(tool, toolsArray),
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
    setCurrentStep(prev => {
      switch(prev) {
        case 'source': return 'select';
        case 'select': return 'configure';
        case 'configure': return 'installing';
        default: return prev;
      }
    });
  }, []);

  const goToPreviousStep = useCallback(() => {
    setCurrentStep(prev => {
      switch(prev) {
        case 'select': return 'source';
        case 'configure': return 'select';
        case 'installing': return 'configure';
        default: return prev;
      }
    });
  }, []);

  const canProceed = useCallback(() => {
    switch (currentStep) {
      case 'source':
        return selectedTool !== null;
      case 'select':
        return true; // Always allow proceeding from review step
      case 'configure':
        return true;
      default:
        return false;
    }
  }, [currentStep, selectedTool]);

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
    selectedTools,
    setSelectedTools,
    canProceed: canProceed(),
    renderStepContent,
    teammate
  };
} 