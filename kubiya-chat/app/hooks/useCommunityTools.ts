import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import { CommunityTool } from '@/app/types/tool';

async function fetchCommunityTools(): Promise<CommunityTool[]> {
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

export function useCommunityTools(initialData?: CommunityTool[]) {
  const queryOptions: UseQueryOptions<CommunityTool[], Error> = {
    queryKey: ['community-tools'],
    queryFn: fetchCommunityTools,
    initialData: initialData ? () => initialData : undefined,
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: 2
  };

  return useQuery(queryOptions);
} 