import type { UseFormReturn } from 'react-hook-form';
import type { TeammateDetails } from '@/app/types/teammate';
import type { ReactNode, ReactElement } from 'react';
import type { ToolArgument, ToolSource } from '@/app/types/tool';
import type { Dispatch, SetStateAction } from 'react';
import { z } from 'zod';
import { sourceFormSchema } from './schema';
import { useForm } from 'react-hook-form';
import type { FormValues } from './schema';

interface CommitInfo {
  sha: string;
  date: string;
  message: string;
  author: {
    name: string;
    avatar?: string;
  };
}

export interface CommunityTool {
  id: string;
  name: string;
  description: string;
  type: string;
  icon_url?: string;
  path: string;
  runner?: string;
  image?: string;
  content?: string;
  workdir?: string;
  args?: ToolArgument[];
  env?: string[];
  secrets?: string[];
  with_volumes?: Array<{ path: string; name: string; } | string>;
  with_files?: Array<{ source?: string; target?: string; destination?: string; content?: string; } | string>;
  mounts?: Array<{ source: string; target: string; } | string>;
  mermaid?: string;
  source?: ToolSource;
  uuid?: string;
  alias?: string;
  readme_summary?: string;
  lastCommit?: CommitInfo;
  contributors_count?: number;
  isDiscovering: boolean;
  loadingState: 'idle' | 'loading' | 'success' | 'error';
  tools: CommunityTool[];
  error?: string;
  lastUpdated?: string;
  stars?: number;
  created_by?: string;
  created_at?: string;
  updated_at?: string;
}

export interface FormState {
  isOpen: boolean;
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
    data: any | null;
  };
  methods?: UseFormReturn<any>;
}

export interface Tool {
  name: string;
  description: string;
  type?: string;
  icon_url?: string;
  tools: Array<{
    name: string;
    description?: string;
    args?: Array<{
      name: string;
      required?: boolean;
    }>;
  }>;
  args?: Array<{
    name: string;
    required?: boolean;
  }>;
  image?: string;
}

export interface InstallToolFormState {
  isOpen: boolean;
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
    data: any | null;
    isComplete: boolean;
  };
}

export interface Step {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
}

export interface CategoryInfo {
  id: string;
  name: string;
  description?: string;
  icon?: string;
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
  formState: InstallToolFormState;
  methods: UseFormReturn<FormValues>;
  onBack?: () => void;
  onNext?: () => void;
  onSubmit: (data: FormValues) => Promise<void>;
  canProceed: boolean;
}

export interface InstallToolFormProps {
  isOpen: boolean;
  onClose: () => void;
  onInstall: (
    values: FormValues,
    updateProgress: (stepId: string, status: 'pending' | 'loading' | 'success' | 'error', error?: string) => void
  ) => Promise<void>;
  teammate: TeammateDetails;
  initialValues?: Partial<FormValues>;
}

export interface InstallToolState {
  formState: InstallToolFormState;
  selectedTool: CommunityTool | null;
  methods: UseFormReturn<FormValues>;
  currentStep: string;
  activeCategory: string | null;
  setActiveCategory: (category: string) => void;
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
  selectedTools: Set<string>;
  setSelectedTools: React.Dispatch<React.SetStateAction<Set<string>>>;
  canProceed: boolean;
  renderStepContent: () => React.ReactNode;
  teammate: TeammateDetails;
  setState: React.Dispatch<React.SetStateAction<InstallToolFormState>>;
}

export interface UseInstallToolReturn {
  formState: InstallToolFormState;
  methods: UseFormReturn<FormValues>;
  currentStep: string;
  activeCategory: string | null;
  setActiveCategory: (category: string | null) => void;
  selectedTool: CommunityTool | null;
  handleToolSelect: (tool: CommunityTool) => void;
  failedIcons: Set<string>;
  handleIconError: (url: string) => void;
  expandedTools: Set<string>;
  setExpandedTools: React.Dispatch<React.SetStateAction<Set<string>>>;
  handleCommunityToolSelect: (tool: CommunityTool) => void;
  handleRefresh: () => Promise<void>;
  handleSubmit: (data: FormValues) => Promise<void>;
  goToNextStep: () => void;
  goToPreviousStep: () => void;
  selectedTools: Set<string>;
  setSelectedTools: React.Dispatch<React.SetStateAction<Set<string>>>;
  canProceed: boolean;
  renderStepContent: () => React.ReactNode;
  teammate: TeammateDetails;
  setState: React.Dispatch<React.SetStateAction<InstallToolFormState>>;
  steps: InstallationStep[];
  setSteps: (steps: InstallationStep[]) => void;
  isLoading: boolean;
  installationSteps: InstallationStep[];
  startInstallation: () => void;
  cancelInstallation: () => void;
  updateStepStatus: (stepId: string, status: 'pending' | 'loading' | 'success' | 'error', error?: string) => void;
  isInstallationComplete: boolean;
  resetInstallation: () => void;
}

export interface UseInstallToolProps {
  onInstall: (
    values: FormValues,
    updateProgress: (stepId: string, status: 'pending' | 'loading' | 'success' | 'error', error?: string) => void
  ) => Promise<void>;
  teammate: TeammateDetails;
  onClose?: () => void;
}

export type ExtendedCommunityTool = CommunityTool & {
  runner: string;
};

export type InstallationStep = {
  id: string;
  status: 'pending' | 'loading' | 'success' | 'error';
  description: string;
  error?: string;
};

export type InstallationStatus = {
  isComplete: boolean;
  error: string | null;
  currentStep: string;
};

export type { FormValues }; 