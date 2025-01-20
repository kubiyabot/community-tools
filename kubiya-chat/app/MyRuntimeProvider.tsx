"use client";

import React, { useState, useEffect, type ReactNode, createContext, useContext, SetStateAction, useCallback } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
  type ModelConfig,
  type LocalRuntimeOptions,
  type ChatModelRunOptions,
  useThreadRuntime,
  type ModelConfigProvider,
  ChatModelRunResult,
  ContentPart
} from "@assistant-ui/react";
import { useConfig } from "@/lib/config-context";
import { ApiKeySetup } from "@/app/components/ApiKeySetup";
import { useUser } from '@auth0/nextjs-auth0/client';
import { getKubiyaConfig } from "../lib/config";
import { TeammateSelector } from "./components/TeammateSelector";
import { UserProfile } from "./components/UserProfile";
import { UserProfileButton } from './components/UserProfileButton';
import { Chat } from './components/assistant-ui/Chat';
import { useRouter } from 'next/navigation';

interface TeammateConfig {
  teammate: string;
  threadId: string;
  sessionId: string;
}

interface CustomModelConfig extends ModelConfig {
  teammate: string;
  threadId: string;
  sessionId: string;
  model: string;
  temperature: number;
  maxTokens: number;
}

interface Teammate {
  uuid: string;
  name: string;
  description?: string;
  llm_model?: string;
  instruction_type?: string;
}

interface CustomRuntimeOptions {
  model: string;
  temperature: number;
  maxTokens: number;
  teammate: string;
  threadId: string;
  sessionId: string;
}

interface Session {
  id: string;
  title?: string;
}

interface TeammateContextType {
  teammates: any[];
  selectedTeammate: string | undefined;
  setSelectedTeammate: (id: string) => void;
  isLoading: boolean;
  error?: {
    error: string;
    details: string;
    status?: number;
    supportInfo?: {
      message: string;
      email: string;
      subject: string;
      body: string;
    };
  };
  currentState?: TeammateState;
}

const TeammateContext = createContext<TeammateContextType>({
  teammates: [],
  selectedTeammate: undefined,
  setSelectedTeammate: () => {},
  isLoading: true,
});

export const useTeammateContext = () => useContext(TeammateContext);

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

interface TextContent {
  type: 'text';
  text: string;
}

interface ToolCall {
  type: 'tool_init' | 'tool_output';
  id: string;
  name?: string;
  arguments?: any;
  message?: string;
  timestamp: string;
}

interface MessageContent {
  content: TextContent[];
  role: 'system' | 'assistant';
  id?: string;
  tool_calls?: ToolCall[];
}

const backendApi = async ({ 
  messages, 
  abortSignal, 
  config,
  apiKey,
  router
}: { 
  messages: any[], 
  abortSignal?: AbortSignal, 
  config: TeammateConfig,
  apiKey: string,
  router: any
}) => {
  if (!messages.length) {
    console.error('[Runtime] No messages to send');
    throw new Error('No messages to send');
  }

  if (!config.teammate) {
    console.error('[Runtime] Invalid teammate:', config.teammate);
    throw new Error('Please select a teammate before sending a message');
  }

  const lastMessage = messages[messages.length - 1];
  const messageContent = typeof lastMessage.content === 'string' 
    ? lastMessage.content 
    : Array.isArray(lastMessage.content) 
      ? lastMessage.content.find((c: { type: string; text?: string }) => c.type === 'text')?.text || ''
      : '';

  // First, ensure we have a valid session
  const sessionResponse = await fetch('/api/auth/me', {
    credentials: 'include'
  });

  if (!sessionResponse.ok) {
    if (sessionResponse.status === 401) {
      router.push('/api/auth/login');
      throw new Error('Session expired');
    }
    throw new Error(`Failed to validate session: ${sessionResponse.status}`);
  }

  const { accessToken } = await sessionResponse.json();

  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Authorization': `Bearer ${accessToken}`
    },
    credentials: 'include',
    body: JSON.stringify({
      message: messageContent.trim(),
      agent_uuid: config.teammate,
      thread_id: config.threadId,
      session_id: config.sessionId
    }),
    signal: abortSignal
  });

  if (!response.ok) {
    if (response.status === 401) {
      router.push('/api/auth/login');
      throw new Error('Session expired');
    }
    throw new Error(`API request failed: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('No response stream available');
  }

  return reader;
};

const handleStreamEvents = async function*(reader: ReadableStreamDefaultReader<Uint8Array>): AsyncGenerator<MessageContent, void, unknown> {
  const decoder = new TextDecoder();
  let buffer = '';
  let systemMessages = new Set<string>();
  let lastMessageText = "";
  let lastMessageType: 'system' | 'assistant' | null = null;
  let messageId = `msg_${Date.now()}`;
  let currentToolId = `tool_${Date.now()}`;

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
          // Handle data: prefix
          const content = line.startsWith('data: ') ? line.slice(6) : line;
          if (content === '[DONE]') break;

          try {
            // Try to parse as JSON first
            const event = JSON.parse(content);
            if (event.type === 'system_message' && event.message) {
              const text = event.message.trim();
              if (text && !systemMessages.has(text)) {
                systemMessages.add(text);
                yield {
                  content: [{ type: "text", text } as TextContent],
                  role: 'system',
                  id: event.id || `system_${Date.now()}_${systemMessages.size}`
                };
              }
              continue;
            }

            // Handle other event types
            if (event.type === 'tool') {
              const toolId = event.id || currentToolId;
              
              // Try to extract tool info from text or event
              let toolName = event.tool_name;
              let args = event.arguments;
              
              if (!toolName && event.message) {
                const toolMatch = event.message.match(/Tool:\s*(\w+)(?:\s*\n|\s+)Arguments:\s*({[\s\S]*})/i);
                if (toolMatch) {
                  try {
                    toolName = toolMatch[1];
                    args = JSON.parse(toolMatch[2]);
                  } catch (e) {
                    console.warn('Failed to parse tool arguments:', e);
                  }
                }
              }

              if (toolName) {
                yield {
                  content: [],
                  role: 'assistant',
                  id: toolId,
                  tool_calls: [{
                    type: 'tool_init',
                    id: toolId,
                    name: toolName,
                    arguments: args,
                    timestamp: new Date().toISOString()
                  }]
                };
              }
            } else if (event.type === 'tool_output') {
              const toolId = event.id || currentToolId;
              yield {
                content: [],
                role: 'assistant',
                id: toolId,
                tool_calls: [{
                  type: 'tool_output',
                  id: toolId,
                  message: event.message,
                  timestamp: new Date().toISOString()
                }]
              };
            } else if ((event.type === 'msg' || event.type === 'assistant') && event.message) {
              lastMessageText = event.message;
              lastMessageType = 'assistant';
              yield {
                content: [{ type: "text", text: event.message } as TextContent],
                role: 'assistant',
                id: messageId
              };
            }
          } catch (parseError) {
            // If JSON parsing fails, check for system message patterns
            if (content.includes('WARNING:') || content.includes('ERROR:')) {
              const text = content.replace(/^(WARNING:|ERROR:)\s*/, '').trim();
              if (text && !systemMessages.has(text)) {
                systemMessages.add(text);
                yield {
                  content: [{ type: "text", text } as TextContent],
                  role: 'system',
                  id: `system_${Date.now()}_${systemMessages.size}`
                };
              }
            } else if (!content.startsWith('{') && !content.startsWith('[')) {
              // If it's not JSON and not a system message, treat as assistant message
              lastMessageText = content;
              lastMessageType = 'assistant';
              yield {
                content: [{ type: "text", text: content } as TextContent],
                role: 'assistant',
                id: messageId
              };
            }
          }
        } catch (e) {
          console.warn('[Runtime] Error processing message:', e);
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
};

interface ThreadMetadata {
  teammateId: string;
  createdAt: string;
  updatedAt: string;
}

interface ThreadState {
  messages: any[];
  lastMessageId?: string;
  metadata: ThreadMetadata;
}

interface TeammateState {
  sessions: Session[];
  currentThreadId: string;
  currentSessionId: string;
  lastMessageId?: string;
  threads: Record<string, ThreadState>;
}

interface TeammateStates {
  [teammateId: string]: TeammateState;
}

interface RuntimeOptions {
  model: string;
  temperature: number;
  maxTokens: number;
}

export default function MyRuntimeProvider({ children }: { children: ReactNode }) {
  const [teammates, setTeammates] = useState<any[]>([]);
  const [selectedTeammate, setSelectedTeammate] = useState<string | undefined>(undefined);
  const [teammateStates, setTeammateStates] = useState<TeammateStates>({});
  const [isLoading, setIsLoading] = useState(true);
  const { apiKey, authType, setApiKey, setAuthType, clearApiKey } = useConfig();
  const [mounted, setMounted] = useState(false);
  const { user, isLoading: isUserLoading } = useUser();
  const [error, setError] = useState<TeammateContextType['error']>();
  const router = useRouter();

  const createThreadState = useCallback((teammateId: string): ThreadState => {
    const now = new Date().toISOString();
    return {
      messages: [],
      lastMessageId: undefined,
      metadata: {
        teammateId,
        createdAt: now,
        updatedAt: now
      }
    };
  }, []);

  const createTeammateState = useCallback((teammateId: string): TeammateState => {
    const threadId = Date.now().toString();
    const sessionId = Date.now().toString();
    
    return {
      sessions: [],
      currentThreadId: threadId,
      currentSessionId: sessionId,
      threads: {
        [threadId]: createThreadState(teammateId)
      }
    };
  }, [createThreadState]);

  const updateTeammateState = useCallback((teammateId: string, newState: TeammateState) => {
    setTeammateStates(prev => {
      const updated: TeammateStates = {
        ...prev,
        [teammateId]: newState
      };
      return updated;
    });
    localStorage.setItem(`teammate_state_${teammateId}`, JSON.stringify(newState));
  }, []);

  // Handle initial mounting and hydration
  useEffect(() => {
    setMounted(true);
    // Load stored teammate on mount
    const storedTeammate = localStorage.getItem('selectedTeammate');
    if (storedTeammate) {
      setSelectedTeammate(storedTeammate);
      const storedState = localStorage.getItem(`teammate_state_${storedTeammate}`);
      if (storedState) {
        try {
          const parsedState = JSON.parse(storedState) as TeammateState;
          setTeammateStates(prev => {
            const updated: TeammateStates = {
              ...prev,
              [storedTeammate]: parsedState
            };
            return updated;
          });
        } catch (e) {
          console.error(`Failed to parse stored state for teammate ${storedTeammate}:`, e);
        }
      }
    }
  }, []);

  // Fetch teammates when mounted and apiKey is available
  useEffect(() => {
    if (!mounted || !apiKey || !user) return;

    const fetchTeammates = async () => {
      try {
        const response = await fetch('/api/teammates', {
          headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (!response.ok) {
          throw new Error(await response.text());
        }
        
        const data = await response.json();
        console.log('Fetched teammates:', data.length);
        setTeammates(data);
        
        // If there's a stored teammate, verify it exists in the fetched data
        const storedTeammate = localStorage.getItem('selectedTeammate');
        if (storedTeammate && data.some((t: any) => t.uuid === storedTeammate)) {
          setSelectedTeammate(storedTeammate);
          // Initialize state if needed
          if (!teammateStates[storedTeammate]) {
            const newState = createTeammateState(storedTeammate);
            updateTeammateState(storedTeammate, newState);
          }
        } else if (data.length > 0) {
          // Otherwise select the first teammate
          const firstTeammate = data[0].uuid;
          setSelectedTeammate(firstTeammate);
          localStorage.setItem('selectedTeammate', firstTeammate);
          if (!teammateStates[firstTeammate]) {
            const newState = createTeammateState(firstTeammate);
            updateTeammateState(firstTeammate, newState);
          }
        }
        
        setError(undefined);
      } catch (error) {
        console.error('Error fetching teammates:', error);
        setError({
          error: 'Failed to fetch teammates',
          details: error instanceof Error ? error.message : 'Unknown error'
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchTeammates();
  }, [mounted, apiKey, user]);

  // Handle teammate selection
  const handleTeammateSelect = useCallback((id: string) => {
    if (!id) {
      console.warn('[Runtime] Attempted to select invalid teammate ID');
      return;
    }
    console.log('[Runtime] Selecting teammate:', id);
    setSelectedTeammate(id);
    localStorage.setItem('selectedTeammate', id);
    
    // Initialize state if it doesn't exist
    if (!teammateStates[id]) {
      console.log('[Runtime] Initializing state for teammate:', id);
      const newState = createTeammateState(id);
      updateTeammateState(id, newState);
    }
  }, [teammateStates, createTeammateState, updateTeammateState]);

  const runtime = useKubiyaRuntime(
    selectedTeammate,
    teammateStates[selectedTeammate || '']?.sessions || [],
    (newSessions: SetStateAction<Session[]>) => {
      if (!selectedTeammate) return;
      
      setTeammateStates(prev => {
        const currentState = prev[selectedTeammate];
        if (!currentState) {
          const newState = createTeammateState(selectedTeammate);
          return {
            ...prev,
            [selectedTeammate]: newState
          };
        }

        const threadId = currentState.currentThreadId;
        const updatedSessions = typeof newSessions === 'function' 
          ? newSessions(currentState.sessions || [])
          : newSessions;

        const now = new Date().toISOString();
        const updatedState: TeammateState = {
          ...currentState,
          sessions: updatedSessions,
          threads: {
            ...currentState.threads,
            [threadId]: {
              messages: updatedSessions,
              lastMessageId: updatedSessions[updatedSessions.length - 1]?.id,
              metadata: currentState.threads[threadId]?.metadata || {
                teammateId: selectedTeammate,
                createdAt: now,
                updatedAt: now
              }
            }
          }
        };

        localStorage.setItem(`teammate_state_${selectedTeammate}`, JSON.stringify(updatedState));
        return {
          ...prev,
          [selectedTeammate]: updatedState
        };
      });
    },
    authType,
    apiKey,
    selectedTeammate ? teammateStates[selectedTeammate] : undefined,
    selectedTeammate ? (newState: TeammateState) => {
      setTeammateStates(prev => ({
        ...prev,
        [selectedTeammate]: newState
      }));
      localStorage.setItem(`teammate_state_${selectedTeammate}`, JSON.stringify(newState));
    } : undefined
  );

  // Show loading state while initializing
  if (!mounted || isUserLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-b from-[#0F172A] to-[#1E293B]">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-[#7C3AED] border-t-transparent mb-6"></div>
        <p className="text-white text-lg font-medium">Loading your workspace...</p>
      </div>
    );
  }

  // Show API key setup if no key, auth type, or user
  if (!apiKey || !authType || !user) {
    return <ApiKeySetup />;
  }

  // Only show loading state for teammate loading
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-b from-[#0F172A] to-[#1E293B]">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-[#7C3AED] border-t-transparent mb-6"></div>
        <p className="text-white text-lg font-medium">Loading teammates...</p>
      </div>
    );
  }

  return (
    <TeammateContext.Provider value={{
      teammates,
      selectedTeammate,
      setSelectedTeammate: handleTeammateSelect,
      isLoading,
      error,
      currentState: selectedTeammate ? teammateStates[selectedTeammate] : undefined
    }}>
      <AssistantRuntimeProvider runtime={runtime}>
        {children}
      </AssistantRuntimeProvider>
    </TeammateContext.Provider>
  );
}

function useAuth0Init(
  memoizedSetApiKey: (key: string) => void,
  memoizedSetAuthType: (type: 'sso' | 'apiKey') => void,
  memoizedClearApiKey: () => void,
  memoizedSetIsLoading: (loading: boolean) => void,
  setTeammates: (teammates: Teammate[]) => void,
  setSelectedTeammate: (id: string) => void,
  setError: (error: TeammateContextType['error'] | undefined) => void
) {
  const { user, error: userError, isLoading: isAuthLoading } = useUser();
  const [initializationAttempted, setInitializationAttempted] = useState(false);

  // Handle auth errors
  useEffect(() => {
    if (!isAuthLoading && userError) {
      console.log('Auth initialization failed:', userError instanceof Error ? userError.message : 'Unknown error');
      memoizedClearApiKey();
      memoizedSetIsLoading(false);
      setError({
        error: 'Authentication Failed',
        details: userError instanceof Error ? userError.message : 'Unknown error',
        supportInfo: {
          message: 'Please contact the Kubiya support team for assistance.',
          email: 'support@kubiya.ai',
          subject: 'Authentication Issue - Chat UI',
          body: `Hi Kubiya Support,\n\nI'm experiencing authentication issues with the Chat UI.\n\nError Details:\n${userError instanceof Error ? userError.message : 'Unknown error'}`
        }
      });
      setInitializationAttempted(true);
    }
  }, [userError, isAuthLoading, memoizedClearApiKey, memoizedSetIsLoading, setError]);

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
            setError({
              error: 'Session Expired',
              details: 'Your session has expired. Please sign in again.',
              supportInfo: {
                message: 'Please try signing in again. If the issue persists, contact support.',
                email: 'support@kubiya.ai',
                subject: 'Session Issue - Chat UI', 
                body: `Hi Kubiya Support,\n\nMy session expired unexpectedly in the Chat UI.`
              }
            });
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
          setError({
            error: 'Missing Access Token',
            details: 'Unable to get access token from your profile.',
            supportInfo: {
              message: 'Please try signing in again. If the issue persists, contact support.',
              email: 'support@kubiya.ai',
              subject: 'Token Issue - Chat UI',
              body: `Hi Kubiya Support,\n\nI'm unable to get an access token in the Chat UI.`
            }
          });
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

            let errorData;
            try {
              errorData = await teammatesResponse.json();
              console.error('Error details:', errorData);
              setError(errorData);
            } catch {
              console.error('Could not parse error response');
              setError({
                error: 'Failed to fetch teammates',
                details: `Server returned ${teammatesResponse.status}`,
                supportInfo: {
                  message: 'Please contact the Kubiya support team for assistance.',
                  email: 'support@kubiya.ai',
                  subject: 'Teammates Issue - Chat UI',
                  body: `Hi Kubiya Support,\n\nI'm unable to fetch teammates in the Chat UI.\n\nError Details:\nStatus: ${teammatesResponse.status}\nStatus Text: ${teammatesResponse.statusText}`
                }
              });
            }

            if (teammatesResponse.status === 401) {
              memoizedClearApiKey();
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
          setError(undefined);
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
        setError({
          error: 'Authentication Failed',
          details: error instanceof Error ? error.message : 'Unknown error',
          supportInfo: {
            message: 'Please contact the Kubiya support team for assistance.',
            email: 'support@kubiya.ai',
            subject: 'Authentication Issue - Chat UI',
            body: `Hi Kubiya Support,\n\nI'm experiencing authentication issues with the Chat UI.\n\nError Details:\n${error instanceof Error ? error.message : 'Unknown error'}`
          }
        });
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
    setSelectedTeammate,
    setError
  ]);

  return { isAuthLoading, userError };
}

// Update AuthType definition
type AuthType = 'sso' | 'apiKey' | null;

const useKubiyaRuntime = (
  selectedTeammate: string | undefined,
  sessions: Session[],
  setSessions: React.Dispatch<React.SetStateAction<Session[]>>,
  authType: AuthType,
  token: string | null,
  teammateState?: TeammateState,
  setTeammateState?: (state: TeammateState) => void
) => {
  const router = useRouter();
  
  const config = React.useMemo<CustomModelConfig>(() => ({
    model: 'kubiya',
    temperature: 1,
    maxTokens: 4096,
    teammate: selectedTeammate || '',
    threadId: teammateState?.currentThreadId || Date.now().toString(),
    sessionId: teammateState?.currentSessionId || Date.now().toString()
  }), [selectedTeammate, teammateState]);

  const adapter = React.useMemo<ChatModelAdapter>(() => ({
    async *run(options: ChatModelRunOptions): AsyncGenerator<MessageContent, void, unknown> {
      const customConfig = {
        ...options.config,
        teammate: config.teammate,
        threadId: config.threadId,
        sessionId: config.sessionId
      } as CustomModelConfig;

      if (!customConfig.teammate) {
        yield {
          content: [{ type: "text", text: "Please select a teammate before sending a message" } as TextContent],
          role: 'system',
          id: `system_${Date.now()}`
        };
        return;
      }

      try {
        const stream = await backendApi({ 
          messages: options.messages, 
          abortSignal: options.abortSignal, 
          config: {
            teammate: customConfig.teammate,
            threadId: customConfig.threadId,
            sessionId: customConfig.sessionId
          },
          apiKey: token || '',
          router
        });

        if (!stream) {
          yield {
            content: [{ type: "text", text: "Failed to initialize stream" } as TextContent],
            role: 'system',
            id: `system_${Date.now()}`
          };
          return;
        }

        yield* handleStreamEvents(stream);
      } catch (error) {
        if (error instanceof Error && error.message.includes('Session expired')) {
          // Let the error propagate but don't yield anything
          throw error;
        }
        
        yield {
          content: [{ type: "text", text: error instanceof Error ? error.message : "An error occurred" } as TextContent],
          role: 'system',
          id: `system_${Date.now()}`
        };
      }
    }
  }), [config, token, router]);

  return useLocalRuntime(adapter);
}; 