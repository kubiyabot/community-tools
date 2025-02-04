interface CommitInfo {
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
  loadingState: 'idle' | 'loading' | 'success' | 'error';
  tools: any[];
  error?: string;
  isDiscovering?: boolean;
  icon_url?: string;
  readme?: string;
  readme_summary?: string;
  lastCommit?: CommitInfo;
  contributors_count?: number;
  stars?: number;
  lastUpdated?: string;
}

export interface GitHubContentsResponse {
  name: string;
  path: string;
  sha: string;
  size: number;
  url: string;
  html_url: string;
  git_url: string;
  download_url: string | null;
  type: 'file' | 'dir' | 'symlink' | 'submodule';
  content?: string;
  encoding?: string;
} 