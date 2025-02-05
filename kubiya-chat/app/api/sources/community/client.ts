import { CommunityTool } from '@/app/types/tool';

export async function fetchCommunityTools(): Promise<CommunityTool[]> {
  const response = await fetch('/api/v1/sources/community', {
    headers: {
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache'
    }
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || 'Failed to fetch community tools');
  }
  
  const data = await response.json();
  return data.map((tool: any) => ({
    ...tool,
    id: tool.path || tool.name,
    type: 'community',
    isDiscovering: false,
    loadingState: 'idle',
    tools: tool.tools || []
  }));
}

export async function getToolMetadata(path: string): Promise<any> {
  const response = await fetch('/api/v1/sources/community', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache'
    },
    body: JSON.stringify({ path }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || 'Failed to fetch tool metadata');
  }

  return response.json();
} 