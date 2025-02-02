import * as React from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/app/components/ui/tabs';
import { useInstallToolContext } from '../context';
import { CommunityToolsTab } from './CommunityToolsTab';
import { CustomSourceTab } from '../components/CustomSourceTab';
import { PreviewStep } from '../components/PreviewStep';
import { ConfigureStep } from '../components/ConfigureStep';
import { GitBranch, GitPullRequest } from 'lucide-react';
import type { FormState } from '../types';

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
    handleCommunityToolSelect,
    handleRefresh
  } = useInstallToolContext();

  return (
    <div className="space-y-6">
      <Tabs defaultValue="community" className="w-full">
        <TabsList className="w-full grid grid-cols-2">
          <TabsTrigger value="community" className="flex items-center gap-2">
            <GitBranch className="h-4 w-4" />
            Community Tools
          </TabsTrigger>
          <TabsTrigger value="custom" className="flex items-center gap-2">
            <GitPullRequest className="h-4 w-4" />
            Custom Source
          </TabsTrigger>
        </TabsList>

        <TabsContent value="community" className="mt-6">
          <CommunityToolsTab
            formState={formState}
            onRefresh={handleRefresh}
            onToolSelect={handleToolSelect}
            selectedTool={selectedTool}
            failedIcons={failedIcons}
            onIconError={handleIconError}
            expandedTools={expandedTools}
            setExpandedTools={setExpandedTools}
          />
        </TabsContent>

        <TabsContent value="custom" className="mt-6">
          <CustomSourceTab methods={methods} />
        </TabsContent>
      </Tabs>

      {formState.preview.data && <PreviewStep />}
      {formState.preview.data && <ConfigureStep />}
    </div>
  );
} 