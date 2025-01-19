import { withMiddlewareAuthRequired } from '@auth0/nextjs-auth0/edge';
import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'edge';
export const maxDuration = 300;

interface Message {
  role: 'user' | 'assistant';
  content: string | { type: string; text: string; }[];
}

export const POST = withMiddlewareAuthRequired(async function POST(req: NextRequest) {
  try {
    const authHeader = req.headers.get('authorization');
    if (!authHeader) {
      return new Response('Unauthorized - No token provided', { status: 401 });
    }

    const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7) : authHeader;
    if (!token) {
      return new Response('Unauthorized - Invalid token format', { status: 401 });
    }

    const body = await req.json();
    const { message, agent_uuid, session_id } = body;

    if (!message || !agent_uuid || !session_id) {
      return new Response('Bad Request - Missing required fields', { status: 400 });
    }

    const response = await fetch('https://api.kubiya.ai/api/v1/converse', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'Authorization': `Bearer ${token}`,
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
      },
      body: JSON.stringify({
        message,
        agent_uuid,
        session_id
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      return new Response(errorText, { status: response.status });
    }

    // Return the streaming response directly
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache, no-transform',
        'Connection': 'keep-alive',
      },
    });

  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' }, 
      { status: 500 }
    );
  }
}); 