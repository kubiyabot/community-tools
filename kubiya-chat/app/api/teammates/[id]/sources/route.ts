import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

interface TeammateResponse {
  sources?: string[];
}

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    // Get the session and extract the access token
    const res = NextResponse.next();
    const session = await getSession(req, res);
    
    // Await the params to fix the NextJS dynamic route issue
    const teammateId = await params.id;
    
    if (!session?.idToken) {
      console.error('Sources endpoint - No ID token found');
      return new Response(JSON.stringify({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }), { 
        status: 401,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    // Log request details
    console.log('Sources endpoint - Request details:', {
      teammateId,
      hasToken: !!session.idToken,
      orgId: session.user?.org_id
    });

    // First get the teammate details to ensure it exists
    const teammateResponse = await fetch(`https://api.kubiya.ai/api/v1/agents/${teammateId}`, {
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      },
    });

    if (!teammateResponse.ok) {
      console.error('Sources endpoint - Failed to fetch teammate:', {
        status: teammateResponse.status,
        statusText: teammateResponse.statusText
      });
      throw new Error(`Failed to fetch teammate: ${await teammateResponse.text()}`);
    }

    const teammate = await teammateResponse.json();
    const sourceIds = teammate.sources || [];

    if (sourceIds.length === 0) {
      console.log('Sources endpoint - No sources found for teammate:', teammateId);
      return new Response(JSON.stringify([]), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    // Log success with source IDs
    console.log('Sources endpoint - Successfully fetched sources:', {
      count: sourceIds.length,
      sourceIds
    });

    // Map source IDs to simple objects with consistent format
    const sources = sourceIds.map((sourceId: string) => ({
      sourceId,
      name: `Source ${sourceId.slice(0, 8)}`
    }));

    // Log the final formatted response
    console.log('Sources endpoint - Returning formatted sources:', {
      count: sources.length,
      firstSource: sources[0]
    });

    return new Response(JSON.stringify(sources), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });
  } catch (error) {
    console.error('Sources endpoint error:', {
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined,
      params: await params
    });
    return new Response(JSON.stringify({ 
      error: 'Failed to fetch sources',
      details: error instanceof Error ? error.message : 'Unknown error'
    }), { 
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });
  }
} 