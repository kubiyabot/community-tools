import { type ChatModelAdapter, type ChatModelRunOptions } from '@assistant-ui/react';
import { type AuthType } from './config-context';

interface AuthenticatedRuntimeOptions {
  authType: AuthType;
}

export function createAuthenticatedRuntime(token?: string, options?: AuthenticatedRuntimeOptions): ChatModelAdapter {
  return {
    async *run({ messages, abortSignal }: ChatModelRunOptions) {
      const lastMessage = messages[messages.length - 1];
      const messageContent = typeof lastMessage?.content === 'string' 
        ? lastMessage.content 
        : Array.isArray(lastMessage?.content) 
          ? lastMessage.content.find((part) => 
              'type' in part && part.type === 'text' && 'text' in part
            )?.text || ''
          : '';

      const authHeader = token && options?.authType 
        ? (options.authType === 'sso' ? `Bearer ${token}` : `userkey ${token}`) 
        : '';

      const response = await fetch('/api/converse', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(authHeader && { Authorization: authHeader })
        },
        body: JSON.stringify({ message: messageContent }),
        signal: abortSignal
      });

      if (!response.ok) {
        throw new Error('Failed to submit message');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const text = new TextDecoder().decode(value);
          const lines = text.split('\n').filter(Boolean);
          
          for (const line of lines) {
            try {
              const event = JSON.parse(line);
              
              if (event.type === 'tool') {
                const toolId = crypto.randomUUID();
                yield {
                  content: [],
                  tool_calls: [{
                    type: 'tool_init',
                    id: toolId,
                    message: event.content || event.message,
                    timestamp: new Date().toISOString()
                  }]
                };
              } else if (event.type === 'tool_output') {
                yield {
                  content: [],
                  tool_calls: [{
                    type: 'tool_output',
                    id: event.id,
                    message: event.content || event.message,
                    timestamp: new Date().toISOString()
                  }]
                };
              } else {
                yield {
                  content: [{
                    type: "text",
                    text: event.content || event.message || '',
                  }],
                };
              }
            } catch (error) {
              console.error('Failed to parse line:', error);
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    }
  };
} 