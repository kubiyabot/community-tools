import * as React from 'react';
import type { UseFormReturn } from 'react-hook-form';
import type { CommunityTool, FormState } from '../types';

interface InstallToolContextType {
  currentStep: string;
  formState: FormState;
  activeCategory: string | null;
  setActiveCategory: (category: string) => void;
  selectedTool: CommunityTool | null;
  handleToolSelect: (tool: CommunityTool) => void;
  failedIcons: Set<string>;
  handleIconError: (url: string) => void;
  expandedTools: Set<string>;
  setExpandedTools: React.Dispatch<React.SetStateAction<Set<string>>>;
  methods: UseFormReturn<any>;
  handleCommunityToolSelect: (tool: CommunityTool) => Promise<void>;
  handleRefresh: () => Promise<void>;
  handleSubmit: () => Promise<void>;
  goToNextStep: () => void;
  goToPreviousStep: () => void;
  canProceed: boolean;
}

const InstallToolContext = React.createContext<InstallToolContextType | undefined>(undefined);

export function useInstallToolContext() {
  const context = React.useContext(InstallToolContext);
  if (!context) {
    throw new Error('useInstallToolContext must be used within an InstallToolProvider');
  }
  return context;
}

export function InstallToolProvider({ children, value }: { children: React.ReactNode; value: InstallToolContextType }) {
  return (
    <InstallToolContext.Provider value={value}>
      {children}
    </InstallToolContext.Provider>
  );
} 