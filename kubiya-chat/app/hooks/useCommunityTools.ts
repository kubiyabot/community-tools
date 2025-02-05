import { useQuery } from '@tanstack/react-query';
import { fetchCommunityTools } from '@/app/api/sources/community/client';

interface CommunityTool {
  name: string;
  path: string;
  description: string;
  category: string;
  icon: string;
  runner: string;
}

interface UseCommunityToolsOptions {
  enabled?: boolean;
  initialData?: CommunityTool[];
  gcTime?: number;
}

export function useCommunityTools(options: UseCommunityToolsOptions = {}) {
  const { 
    enabled = true, 
    initialData,
    gcTime = 1000 * 60 * 60 // 1 hour default cache
  } = options;

  return useQuery({
    queryKey: ['community-tools'],
    queryFn: fetchCommunityTools,
    enabled,
    initialData,
    gcTime,
    staleTime: 1000 * 60 * 5, // Consider data stale after 5 minutes
    refetchOnWindowFocus: false,
    retry: 2
  });
} 