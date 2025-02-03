import * as React from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/app/components/ui/tabs';
import { useInstallToolContext } from '../context';
import { CommunityToolsTab } from './CommunityToolsTab';
import { CustomSourceTab } from '../components/CustomSourceTab';
import { PreviewStep } from '../components/PreviewStep';
import { ConfigureStep } from '../components/ConfigureStep';
import { GitBranch, GitPullRequest, Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import { CategoriesSidebar } from '../components/CategoriesSidebar';
import { CommunityToolsSkeleton } from '../components/CommunityToolsSkeleton';
import { ToolsLayout } from '../components/ToolsLayout';
import { TOOL_CATEGORIES } from '../../../../../constants/tools';

// Convert TOOL_CATEGORIES to array format
const toolCategoriesArray = Object.entries(TOOL_CATEGORIES).map(([key, category]) => ({
  ...category,
  id: key
}));

export function StepContent() {
  const {
    formState,
    selectedTool,
    handleToolSelect,
    failedIcons,
    handleIconError,
    expandedTools,
    setExpandedTools,
    methods,
    handleRefresh,
    currentStep,
    activeCategory,
    setActiveCategory
  } = useInstallToolContext();

  const renderContent = () => {
    switch (currentStep) {
      case 'source':
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
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-lg font-medium text-slate-200">All Tools</h2>
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                        <input 
                          type="text"
                          placeholder="Search tools..."
                          className={cn(
                            "h-9 w-[300px] pl-9 pr-4 rounded-md",
                            "bg-slate-800/50 border border-slate-700",
                            "text-sm text-slate-200 placeholder:text-slate-400",
                            "focus:outline-none focus:ring-2 focus:ring-purple-400/20"
                          )}
                        />
                      </div>
                    </div>
                    
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

      case 'select':
        return (
          <div className="p-6 h-full overflow-auto">
            <PreviewStep />
          </div>
        );

      case 'configure':
        return (
          <div className="p-6 h-full overflow-auto">
            <ConfigureStep />
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className={cn(
      "flex-1 min-h-0 overflow-hidden",
      "bg-gradient-to-b from-slate-900 to-slate-900/50",
      "dark text-slate-50"
    )}>
      {renderContent()}
    </div>
  );
} 