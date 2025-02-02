export interface CommunityTool {
  name: string;
  path: string;
  description: string;
  tools_count: number;
  loadingState: 'idle' | 'loading' | 'success' | 'error';
  tools: any[];
  error?: string;
  isDiscovering?: boolean;
  icon?: string;
}

export interface GitHubContentsResponse {
  name: string;
  path: string;
  type: string;
  download_url: string | null;
} 