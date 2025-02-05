import { useQuery } from '@tanstack/react-query';
import { CommunityTool } from '@/app/types/tool';

async function fetchCommunityTools(): Promise<CommunityTool[]> {
  const response = await fetch('/api/sources/community/list');
  if (!response.ok) {
    throw new Error('Failed to fetch community tools');
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

export function useCommunityTools(initialData?: CommunityTool[]) {
  return useQuery({
    queryKey: ['community-tools'],
    queryFn: fetchCommunityTools,
    initialData: initialData ? () => initialData : undefined,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
} 