"use client";

import { Thread, useAssistantToolUI, ThreadMessage, AssistantRuntimeProvider, useLocalRuntime, type ChatModelAdapter, type ModelConfig, type ChatModelRunOptions, type ThreadMessage as ThreadMessageType, type TextContentPart, type ChatModelRunResult, type ThreadAssistantContentPart, type LocalRuntimeOptions } from "@assistant-ui/react";
import { useUser } from '@auth0/nextjs-auth0/client';
import { LoginButton } from './LoginButton';
import { AssistantMessage as BaseAssistantMessage } from './assistant-ui/AssistantMessage';
import { UserMessage as BaseUserMessage } from './assistant-ui/UserMessage';
import { ToolExecution } from './assistant-ui/ToolExecution';
import { useState, useEffect } from 'react';

// Wrap message components to match Thread's expected interface
const AssistantMessage = (props: any) => (
  <BaseAssistantMessage message={props.message as ThreadMessage & { role: 'assistant' | 'system' }} />
);

const UserMessage = (props: any) => (
  <BaseUserMessage message={props.message as ThreadMessage & { role: 'user' }} />
);

const createModelAdapter = (token: string): ChatModelAdapter => {
  if (!token) {
    throw new Error('Access token is required');
  }

  return {
    async *run({ messages }) {
      const lastMessage = messages[messages.length - 1];
      const textContent = lastMessage.content.find((c): c is TextContentPart => c.type === 'text');
      const messageText = textContent?.text || '';

      const response = await fetch('/api/converse', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive'
        },
        body: JSON.stringify({ 
          message: messageText,
          session_id: Date.now().toString()
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.statusText}`);
      }

      try {
        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('No response body');
        }

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (!line.trim()) continue;
            try {
              const event = JSON.parse(line);
              yield {
                content: [{ type: 'text', text: event.message || event.content || '' }]
              };
            } catch (e) {
              console.error('Failed to parse event:', e);
            }
          }
        }
      } catch (error) {
        console.error('Stream error:', error);
        yield {
          content: [{ type: 'text', text: 'Error: Failed to process response stream' }]
        };
      }
    }
  };
};

export default function MyAssistant() {
  const { user, isLoading } = useUser();

  // Register tool UIs
  useAssistantToolUI({
    toolName: "tool",
    render: ToolExecution
  });

  useAssistantToolUI({
    toolName: "tool_output",
    render: ToolExecution
  });

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0f172a]">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0f172a]">
        <LoginButton />
      </div>
    );
  }

  if (!user.accessToken) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0f172a]">
        <div className="text-white">No access token available</div>
      </div>
    );
  }

  const modelAdapter = createModelAdapter(user.sub || '');
  const runtime = useLocalRuntime(modelAdapter);

  return (
    <div className="min-h-screen bg-[#0f172a]">
      <div className="container mx-auto px-4 py-4">
        <AssistantRuntimeProvider runtime={runtime}>
          <Thread
            components={{
              AssistantMessage,
              UserMessage
            }}
          />
        </AssistantRuntimeProvider>
      </div>
    </div>
  );
}
