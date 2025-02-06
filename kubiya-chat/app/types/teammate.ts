import { Integration } from './integration';

export interface TeammateInfo {
  uuid: string;
  name: string;
  team_id?: string;
  user_id?: string;
  org_id?: string;
  email?: string;
  context?: string;
  integrations?: (Integration | string)[];
  avatar?: string;
  role?: string;
  status?: 'active' | 'inactive' | 'busy';
  lastActive?: string;
  preferences?: {
    notifications?: boolean;
    theme?: 'light' | 'dark' | 'system';
    language?: string;
  };
}

export interface TeammateContextType {
  teammates: TeammateInfo[];
  selectedTeammate?: TeammateInfo;
  setSelectedTeammate: (teammate: TeammateInfo | string) => void;
  isLoading?: boolean;
  error?: Error;
}

export interface SourceMetadata {
  git_url?: string;
  git_branch?: string;
  git_commit?: string;
  git_path?: string;
  docker_image?: string;
  last_updated?: string;
  created_at?: string;
}

export interface Tool {
  id: string;
  name: string;
  description?: string;
  type: string;
  icon_url?: string;
  image?: string;
  code?: string;
  entrypoint?: string;
  workdir?: string;
  args?: Array<{
    name: string;
    type: string;
    description: string;
    required?: boolean;
  }>;
  env?: string[];
  secrets?: string[];
  mounts?: Array<{
    source: string;
    target: string;
  }>;
  source?: {
    name: string;
    url: string;
    metadata: SourceMetadata;
  };
  with_files?: Array<{
    source: string;
    target: string;
    content?: string;
  }>;
  mermaid?: string;
}

export interface TeammateDetails {
  id: string;
  uuid: string;
  name: string;
  runners?: string[];
  sources?: SourceInfo[];
  llm_model?: string;
  tools?: any[];
  avatar_url?: string;
  description?: string;
  integrations?: Integration[];
  capabilities?: {
    llm_model?: string;
    instruction_type?: string;
    runner?: string;
  };
  metadata: {
    created_at: string;
    last_updated: string;
    tools_count: number;
    integrations_count: number;
    sources_count: number;
    capabilities?: string[];
    user_created?: string;
    user_last_updated?: string;
    runtime?: {
      [key: string]: any;
    };
    workspace?: {
      id: string;
    };
    management?: {
      managed_by?: string;
    };
  };
  environment_variables?: Record<string, string>;
  allowed_groups?: string[];
  allowed_users?: string[];
  owners?: string[];
  status?: 'active' | 'inactive' | 'error';
}

export interface TeammateWithCapabilities extends TeammateDetails {
  // No need to redeclare capabilities since it's already in TeammateDetails
}

export interface SourceInfo {
  uuid: string;
  sourceId?: string;
  name: string;
  url: string;
  type?: string;
  tools?: any[];
  isLoading?: boolean;
  error?: string;
  connected_agents_count: number;
  connected_tools_count: number;
  connected_workflows_count: number;
  kubiya_metadata: {
    created_at: string;
    last_updated: string;
    user_created: string;
    user_last_updated: string;
  };
  errors_count: number;
  source_meta: {
    id: string;
    url: string;
    commit?: string;
    committer?: string;
    branch?: string;
  };
  dynamic_config: any;
  runner: string;
  managed_by: string;
  task_id: string;
}

export interface SourceResponse {
  synced: boolean;
  source: {
    name: string;
    summary: {
      agents: number;
      tools: number;
      workflows: number;
      errors: number;
      lastUpdated: string;
      branch: string;
      commit?: string;
    };
    details: {
      url: string;
      metadata: {
        created_at: string;
        last_updated: string;
        user_created: string;
        user_last_updated: string;
      };
      sourceMeta: {
        id: string;
        url: string;
        commit?: string;
        committer?: string;
        branch?: string;
      };
      errors: Array<{
        file: string;
        error: string;
        traceback?: string;
      }>;
    };
  };
  timestamp: number;
  success: boolean;
  message: string;
} 