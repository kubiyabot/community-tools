"use client";

import React, { useState, useEffect, type ReactNode, createContext, useContext, SetStateAction, useCallback } from "react";
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
import { getKubiyaConfig } from "../lib/config";
import { TeammateSelector } from "./components/TeammateSelector";
import { UserProfile } from "./components/UserProfile";
import { UserProfileButton } from './components/UserProfileButton';
import { Chat } from './components/assistant-ui/Chat';

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

const backendApi = async ({ messages, abortSignal, config }: any) => {
  if (!messages.length) {
    console.error('[Runtime] No messages to send');
    throw new Error('No messages to send');
  }

  if (!config) {
    console.error('[Runtime] No config provided');
    throw new Error('No configuration provided');
  }

  if (!config.teammate || typeof config.teammate !== 'string' || !config.teammate.trim()) {
    console.error('[Runtime] Invalid teammate:', config.teammate);
    throw new Error('Please select a teammate before sending a message');
  }

  if (!config.threadId || typeof config.threadId !== 'string' || !config.threadId.trim()) {
    console.error('[Runtime] Invalid thread ID:', config.threadId);
    throw new Error('Invalid thread ID');
  }

  if (!config.sessionId || typeof config.sessionId !== 'string' || !config.sessionId.trim()) {
    console.error('[Runtime] Invalid session ID:', config.sessionId);
    throw new Error('Invalid session ID');
  }

  const lastMessage = messages[messages.length - 1];
  const messageContent = typeof lastMessage.content === 'string' 
    ? lastMessage.content 
    : Array.isArray(lastMessage.content) 
      ? lastMessage.content.find((c: ContentPart) => c.type === 'text')?.text || ''
      : '';

  if (!messageContent) {
    console.error('[Runtime] Empty message content');
    throw new Error('Empty message content');
  }

  console.log('[Runtime] Sending message:', {
    content: messageContent,
    teammate: config.teammate,
    threadId: config.threadId,
    sessionId: config.sessionId,
    hasAbortSignal: !!abortSignal
  });

  try {
    const response = await fetch('/api/chat', {
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
      let errorMessage = `Failed to fetch response: ${response.status}`;
      let errorDetails = '';
      
      try {
        const errorData = await response.json();
        console.error('[Runtime] Backend API error:', {
          status: response.status,
          statusText: response.statusText,
          error: errorData
        });
        
        errorMessage = errorData.error || errorData.message || errorMessage;
        errorDetails = errorData.details || '';
        
        if (response.status === 401) {
          window.location.href = '/api/auth/login';
          return;
        }
      } catch (parseError) {
        console.error('[Runtime] Failed to parse error response:', parseError);
      }

      throw new Error(`${errorMessage}${errorDetails ? `: ${errorDetails}` : ''}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      console.error('[Runtime] No reader available from response');
      throw new Error('No reader available');
    }

    return {
      async *[Symbol.asyncIterator]() {
        const decoder = new TextDecoder();
        let buffer = '';
        let lastMessage = '';

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
              const trimmedLine = line.trim();
              if (!trimmedLine || !trimmedLine.startsWith('data: ')) continue;
              
              const data = trimmedLine.slice(6);
              if (data === '[DONE]') {
                console.log('[Runtime] Received [DONE] event');
                yield { type: 'done' } as StreamEvent;
                return;
              }
              
              try {
                const event = JSON.parse(data) as KubiyaEvent;
                console.log('[Runtime] Processing event:', {
                  type: event.type,
                  messageId: event.id,
                  messagePreview: event.message?.substring(0, 50)
                });
                
                if (event.type === 'msg' || event.type === 'system_message') {
                  if (event.message === lastMessage) {
                    continue; // Skip duplicate messages
                  }
                  lastMessage = event.message;
                  
                  yield {
                    type: event.type,
                    text: event.message,
                    id: event.id
                  } as StreamEvent;
                } else if (event.type === 'tool') {
                  yield {
                    type: 'tool',
                    text: event.message,
                    id: event.id
                  } as StreamEvent;
                }
              } catch (e) {
                console.error('[Runtime] Error parsing event:', {
                  error: e,
                  line: trimmedLine
                });
                throw e;
              }
            }
          }
        } finally {
          console.log('[Runtime] Releasing reader lock');
          reader.releaseLock();
        }
      }
    };
  } catch (error) {
    console.error('[Runtime] Backend API error:', {
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined
    });
    throw error;
  }
};

const MyModelAdapter: ChatModelAdapter = {
  async *run({ messages, abortSignal, config }) {
    try {
      const stream = await backendApi({ messages, abortSignal, config });
      
      if (!stream) {
        yield {
          content: [{ 
            type: "text", 
            text: "Error: Failed to initialize message stream" 
          }],
          isComplete: true,
          role: 'system'
        };
        return;
      }

      let text = "";
      let hasError = false;

      for await (const event of stream) {
        if (event.type === 'done') {
          if (!hasError) {
            yield {
              content: [{ type: "text", text }],
              isComplete: true
            };
          }
          return;
        }

        if (event.type === 'system_message') {
          // Handle system messages as separate messages
          yield {
            content: [{ 
              type: "text", 
              text: `System: ${event.text || ''}`
            }],
            isComplete: true,
            role: 'system'
          };

          // If it's an error message, mark it
          if (event.text?.toLowerCase().includes('error')) {
            hasError = true;
            // Don't throw, just yield the error as a system message
            yield {
              content: [{ 
                type: "text", 
                text: `Error: ${event.text}` 
              }],
              isComplete: true,
              role: 'system'
            };
          }
          continue;
        }

        if (event.type === 'msg') {
          text = event.text || '';
          if (!hasError) {
            yield {
              content: [{ type: "text", text }],
              isComplete: false
            };
          }
        } else if (event.type === 'tool') {
          text += event.text || '';
          if (!hasError) {
            yield {
              content: [{ type: "text", text }],
              isComplete: false
            };
          }
        }
      }
    } catch (error) {
      // Instead of throwing, yield the error as a system message
      yield {
        content: [{ 
          type: "text", 
          text: `Error: ${error instanceof Error ? error.message : 'An unexpected error occurred'}`
        }],
        isComplete: true,
        role: 'system'
      };
    }
  },
};

interface TeammateState {
  sessions: Session[];
  currentThreadId: string;
  currentSessionId: string;
  lastMessageId?: string;
  threads: {
    [threadId: string]: {
      messages: any[];
      lastMessageId?: string;
    };
  };
}

interface TeammateStates {
  [teammateId: string]: TeammateState;
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
          const parsedState = JSON.parse(storedState);
          setTeammateStates(prev => ({
            ...prev,
            [storedTeammate]: parsedState
          }));
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
            initializeTeammateState(storedTeammate);
          }
        } else if (data.length > 0) {
          // Otherwise select the first teammate
          const firstTeammate = data[0].uuid;
          setSelectedTeammate(firstTeammate);
          localStorage.setItem('selectedTeammate', firstTeammate);
          if (!teammateStates[firstTeammate]) {
            initializeTeammateState(firstTeammate);
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

  const initializeTeammateState = useCallback((teammateId: string) => {
    const threadId = Date.now().toString();
    const sessionId = Date.now().toString();
    const newState: TeammateState = {
      sessions: [],
      currentThreadId: threadId,
      currentSessionId: sessionId,
      threads: {
        [threadId]: {
          messages: [],
          lastMessageId: undefined
        }
      }
    };
    
    setTeammateStates(prev => ({
      ...prev,
      [teammateId]: newState
    }));
    
    localStorage.setItem(`teammate_state_${teammateId}`, JSON.stringify(newState));
    return newState;
  }, []);

  // Handle teammate selection
  const handleTeammateSelect = useCallback((id: string) => {
    console.log('[Runtime] Selecting teammate:', id);
    setSelectedTeammate(id);
    localStorage.setItem('selectedTeammate', id);
    
    // Initialize state if it doesn't exist
    if (!teammateStates[id]) {
      initializeTeammateState(id);
    }
  }, [teammateStates, initializeTeammateState]);

  const runtime = useKubiyaRuntime(
    selectedTeammate,
    teammateStates[selectedTeammate || '']?.sessions || [],
    (newSessions: SetStateAction<Session[]>) => {
      if (!selectedTeammate) return;
      
      setTeammateStates(prev => {
        const currentState = prev[selectedTeammate];
        if (!currentState) {
          const newState = initializeTeammateState(selectedTeammate);
          return {
            ...prev,
            [selectedTeammate]: newState
          };
        }

        const threadId = currentState.currentThreadId;
        const updatedSessions = typeof newSessions === 'function' 
          ? newSessions(currentState.sessions || [])
          : newSessions;

        const updatedState = {
          ...currentState,
          sessions: updatedSessions,
          threads: {
            ...currentState.threads,
            [threadId]: {
              messages: updatedSessions,
              lastMessageId: updatedSessions[updatedSessions.length - 1]?.id
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
      setTeammateStates(prev => {
        const updatedState = {
          ...newState,
          threads: {
            ...newState.threads,
            [newState.currentThreadId]: newState.threads[newState.currentThreadId] || {
              messages: [],
              lastMessageId: undefined
            }
          }
        };
        localStorage.setItem(`teammate_state_${selectedTeammate}`, JSON.stringify(updatedState));
        return {
          ...prev,
          [selectedTeammate]: updatedState
        };
      });
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
  memoizedSetAuthType: (type: 'sso' | 'apikey') => void,
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

const useKubiyaRuntime = (
  selectedTeammate: string | undefined,
  sessions: Session[],
  setSessions: React.Dispatch<React.SetStateAction<Session[]>>,
  authType: 'sso' | 'apikey' | null,
  token: string | null,
  teammateState?: TeammateState,
  setTeammateState?: (state: TeammateState) => void
) => {
  // Always call hooks at the top level
  const modelAdapter = React.useMemo(
    () => selectedTeammate ? MyModelAdapter : dummyModelAdapter,
    [selectedTeammate]
  );

  const runtimeConfig = React.useMemo<TeammateConfig>(() => {
    // Return a default config if no teammate is selected
    if (!selectedTeammate) {
      const defaultThreadId = Date.now().toString();
      const defaultSessionId = Date.now().toString();
      return {
        teammate: '',
        threadId: defaultThreadId,
        sessionId: defaultSessionId
      };
    }

    if (!teammateState) {
      const newState = {
        sessions: [],
        currentThreadId: Date.now().toString(),
        currentSessionId: Date.now().toString(),
        threads: {}
      };
      setTeammateState?.(newState);
      return {
        teammate: selectedTeammate,
        threadId: newState.currentThreadId,
        sessionId: newState.currentSessionId
      };
    }

    const threadId = teammateState.currentThreadId;
    const sessionId = teammateState.currentSessionId;

    // If thread state doesn't exist, update it through the setter
    if (setTeammateState && !teammateState.threads[threadId]) {
      const updatedState = {
        ...teammateState,
        threads: {
          ...teammateState.threads,
          [threadId]: {
            messages: [],
            lastMessageId: undefined
          }
        }
      };
      setTeammateState(updatedState);
    }

    return {
      teammate: selectedTeammate,
      threadId,
      sessionId
    };
  }, [selectedTeammate, teammateState, setTeammateState]);

  const runtimeOptions = React.useMemo<CustomRuntimeOptions>(() => ({
    config: runtimeConfig,
    sessions: sessions || [],
    setSessions,
  }), [runtimeConfig, sessions, setSessions]);

  // Only use the real adapter if we have a valid teammate
  if (!selectedTeammate) {
    return useLocalRuntime(dummyModelAdapter, runtimeOptions);
  }

  return useLocalRuntime(modelAdapter, runtimeOptions);
}; 