import type { SourceInfo } from './source';
import type { ReactNode } from 'react';

export interface ToolLoadingState {
  isLoading: boolean;
  progress: number;
  message?: string;
  error?: string;
}

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

export interface ToolDefinition {
  name: string;
  description?: string;
  type?: string;
  icon_url?: string;
  tools?: any[];
}

export interface CategoryInfo {
  name: string;
  description: string;
  icon: React.ReactElement;
  matcher: (tool: CommunityTool) => boolean;
}

export interface RetryQueueItem {
  tool: CommunityTool;
  retryCount: number;
  lastError: string;
}

export interface ToolState {
  isLoading: boolean;
  error: string | null;
  data: {
    tools: any[];
    errors?: {
      file: string;
      type: string;
      error: string;
      details: string;
    }[];
    source: SourceInfo;
  } | null;
}

export interface FormState {
  communityTools: {
    isLoading: boolean;
    error: string | null;
    data: CommunityTool[];
    loadingStates: Record<string, boolean>;
  };
  preview: {
    isLoading: boolean;
    error: string | null;
    data: any;
  };
  installation: {
    isLoading: boolean;
    error: string | null;
  };
} 