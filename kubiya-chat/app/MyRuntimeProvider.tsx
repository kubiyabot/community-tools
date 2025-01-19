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
  type ModelConfigProvider
} from "@assistant-ui/react";
import { useConfig } from "@/lib/config-context";
import { ApiKeySetup } from "@/app/components/ApiKeySetup";
import { useUser } from '@auth0/nextjs-auth0/client';
import { getKubiyaConfig } from "../lib/config";
import { TeammateSelector } from "./components/TeammateSelector";
import { UserProfile } from "./components/UserProfile";
import { UserProfileButton } from './components/UserProfileButton';
import { Chat } from './components/assistant-ui/Chat';

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

interface ContentPart {
  type: string;
  text?: string;
}

const backendApi = async ({ messages, abortSignal, config }: { messages: any[], abortSignal?: AbortSignal, config: TeammateConfig }) => {
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
      ? lastMessage.content.find((c: ContentPart) => c.type === 'text')?.text || ''
      : '';

  console.log('[Runtime] Sending message:', {
    content: messageContent,
    agent_uuid: config.teammate,
    thread_id: config.threadId,
    session_id: config.sessionId
  });

  const response = await fetch('/api/converse', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    },
    body: JSON.stringify({
      message: messageContent.trim(),
      agent_uuid: config.teammate,
      thread_id: config.threadId,
      session_id: config.sessionId
    }),
    signal: abortSignal
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('No response stream available');
  }

  return {
    async *[Symbol.asyncIterator]() {
      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            console.log('[Runtime] Stream complete');
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (!line.trim() || !line.startsWith('data: ')) continue;
            
            const data = line.slice(6);
            console.log('[Runtime] Raw SSE data:', data);
            
            if (data === '[DONE]') {
              yield { type: 'done' } as StreamEvent;
              return;
            }

            try {
              const event = JSON.parse(data);
              console.log('[Runtime] Parsed event:', event);
              
              if (event.type === 'msg' || event.type === 'system_message') {
                yield {
                  type: event.type,
                  text: event.message || event.text,
                  id: event.id
                } as StreamEvent;
              }
            } catch (e) {
              console.error('[Runtime] Failed to parse event:', e);
              continue;
            }
          }
        }
      } finally {
        console.log('[Runtime] Releasing reader lock');
        reader.releaseLock();
      }
    }
  };
};

const MyModelAdapter: ChatModelAdapter = {
  async *run(options: ChatModelRunOptions) {
    const config = options.config as CustomModelConfig;
    if (!config?.teammate) {
      yield {
        content: [{ type: "text", text: "Please select a teammate before sending a message" }],
        isComplete: true,
        role: 'system'
      };
      return;
    }

    const stream = await backendApi({ 
      messages: options.messages, 
      abortSignal: options.abortSignal, 
      config: {
        teammate: config.teammate,
        threadId: config.threadId,
        sessionId: config.sessionId
      }
    });

    if (!stream) {
      yield {
        content: [{ type: "text", text: "Failed to initialize stream" }],
        isComplete: true,
        role: 'system'
      };
      return;
    }

    let lastMessage = '';
    for await (const event of stream) {
      if (event.type === 'done') break;
      
      if (event.text && event.text !== lastMessage) {
        lastMessage = event.text;
        console.log('[Runtime] Processing message:', event.text);
        
        yield {
          content: [{ type: "text", text: event.text }],
          isComplete: false,
          role: 'assistant'
        };
      }
    }

    yield {
      content: [{ type: "text", text: lastMessage }],
      isComplete: true,
      role: 'assistant'
    };
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

const dummyModelAdapter: ChatModelAdapter = {
  async *run() {
    yield {
      content: [{ type: "text", text: "Please select a teammate to start chatting." }],
      isComplete: true,
      role: 'system'
    };
  }
};

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
  const config = React.useMemo<CustomModelConfig>(() => ({
    model: 'kubiya',
    temperature: 1,
    maxTokens: 4096,
    teammate: selectedTeammate || '',
    threadId: teammateState?.currentThreadId || Date.now().toString(),
    sessionId: teammateState?.currentSessionId || Date.now().toString()
  }), [selectedTeammate, teammateState]);

  const adapter = React.useMemo<ChatModelAdapter>(() => ({
    ...MyModelAdapter,
    async *run(options: ChatModelRunOptions) {
      const customConfig = {
        ...options.config,
        teammate: config.teammate,
        threadId: config.threadId,
        sessionId: config.sessionId
      } as CustomModelConfig;

      if (!customConfig.teammate) {
        yield {
          content: [{ type: "text", text: "Please select a teammate before sending a message" }],
          isComplete: true,
          role: 'system'
        };
        return;
      }

      const stream = await backendApi({ 
        messages: options.messages, 
        abortSignal: options.abortSignal, 
        config: {
          teammate: customConfig.teammate,
          threadId: customConfig.threadId,
          sessionId: customConfig.sessionId
        }
      });

      if (!stream) {
        yield {
          content: [{ type: "text", text: "Failed to initialize stream" }],
          isComplete: true,
          role: 'system'
        };
        return;
      }

      let lastMessage = '';
      for await (const event of stream) {
        if (event.type === 'done') break;
        
        if (event.text && event.text !== lastMessage) {
          lastMessage = event.text;
          console.log('[Runtime] Processing message:', event.text);
          
          yield {
            content: [{ type: "text", text: event.text }],
            isComplete: false,
            role: 'assistant'
          };
        }
      }

      yield {
        content: [{ type: "text", text: lastMessage }],
        isComplete: true,
        role: 'assistant'
      };
    }
  }), [config]);

  return useLocalRuntime(adapter);
}; 