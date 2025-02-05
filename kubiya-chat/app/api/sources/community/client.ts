'use server';

import { CommunityTool } from './types';
import { NextRequest } from 'next/server';

export async function listTools(request?: NextRequest): Promise<CommunityTool[]> {
  try {
    const response = await fetch('/api/sources/community', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch tools');
    }

    return response.json();
  } catch (error) {
    console.error('Error listing tools:', error);
    return [];
  }
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