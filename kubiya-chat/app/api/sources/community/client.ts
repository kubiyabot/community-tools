'use server';

import { CommunityTool } from './types';
import { NextRequest } from 'next/server';

function getBaseUrl() {
  // First try VERCEL_URL
  if (process.env.VERCEL_URL) {
    return `https://${process.env.VERCEL_URL}`;
  }
  
  // Then try NEXT_PUBLIC_APP_URL
  if (process.env.NEXT_PUBLIC_APP_URL) {
    return process.env.NEXT_PUBLIC_APP_URL;
  }
  
  // Finally, fallback to localhost
  return process.env.NODE_ENV === 'development' 
    ? 'http://localhost:3000'
    : 'https://localhost:3000';
}

// Helper function to handle fetch with retries and timeouts
async function safeFetch(path: string, options: RequestInit = {}, maxRetries = 3) {
  let lastError;
  const baseUrl = getBaseUrl();
  const url = new URL(path, baseUrl).toString();
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        next: { revalidate: 60 }, // Cache for 60 seconds
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return response;
    } catch (error) {
      lastError = error;
      if (error instanceof Error && error.name === 'AbortError') {
        break; // Don't retry on timeout
      }
      // Wait before retrying (exponential backoff)
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
    }
  }
  
  throw lastError;
}

export async function listTools(request?: NextRequest): Promise<CommunityTool[]> {
  try {
    const response = await safeFetch('/api/v1/sources/community', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return response.json();
  } catch (error) {
    console.error('Error listing tools:', error);
    return [];
  }
}

export async function getToolMetadata(path: string, request?: NextRequest): Promise<any> {
  try {
    const response = await safeFetch(`/api/v1/sources/community/${encodeURIComponent(path)}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return response.json();
  } catch (error) {
    console.error('Error getting tool metadata:', error);
    throw error;
  }
} 