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

function ProfileSidebar({ user, onLogout }: { user: any, onLogout: () => void }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="fixed top-4 right-4 z-50">
      {/* Profile Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 bg-[#1F2937] rounded-lg p-2 hover:bg-[#374151] transition-colors duration-200"
      >
        <img
          src={user.picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}`}
          alt={user.name}
          className="w-8 h-8 rounded-full"
        />
        <svg className={`w-4 h-4 text-white transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 bg-[#1F2937] rounded-xl shadow-2xl p-4 border border-[#374151]">
          {/* User Info */}
          <div className="flex items-center space-x-3 mb-4 pb-4 border-b border-[#374151]">
            <img
              src={user.picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}`}
              alt={user.name}
              className="w-12 h-12 rounded-full"
            />
            <div className="flex-1 min-w-0">
              <p className="text-white font-medium truncate">{user.name}</p>
              <p className="text-gray-400 text-sm truncate">{user.email}</p>
            </div>
          </div>

          {/* Organization Info */}
          <div className="mb-4 pb-4 border-b border-[#374151]">
            <h4 className="text-gray-400 text-xs uppercase mb-2">Organization</h4>
            <p className="text-white text-sm">{user.org_name || 'Default Organization'}</p>
            <p className="text-gray-400 text-xs">{user.org_id}</p>
          </div>

          {/* Navigation Links */}
          <div className="space-y-2">
            <a
              href="https://app.kubiya.ai"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-2 text-white hover:bg-[#374151] rounded-lg p-2 transition-colors duration-200 group"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span>Management Console</span>
              <svg className="w-4 h-4 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </a>
            <a
              href="https://docs.kubiya.ai"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-2 text-white hover:bg-[#374151] rounded-lg p-2 transition-colors duration-200 group"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <span>Documentation</span>
              <svg className="w-4 h-4 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </a>
            <a
              href="/api/auth/logout"
              className="flex items-center space-x-2 text-red-400 hover:bg-red-400/10 rounded-lg p-2 transition-colors duration-200"
              onClick={(e) => {
                e.preventDefault();
                onLogout();
                window.location.href = '/api/auth/logout';
              }}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span>Logout</span>
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

export default function MyRuntimeProvider({ children }: { children: ReactNode }) {
  const [selectedTeammate, setSelectedTeammate] = useState<string>();
  const [teammates, setTeammates] = useState<Teammate[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { apiKey, authType, setApiKey, setAuthType, clearApiKey } = useConfig();
  const [mounted, setMounted] = useState(false);
  const { user } = useUser();

  useEffect(() => {
    setMounted(true);
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

  // Debug logging - Move inside useEffect to avoid render-time side effects
  useEffect(() => {
    if (process.env.NODE_ENV !== 'production') {
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
    }
  }, [apiKey, authType, teammates.length, selectedTeammate, isLoading, runtime, isAuthLoading, userError]);

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

  // Show error state
  if (userError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-b from-[#0F172A] to-[#1E293B] px-4">
        <div className="max-w-2xl w-full bg-[#1F2937] rounded-xl shadow-2xl p-8">
          <div className="flex items-center justify-center w-16 h-16 mx-auto mb-6 rounded-full bg-red-100">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-white text-center mb-4">Authentication Error</h2>
          <p className="text-gray-300 text-center mb-6">{userError instanceof Error ? userError.message : 'Unknown error'}</p>
          <div className="flex justify-center">
            <ApiKeySetup />
          </div>
        </div>
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
      <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-b from-[#0F172A] to-[#1E293B] px-4">
        <div className="max-w-3xl w-full bg-[#1F2937] rounded-xl shadow-2xl p-8">
          <div className="flex items-center justify-center w-20 h-20 mx-auto mb-6 rounded-full bg-[#7C3AED] bg-opacity-10">
            <svg className="w-10 h-10 text-[#7C3AED]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h2 className="text-3xl font-bold text-white text-center mb-6">Welcome to Kubiya Chat</h2>
          <p className="text-xl text-gray-300 text-center mb-8">
            Let's get you set up with your first teammate
          </p>
          <div className="bg-[#2D3748] rounded-lg p-6 mb-8">
            <h3 className="text-xl font-semibold text-white mb-4">Getting Started</h3>
            <ol className="space-y-6">
              <li className="flex items-start">
                <span className="flex items-center justify-center w-8 h-8 rounded-full bg-[#7C3AED] text-white font-bold mr-4 flex-shrink-0">1</span>
                <div>
                  <p className="text-gray-300 mb-2">Visit the Kubiya Management Console to create your teammates</p>
                  <a 
                    href="https://app.kubiya.ai" 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className="inline-flex items-center px-4 py-2 bg-[#7C3AED] text-white rounded-lg hover:bg-[#6D28D9] transition-colors duration-200 group"
                  >
                    Open Console
                    <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  </a>
                </div>
              </li>
              <li className="flex items-start">
                <span className="flex items-center justify-center w-8 h-8 rounded-full bg-[#7C3AED] text-white font-bold mr-4 flex-shrink-0">2</span>
                <div>
                  <p className="text-gray-300 mb-2">Learn how to configure your teammates effectively</p>
                  <a 
                    href="https://docs.kubiya.ai" 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className="inline-flex items-center px-4 py-2 bg-[#7C3AED] text-white rounded-lg hover:bg-[#6D28D9] transition-colors duration-200 group"
                  >
                    View Documentation
                    <svg className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  </a>
                </div>
              </li>
            </ol>
          </div>
          <div className="flex justify-center">
            <button 
              onClick={() => window.location.reload()}
              className="inline-flex items-center px-6 py-3 bg-white text-[#1F2937] rounded-lg hover:bg-gray-100 transition-colors duration-200 font-medium group"
            >
              <svg className="w-4 h-4 mr-2 group-hover:rotate-180 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh Page
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Render children with runtime provider and profile sidebar
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {user && <ProfileSidebar user={user} onLogout={memoizedClearApiKey} />}
      {children}
    </AssistantRuntimeProvider>
  );
} 