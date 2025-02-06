import * as React from 'react';
import { Dispatch, SetStateAction } from 'react';
import type { FormState } from '../types';
import type { CommunityTool } from '@/app/types/tool';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/app/components/ui/tabs';
import { GitBranch, GitPullRequest, AlertCircle, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { CategoriesSidebar } from './CategoriesSidebar';
import { CommunityToolsSkeleton } from './CommunityToolsSkeleton';
import { ToolsLayout } from './ToolsLayout';
import { TOOL_CATEGORIES } from '../../../../../constants/tools';
import { useInstallToolContext } from '../context';
import { CustomSourceTab } from './CustomSourceTab';
import { Button } from '@/app/components/ui/button';
import { useCommunityTools } from '@/app/hooks/useCommunityTools';
import { CommunityToolsTab } from './CommunityToolsTab';

// Convert TOOL_CATEGORIES to array format
const toolCategoriesArray = Object.entries(TOOL_CATEGORIES).map(([key, category]) => ({
  ...category,
  id: key
}));

export interface SelectStepProps {
  formState: FormState;
  onToolSelect: (tool: CommunityTool) => void;
  onRefresh: () => Promise<void>;
  failedIcons: Set<string>;
  onIconError: (url: string) => void;
  expandedTools: Set<string>;
  setExpandedTools: Dispatch<SetStateAction<Set<string>>>;
}

export function SelectStep({
  formState,
  onToolSelect,
  onRefresh,
  failedIcons,
  onIconError,
  expandedTools,
  setExpandedTools
}: SelectStepProps) {
  const {
    selectedTool,
    handleToolSelect,
    handleRefresh,
    teammate,
    activeCategory,
    setActiveCategory,
    methods
  } = useInstallToolContext();

  // Use the community tools hook
  const { 
    data: communityTools,
    isLoading: communityToolsLoading,
    error: communityToolsError,
    refetch: refetchCommunityTools
  } = useCommunityTools();

  // Update formState when tools are loaded
  React.useEffect(() => {
    if (communityTools) {
      formState.communityTools = {
        data: Array.isArray(communityTools) ? communityTools : [],
        isLoading: false,
        error: null
      };
    }
  }, [communityTools, formState]);

  // Update formState when loading state changes
  React.useEffect(() => {
    formState.communityTools.isLoading = communityToolsLoading;
  }, [communityToolsLoading, formState]);

  // Update formState when error state changes
  React.useEffect(() => {
    formState.communityTools.error = communityToolsError?.message || null;
  }, [communityToolsError, formState]);

  // When a tool is selected, ensure we use the full source URL
  const handleToolSelection = (tool: CommunityTool) => {
    if (tool.source?.url) {
      // Set the full URL from the tool's source
      methods.setValue('url', tool.source.url);
      // Also set the name if not already set
      if (!methods.getValues('name')) {
        methods.setValue('name', tool.name);
      }
    } else {
      console.warn('Tool selected without source URL:', tool);
    }
    handleToolSelect(tool);
  };

  // Handle refresh
  const handleRefreshTools = async () => {
    await refetchCommunityTools();
    if (onRefresh) {
      await onRefresh();
    }
  };

  return (
    <div className="flex flex-col h-full">
      <Tabs defaultValue="community" className="w-full h-full">
        <TabsList className="w-full grid grid-cols-2 bg-slate-800/50 p-1">
          <TabsTrigger 
            value="community" 
            className={cn(
              "flex items-center gap-2 py-2.5",
              "data-[state=active]:bg-slate-900 data-[state=active]:text-purple-400",
              "data-[state=inactive]:text-slate-400"
            )}
          >
            <GitBranch className="h-4 w-4" />
            Community Tools
          </TabsTrigger>
          <TabsTrigger 
            value="custom" 
            className={cn(
              "flex items-center gap-2 py-2.5",
              "data-[state=active]:bg-slate-900 data-[state=active]:text-purple-400",
              "data-[state=inactive]:text-slate-400"
            )}
          >
            <GitPullRequest className="h-4 w-4" />
            Custom Source
          </TabsTrigger>
        </TabsList>

        <TabsContent value="community" className="flex-1 h-full">
          <div className="grid grid-cols-[240px,1fr] h-full">
            {/* Categories Sidebar */}
            <div className="border-r border-slate-800 p-4 bg-slate-900/50">
              <div className="text-sm font-medium text-slate-400 mb-3">Categories</div>
              <CategoriesSidebar 
                categories={TOOL_CATEGORIES}
                tools={formState.communityTools.data}
                activeCategory={activeCategory}
                onCategorySelect={setActiveCategory}
              />
            </div>

            {/* Tools List */}
            <div className="p-6">
              <CommunityToolsTab
                formState={formState}
                onRefresh={handleRefreshTools}
                onToolSelect={handleToolSelection}
                selectedTool={selectedTool}
                failedIcons={failedIcons}
                onIconError={onIconError}
                expandedTools={expandedTools}
                setExpandedTools={setExpandedTools}
              />
            </div>
          </div>
        </TabsContent>

        <TabsContent value="custom" className="flex-1">
          <div className="p-6">
            <CustomSourceTab methods={methods} />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
} 