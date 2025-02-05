export interface ToolArgument {
  name: string;
  type: string;
  description: string;
  required?: boolean;
  default?: any;
  enum?: any[];
  pattern?: string;
  min?: number;
  max?: number;
  minLength?: number;
  maxLength?: number;
}

export interface ToolSource {
  name: string;
  url: string;
  metadata?: {
    git_branch?: string;
    git_commit?: string;
    git_path?: string;
    docker_image?: string;
    last_updated?: string;
    created_at?: string;
  };
}

export interface Tool {
  id: string;
  name: string;
  description: string;
  type: string;
  image?: string;
  content?: string;
  workdir?: string;
  env?: string[];
  secrets?: string[];
  with_volumes?: Array<{ path: string; name: string; } | string>;
  with_files?: Array<{ source?: string; target?: string; destination?: string; content?: string; } | string>;
  mounts?: Array<{ source: string; target: string; } | string>;
  args?: Array<ToolArgument>;
  mermaid?: string;
  icon_url?: string;
  created_by?: string;
  created_at?: string;
  updated_at?: string;
  source?: ToolSource;
  uuid?: string;
  alias?: string;
}

export interface SimpleIntegration {
  name: string;
  integration_type: string;
  metadata?: Record<string, string>;
}

export interface CommitInfo {
  sha: string;
  date: string;
  message: string;
  author: {
    name: string;
    avatar?: string;
  };
}

export interface CommunityTool {
  name: string;
  path: string;
  description: string;
  tools_count: number;
  icon_url?: string;
  readme?: string;
  tools: any[];
  isDiscovering: boolean;
  error?: string;
  lastUpdated?: string;
  stars?: number;
  source?: {
    name: string;
    url: string;
    metadata: {
      git_branch: string;
      last_updated: string;
    };
  };
  lastCommit?: {
    sha: string;
    date: string;
    message: string;
    author: {
      name: string;
      avatar?: string;
    };
  };
  id: string;
  type: string;
  loadingState: 'idle' | 'loading' | 'error' | 'success';
} 