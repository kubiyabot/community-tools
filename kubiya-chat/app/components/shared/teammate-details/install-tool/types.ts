import type { TeammateDetails } from '@/app/types/teammate';
import type { ReactNode, ReactElement } from 'react';
import type { UseFormReturn } from 'react-hook-form';
import type { CommunityTool as BaseCommunityTool } from '@/app/types/tools';

export interface CommunityTool {
  name: string;
  path: string;
  description: string;
  tools_count: number;
  icon?: string;
  readme?: string;
  tools: any[];
  isDiscovering: boolean;
  error?: string;
  lastUpdated?: string;
  stars?: number;
  loadingState: 'idle' | 'loading' | 'success' | 'error';
}

export interface FormState {
  communityTools: {
    isLoading: boolean;
    error: string | null;
    data: CommunityTool[];
  };
  preview: {
    isLoading: boolean;
    error: string | null;
    data: any | null;
  };
  installation: {
    isLoading: boolean;
    error: string | null;
  };
}

export interface Step {
  id: string;
  title: string;
  description: string;
  icon: ReactElement;
}

export interface CategoryInfo {
  name: string;
  description: string;
  Icon: React.ComponentType<{ className?: string }>;
  matcher: (tool: CommunityTool) => boolean;
}

export interface CommunityToolCardProps {
  tool: CommunityTool;
  isSelected: boolean;
  onSelect: () => void;
  failedIcons?: Set<string>;
  onIconError?: (url: string) => void;
  expandedTools?: Set<string>;
  setExpandedTools?: React.Dispatch<React.SetStateAction<Set<string>>>;
}

export interface DialogFooterProps {
  currentStep: string;
  onClose: () => void;
  formState: FormState;
  methods: UseFormReturn<any>;
  onBack?: () => void;
  onNext?: () => void;
  onSubmit?: () => void;
  canProceed: boolean;
}

export interface InstallToolFormProps {
  isOpen: boolean;
  onClose: () => void;
  onInstall: (data: any) => void;
  teammate: TeammateDetails;
}

export interface UseInstallToolReturn {
  formState: FormState;
  selectedCommunityTool: CommunityTool | null;
  methods: UseFormReturn<any>;
  currentStep: string;
  activeCategory: string | null;
  setActiveCategory: React.Dispatch<React.SetStateAction<string | null>>;
  selectedTool: CommunityTool | null;
  handleToolSelect: (tool: CommunityTool) => void;
  failedIcons: Set<string>;
  handleIconError: (url: string) => void;
  expandedTools: Set<string>;
  setExpandedTools: React.Dispatch<React.SetStateAction<Set<string>>>;
  handleCommunityToolSelect: (tool: CommunityTool) => Promise<void>;
  handleRefresh: () => Promise<void>;
  handleSubmit: () => Promise<void>;
  goToNextStep: () => void;
  goToPreviousStep: () => void;
  canProceed: boolean;
  renderStepContent: () => React.ReactNode;
}

export interface UseInstallToolProps {
  onInstall: (data: any) => void;
  teammate: TeammateDetails;
} 