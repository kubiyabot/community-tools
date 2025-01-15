import { NextRequest } from 'next/server';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    // Get all headers for debugging
    const headers = Object.fromEntries(req.headers.entries());
    console.log('Teammates endpoint - All request headers:', headers);

    // Get the authorization header from the request
    const authHeader = headers.authorization || headers.Authorization;
    console.log('Teammates endpoint - Auth header:', {
      exists: !!authHeader,
      type: authHeader?.split(' ')[0],
      prefix: authHeader ? authHeader.substring(0, 20) + '...' : null
    });

    if (!authHeader) {
      console.error('Teammates endpoint - No authorization header found');
      return new Response(JSON.stringify({ 
        error: 'Not authenticated',
        details: 'No authorization header found'
      }), { 
        status: 401,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    // Validate auth header format
    const [authType, token] = authHeader.split(' ');
    if (!authType || !token || !['Bearer', 'bearer'].includes(authType)) {
      console.error('Teammates endpoint - Invalid authorization header format');
      return new Response(JSON.stringify({ 
        error: 'Invalid authorization',
        details: 'Invalid authorization header format'
      }), { 
        status: 401,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    // Forward the request to Kubiya API
    console.log('Teammates endpoint - Forwarding request to Kubiya API');
    const kubiyaResponse = await fetch('https://api.kubiya.ai/api/v1/agents', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    });

    // Log the Kubiya API response headers
    const responseHeaders = Object.fromEntries(kubiyaResponse.headers.entries());
    console.log('Teammates endpoint - Kubiya API response:', {
      status: kubiyaResponse.status,
      statusText: kubiyaResponse.statusText,
      headers: responseHeaders
    });

    if (!kubiyaResponse.ok) {
      let errorData;
      try {
        errorData = await kubiyaResponse.json();
      } catch {
        errorData = {
          error: kubiyaResponse.statusText,
          status: kubiyaResponse.status,
          details: 'Could not parse error response'
        };
      }

      console.error('Teammates endpoint - Kubiya API error:', {
        status: kubiyaResponse.status,
        statusText: kubiyaResponse.statusText,
        errorData
      });
      
      return new Response(JSON.stringify(errorData), { 
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

    console.log('Teammates endpoint - Successfully fetched teammates:', {
      count: Array.isArray(data) ? data.length : 'not an array',
      firstTeammate: Array.isArray(data) && data[0] ? {
        uuid: data[0].uuid,
        name: data[0].name
      } : null,
      responseType: typeof data
    });
    
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