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
  uuid: string;
  name: string;
  description?: string;
  avatar_url?: string;
  llm_model?: string;
  instruction_type?: string;
  tools?: Tool[];
  runners?: string[];
  integrations?: Array<{
    id: string;
    name: string;
    type: string;
    icon_url?: string;
  }>;
  sources?: string[];  // Array of source UUIDs
  metadata?: {
    created_at: string;
    last_updated: string;
    tools_count: number;
    integrations_count: number;
    sources_count: number;
  };
}

export interface TeammateWithCapabilities extends TeammateDetails {
  capabilities?: {
    llm_model?: string;
    instruction_type?: string;
    runner?: string;
  };
} 