import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

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

    const body = await req.json();

    // Call Kubiya API to create webhook
    const response = await fetch('https://api.kubiya.ai/api/v1/event', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      },
      body: JSON.stringify({
        name: `${body.provider}_${body.eventType}`,
        source: body.provider,
        agent_id: body.agentId,
        prompt: body.promptTemplate,
        communication: {
          method: body.platform === 'slack' ? 'Slack' : 'Teams',
          destination: body.channel
        },
        created_by: session.user?.email || '',
        filter: body.filter || ''
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: response.statusText }));
      console.error('Error from Kubiya API:', errorData);
      return NextResponse.json({ 
        error: 'Failed to create webhook',
        details: errorData.message || `API responded with status: ${response.status}`
      }, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json({
      id: data.id,
      webhookUrl: data.webhook_url,
      name: data.name,
      source: data.source,
      communication: data.communication,
      created_at: data.created_at,
      created_by: data.created_by,
      org: data.org,
      teammate: data.agent_id ? {
        uuid: data.agent_id,
        name: data.agent_name || 'Unknown Agent'
      } : undefined
    });
  } catch (error) {
    console.error('Error creating webhook:', error);
    return NextResponse.json({ 
      error: 'Internal Server Error',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
} 