import type { Integration } from '@/app/types/integration';
import type { Tool } from '@/app/types/tool';
import type { TeammateDetails as BaseTeammateDetails } from '@/app/types/teammate';
import type { SourceInfo } from '@/app/types/source';

// Define the Starter type
export interface Starter {
  command: string;
  display_name?: string;
}

// Define the Runner type
export interface Runner {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'inactive' | 'error';
  metadata?: {
    version?: string;
    platform?: string;
    created_at?: string;
    last_updated?: string;
    user_created?: string;
    user_last_updated?: string;
    is_hosted?: boolean;
    cluster_type?: 'kubernetes' | 'docker' | 'local';
    cluster_name?: string;
    namespace?: string;
    node_count?: number;
    resources?: {
      cpu?: string;
      memory?: string;
      storage?: string;
    };
    error_message?: string;
  };
}

// Extend the base TeammateDetails to include additional properties needed in the UI
export interface TeammateDetails extends Omit<BaseTeammateDetails, 'integrations' | 'runners' | 'allowed_groups' | 'allowed_users' | 'owners' | 'starters'> {
  status?: 'active' | 'inactive' | 'error';
  metadata?: {
    created_at: string;
    last_updated: string;
    tools_count: number;
    integrations_count: number;
    sources_count: number;
    capabilities?: string[];
    user_created?: string;
    user_last_updated?: string;
    runtime?: {
      secrets?: string[];
      accessible_secrets?: string[];
    };
  };
  environment_variables?: Record<string, string>;
  allowed_groups?: string[];
  allowed_users?: string[];
  owners?: string[];
  starters?: Starter[];
  runners?: Runner[];
  integrations?: Integration[];
}

export interface VendorSpecific {
  arn?: string;
  region?: string;
  secret_name?: string;
  account_id?: string;
  role_name?: string;
  external_id?: string;
}

export interface IntegrationConfig {
  name: string;
  is_default: boolean;
  vendor_specific?: VendorSpecific;
}

export interface KubiyaMetadata {
  created_at?: string;
  user_created?: string;
}

export interface ToolFile {
  source: string;
  target: string;
  content?: string;
  type?: string;
  description?: string;
}

export interface ToolVolume {
  source: string;
  target: string;
  type?: string;
  description?: string;
  size?: string;
  access_mode?: string;
}

export interface ToolSource {
  id: string;
  url: string;
  commit?: string;
  committer?: string;
  branch?: string;
}

export interface ToolMetadata {
  git_url?: string;
  git_branch?: string;
  git_path?: string;
  git_commit?: string;
  git_author?: string;
  docker_image?: string;
  repository?: string;
  entrypoint?: string;
  last_updated?: string;
  created_at?: string;
  version?: string;
  author?: string;
  documentation_url?: string;
  language?: string;
  framework?: string;
  tags?: string[];
  runtime?: {
    runner?: string;
    environment?: string;
    secrets?: string[];
    timeout?: number;
    memory?: string;
    cpu?: string;
  };
}

export interface SourceMetadata {
  tools?: Tool[];
  name?: string;
  description?: string;
  repository?: string;
  errors?: Array<{
    file: string;
    type: string;
    error: string;
    details: string;
  }>;
  errors_count: number;
  connected_agents_count: number;
  connected_tools_count: number;
  connected_workflows_count: number;
  last_updated?: string;
  source_meta?: {
    id: string;
    url: string;
    branch: string;
    commit: string;
    committer: string;
  };
  kubiya_metadata?: {
    created_at: string;
    last_updated: string;
    user_created?: string;
    user_last_updated?: string;
  };
}

export interface Source {
  sourceId: string;
  name: string;
  url?: string;
  type?: string;
  sourceMeta?: {
    id: string;
    url: string;
    commit: string;
    committer: string;
    branch: string;
  };
  connected_tools_count: number;
  connected_agents_count: number;
  errors_count: number;
  kubiya_metadata?: {
    created_at: string;
    last_updated: string;
    user_created: string;
    user_last_updated: string;
  };
}

export interface TeammateTabProps {
  teammate: TeammateDetails | null;
  activeTab?: string;
  onTabChange?: (tab: string) => void;
  sources?: SourceInfo[];
  isLoading?: boolean;
}

export interface TeammateHeaderProps {
  teammate: TeammateDetails;
  integrations?: any;
}

export interface TeammateNavigationProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export interface TeammateDetailsProps {
  teammate: TeammateDetails | null;
  activeTab: string;
  onTabChange: (tab: string) => void;
  children?: React.ReactNode;
}

export interface SourceError {
  file: string;
  type: string;
  error: string;
  details: string;
}

export interface SourceMeta {
  id: string;
  url: string;
  branch?: string;
  commit?: string;
  committer?: string;
}

export interface SourceDetails {
  id: string;
  uuid: string;
  name: string;
  url: string;
  description?: string;
  connected_agents_count: number;
  connected_tools_count: number;
  connected_workflows_count: number;
  errors_count: number;
  kubiya_metadata: {
    created_at: string;
    last_updated: string;
    user_created?: string;
    user_last_updated?: string;
  };
  source_meta: {
    id: string;
    url: string;
    branch: string;
    commit: string;
    committer: string;
  };
  tools?: Tool[];
  metadata: SourceMetadata;
}

export interface IntegrationsTabProps {
  teammate: TeammateDetails | null;
  isLoading: boolean;
}

export interface RuntimeTabProps {
  teammate: TeammateDetails;
} 