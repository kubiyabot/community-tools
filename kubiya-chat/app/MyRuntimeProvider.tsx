"use client";

import React, { useState, useEffect, type ReactNode, useMemo } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
  type ModelConfig,
  type LocalRuntimeOptions,
  type ChatModelRunOptions,
} from "@assistant-ui/react";
import { ToolUI } from "./components/ToolUI";
import { useConfig, type AuthType } from "@/lib/config-context";
import { ApiKeySetup } from "@/components/ApiKeySetup";

interface TeammateConfig extends ModelConfig {
  teammate: string;
}

interface Teammate {
  id: string;
  name: string;
  description: string;
  uuid: string;
}

interface CustomRuntimeOptions extends LocalRuntimeOptions {
  config: TeammateConfig;
  sessions: Session[];
  setSessions: React.Dispatch<React.SetStateAction<Session[]>>;
}

interface Session {
  id: string;
  title?: string;
}

interface ConversationPayload {
  message: string;
  agent_uuid: string;
  session_id?: string;
}

interface ChatModelRunOptionsWithSessions extends ChatModelRunOptions {
  setSessions?: React.Dispatch<React.SetStateAction<Session[]>>;
  sessions?: Session[];
}

interface StreamEvent {
  type: string;
  message?: string;
  content?: string;
  id?: string;
  session_id?: string;
  name?: string;
}

const createKubiyaModelAdapter = (
  selectedTeammate: string | undefined, 
  authOptions: { authType: AuthType },
  token?: string
): ChatModelAdapter => ({
  async *run(options: ChatModelRunOptionsWithSessions) {
    const MAX_RETRIES = 3;
    let retryCount = 0;
    
    if (!selectedTeammate) {
      console.error('No teammate selected');
      yield {
        content: [{
          type: "text",
          text: "Error: No teammate selected. Please select a teammate and try again.",
        }],
      };
      return;
    }

    if (!token) {
      console.error('No auth token available');
      yield {
        content: [{
          type: "text",
          text: "Error: No authentication token available. Please sign in again.",
        }],
      };
      return;
    }

    // Get the last message
    const currentMessage = options.messages[options.messages.length - 1];
    const messageContent = typeof currentMessage?.content === 'string' 
      ? currentMessage.content 
      : Array.isArray(currentMessage?.content) 
        ? currentMessage.content.find((part) => 
            'type' in part && part.type === 'text' && 'text' in part
          )?.text || ''
        : '';

    if (!messageContent) {
      console.error('No message content found');
      return;
    }

    while (retryCount < MAX_RETRIES) {
      let aborted = false;
      const controller = new AbortController();
      const { signal } = controller;

      try {
        // Get or generate session ID
        let sessionId = localStorage.getItem(`chat_session_${selectedTeammate}`);
        if (!sessionId) {
          // Generate new session ID using nanoseconds (matching Go's implementation)
          const timestamp = BigInt(Date.now()) * BigInt(1000000); // Convert to nanoseconds
          sessionId = timestamp.toString();
          localStorage.setItem(`chat_session_${selectedTeammate}`, sessionId);
          
          // Add to sessions list
          const newSession = { id: sessionId, title: 'New Thread' };
          options.setSessions?.([newSession, ...options.sessions || []].slice(0, 5));
          localStorage.setItem(`sessions_${selectedTeammate}`, JSON.stringify([newSession, ...options.sessions || []].slice(0, 5)));
        }

        const payload: ConversationPayload = {
          message: messageContent,
          agent_uuid: selectedTeammate,
          session_id: sessionId
        };

        const response = await fetch('/api/converse', {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Authorization": authOptions.authType === 'sso' ? `Bearer ${token}` : `userkey ${token}`
          },
          body: JSON.stringify(payload),
          signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        if (!response.body) {
          throw new Error("No response body");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let lastActivityTime = Date.now();
        const TIMEOUT_MS = 30000; // 30 seconds timeout

        let currentEvent: StreamEvent | undefined;

        try {
          while (!aborted) {
            if (Date.now() - lastActivityTime > TIMEOUT_MS) {
              console.log('Stream timeout - no activity for 30 seconds');
              break;
            }

            const { done, value } = await reader.read();
            
            if (done) {
              console.log('SSE stream complete');
              break;
            }

            lastActivityTime = Date.now();
            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (!line.trim()) continue;

              try {
                currentEvent = JSON.parse(line) as StreamEvent;

                if (currentEvent.type === 'session_init' && currentEvent.session_id) {
                  localStorage.setItem(`chat_session_${selectedTeammate}`, currentEvent.session_id);
                  continue;
                }

                if (currentEvent.type === 'assistant' || currentEvent.type === 'msg') {
                  const messageText = currentEvent.message || currentEvent.content || '';
                  const isComplete = messageText.endsWith('?');
                  
                  yield {
                    content: [{
                      type: "text",
                      text: messageText,
                    }],
                  };

                  if (isComplete) break;
                } else if (currentEvent.type === 'tool') {
                  const toolContent = currentEvent.content || currentEvent.message || '';
                  if (!toolContent) {
                    console.error('No tool content found');
                    continue;
                  }

                  const toolLines = toolContent.split('\n');
                  const toolName = toolLines[0].replace('Tool: ', '');
                  const argsStr = toolLines[1].replace('Arguments: ', '');
                  const args = JSON.parse(argsStr);

                  yield {
                    content: [],
                    tool_calls: [{
                      type: 'tool_init',
                      id: currentEvent.id,
                      message: `${toolName} ${Object.entries(args)
                        .map(([key, value]) => `${key}=${value}`)
                        .join(' ')}`,
                      timestamp: new Date().toISOString()
                    }]
                  };
                } else if (currentEvent.type === 'tool_output') {
                  const toolContent = currentEvent.content || currentEvent.message || '';
                  
                  if (toolContent) {
                    yield {
                      content: [],
                      tool_calls: [{
                        type: 'tool_output',
                        id: currentEvent.id,
                        name: currentEvent.name || 'unknown',
                        message: toolContent,
                        timestamp: new Date().toISOString()
                      }]
                    };
                  }
                } else if (currentEvent.type === 'system_message') {
                  if (currentEvent.message?.startsWith('ERROR:')) {
                    throw new Error(currentEvent.message);
                  } else {
                    yield {
                      content: [{
                        type: "text",
                        text: currentEvent.message || '',
                      }],
                    };
                  }
                }
              } catch (e) {
                console.error("Failed to parse or process event:", e);
                if (e instanceof Error && e.message.startsWith('ERROR:')) {
                  throw e;
                }
              }
            }
          }
        } finally {
          aborted = true;
          reader.releaseLock();
          controller.abort();
        }

      } catch (error) {
        console.error("Chat error:", error);
        retryCount++;
        
        if (retryCount === MAX_RETRIES) {
          yield {
            content: [{
              type: "text",
              text: `Error: ${error instanceof Error ? error.message : 'An unknown error occurred'}. Please try again later.`,
            }],
          };
        } else {
          console.log(`Retrying... Attempt ${retryCount + 1} of ${MAX_RETRIES}`);
          await new Promise(resolve => setTimeout(resolve, Math.min(1000 * Math.pow(2, retryCount) + Math.random() * 1000, 10000)));
        }
      }
    }
  }
});

function useKubiyaRuntime(
  selectedTeammate: string | undefined,
  sessions: Session[],
  setSessions: React.Dispatch<React.SetStateAction<Session[]>>,
  authType: AuthType | null,
  token: string | null
) {
  const runtimeConfig = useMemo<TeammateConfig>(() => ({
    teammate: selectedTeammate || '',
  }), [selectedTeammate]);

  const runtimeOptions = useMemo<CustomRuntimeOptions>(() => ({
    config: runtimeConfig,
    sessions,
    setSessions,
  }), [runtimeConfig, sessions, setSessions]);

  const modelAdapter = useMemo(
    () => createKubiyaModelAdapter(
      selectedTeammate, 
      { authType: authType || 'apikey' },
      token || undefined
    ),
    [selectedTeammate, authType, token]
  );

  return useLocalRuntime(modelAdapter, runtimeOptions);
}

export default function MyRuntimeProvider({ children }: { children: ReactNode }) {
  const [selectedTeammate, setSelectedTeammate] = useState<string>();
  const [teammates, setTeammates] = useState<Teammate[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { apiKey, authType, clearApiKey } = useConfig();

  // Use layout effect to handle initial loading state
  React.useLayoutEffect(() => {
    if (!apiKey || !authType) {
      setIsLoading(false);
    }
  }, [apiKey, authType]);

  // Fetch teammates
  useEffect(() => {
    if (!apiKey || !authType || !isLoading) return;

    async function fetchTeammates() {
      try {
        const authHeader = authType === 'sso' ? `Bearer ${apiKey}` : `userkey ${apiKey}`;
        console.log('Using auth type:', authType);

        const response = await fetch('https://api.kubiya.ai/api/v1/agents', {
          headers: {
            'Authorization': authHeader,
            'Accept': 'application/json',
          }
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch teammates: ${response.status}`);
        }

        const data = await response.json();
        console.log('Fetched teammates:', data);
        setTeammates(data);
        
        if (data.length > 0) {
          setSelectedTeammate(data[0].uuid);
        }
      } catch (error) {
        console.error('Error fetching teammates:', error);
        if (error instanceof Error && error.message.includes('401')) {
          clearApiKey();
        }
      } finally {
        setIsLoading(false);
      }
    }

    fetchTeammates();
  }, [apiKey, authType, clearApiKey, isLoading]);

  const runtime = useKubiyaRuntime(selectedTeammate, sessions, setSessions, authType, apiKey);

  // Debug logging
  useEffect(() => {
    console.log('Current state:', {
      hasApiKey: !!apiKey,
      authType,
      teammatesCount: teammates.length,
      selectedTeammate,
      isLoading,
      hasRuntime: !!runtime
    });
  }, [apiKey, authType, teammates.length, selectedTeammate, isLoading, runtime]);

  if (!apiKey || !authType) {
    return <ApiKeySetup />;
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-[#0F172A]">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[#7C3AED] border-t-transparent mb-4"></div>
        <p className="text-white text-sm">Loading teammates...</p>
      </div>
    );
  }

  if (teammates.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-[#0F172A]">
        <p className="text-white text-sm">No teammates available. Please check your account.</p>
      </div>
    );
  }

  if (!selectedTeammate) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-[#0F172A]">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[#7C3AED] border-t-transparent mb-4"></div>
        <p className="text-white text-sm">Initializing teammate...</p>
      </div>
    );
  }

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ToolUI>{children}</ToolUI>
    </AssistantRuntimeProvider>
  );
} 