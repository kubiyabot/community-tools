"use client";

import { Thread, useAssistantToolUI } from "@assistant-ui/react";
import { useUser } from '@auth0/nextjs-auth0/client';
import { LoginButton } from './LoginButton';
import { AssistantMessage } from './assistant-ui/AssistantMessage';
import { UserMessage } from './assistant-ui/UserMessage';
import { ToolExecution } from './assistant-ui/ToolExecution';

export default function MyAssistant() {
  const { user } = useUser();

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
      <div className="flex h-screen items-center justify-center bg-[#0f172a]">
        <LoginButton />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0f172a]">
      <div className="container mx-auto px-4 py-4">
        <Thread
          components={{
            AssistantMessage,
            UserMessage
          }}
        />
      </div>
    </div>
  );
}
