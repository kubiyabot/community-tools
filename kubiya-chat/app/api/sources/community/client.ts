'use server';

import type { CommunityTool } from '@/app/types/tool';
import { NextRequest } from 'next/server';

export async function fetchCommunityTools(): Promise<CommunityTool[]> {
  const response = await fetch('/api/v1/sources/community', {
    headers: {
      'Cache-Control': 'max-age=3600', // Cache for 1 hour
    }
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch community tools: ${response.statusText}`);
  }
  
  return response.json();
}

export async function getToolMetadata(path: string, request?: NextRequest): Promise<any> {
  try {
    const response = await fetch('/api/sources/community', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ path }),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch tool metadata');
    }

    return response.json();
  } catch (error) {
    console.error('Error getting tool metadata:', error);
    throw error;
  }
} 