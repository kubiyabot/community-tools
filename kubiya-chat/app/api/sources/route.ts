import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const res = NextResponse.next();
    const session = await getSession(req, res);
    
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
      hasToken: !!session.idToken,
      orgId: session.user?.org_id
    });

    // Fetch sources directly from the sources API
    const sourcesResponse = await fetch(`https://api.kubiya.ai/api/v1/sources`, {
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

    if (!sourcesResponse.ok) {
      console.error('Sources endpoint - Failed to fetch sources:', {
        status: sourcesResponse.status,
        statusText: sourcesResponse.statusText
      });
      throw new Error(`Failed to fetch sources: ${await sourcesResponse.text()}`);
    }

    const sources = await sourcesResponse.json();

    // Log success
    console.log('Sources endpoint - Successfully fetched sources:', {
      count: sources.length
    });

    // Map sources to the expected format
    const formattedSources = sources
      .filter((source: any) => source && source.id)
      .map((source: any) => ({
        sourceId: source.id,
        name: source.name || `Source ${source.id.slice(0, 8)}`,
        description: source.description,
        type: source.type
      }));

    // Log the final response for debugging
    console.log('Sources endpoint - Returning response:', {
      sourcesCount: formattedSources.length,
      firstSource: formattedSources[0]
    });

    return new Response(JSON.stringify(formattedSources), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });
  } catch (error) {
    console.error('Sources endpoint error:', {
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined
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