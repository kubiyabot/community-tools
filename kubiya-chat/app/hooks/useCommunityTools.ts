import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { CommunityTool } from '@/app/api/sources/community/types';

interface UseCommunityToolsOptions {
  enabled?: boolean;
  initialData?: CommunityTool[];
  gcTime?: number;
}

const fetchCommunityTools = async (): Promise<CommunityTool[]> => {
  const response = await fetch('/api/sources/community/list', {
    headers: {
      'Cache-Control': 'max-age=3600', // Cache for 1 hour
    }
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch community tools');
  }
  
  const data = await response.json();
  return data.map((tool: any) => ({
    ...tool,
    loadingState: tool.loadingState || 'idle'
  }));
};

export function useCommunityTools(options: UseCommunityToolsOptions = {}) {
  const { 
    enabled = true, 
    initialData,
    gcTime = 1000 * 60 * 60 // 1 hour default cache
  } = options;

  const {
    data: tools,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['communityTools'],
    queryFn: fetchCommunityTools,
    enabled,
    initialData: initialData as CommunityTool[],
    gcTime,
    staleTime: 1000 * 60 * 5, // Consider data stale after 5 minutes
    refetchOnWindowFocus: false,
    retry: 2,
  });

  return {
    tools,
    isLoading,
    error,
    refetch
  };
} 