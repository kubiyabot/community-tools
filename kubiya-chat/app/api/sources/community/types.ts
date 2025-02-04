export interface ErrorResponse {
  error?: string;
  message?: string;
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
  readme_summary?: string;
  tools?: any[];
  isDiscovering?: boolean;
  error?: string;
  lastUpdated?: string;
  stars?: number;
  lastCommit?: CommitInfo;
  contributors_count?: number;
  loadingState: 'idle' | 'loading' | 'success' | 'error';
}

export interface GitHubContentsResponse {
  tools?: any[];
  description?: string;
} 