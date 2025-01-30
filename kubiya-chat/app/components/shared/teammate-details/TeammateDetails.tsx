import React from 'react';
import { TeammateHeader } from './TeammateHeader';
import { TeammateNavigation } from './TeammateNavigation';
import type { TeammateDetails as TeammateDetailsType } from './types';
import { TooltipProvider } from '@/app/components/ui/tooltip';

interface TeammateDetailsProps {
  teammate: TeammateDetailsType | null;
  activeTab: string;
  onTabChange: (tab: string) => void;
  children?: React.ReactNode;
  integrations?: any;
}

export function TeammateDetails({ teammate, activeTab, onTabChange, children, integrations }: TeammateDetailsProps) {
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
            {children}
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
} 