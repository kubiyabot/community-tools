"use client";

import React, { useState, useEffect, type ReactNode, createContext, useContext } from "react";
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
import { getKubiyaConfig } from "../lib/config";
import { TeammateSelector } from "./components/TeammateSelector";

interface TeammateConfig extends ModelConfig {
  teammate: string;
}

interface Teammate {
  uuid: string;
  name: string;
  description?: string;
  llm_model?: string;
  instruction_type?: string;
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

interface TeammateContextType {
  teammates: Teammate[];
  selectedTeammate?: string;
  setSelectedTeammate: (uuid: string) => void;
  isLoading: boolean;
}

export const TeammateContext = createContext<TeammateContextType | null>(null);

export function useTeammateContext() {
  const context = useContext(TeammateContext);
  if (!context) {
    throw new Error('useTeammateContext must be used within a TeammateContext.Provider');
  }
  return context;
}

const createKubiyaModelAdapter = (
  selectedTeammate: string | undefined, 
  authOptions: { authType: 'sso' | 'apikey' },
  token?: string
): ChatModelAdapter => {
  return {
    async *run(options: ChatModelRunOptions) {
      const kubiyaConfig = getKubiyaConfig();
      const MAX_RETRIES = 3;
      let retryCount = 0;

      if (!selectedTeammate) {
        yield {
          content: [{
            type: "text",
            text: "Error: No teammate selected. Please select a teammate and try again.",
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

      while (retryCount < MAX_RETRIES) {
        try {
          // Get or generate session ID
          let sessionId = localStorage.getItem(`chat_session_${selectedTeammate}`);
          if (!sessionId) {
            const timestamp = BigInt(Date.now()) * BigInt(1000000);
            sessionId = timestamp.toString();
            localStorage.setItem(`chat_session_${selectedTeammate}`, sessionId);
          }

          const response = await fetch('/api/converse', {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Accept": "text/event-stream",
              "Cache-Control": "no-cache",
              "Connection": "keep-alive",
              "Authorization": authOptions.authType === 'sso' ? `Bearer ${token}` : `UserKey ${kubiyaConfig.apiKey}`
            },
            body: JSON.stringify({
              message: messageContent,
              agent_uuid: selectedTeammate,
              session_id: sessionId
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
          break;
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
            await new Promise(resolve => setTimeout(resolve, Math.min(1000 * Math.pow(2, retryCount), 10000)));
          }
        }
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

  // Handle auth errors
  useEffect(() => {
    if (!isAuthLoading && userError) {
      console.log('Auth initialization failed:', userError instanceof Error ? userError.message : 'Unknown error');
      memoizedClearApiKey();
      memoizedSetIsLoading(false);
      setInitializationAttempted(true);
    }
  }, [userError, isAuthLoading, memoizedClearApiKey, memoizedSetIsLoading]);

  // Handle auth initialization
  useEffect(() => {
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
              statusText: teammatesResponse.statusText
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
  }, [
    user,
    isAuthLoading,
    initializationAttempted,
    memoizedSetApiKey,
    memoizedSetAuthType,
    memoizedClearApiKey,
    memoizedSetIsLoading,
    setTeammates,
    setSelectedTeammate
  ]);

  return { isAuthLoading, userError };
}

export default function MyRuntimeProvider({ children }: { children: ReactNode }) {
  const [selectedTeammate, setSelectedTeammate] = useState<string>();
  const [teammates, setTeammates] = useState<Teammate[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { apiKey, authType, setApiKey, setAuthType, clearApiKey } = useConfig();
  const [mounted, setMounted] = useState(false);
  const { user } = useUser();

  // Handle initial mounting and hydration
  useEffect(() => {
    setMounted(true);
    
    // Load stored teammate and sessions after mounting
    if (typeof window !== 'undefined') {
      const storedTeammate = localStorage.getItem('selectedTeammate');
      if (storedTeammate) {
        setSelectedTeammate(storedTeammate);
        const storedSessions = localStorage.getItem(`sessions_${storedTeammate}`);
        if (storedSessions) {
          setSessions(JSON.parse(storedSessions));
        }
      }
    }
  }, []);

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

  // Add teammate selection handler
  const handleTeammateSelect = (id: string) => {
    setSelectedTeammate(id);
    localStorage.setItem('selectedTeammate', id);
    // Reset sessions when teammate changes
    setSessions([]);
  };

  if (!mounted) {
    return null;
  }

  // Show loading state while initializing
  if (isAuthLoading || isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-b from-[#0F172A] to-[#1E293B]">
        <div className="animate-spin rounded-full h-12 w-12 border-3 border-[#7C3AED] border-t-transparent mb-6"></div>
        <p className="text-white text-lg font-medium">Loading your workspace...</p>
      </div>
    );
  }

  // Show API key setup if no key or auth type
  if (!apiKey || !authType) {
    return <ApiKeySetup />;
  }

  return (
    <TeammateContext.Provider value={{
      teammates,
      selectedTeammate,
      setSelectedTeammate: handleTeammateSelect,
      isLoading
    }}>
      <div className="flex h-screen">
        {/* Sidebar */}
        <div className="w-72 flex-shrink-0 flex flex-col bg-[#0A0F1E] border-r border-[#1E293B]">
          <div className="p-4 border-b border-[#1E293B]">
            <TeammateSelector />
          </div>
          {/* Add session list here if needed */}
        </div>

        {/* Main content */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <div className="h-16 border-b border-[#1E293B] flex items-center justify-between px-6">
            <div className="flex items-center space-x-4">
              <h1 className="text-white font-medium">Kubiya Chat</h1>
            </div>
            {user && (
              <div className="flex items-center space-x-4">
                <img
                  src={user.picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name || '')}`}
                  alt={user.name || 'User'}
                  className="w-8 h-8 rounded-full"
                />
                <span className="text-white">{user.name}</span>
              </div>
            )}
          </div>

          {/* Chat area */}
          <div className="flex-1 overflow-hidden">
            <AssistantRuntimeProvider runtime={runtime}>
              {children}
            </AssistantRuntimeProvider>
          </div>
        </div>
      </div>
    </TeammateContext.Provider>
  );
} 