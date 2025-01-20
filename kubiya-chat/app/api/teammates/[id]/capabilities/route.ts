import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

// CORS headers for preflight requests
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

export async function OPTIONS() {
  return NextResponse.json({}, { headers: corsHeaders });
}

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    // Get the session and extract the access token
    const res = NextResponse.next();
    const session = await getSession(request, res);
    
    // Add detailed session logging
    console.log('Capabilities endpoint - Full session:', {
      hasAccessToken: !!session?.accessToken,
      hasUser: !!session?.user,
      userFields: session?.user ? Object.keys(session.user) : [],
      userEmail: session?.user?.email,
      userSub: session?.user?.sub,
      tokenPrefix: session?.accessToken ? session.accessToken.substring(0, 50) + '...' : null
    });

    if (!session?.idToken) {
      console.error('Capabilities endpoint - No ID token found');
      return new Response(JSON.stringify({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }), { 
        status: 401,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store',
          ...corsHeaders
        }
      });
    }

    // Log the token type for debugging
    console.log('Capabilities endpoint - Using token:', {
      type: 'id_token',
      prefix: session.idToken.substring(0, 20) + '...'
    });

    // Await params.id before using it
    const teammateId = await params.id;

    // Use the awaited teammateId
    const teammateResponse = await fetch(`https://api.kubiya.ai/api/v1/agents/${teammateId}`, {
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      },
    });

    if (!teammateResponse.ok) {
      console.error('Failed to fetch teammate details:', {
        status: teammateResponse.status,
        statusText: teammateResponse.statusText,
      });
      const errorData = await teammateResponse.json().catch(() => ({ message: teammateResponse.statusText }));
      throw new Error(errorData.message || `Failed to fetch teammate details: ${teammateResponse.status}`);
    }

    const teammateData = await teammateResponse.json();
    const sourceIds = teammateData.sources || [];

    // Fetch capabilities from each source
    const capabilities = [];
    for (const sourceId of sourceIds) {
      // First get source metadata
      const metadataResponse = await fetch(`https://api.kubiya.ai/api/v1/sources/${sourceId}/metadata`, {
        headers: {
          'Authorization': `Bearer ${session.idToken}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-Organization-ID': session.user?.org_id || '',
          'X-Kubiya-Client': 'chat-ui'
        },
      });

      if (metadataResponse.ok) {
        const metadata = await metadataResponse.json();
        const tools = metadata.tools || [];
        
        // Transform tools into capabilities
        const sourceCapabilities = tools.map((tool: any) => ({
          name: tool.name,
          description: tool.description || 'No description available',
          source: {
            id: sourceId,
            name: metadata.name || sourceId
          },
          schema: tool.schema || {},
          parameters: tool.args || [],
          type: tool.type || 'unknown',
          icon_url: tool.icon_url,
          mermaid: tool.mermaid,
          content: tool.content,
          with_files: tool.with_files,
          with_volumes: tool.with_volumes,
          env: tool.env,
          metadata: tool.metadata || {}
        }));

        capabilities.push(...sourceCapabilities);
      }
    }

    return new Response(JSON.stringify(capabilities), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store',
        ...corsHeaders
      }
    });
  } catch (error) {
    console.error('Error fetching teammate capabilities:', error);
    return new Response(JSON.stringify({
      error: 'Authentication Failed',
      status: error instanceof Error && error.message.includes('401') ? 401 : 500,
      details: 'Unable to authenticate with Kubiya API. This might be due to an expired session or misconfigured permissions.',
      supportInfo: {
        message: 'Please contact the Kubiya support team for assistance.',
        email: 'support@kubiya.ai',
        subject: 'Authentication Issue - Chat UI',
        body: `Hi Kubiya Support,\n\nI'm experiencing authentication issues with the Chat UI.\n\nError Details:\n${error instanceof Error ? error.message : 'Unknown error'}`
      }
    }), { 
      status: error instanceof Error && error.message.includes('401') ? 401 : 500,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store',
        ...corsHeaders
      }
    });
  }
} 