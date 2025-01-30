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
}

export interface DynamicConfig {
  [key: string]: any;
}

export interface SourceInfo {
  sourceId: string;
  uuid: string;
  name: string;
  url: string;
  type: string;
  tools: Tool[];
  isLoading?: boolean;
  error?: string;
  connected_agents_count: number;
  connected_tools_count: number;
  connected_workflows_count: number;
  kubiya_metadata: KubiyaMetadata;
  errors_count: number;
  source_meta: SourceMeta;
  dynamic_config: DynamicConfig | null;
  runner: string;
  managed_by: string;
  task_id: string;
} 