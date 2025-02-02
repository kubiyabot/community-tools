import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

const KUBIYA_API_URL = process.env.KUBIYA_API_URL || 'https://api.kubiya.ai';

async function getAvailableRunners(session: any) {
  try {
    const response = await fetch(`${KUBIYA_API_URL}/api/v3/runners`, {
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      }
    });

    if (!response.ok) {
      console.warn('Failed to fetch runners, using default');
      return ['docker', 'local'];
    }

    const data = await response.json();
    // Filter active/healthy runners and prioritize non kubiya-hosted runners
    const runners = data
      .filter((runner: any) => runner.status === 'active' || runner.health?.status === 'healthy')
      .map((runner: any) => runner.id);

    // Sort to put kubiya-hosted last
    return runners.sort((a: string, b: string) => {
      if (a === 'kubiya-hosted') return 1;
      if (b === 'kubiya-hosted') return -1;
      return 0;
    });
  } catch (error) {
    console.error('Error fetching runners:', error);
    return ['docker', 'local']; // Fallback to standard runners
  }
}

async function tryWithRunner(url: string, runner: string, session: any, method: string, body?: any) {
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
      'X-Organization-ID': session.user?.org_id || '',
      'X-Kubiya-Client': 'chat-ui'
    },
    ...(method === 'POST' && { body: JSON.stringify(body) })
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.error || `Failed with runner ${runner}`);
  }

  return response.json();
}

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
    const requestedRunner = searchParams.get('runner');

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

    // Get available runners dynamically
    const availableRunners = await getAvailableRunners(session);
    
    // If a specific runner is requested, try it first
    const runnersToTry = requestedRunner 
      ? [requestedRunner, ...availableRunners.filter((r: string) => r !== requestedRunner)]
      : availableRunners;

    let lastError = null;

    // Try each runner in sequence
    for (const runner of runnersToTry) {
      try {
        const data = await tryWithRunner(url, runner, session, method, body);
        console.log(`Successfully loaded with runner: ${runner}`);

        // Ensure we have a valid tools array in the response
        const formattedData = {
          tools: Array.isArray(data.tools) ? data.tools : 
                 Array.isArray(data) ? data : 
                 [],
          source: {
            url,
            runner,
            ...(data.source || {})
          }
        };

        return NextResponse.json(formattedData, {
          headers: {
            'Cache-Control': 'no-store'
          }
        });
      } catch (error) {
        console.warn(`Failed with runner ${runner}:`, error);
        lastError = error;
        // Continue to next runner
      }
    }

    // If all runners failed
    console.error('All runners failed:', lastError);
    return NextResponse.json({ 
      error: 'Failed to load source',
      details: lastError instanceof Error ? lastError.message : 'All runners failed'
    }, { status: 500 });
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