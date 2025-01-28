import { getSession } from '@auth0/nextjs-auth0/edge';
import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

// CORS headers for preflight requests
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

export async function OPTIONS() {
  return new Response(JSON.stringify({}), { 
    headers: {
      ...corsHeaders,
      'Content-Type': 'application/json'
    }
  });
}

interface TeammateResponse {
  sources?: string[];
}

export async function GET(request: NextRequest, context: { params: { id: string } }) {
  try {
    // Get the session using Auth0's Edge API with both request and response
    const response = NextResponse.next();
    const session = await getSession(request, response);
    
    // Await the params to fix the NextJS dynamic route issue
    const { id: teammateId } = await context.params;
    
    if (!session?.idToken) {
      console.error('Sources endpoint - No ID token found');
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { 
          ...corsHeaders,
          'Content-Type': 'application/json' 
        },
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
      }
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
      const emptyResponse = new Response(JSON.stringify([]), {
        status: 200,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });

      // Copy any session cookies
      response.headers.forEach((value, key) => {
        if (key.toLowerCase() === 'set-cookie') {
          emptyResponse.headers.append(key, value);
        }
      });

      return emptyResponse;
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

    // Create response with session cookies
    const responseWithSources = new Response(JSON.stringify(sources), {
      status: 200,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });

    // Copy any session cookies
    response.headers.forEach((value, key) => {
      if (key.toLowerCase() === 'set-cookie') {
        responseWithSources.headers.append(key, value);
      }
    });

    return responseWithSources;
  } catch (error) {
    console.error('Sources endpoint error:', {
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined,
      params: await context.params
    });

    return new Response(JSON.stringify({ 
      error: 'Failed to fetch sources',
      details: error instanceof Error ? error.message : 'Unknown error'
    }), { 
      status: 500,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });
  }
} 