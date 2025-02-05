import { Tool } from './tool';

export interface KubiyaMetadata {
  created_at: string;
  last_updated: string;
  user_created: string;
  user_last_updated: string;
}

export interface SourceMeta {
  id: string;
  url: string;
  commit: string;
  committer: string;
  branch: string;
  repository?: string;
  owner?: string;
  repo?: string;
}

export interface DynamicConfig {
  [key: string]: any;
}

export interface SourceInfo {
  uuid: string;
  sourceId: string;
  name: string;
  url: string;
  type: string;
  runner: string;
  tools: any[];
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
    branch: string;
    commit: string;
    committer: string;
  };
  dynamic_config: any;
  managed_by: string;
  task_id: string;
} 