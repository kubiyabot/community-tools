"use client";

import React, { useState, useEffect, type ReactNode } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
  type ModelConfig,
  type LocalRuntimeOptions,
  type ChatModelRunOptions,
} from "@assistant-ui/react";
import { useConfig } from "@/lib/config-context";
import { ApiKeySetup } from "@/app/components/ApiKeySetup";
import { useUser } from '@auth0/nextjs-auth0/client';

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

const createKubiyaModelAdapter = (
  selectedTeammate: string | undefined, 
  authOptions: { authType: 'sso' | 'apikey' },
  token?: string
): ChatModelAdapter => {
  return {
    async *run(options: ChatModelRunOptions) {
      if (!selectedTeammate) {
        yield {
          content: [{
            type: "text",
            text: "Error: No teammate selected. Please select a teammate and try again.",
          }],
        };
        return;
      }

      if (!token) {
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
        yield {
          content: [{
            type: "text",
            text: "Error: No message content found.",
          }],
        };
        return;
      }

      try {
        const response = await fetch('/api/converse', {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Authorization": authOptions.authType === 'sso' ? `Bearer ${token}` : `userkey ${token}`
          },
          body: JSON.stringify({
            message: messageContent,
            agent_uuid: selectedTeammate
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error("No response body");
        }

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
              if (!line.trim()) continue;

              try {
                const event = JSON.parse(line);
                if (event.type === 'assistant' || event.type === 'msg') {
                  yield {
                    content: [{
                      type: "text",
                      text: event.message || event.content || '',
                    }],
                  };
                }
              } catch (e) {
                console.error("Failed to parse event:", e);
              }
            }
          }
        } finally {
          reader.releaseLock();
        }
      } catch (error) {
        console.error("Chat error:", error);
        yield {
          content: [{
            type: "text",
            text: `Error: ${error instanceof Error ? error.message : 'An unknown error occurred'}. Please try again later.`,
          }],
        };
      }
    }
  };
};

function useKubiyaRuntime(
  selectedTeammate: string | undefined,
  sessions: Session[],
  setSessions: React.Dispatch<React.SetStateAction<Session[]>>,
  authType: 'sso' | 'apikey' | null,
  token: string | null
) {
  const runtimeConfig = React.useMemo<TeammateConfig>(() => ({
    teammate: selectedTeammate || '',
  }), [selectedTeammate]);

  const runtimeOptions = React.useMemo<CustomRuntimeOptions>(() => ({
    config: runtimeConfig,
    sessions,
    setSessions,
  }), [runtimeConfig, sessions, setSessions]);

  const modelAdapter = React.useMemo(
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
  const { apiKey, authType, setApiKey, setAuthType, clearApiKey } = useConfig();
  const { user, error: userError } = useUser();

  // Use layout effect to handle initial loading state and Auth0 session
  React.useLayoutEffect(() => {
    if (user?.sub) {
      // If we have an Auth0 user, set the auth type to SSO
      setAuthType('sso');
      // Get the access token from the session cookie
      fetch('/api/auth/token')
        .then(response => response.json())
        .then(data => {
          if (data.accessToken) {
            setApiKey(data.accessToken);
          } else {
            setIsLoading(false);
          }
        })
        .catch(error => {
          console.error('Failed to get access token:', error);
          clearApiKey();
          setIsLoading(false);
        });
    } else if (!apiKey || !authType) {
      setIsLoading(false);
    }
  }, [user, apiKey, authType, setApiKey, setAuthType, clearApiKey]);

  // Handle Auth0 errors
  useEffect(() => {
    if (userError) {
      console.error('Auth0 error:', userError);
      clearApiKey();
      setIsLoading(false);
    }
  }, [userError, clearApiKey]);

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
      {children}
    </AssistantRuntimeProvider>
  );
} 