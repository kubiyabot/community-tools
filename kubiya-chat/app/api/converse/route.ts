import { NextRequest } from 'next/server';
import { getKubiyaConfig } from '../../config';

export const dynamic = 'force-dynamic';
export const runtime = 'edge';

interface ToolExecution {
  startTime: Date;
  name: string;
  output: string;
  messageId: string;
  isFinal: boolean;
  hasInitMessage: boolean;
  hasOutputMessage: boolean;
  isComplete: boolean;
}

const toolExecutions = new Map<string, ToolExecution>();

export async function POST(req: NextRequest) {
  try {
    const kubiyaConfig = getKubiyaConfig();
    const payload = await req.json();
    const isFirstMessage = !payload.session_id;
    const sessionId = payload.session_id || crypto.randomUUID();

    // For first message, don't send session_id to API but include it in response
    const enhancedPayload = {
      ...payload,
      session_id: isFirstMessage ? undefined : sessionId
    };

    console.log('Converse request details:', {
      url: 'https://api.kubiya.ai/api/v1/converse',
      payload: enhancedPayload,
      hasApiKey: !!kubiyaConfig.apiKey,
      apiKeyLength: kubiyaConfig.apiKey?.length,
      isFirstMessage,
      hasSessionId: !!payload.session_id,
      sessionId,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': kubiyaConfig.apiKey ? 'UserKey present' : 'No UserKey'
      }
    });

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    try {
      const response = await fetch('https://api.kubiya.ai/api/v1/converse', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `UserKey ${kubiyaConfig.apiKey}`,
        },
        body: JSON.stringify(enhancedPayload),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      console.log('Kubiya API response:', {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries())
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Kubiya API error response:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }

      const responseBody = response.body;
      if (!responseBody) {
        throw new Error('No response body from Kubiya API');
      }

      // Create a TransformStream to handle the response
      const stream = new TransformStream();
      const writer = stream.writable.getWriter();
      const encoder = new TextEncoder();
      const decoder = new TextDecoder();

      // Start piping the response
      (async () => {
        try {
          const reader = responseBody.getReader();
          let buffer = '';
          let messageCount = 0;
          let lastActivity = Date.now();
          const activityTimeout = 60000;

          const checkActivity = setInterval(() => {
            if (Date.now() - lastActivity > activityTimeout) {
              console.log('Activity timeout reached, closing connection');
              clearInterval(checkActivity);
              reader.cancel();
              writer.close().catch(console.error);
            }
          }, 10000);

          console.log('Starting to read response stream...');

          // If this is the first message, send session ID immediately
          if (isFirstMessage) {
            const initMessage = JSON.stringify({
              type: 'session_init',
              session_id: sessionId,
              timestamp: new Date().toISOString()
            }) + '\n';
            await writer.write(encoder.encode(initMessage));
            messageCount++;
          }

          try {
            while (true) {
              const { done, value } = await reader.read();
              
              if (done) {
                console.log('Response stream complete, messages processed:', messageCount);
                if (buffer.trim()) {
                  console.log('Processing final buffer content:', buffer);
                  const chunk = JSON.stringify({
                    message: buffer.trim(),
                    type: 'assistant',
                    session_id: sessionId
                  }) + '\n';
                  await writer.write(encoder.encode(chunk));
                  messageCount++;
                }
                clearInterval(checkActivity);
                await writer.close();
                break;
              }

              lastActivity = Date.now();
              const text = decoder.decode(value, { stream: true });
              console.log('Received chunk:', { length: text.length, content: text });
              buffer += text;

              const lines = buffer.split('\n');
              buffer = lines.pop() || '';

              for (const line of lines) {
                if (!line.trim()) continue;

                try {
                  console.log('Processing line:', line);
                  const parsed = JSON.parse(line);
                  parsed.session_id = sessionId;
                  
                  if (parsed.type === 'tool' || parsed.type === 'tool_output') {
                    let toolExec = toolExecutions.get(parsed.messageId);
                    if (!toolExec) {
                      toolExec = {
                        startTime: new Date(),
                        name: '',
                        messageId: parsed.messageId,
                        output: '',
                        isFinal: false,
                        hasInitMessage: false,
                        hasOutputMessage: false,
                        isComplete: false
                      };
                      toolExecutions.set(parsed.messageId, toolExec);
                    }

                    if (parsed.type === 'tool' && parsed.content) {
                      toolExec.name = parsed.content;
                    }

                    if (!toolExec.hasInitMessage) {
                      toolExec.hasInitMessage = true;
                      const initMsg = {
                        content: toolExec.name,
                        type: 'tool_init',
                        final: false,
                        messageId: parsed.messageId,
                        timestamp: new Date().toISOString()
                      };
                      await writer.write(encoder.encode(JSON.stringify(initMsg) + '\n'));
                      messageCount++;
                    }

                    if (parsed.content && parsed.type === 'tool_output') {
                      toolExec.output += parsed.content + '\n';
                      const outputMsg = {
                        content: toolExec.output,
                        type: 'tool_output',
                        messageId: parsed.messageId,
                        final: false,
                        timestamp: new Date().toISOString()
                      };
                      await writer.write(encoder.encode(JSON.stringify(outputMsg) + '\n'));
                      messageCount++;
                      toolExec.hasOutputMessage = true;
                    }

                    if (parsed.final && !toolExec.isComplete) {
                      toolExec.isFinal = true;
                      toolExec.isComplete = true;

                      if (toolExec.hasOutputMessage) {
                        const finalOutputMsg = {
                          content: toolExec.output,
                          type: 'tool_output',
                          messageId: parsed.messageId,
                          final: true,
                          timestamp: new Date().toISOString()
                        };
                        await writer.write(encoder.encode(JSON.stringify(finalOutputMsg) + '\n'));
                        messageCount++;
                      }

                      if (toolExec.name) {
                        const completionMsg = {
                          content: `🔧 Executed \`${toolExec.name}\``,
                          type: 'tool_execution_complete',
                          final: true,
                          timestamp: new Date().toISOString()
                        };
                        await writer.write(encoder.encode(JSON.stringify(completionMsg) + '\n'));
                        messageCount++;
                      }

                      toolExecutions.delete(parsed.messageId);
                    }
                  } else {
                    console.log('Forwarding parsed message:', parsed);
                    await writer.write(encoder.encode(JSON.stringify(parsed) + '\n'));
                    messageCount++;
                  }
                } catch (e) {
                  console.log('Error parsing line:', e);
                  console.log('Forwarding as raw message:', line);
                  const chunk = JSON.stringify({
                    message: line,
                    type: 'assistant',
                    session_id: sessionId
                  }) + '\n';
                  await writer.write(encoder.encode(chunk));
                  messageCount++;
                }
              }
            }
          } finally {
            clearInterval(checkActivity);
          }
        } catch (error) {
          console.error('Stream processing error:', error);
          const errorMessage = JSON.stringify({
            message: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
            type: 'system_message',
            session_id: sessionId
          }) + '\n';
          await writer.write(encoder.encode(errorMessage));
          await writer.close();
        }
      })();

      console.log('Returning SSE response stream');
      return new Response(stream.readable, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
      });
    } catch (fetchError) {
      clearTimeout(timeoutId);
      throw fetchError;
    }
  } catch (error) {
    console.error('API error:', error);
    return new Response(
      JSON.stringify({
        message: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        type: 'system_message'
      }),
      {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
  }
} 