import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

const KUBIYA_API_URL = process.env.KUBIYA_API_URL || 'https://api.kubiya.ai';

async function handleSourceLoad(req: NextRequest, method: string) {
  try {
    const res = NextResponse.next();
    const session = await getSession(req, res);
    
    if (!session?.idToken) {
      return NextResponse.json({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }, { status: 401 });
    }

    const { searchParams } = new URL(req.url);
    const url = searchParams.get('url');
    const runner = searchParams.get('runner') || 'kubiya-hosted';

    if (!url) {
      return NextResponse.json({ error: 'URL parameter is required' }, { status: 400 });
    }

    let body = {};
    if (method === 'POST') {
      try {
        body = await req.json();
      } catch (e) {
        console.warn('Failed to parse request body, using empty object');
      }
    }

    const apiUrl = new URL('/api/v1/sources/load', KUBIYA_API_URL);
    apiUrl.searchParams.set('url', url);
    apiUrl.searchParams.set('runner', runner);

    const response = await fetch(apiUrl.toString(), {
      method,
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      },
      ...(method === 'POST' && { body: JSON.stringify(body) })
    });

    let data;
    try {
      data = await response.json();
    } catch (e) {
      return NextResponse.json({ 
        error: 'Invalid JSON response from server',
        details: 'Failed to parse server response'
      }, { status: 500 });
    }

    if (!response.ok) {
      return NextResponse.json({ 
        error: data.error || 'Failed to load source', 
        details: JSON.stringify(data) 
      }, { status: response.status });
    }

    // Ensure we have a valid tools array in the response
    const formattedData = {
      tools: Array.isArray(data.tools) ? data.tools : 
             Array.isArray(data) ? data : 
             [],
      source: {
        url: url,
        runner: runner
      }
    };

    return NextResponse.json(formattedData, {
      headers: {
        'Cache-Control': 'no-store'
      }
    });
  } catch (error) {
    console.error('Error loading source:', error);
    return NextResponse.json({ 
      error: 'Internal server error',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
}

export async function GET(req: NextRequest) {
  return handleSourceLoad(req, 'GET');
}

export async function POST(req: NextRequest) {
  return handleSourceLoad(req, 'POST');
} 