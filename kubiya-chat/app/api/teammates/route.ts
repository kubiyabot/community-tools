import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';
import { revalidateTag } from 'next/cache';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

// Add cache tags for teammates
const TEAMMATES_CACHE_TAG = 'teammates';

export async function GET(req: NextRequest) {
  try {
    // Get the session and extract the access token
    const res = NextResponse.next();
    const session = await getSession(req, res);
    
    // Check for force refresh in the request
    const forceRefresh = req.headers.get('x-force-refresh') === 'true';
    
    // Add detailed session logging
    console.log('Teammates endpoint - Full session:', {
      hasAccessToken: !!session?.accessToken,
      hasUser: !!session?.user,
      userFields: session?.user ? Object.keys(session.user) : [],
      userEmail: session?.user?.email,
      userSub: session?.user?.sub,
      tokenPrefix: session?.accessToken ? session.accessToken.substring(0, 50) + '...' : null,
      forceRefresh
    });

    if (!session?.idToken) {
      console.error('Teammates endpoint - No ID token found');
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

    // Log the token type for debugging
    console.log('Teammates endpoint - Using token:', {
      type: 'id_token',
      prefix: session.idToken.substring(0, 20) + '...'
    });

    // Forward the request to Kubiya API with the ID token
    const kubiyaResponse = await fetch('https://api.kubiya.ai/api/v1/agents', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Cache-Control': forceRefresh ? 'no-cache' : 'max-age=300',
        'Pragma': forceRefresh ? 'no-cache' : 'cache',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      },
      next: {
        tags: [TEAMMATES_CACHE_TAG],
        revalidate: forceRefresh ? 0 : 300
      }
    });

    // Log request details for debugging
    console.log('Teammates endpoint - Request details:', {
      url: 'https://api.kubiya.ai/api/v1/agents',
      method: 'GET',
      token: {
        prefix: session.idToken.substring(0, 20) + '...',
        user: {
          email: session.user?.email,
          sub: session.user?.sub,
          org_id: session.user?.org_id
        }
      }
    });

    // Log response for debugging
    if (!kubiyaResponse.ok) {
      let errorData;
      try {
        errorData = await kubiyaResponse.json();
        console.error('Teammates endpoint - Full error response:', {
          status: kubiyaResponse.status,
          headers: Object.fromEntries(kubiyaResponse.headers.entries()),
          body: errorData
        });
      } catch (e) {
        errorData = {
          error: kubiyaResponse.statusText,
          status: kubiyaResponse.status,
          details: 'Could not parse error response'
        };
      }

      return new Response(JSON.stringify({
        error: 'Authentication Failed',
        status: kubiyaResponse.status,
        details: 'Unable to authenticate with Kubiya API. This might be due to an expired session or misconfigured permissions.',
        supportInfo: {
          message: 'Please contact the Kubiya support team for assistance.',
          email: 'support@kubiya.ai',
          subject: 'Authentication Issue - Chat UI',
          body: `Hi Kubiya Support,\n\nI'm experiencing authentication issues with the Chat UI.\n\nError Details:\nStatus: ${kubiyaResponse.status}\nMessage: ${errorData?.msg || kubiyaResponse.statusText}`
        }
      }), { 
        status: kubiyaResponse.status,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    let data;
    try {
      data = await kubiyaResponse.json();
      
      // Ensure each teammate has the required metadata field
      if (Array.isArray(data)) {
        data = data.map(teammate => ({
          ...teammate,
          metadata: teammate.metadata || {}  // Ensure metadata exists
        }));
      }
      
      console.log('Teammates endpoint - Successfully fetched teammates:', {
        count: Array.isArray(data) ? data.length : 'not an array',
        firstTeammate: Array.isArray(data) && data[0] ? {
          uuid: data[0].uuid,
          name: data[0].name,
          metadata: data[0].metadata
        } : null,
        responseType: typeof data
      });
    } catch (e) {
      console.error('Teammates endpoint - Failed to parse response:', e);
      return new Response(JSON.stringify({ 
        error: 'Invalid response',
        details: 'Failed to parse Kubiya API response'
      }), { 
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    return new Response(JSON.stringify(data), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });
  } catch (error) {
    console.error('Teammates endpoint error:', {
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined
    });
    return new Response(JSON.stringify({ 
      error: 'Failed to fetch teammates',
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

// Add POST method to handle cache invalidation
export async function POST(req: NextRequest) {
  try {
    const { action } = await req.json();
    
    if (action === 'revalidate') {
      revalidateTag(TEAMMATES_CACHE_TAG);
      return NextResponse.json({ revalidated: true, timestamp: Date.now() });
    }
    
    return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
  } catch (error) {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 });
  }
} 