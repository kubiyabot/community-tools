import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

const KUBIYA_API_URL = process.env.KUBIYA_API_URL || 'https://api.kubiya.ai';

// Get auth headers from environment or session
async function getAuthHeaders(req?: NextRequest): Promise<HeadersInit> {
  if (req) {
    const res = NextResponse.next();
    const session = await getSession(req, res);
    if (session?.idToken) {
      return {
        'Authorization': `Bearer ${session.idToken}`,
        'X-Organization-ID': session.user?.org_id || '',
      };
    }
  }
  
  // Fallback to API key if no session
  const apiKey = process.env.KUBIYA_API_KEY;
  if (apiKey) {
    return {
      'Authorization': `Bearer ${apiKey}`,
    };
  }

  throw new Error('No authorization credentials available');
}

export async function fetchSource(url: string, req?: NextRequest) {
  const authHeaders = await getAuthHeaders(req);
  
  const apiUrl = new URL('/api/v1/sources/load', KUBIYA_API_URL);
  apiUrl.searchParams.set('url', url);

  const response = await fetch(apiUrl.toString(), {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache',
      'X-Kubiya-Client': 'chat-ui',
      ...authHeaders
    } as HeadersInit
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.error || 'Failed to load source');
  }

  return response.json();
} 