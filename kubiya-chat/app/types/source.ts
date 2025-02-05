import { Tool } from './tool';

export interface KubiyaMetadata {
  created_at: string;
  last_updated: string;
  user_created: string;
  user_last_updated: string;
}

export interface SourceError {
  file: string;
  error: string;
  details?: string;
}

export interface SourceMeta {
  id: string;
  url: string;
  commit?: string;
  committer?: string;
  branch?: string;
  repository?: string;
  owner?: string;
  repo?: string;
}

export interface DynamicConfig {
  [key: string]: any;
}

export interface SourceInfo {
  id: string;
  name: string;
  url?: string;
  source_meta?: SourceMeta;
  errors?: SourceError[];
  dynamic_config?: any;
  runner?: string;
  error?: string;
  uuid: string;
  sourceId: string;
  type: string;
  tools: any[];
  isLoading?: boolean;
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
  managed_by: string;
  task_id: string;
} 