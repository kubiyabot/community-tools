import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    // Get the session and extract the access token
    const res = NextResponse.next();
    const session = await getSession(req, res);
    
    // Add detailed session logging
    console.log('Chat endpoint - Full session:', {
      hasAccessToken: !!session?.accessToken,
      hasUser: !!session?.user,
      userFields: session?.user ? Object.keys(session.user) : [],
      userEmail: session?.user?.email,
      userSub: session?.user?.sub,
      tokenPrefix: session?.idToken ? session.idToken.substring(0, 50) + '...' : null
    });

    if (!session?.idToken) {
      console.error('Chat endpoint - No ID token found');
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

    const { message, agent_uuid, session_id } = await req.json();

    if (!message || !agent_uuid || !session_id) {
      return new Response(JSON.stringify({
        error: 'Bad Request',
        details: 'Missing required fields: message, agent_uuid, or session_id'
      }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    // Log the token type for debugging
    console.log('Chat endpoint - Using token:', {
      type: 'id_token',
      prefix: session.idToken.substring(0, 20) + '...'
    });

    // Forward the request to Kubiya API with the ID token
    const response = await fetch('https://api.kubiya.ai/api/v1/converse', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'text/event-stream',
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      },
      body: JSON.stringify({
        message,
        agent_uuid,
        session_id
      })
    });

    // Log request details for debugging
    console.log('Chat endpoint - Request details:', {
      url: 'https://api.kubiya.ai/api/v1/converse',
      method: 'POST',
      token: {
        prefix: session.idToken.substring(0, 20) + '...',
        user: {
          email: session?.user?.email,
          sub: session?.user?.sub,
          org_id: session?.user?.org_id
        }
      }
    });

    if (!response.ok) {
      console.error('Chat endpoint - Request failed:', {
        status: response.status,
        statusText: response.statusText
      });

      let errorData;
      try {
        errorData = await response.json();
        console.error('Chat endpoint - Full error response:', {
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
        error: 'Chat Request Failed',
        status: response.status,
        details: 'Unable to process chat request. This might be due to an expired session or misconfigured permissions.',
        supportInfo: {
          message: 'Please contact the Kubiya support team for assistance.',
          email: 'support@kubiya.ai',
          subject: 'Chat Issue - Chat UI',
          body: `Hi Kubiya Support,\n\nI'm experiencing issues with the Chat UI.\n\nError Details:\nStatus: ${response.status}\nMessage: ${errorData?.msg || response.statusText}`
        }
      }), { 
        status: response.status,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    // Stream the response
    const stream = response.body;
    if (!stream) {
      throw new Error('No response body');
    }

    // Transform the stream into proper SSE format
    const transformStream = new TransformStream({
      transform(chunk, controller) {
        const text = new TextDecoder().decode(chunk);
        const lines = text.split('\n');
        
        let systemMessages: string[] = [];
        let lastEvent = null;
        let lastSystemBatch = 0;
        
        for (const line of lines) {
          if (!line.trim()) continue;
          
          try {
            // Log raw SSE line for debugging
            console.log('[SSE Raw]', line);
            
            // Parse the JSON to get the message ID and type
            const event = JSON.parse(line);
            
            // Log parsed event
            console.log('[SSE Event]', {
              type: event.type,
              id: event.id,
              messageLength: event.message?.length,
              message: event.message?.substring(0, 100) + (event.message?.length > 100 ? '...' : ''),
              toolName: event.tool_name,
              hasArgs: !!event.arguments,
              timestamp: new Date().toISOString()
            });
            
            // Collect system messages
            if (event.type === 'system_message') {
              systemMessages.push(event.message);
              console.log('[SSE System]', {
                messageCount: systemMessages.length,
                lastMessage: event.message,
                batchSize: systemMessages.length
              });
              
              // Send batched system messages if we have enough or after a delay
              const now = Date.now();
              if (systemMessages.length >= 3 || (now - lastSystemBatch > 1000 && systemMessages.length > 0)) {
                const batchEvent = {
                  type: 'system_message',
                  messages: systemMessages,
                  id: `system_${now}`
                };
                console.log('[SSE Batch]', {
                  type: 'system_message',
                  messageCount: systemMessages.length,
                  messages: systemMessages,
                  id: batchEvent.id
                });
                controller.enqueue(new TextEncoder().encode(`data: ${JSON.stringify(batchEvent)}\n\n`));
                systemMessages = [];
                lastSystemBatch = now;
              }
              continue;
            }
            
            // If we have collected system messages and we're getting a non-system message,
            // send all system messages as a batch first
            if (systemMessages.length > 0 && (event.type === 'msg' || event.type === 'assistant')) {
              const batchEvent = {
                type: 'system_message',
                messages: systemMessages,
                id: `system_${Date.now()}`
              };
              console.log('[SSE Flush]', {
                type: 'system_message',
                messageCount: systemMessages.length,
                messages: systemMessages,
                id: batchEvent.id
              });
              controller.enqueue(new TextEncoder().encode(`data: ${JSON.stringify(batchEvent)}\n\n`));
              systemMessages = [];
              lastSystemBatch = Date.now();
            }
            
            // For chat messages, only send if the message is different from the last one
            if (event.type === 'msg' || event.type === 'assistant') {
              if (!lastEvent || 
                  lastEvent.id !== event.id || 
                  lastEvent.message !== event.message) {
                const chatEvent = {
                  type: event.type,
                  message: event.message,
                  id: event.id,
                  shouldUpdate: lastEvent?.id === event.id
                };
                console.log('[SSE Chat]', {
                  type: event.type,
                  id: event.id,
                  messageLength: event.message?.length,
                  preview: event.message?.substring(0, 100) + (event.message?.length > 100 ? '...' : ''),
                  isUpdate: lastEvent?.id === event.id
                });
                controller.enqueue(new TextEncoder().encode(`data: ${JSON.stringify(chatEvent)}\n\n`));
                lastEvent = event;
              }
            } else if (event.type === 'tool' || event.type === 'tool_output') {
              console.log('[SSE Tool]', {
                type: event.type,
                id: event.id,
                toolName: event.tool_name,
                hasArgs: !!event.arguments,
                argsPreview: event.arguments ? JSON.stringify(event.arguments).substring(0, 100) + '...' : null,
                messagePreview: event.message?.substring(0, 100) + (event.message?.length > 100 ? '...' : '')
              });
              controller.enqueue(new TextEncoder().encode(`data: ${JSON.stringify(event)}\n\n`));
            }
          } catch (e) {
            console.error('[SSE Error] Failed to parse line:', {
              error: e,
              line: line.substring(0, 100) + (line.length > 100 ? '...' : '')
            });
          }
        }
      }
    });

    return new Response(stream.pipeThrough(transformStream), {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'X-Accel-Buffering': 'no'
      }
    });

  } catch (error) {
    console.error('Chat endpoint error:', {
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined
    });
    return new Response(JSON.stringify({ 
      error: 'Failed to process chat request',
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
