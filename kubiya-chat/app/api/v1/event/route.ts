import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

export const runtime = 'edge';

// GET handler for listing webhooks
export async function GET(req: NextRequest) {
  try {
    const res = NextResponse.next();
    const session = await getSession(req, res);

    if (!session?.idToken) {
      return NextResponse.json({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }, { status: 401 });
    }

    // Log request details for debugging
    console.log('List webhooks endpoint - Request details:', {
      url: 'https://api.kubiya.ai/api/v1/event',
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

    const response = await fetch('https://api.kubiya.ai/api/v1/event', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      }
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
        console.error('List webhooks endpoint - Full error response:', {
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

      return NextResponse.json({
        error: 'Failed to list webhooks',
        status: response.status,
        details: errorData?.error || 'Unable to list webhooks. This might be due to an expired session or misconfigured permissions.',
        supportInfo: {
          message: 'Please contact the Kubiya support team for assistance.',
          email: 'support@kubiya.ai',
          subject: 'Webhook Listing Issue - Chat UI',
          body: `Hi Kubiya Support,\n\nI'm experiencing issues listing webhooks in the Chat UI.\n\nError Details:\nStatus: ${response.status}\nMessage: ${errorData?.error || response.statusText}`
        }
      }, { status: response.status });
    }

    const webhooks = await response.json();
    return NextResponse.json(webhooks);
  } catch (error) {
    console.error('Error listing webhooks:', error);
    return NextResponse.json(
      { error: 'Failed to list webhooks', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

// POST handler for creating webhooks
export async function POST(req: NextRequest) {
  try {
    const res = NextResponse.next();
    const session = await getSession(req, res);

    if (!session?.idToken) {
      return NextResponse.json({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }, { status: 401 });
    }

    let data;
    try {
      const rawData = await req.text();
      data = JSON.parse(rawData);
    } catch (e) {
      return NextResponse.json({
        error: 'Invalid JSON format',
        details: 'Request body must be valid JSON'
      }, { status: 400 });
    }

    // Validate required fields
    if (!data.name || !data.source || !data.prompt || !data.communication) {
      return NextResponse.json({
        error: 'Missing required fields',
        details: 'Required fields: name, source, prompt, communication'
      }, { status: 400 });
    }

    // Validate communication object
    if (!data.communication.destination || !data.communication.method) {
      return NextResponse.json({
        error: 'Invalid communication config',
        details: 'Communication must include destination and method'
      }, { status: 400 });
    }

    // Log request details for debugging
    console.log('Create webhook endpoint - Request details:', {
      url: 'https://api.kubiya.ai/api/v1/event',
      method: 'POST',
      token: {
        prefix: session.idToken.substring(0, 20) + '...',
        user: {
          email: session.user?.email,
          sub: session.user?.sub,
          org_id: session.user?.org_id
        }
      },
      data
    });

    const response = await fetch('https://api.kubiya.ai/api/v1/event', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      },
      body: JSON.stringify({
        ...data,
        created_by: session.user?.email,
        org: session.user?.org_id,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
        console.error('Create webhook endpoint - Full error response:', {
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

      return NextResponse.json({
        error: 'Failed to create webhook',
        status: response.status,
        details: errorData?.error || 'Unable to create webhook. This might be due to an expired session or misconfigured permissions.',
        supportInfo: {
          message: 'Please contact the Kubiya support team for assistance.',
          email: 'support@kubiya.ai',
          subject: 'Webhook Creation Issue - Chat UI',
          body: `Hi Kubiya Support,\n\nI'm experiencing issues creating webhooks in the Chat UI.\n\nError Details:\nStatus: ${response.status}\nMessage: ${errorData?.error || response.statusText}`
        }
      }, { status: response.status });
    }

    const webhook = await response.json();
    return NextResponse.json(webhook);
  } catch (error) {
    console.error('Error creating webhook:', error);
    return NextResponse.json(
      { error: 'Failed to create webhook', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

// DELETE handler for removing webhooks
export async function DELETE(req: NextRequest) {
  try {
    const res = NextResponse.next();
    const session = await getSession(req, res);

    if (!session?.idToken) {
      return NextResponse.json({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }, { status: 401 });
    }

    const url = new URL(req.url);
    const webhookId = url.searchParams.get('webhookId');

    if (!webhookId) {
      return NextResponse.json({
        error: 'Missing webhook ID',
        details: 'Webhook ID is required'
      }, { status: 400 });
    }

    // Log request details for debugging
    console.log('Delete webhook endpoint - Request details:', {
      url: `https://api.kubiya.ai/api/v1/event/${webhookId}`,
      method: 'DELETE',
      token: {
        prefix: session.idToken.substring(0, 20) + '...',
        user: {
          email: session.user?.email,
          sub: session.user?.sub,
          org_id: session.user?.org_id
        }
      }
    });

    const response = await fetch(`https://api.kubiya.ai/api/v1/event/${webhookId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      }
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
        console.error('Delete webhook endpoint - Full error response:', {
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

      return NextResponse.json({
        error: 'Failed to delete webhook',
        status: response.status,
        details: errorData?.error || 'Unable to delete webhook. This might be due to an expired session or misconfigured permissions.',
        supportInfo: {
          message: 'Please contact the Kubiya support team for assistance.',
          email: 'support@kubiya.ai',
          subject: 'Webhook Deletion Issue - Chat UI',
          body: `Hi Kubiya Support,\n\nI'm experiencing issues deleting webhooks in the Chat UI.\n\nError Details:\nStatus: ${response.status}\nMessage: ${errorData?.error || response.statusText}`
        }
      }, { status: response.status });
    }

    return new Response(null, { status: 204 });
  } catch (error) {
    console.error('Error deleting webhook:', error);
    return NextResponse.json(
      { error: 'Failed to delete webhook', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
} 