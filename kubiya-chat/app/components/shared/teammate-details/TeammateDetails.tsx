import React from 'react';
import { TeammateHeader } from './TeammateHeader';
import { TeammateNavigation } from './TeammateNavigation';
import type { TeammateDetails as TeammateDetailsType } from './types';
import { TooltipProvider } from '@/app/components/ui/tooltip';
import { OverviewTab } from './OverviewTab';
import IntegrationsTab from './IntegrationsTab';
import { RuntimeTab } from './RuntimeTab';
import { AccessControlTab } from './AccessControlTab';
import { KnowledgeTab } from './KnowledgeTab';
import { SourcesTab } from './SourcesTab';
import type { ExtendedSourceInfo } from './SourcesTab';

interface TeammateDetailsProps {
  teammate: TeammateDetailsType | null;
  activeTab: string;
  onTabChange: (tab: string) => void;
  children?: React.ReactNode;
  integrations?: any;
  sources?: ExtendedSourceInfo[];
  isLoadingSources?: boolean;
  onSourcesChange?: () => void;
}

export function TeammateDetails({ 
  teammate, 
  activeTab, 
  onTabChange, 
  children, 
  integrations,
  sources,
  isLoadingSources,
  onSourcesChange
}: TeammateDetailsProps) {
  if (!teammate) {
    return (
      <div className="flex items-center justify-center h-full bg-[#0F172A]">
        <div className="text-slate-400">No teammate data available</div>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="flex flex-col h-full bg-[#0F172A]">
        <TeammateHeader teammate={teammate} integrations={integrations} />
        <TeammateNavigation activeTab={activeTab} onTabChange={onTabChange} />
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-[1200px] mx-auto p-8">
            {activeTab === 'overview' && <OverviewTab teammate={teammate} />}
            {activeTab === 'integrations' && <IntegrationsTab teammate={{ ...teammate, integrations: integrations || [] }} />}
            {activeTab === 'knowledge' && <KnowledgeTab teammateId={teammate.id} />}
            {activeTab === 'sources' && (
              <SourcesTab 
                teammate={teammate}
                sources={sources}
                isLoading={isLoadingSources}
                onSourcesChange={onSourcesChange}
              />
            )}
            {activeTab === 'runtime' && <RuntimeTab teammate={teammate} />}
            {activeTab === 'access' && <AccessControlTab teammate={teammate} />}
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
} 