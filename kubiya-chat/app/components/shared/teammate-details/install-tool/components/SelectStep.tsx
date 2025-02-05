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
    data: tools,
    isLoading,
    error,
    refetch
  } = useCommunityTools();

  // Update formState when tools are loaded
  React.useEffect(() => {
    if (tools) {
      formState.communityTools = {
        data: Array.isArray(tools) ? tools : [],
        isLoading: false,
        error: null
      };
    }
  }, [tools, formState]);

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
        <p className="mt-4 text-sm text-slate-400">Loading community tools...</p>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-12">
        <div className="text-red-500 mb-4">
          <AlertCircle className="h-8 w-8" />
        </div>
        <p className="text-sm text-red-400">
          {error instanceof Error ? error.message : 'Failed to load community tools'}
        </p>
        <Button 
          variant="outline" 
          onClick={() => refetch()}
          className="mt-4"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    );
  }

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
              {formState.communityTools.isLoading ? (
                <CommunityToolsSkeleton />
              ) : (
                <ToolsLayout 
                  tools={formState.communityTools.data}
                  categories={toolCategoriesArray}
                  selectedTool={selectedTool}
                  onToolSelect={handleToolSelection}
                  failedIcons={failedIcons}
                  onIconError={onIconError}
                  expandedTools={expandedTools}
                  setExpandedTools={setExpandedTools}
                  handleRefresh={handleRefresh}
                  runners={teammate?.runners || ['kubiya-hosted']}
                  activeCategory={activeCategory}
                  onCategorySelect={setActiveCategory}
                />
              )}
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