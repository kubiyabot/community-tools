import { useState } from 'react';
import { ChatModelAdapter, ChatModelRunOptions, ChatModelRunResult, ThreadMessage } from '@assistant-ui/react';

interface TextContent {
  type: 'text';
  text: string;
}

interface ToolCall {
  type: 'tool_init' | 'tool_output';
  id: string;
  name?: string;
  arguments?: Record<string, unknown>;
  message?: string;
  timestamp?: string;
}

interface KubiyaEvent {
  message?: string;
  messages?: string[];
  text?: string;
  id: string;
  type: 'msg' | 'system_message' | 'tool';
}

interface StreamEvent {
  type: 'msg' | 'system_message' | 'tool' | 'done';
  text?: string;
  id?: string;
  messages?: string[];
}

interface ModelAdapterConfig {
  temperature?: number;
  maxTokens?: number;
}

interface ModelAdapterProps {
  messages: ThreadMessage[];
  abortSignal: AbortSignal;
  config?: ModelAdapterConfig;
}

const isTextContent = (content: any): content is TextContent => {
  return content?.type === 'text' && typeof content?.text === 'string';
};

const handleEvent = (
  event: MessageEvent,
  setMessages: React.Dispatch<React.SetStateAction<ThreadMessage[]>>
) => {
  try {
    const data = JSON.parse(event.data);
    console.log('[SSE] Parsed event:', {
      type: data.type,
      id: data.id,
      messageLength: data.message?.length,
      hasToolName: !!data.tool_name,
      hasArguments: !!data.arguments,
      isSystem: data.type === 'system_message',
      rawData: data
    });

    if (data.type === 'system_message') {
      const now = new Date();
      let messages: string[] = [];

      if (Array.isArray(data.messages) && data.messages.length > 0) {
        messages = data.messages;
      } else {
        try {
          const messageData = JSON.parse(data.message || '{}');
          messages = messageData.messages || [messageData.message];
        } catch (e) {
          messages = [data.message];
        }
      }
      
      const systemMessages = messages
        .filter((msg: string | null | undefined): msg is string => Boolean(msg))
        .map((message: string): ThreadMessage => ({
          id: `${data.id || `system_${Date.now()}`}_${Math.random().toString(36).slice(2)}`,
          role: 'system' as const,
          content: [{
            type: 'text' as const,
            text: message.trim()
          }] as const,
          metadata: {
            custom: {
              isSystemMessage: true,
              type: 'system_message',
              originalId: data.id,
              isComplete: true
            }
          },
          createdAt: now
        }))
        .filter(msg => {
          const content = msg.content[0];
          return isTextContent(content) && content.text.trim().length > 0;
        });

      console.log('[SSE] Created system messages:', systemMessages);

      setMessages((prev: ThreadMessage[]) => {
        const newMessages = systemMessages.filter((systemMessage: ThreadMessage) => {
          return !prev.some(msg => {
            const msgContent = msg.content[0];
            const systemContent = systemMessage.content[0];
            return msg.id === systemMessage.id || 
              (msg.metadata?.custom?.originalId === systemMessage.metadata?.custom?.originalId &&
               isTextContent(msgContent) && isTextContent(systemContent) &&
               msgContent.text === systemContent.text);
          });
        });

        if (newMessages.length === 0) {
          return prev;
        }

        console.log('[SSE] Adding system messages:', newMessages);
        return [...prev, ...newMessages];
      });
      return;
    }

    // ... rest of the event handling ...
  } catch (error) {
    console.error('[SSE] Error processing event:', error);
  }
};

const backendApi = async ({ messages, abortSignal, config }: ChatModelRunOptions) => {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message: messages[messages.length - 1].content
    }),
    signal: abortSignal
  });

  if (!response.ok) {
    throw new Error('Failed to fetch response');
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('No reader available');

  return {
    async *[Symbol.asyncIterator]() {
      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            const trimmedLine = line.trim();
            if (!trimmedLine || !trimmedLine.startsWith('data: ')) continue;
            
            const data = trimmedLine.slice(6);
            if (data === '[DONE]') {
              yield { type: 'done' } as StreamEvent;
              return;
            }
            
            try {
              const event = JSON.parse(data) as KubiyaEvent;
              console.log('[SSE] Parsed event:', {
                type: event.type,
                id: event.id,
                messageLength: event.message?.length,
                hasToolName: 'name' in event,
                hasArguments: 'arguments' in event,
                rawContent: data
              });
              
              if (event.type === 'system_message') {
                try {
                  let messages: string[] = [];
                  if (Array.isArray(event.messages) && (event.messages.length ?? 0) > 0) {
                    messages = event.messages;
                  } else if (event.text) {
                    try {
                      const messageData = JSON.parse(event.text || '{}');
                      messages = messageData.messages || [messageData.message];
                    } catch (e) {
                      messages = [event.text];
                    }
                  }
                  
                  for (const message of messages) {
                    yield {
                      type: 'system_message',
                      text: message,
                      id: event.id,
                      metadata: { 
                        custom: { 
                          isSystemMessage: true,
                          originalId: event.id 
                        } 
                      }
                    } as StreamEvent;
                  }
                } catch (e) {
                  console.error('[SSE] Failed to parse system message:', e);
                  yield {
                    type: 'system_message',
                    text: event.message ?? '',
                    id: event.id,
                    metadata: { 
                      custom: { 
                        isSystemMessage: true,
                        originalId: event.id 
                      } 
                    }
                  } as StreamEvent;
                }
              } else if (event.type === 'msg') {
                yield {
                  type: 'msg',
                  text: event.message ?? '',
                  id: event.id
                } as StreamEvent;
              } else if (event.type === 'tool') {
                yield {
                  type: 'tool',
                  text: event.message ?? '',
                  id: event.id
                } as StreamEvent;
              }
            } catch (e) {
              console.error('Error parsing JSON:', e);
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    }
  };
};

const yieldSystemMessage = (text: string): ChatModelRunResult => {
  console.log('[SSE] Yielding system message:', { text });
  return {
    content: [{ type: "text", text } as TextContent],
    metadata: {
      custom: {
        isSystemMessage: true,
        type: 'system_message',
        isComplete: true
      }
    }
  };
};

const MyModelAdapter: ChatModelAdapter = {
  async *run(options: ChatModelRunOptions): AsyncGenerator<ChatModelRunResult, void, unknown> {
    const stream = await backendApi(options);
 
    let text = "";
    for await (const event of stream) {
      console.log('[SSE] Processing event in run:', event);
      
      if (event.type === 'done') {
        if (text) {
          yield {
            content: [{ type: "text", text }],
            metadata: {
              custom: {
                isComplete: true
              }
            }
          };
        }
        return;
      }

      if (event.type === 'msg') {
        text = event.text ?? '';
        yield {
          content: [{ type: "text", text }],
          metadata: {
            custom: {
              isComplete: false
            }
          }
        };
      } else if (event.type === 'system_message') {
        try {
          let messages: string[] = [];
          if (Array.isArray(event.messages) && (event.messages.length ?? 0) > 0) {
            messages = event.messages;
          } else if (event.text) {
            try {
              const messageData = JSON.parse(event.text || '{}');
              messages = messageData.messages || [messageData.message];
            } catch (e) {
              messages = [event.text];
            }
          }
          
          for (const msg of messages) {
            if (!msg?.trim()) {
              console.log('[SSE] Skipping empty system message');
              continue;
            }
            const result = yieldSystemMessage(msg.trim());
            console.log('[SSE] Yielding system message result:', result);
            yield result;
          }
        } catch (e) {
          console.error('[MyModelAdapter] Failed to parse system message:', e);
        }
      } else if (event.type === 'tool') {
        text += event.text ?? '';
        yield {
          content: [{ type: "text", text }],
          metadata: {
            custom: {
              isComplete: false
            }
          }
        };
      }
    }
  },
}; 