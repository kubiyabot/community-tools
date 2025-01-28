import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    // Get the session and extract the access token
    const res = NextResponse.next();
    const session = await getSession(req, res);

    if (!session?.idToken) {
      console.error('Webhooks endpoint - No ID token found');
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

    const response = await fetch('https://api.kubiya.ai/api/v1/event', {
      method: 'GET',
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

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
        console.error('Webhooks endpoint - Full error response:', {
          status: response.status,
          headers: Object.fromEntries(response.headers.entries()),
          body: errorData
        });
      } catch (e) {
        errorData = {
          error: response.statusText,
          status: response.status,
          details: 'Could not parse error response'
        };
      }

      return new Response(JSON.stringify({
        error: 'Authentication Failed',
        status: response.status,
        details: 'Unable to authenticate with Kubiya API. This might be due to an expired session or misconfigured permissions.',
        supportInfo: {
          message: 'Please contact the Kubiya support team for assistance.',
          email: 'support@kubiya.ai',
          subject: 'Authentication Issue - Chat UI',
          body: `Hi Kubiya Support,\n\nI'm experiencing authentication issues with the Chat UI.\n\nError Details:\nStatus: ${response.status}\nMessage: ${errorData?.msg || response.statusText}`
        }
      }), { 
        status: response.status,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    const data = await response.json();
    
    // Format the response to match the webhook structure
    const webhooks = data.map((event: any) => ({
      id: event.id,
      name: event.name,
      source: event.source,
      agent_id: event.agent_id,
      prompt: event.prompt,
      communication: event.communication,
      created_by: event.created_by,
      webhook_url: event.webhook_url,
      filter: event.filter || ''
    }));

    return new Response(JSON.stringify(webhooks), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });
  } catch (error) {
    console.error('Webhooks endpoint error:', {
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined
    });
    return new Response(JSON.stringify({ 
      error: 'Failed to fetch webhooks',
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