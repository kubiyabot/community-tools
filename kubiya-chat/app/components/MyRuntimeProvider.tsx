"use client";

import { ChatModelAdapter } from '@assistant-ui/react';

interface KubiyaEvent {
  message: string;
  id: string;
  type: 'msg' | 'system_message' | 'tool';
}

interface StreamEvent {
  type: 'msg' | 'system_message' | 'tool' | 'done';
  text?: string;
  id?: string;
}

const backendApi = async ({ messages, abortSignal }: any) => {
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
              console.log('Processing event:', event);
              
              if (event.type === 'msg' || event.type === 'system_message') {
                yield {
                  type: event.type,
                  text: event.message,
                  id: event.id
                } as StreamEvent;
              } else if (event.type === 'tool') {
                yield {
                  type: 'tool',
                  text: event.message,
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

const MyModelAdapter: ChatModelAdapter = {
  async *run({ messages, abortSignal, config }) {
    const stream = await backendApi({ messages, abortSignal, config });
 
    let text = "";
    for await (const event of stream) {
      if (event.type === 'done') {
        yield {
          content: [{ type: "text", text }],
          isComplete: true
        };
        return;
      }

      if (event.type === 'msg' || event.type === 'system_message') {
        text = event.text || '';
      } else if (event.type === 'tool') {
        text += event.text || '';
      }
 
      yield {
        content: [{ type: "text", text }],
        isComplete: false
      };
    }
  },
};

export default function MyRuntimeProvider({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col h-full">
      {children}
    </div>
  );
} 