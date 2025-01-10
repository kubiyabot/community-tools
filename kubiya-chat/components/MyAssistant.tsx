"use client";

import { Thread, useAssistantRuntime } from "@assistant-ui/react";
import { makeMarkdownText } from "@assistant-ui/react-markdown";

const MarkdownText = makeMarkdownText();

export function MyAssistant() {
  const runtime = useAssistantRuntime();
  
  if (!runtime) {
    return <div className="p-4">Loading...</div>;
  }

  return (
    <div className="h-full">
      <Thread
        runtime={runtime}
        assistantMessage={{ components: { Text: MarkdownText } }}
      />
    </div>
  );
}
