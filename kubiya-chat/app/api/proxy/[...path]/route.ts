import { NextRequest } from 'next/server';

// Helper function to validate API key
function getValidatedApiKey(): string {
  const apiKey = process.env.KUBIYA_API_KEY || process.env.NEXT_PUBLIC_KUBIYA_API_KEY;
  if (!apiKey) {
    throw new Error('No API key found');
  }
  return apiKey;
}

// Helper function to get base URL
function getBaseUrl(): string {
  return process.env.NEXT_PUBLIC_KUBIYA_API_URL || 'https://api.kubiya.ai/api/v1';
}

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, Accept',
};

// Helper function to get request headers
function getRequestHeaders(request: NextRequest): HeadersInit {
  const apiKey = getValidatedApiKey();
  
  return {
    'Authorization': `UserKey ${apiKey}`,
    'Content-Type': 'application/json',
    'Accept': request.headers.get('Accept') || 'application/json',
    'User-Agent': 'Kubiya-Chat/1.0',
  };
}

export async function GET(request: NextRequest) {
  try {
    const path = request.nextUrl.pathname.replace('/api/proxy', '');
    const baseUrl = getBaseUrl();

    const response = await fetch(`${baseUrl}${path}`, {
      headers: getRequestHeaders(request),
      cache: 'no-store',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(errorData.message || `API responded with status: ${response.status}`);
    }

    return new Response(response.body, {
      headers: {
        ...corsHeaders,
        ...Object.fromEntries(response.headers),
      },
      status: response.status,
    });
  } catch (error) {
    console.error('Proxy GET error:', error);
    return new Response(
      JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }),
      {
        status: 500,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const path = request.nextUrl.pathname.replace('/api/proxy', '');
    const baseUrl = getBaseUrl();

    const body = await request.json().catch(() => null);
    if (!body) {
      return new Response(
        JSON.stringify({ error: 'Invalid JSON body' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Don't include session_id in the first message
    if (body.message && !body.session_id) {
      delete body.session_id;
    }

    const response = await fetch(`${baseUrl}${path}`, {
      method: 'POST',
      headers: getRequestHeaders(request),
      body: JSON.stringify(body),
      cache: 'no-store',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(errorData.message || `API responded with status: ${response.status}`);
    }

    return new Response(response.body, {
      headers: {
        ...corsHeaders,
        ...Object.fromEntries(response.headers),
      },
      status: response.status,
    });
  } catch (error) {
    console.error('Proxy POST error:', error);
    return new Response(
      JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
}

export async function OPTIONS() {
  return new Response(null, {
    headers: corsHeaders,
  });
} 