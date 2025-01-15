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
import { ApiKeySetup } from "@/components/ApiKeySetup";
import { useUser } from '@auth0/nextjs-auth0/client';

interface TeammateConfig extends ModelConfig {
  teammate: string;
}

interface Teammate {
  uuid: string;
  name: string;
  description?: string;
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

function useAuth0Init(
  memoizedSetApiKey: (key: string) => void,
  memoizedSetAuthType: (type: 'sso' | 'apikey') => void,
  memoizedClearApiKey: () => void,
  memoizedSetIsLoading: (loading: boolean) => void,
  setTeammates: (teammates: Teammate[]) => void,
  setSelectedTeammate: (id: string) => void,
) {
  const { user, error: userError, isLoading: isAuthLoading } = useUser();
  const [initializationAttempted, setInitializationAttempted] = React.useState(false);

  React.useEffect(() => {
    if (!isAuthLoading && userError) {
      console.log('Auth initialization failed:', userError instanceof Error ? userError.message : 'Unknown error');
      memoizedClearApiKey();
      memoizedSetIsLoading(false);
      setInitializationAttempted(true);
    }
  }, [userError, isAuthLoading, memoizedClearApiKey, memoizedSetIsLoading]);

  React.useEffect(() => {
    if (isAuthLoading || initializationAttempted) {
      return;
    }

    const initAuth = async () => {
      try {
        if (!user) {
          console.log('No user session found, clearing state');
          memoizedClearApiKey();
          memoizedSetIsLoading(false);
          setInitializationAttempted(true);
          return;
        }

        console.log('User session found:', { 
          sub: user.sub,
          email: user.email,
          provider: user.sub?.split('|')[0]
        });

        memoizedSetAuthType('sso');
        
        const response = await fetch('/api/auth/me', {
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        });

        if (!response.ok) {
          if (response.status === 401) {
            console.log('Session expired or invalid');
            memoizedClearApiKey();
            memoizedSetIsLoading(false);
            setInitializationAttempted(true);
            return;
          }
          throw new Error(`Profile fetch failed: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Auth session validated:', {
          hasAccessToken: !!data.accessToken,
          isAuthenticated: data.isAuthenticated,
          user: data.user
        });

        if (!data.accessToken) {
          console.log('No access token in profile');
          memoizedClearApiKey();
          memoizedSetIsLoading(false);
          setInitializationAttempted(true);
          return;
        }

        await memoizedSetApiKey(data.accessToken);

        try {
          const token = data.accessToken;
          console.log('Fetching teammates with token:', {
            authType: 'sso',
            hasToken: !!token,
            tokenPrefix: token ? token.substring(0, 10) + '...' : null
          });

          const teammatesResponse = await fetch('/api/teammates', {
            credentials: 'include',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Accept': 'application/json',
              'Cache-Control': 'no-cache',
              'Pragma': 'no-cache'
            }
          });

          if (!teammatesResponse.ok) {
            console.error('Teammates fetch failed:', {
              status: teammatesResponse.status,
              statusText: teammatesResponse.statusText,
              headers: Object.fromEntries(teammatesResponse.headers.entries())
            });

            try {
              const errorData = await teammatesResponse.json();
              console.error('Error details:', errorData);
            } catch {
              console.error('Could not parse error response');
            }

            throw new Error(`Failed to fetch teammates: ${teammatesResponse.status}`);
          }

          const teammatesData = await teammatesResponse.json();
          console.log('Successfully fetched teammates:', {
            count: teammatesData.length,
            firstTeammate: teammatesData[0] ? {
              uuid: teammatesData[0].uuid,
              name: teammatesData[0].name
            } : null
          });
          
          setTeammates(teammatesData);
          if (teammatesData.length > 0) {
            setSelectedTeammate(teammatesData[0].uuid);
          }
        } catch (error) {
          console.error('Error fetching teammates:', error);
          if (error instanceof Error && error.message.includes('401')) {
            memoizedClearApiKey();
          }
          throw error;
        }

      } catch (error) {
        console.error('Auth initialization failed:', error instanceof Error ? error.message : 'Unknown error');
        memoizedClearApiKey();
      } finally {
        memoizedSetIsLoading(false);
        setInitializationAttempted(true);
      }
    };

    initAuth();
  }, [user, isAuthLoading, initializationAttempted, memoizedSetApiKey, memoizedSetAuthType, memoizedClearApiKey, memoizedSetIsLoading, setTeammates, setSelectedTeammate]);

  return { isAuthLoading, userError };
}

export default function MyRuntimeProvider({ children }: { children: ReactNode }) {
  const [selectedTeammate, setSelectedTeammate] = useState<string>();
  const [teammates, setTeammates] = useState<Teammate[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { apiKey, authType, setApiKey, setAuthType, clearApiKey } = useConfig();
  const runtime = useKubiyaRuntime(selectedTeammate, sessions, setSessions, authType, apiKey);

  const memoizedSetApiKey = React.useCallback(setApiKey, []);
  const memoizedSetAuthType = React.useCallback(setAuthType, []);
  const memoizedClearApiKey = React.useCallback(clearApiKey, []);
  const memoizedSetIsLoading = React.useCallback(setIsLoading, []);

  const { isAuthLoading, userError } = useAuth0Init(
    memoizedSetApiKey,
    memoizedSetAuthType,
    memoizedClearApiKey,
    memoizedSetIsLoading,
    setTeammates,
    setSelectedTeammate
  );

  // Debug logging
  useEffect(() => {
    console.log('Current state:', {
      hasApiKey: !!apiKey,
      authType,
      teammatesCount: teammates.length,
      selectedTeammate,
      isLoading,
      hasRuntime: !!runtime,
      isAuthLoading,
      hasError: !!userError
    });
  }, [apiKey, authType, teammates.length, selectedTeammate, isLoading, runtime, isAuthLoading, userError]);

  // Show loading state while initializing
  if (isAuthLoading || isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-[#0F172A]">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[#7C3AED] border-t-transparent mb-4"></div>
        <p className="text-white text-sm">Loading...</p>
      </div>
    );
  }

  // Show error state
  if (userError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-[#0F172A]">
        <p className="text-white text-sm mb-4">Authentication error: {userError instanceof Error ? userError.message : 'Unknown error'}</p>
        <ApiKeySetup />
      </div>
    );
  }

  // Show API key setup if no key or auth type
  if (!apiKey || !authType) {
    return <ApiKeySetup />;
  }

  // Show error state if no teammates available
  if (!isLoading && teammates.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-[#0F172A]">
        <p className="text-white text-sm mb-4">No teammates available. Please check your account.</p>
        <button 
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-[#7C3AED] text-white rounded-lg hover:bg-[#6D28D9] focus:outline-none focus:ring-2 focus:ring-[#7C3AED] focus:ring-offset-2 focus:ring-offset-[#0F172A]"
        >
          Retry
        </button>
      </div>
    );
  }

  // Show loading state while initializing teammate
  if (!selectedTeammate) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-[#0F172A]">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[#7C3AED] border-t-transparent mb-4"></div>
        <p className="text-white text-sm">Initializing teammate...</p>
      </div>
    );
  }

  // Render children with runtime provider
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {children}
    </AssistantRuntimeProvider>
  );
} 