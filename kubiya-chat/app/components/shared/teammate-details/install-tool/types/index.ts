import type { TeammateDetails } from '@/app/types/teammate';
import type { ReactNode, ReactElement } from 'react';

export interface CommunityTool {
  name: string;
  path: string;
  description: string;
  tools_count: number;
  icon?: string;
  readme?: string;
  tools?: any[];
  isDiscovering?: boolean;
  error?: string;
  lastUpdated?: string;
  stars?: number;
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

export interface InstallToolFormProps {
  isOpen: boolean;
  onClose: () => void;
  onInstall: (data: any) => void;
  teammate: TeammateDetails;
}

export interface Step {
  id: string;
  title: string;
  description: string;
  icon: ReactElement;
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

export interface InstallationStep {
  id: string;
  label: string;
  status: 'pending' | 'loading' | 'complete' | 'error';
  error?: string;
}

export interface ToolMetadata {
  isLoading: boolean;
  error: string | null;
  data: CommunityTool[];
}

export interface CategoryInfo {
  name: string;
  description: string;
  Icon: React.ComponentType<{ className?: string }>;
  matcher: (tool: CommunityTool) => boolean;
}

export interface UseInstallToolProps {
  onInstall: (data: any) => void;
  teammate: TeammateDetails;
} 