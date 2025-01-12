"use client";

import { Thread, MessagePrimitive, useLocalRuntime, type ChatModelAdapter, useAssistantToolUI, type ToolCallContentPartComponent } from "@assistant-ui/react";
import { Loader2, Terminal, CheckCircle2 } from 'lucide-react';
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useUser } from '@auth0/nextjs-auth0/client';
import { LoginButton } from '@/components/LoginButton';
import { MarkdownText } from "@/components/assistant-ui/markdown-text";

export const ToolExecution: ToolCallContentPartComponent<Record<string | number, unknown>, unknown> = ({ 
  argsText, 
  status
}) => {
  return (
    <div className="flex flex-col gap-2 bg-[#1E293B]/20 rounded-md p-3">
      <div className="flex items-center gap-2">
        {status.type === 'running' ? (
          <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
        ) : status.type === 'complete' ? (
          <CheckCircle2 className="h-4 w-4 text-green-500" />
        ) : (
          <Terminal className="h-4 w-4 text-red-500" />
        )}
        <Terminal className="h-4 w-4" />
        <span className="font-mono text-sm">Tool Execution</span>
      </div>
      {argsText && (
        <div className="text-sm text-gray-400 font-mono mt-1">
          Arguments: {argsText}
        </div>
      )}
      {status.type === 'complete' && (
        <div className="text-sm text-gray-400 font-mono mt-1">
          Output: Complete
        </div>
      )}
    </div>
  );
};

const AssistantMessage = () => (
  <div className="flex gap-3 p-4">
    <Avatar>
      <AvatarFallback>AI</AvatarFallback>
    </Avatar>
    <MessagePrimitive.Content components={{ Text: MarkdownText }} />
  </div>
);

const UserMessage = () => (
  <div className="flex gap-3 p-4 bg-muted">
    <Avatar>
      <AvatarFallback>U</AvatarFallback>
    </Avatar>
    <MessagePrimitive.Content components={{ Text: MarkdownText }} />
  </div>
);

const modelAdapter: ChatModelAdapter = {
  async *run({ messages, abortSignal }) {
    const lastMessage = messages[messages.length - 1];
    const messageContent = typeof lastMessage?.content === 'string' 
      ? lastMessage.content 
      : Array.isArray(lastMessage?.content) 
        ? lastMessage.content.find((part) => 
            'type' in part && part.type === 'text' && 'text' in part
          )?.text || ''
        : '';

    const response = await fetch('/api/converse', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
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
              yield {
                content: [],
                tool_calls: [{
                  type: 'tool',
                  id: crypto.randomUUID(),
                  message: event.content || event.message,
                  timestamp: new Date().toISOString()
                }]
              };
            } else if (event.type === 'tool_output') {
              yield {
                content: [],
                tool_calls: [{
                  type: 'tool_output',
                  id: crypto.randomUUID(),
                  name: event.name || 'unknown',
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
          } catch {
            console.error('Failed to parse line:', line);
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }
};

export default function MyAssistant() {
  const { user } = useUser();
  const runtime = useLocalRuntime(modelAdapter);

  // Register tool UIs
  useAssistantToolUI({
    toolName: "tool",
    render: ToolExecution
  });

  useAssistantToolUI({
    toolName: "tool_output",
    render: ToolExecution
  });

  if (!user) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoginButton />
      </div>
    );
  }

  return (
    <Thread
      runtime={runtime}
      components={{
        AssistantMessage,
        UserMessage
      }}
    />
  );
}
