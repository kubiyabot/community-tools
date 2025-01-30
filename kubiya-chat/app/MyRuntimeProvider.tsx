"use client";

import React, { useState, useEffect, type ReactNode, createContext, useContext, SetStateAction, useCallback, useMemo } from "react";
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
import { useConfig } from "../lib/config-context";
import { ApiKeySetup } from "./components/ApiKeySetup";
import { useUser } from '@auth0/nextjs-auth0/client';
import { getKubiyaConfig } from "../lib/config";
import { TeammateSelector } from "./components/TeammateSelector";
import { UserProfile } from "./components/UserProfile";
import { UserProfileButton } from './components/UserProfileButton';
import { Chat } from './components/assistant-ui/Chat';
import { useRouter } from 'next/navigation';
import { ToolProvider } from './components/assistant-ui/ToolRegistry';
import { getToolMetadata } from './components/assistant-ui/ToolRegistry';
import { toast } from "@/app/components/ui/use-toast";
import { SessionExpired } from './components/SessionExpired';

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
  selectedTeammate: string | undefined;
  currentState: TeammateState | null;
  teammates: any[];
  teammateCapabilities: Record<string, {
    tools: any[];
    integrations: any[];
    description?: string;
    runner?: string;
    llm_model?: string;
    instruction_type?: string;
  }>;
  loadingTeammateIds: Set<string>;
  loadTeammateCapabilities: (teammateId: string) => Promise<void>;
  switchThread: () => void;
  setTeammateState: (teammateId: string, state: TeammateState) => void;
  handleSubmit: (message: string) => Promise<void>;
  setSelectedTeammate: (teammateId: string | undefined) => void;
}

export const TeammateContext = createContext<TeammateContextType>({
  selectedTeammate: undefined,
  currentState: null,
  teammates: [],
  teammateCapabilities: {},
  loadingTeammateIds: new Set(),
  loadTeammateCapabilities: async () => {},
  switchThread: () => {},
  setTeammateState: () => {},
  handleSubmit: async () => {},
  setSelectedTeammate: () => {}
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
  let currentMessageText = '';
  let currentMessageId = `msg_${Date.now()}`;
  let currentToolId = `tool_${Date.now()}`;

  console.log('[SSE] Starting event stream processing');

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        console.log('[SSE] Stream done');
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.trim()) continue;
        
        try {
          // Handle data: prefix
          const content = line.startsWith('data: ') ? line.slice(6) : line;
          console.log('[SSE] Raw event:', content);

          if (content === '[DONE]') {
            console.log('[SSE] Received [DONE] event');
            // Yield any remaining message content
            if (currentMessageText.trim()) {
              yield {
                content: [{ type: "text", text: currentMessageText } as TextContent],
                role: 'assistant',
                id: currentMessageId
              };
            }
            break;
          }

          try {
            // Try to parse as JSON first
            const event = JSON.parse(content);
            console.log('[SSE] Parsed event:', { 
              type: event.type, 
              id: event.id, 
              messageLength: event.message?.length,
              toolName: event.tool_name,
              hasArgs: !!event.arguments
            });

            if (event.type === 'system_message' && event.message) {
              const text = event.message.trim();
              if (text && !systemMessages.has(text)) {
                console.log('[SSE] Processing system message:', { text });
                systemMessages.add(text);
                yield {
                  content: [{ type: "text", text } as TextContent],
                  role: 'system',
                  id: event.id || `system_${Date.now()}_${systemMessages.size}`
                };
              }
              continue;
            }

            // Handle tool events
            if (event.type === 'tool') {
              console.log('[SSE] Processing tool event:', { 
                toolName: event.tool_name,
                hasArgs: !!event.arguments,
                messageLength: event.message?.length,
                rawEvent: event
              });
              
              const toolId = event.id || currentToolId;
              let toolName = event.tool_name;
              let args = event.arguments;
              
              if (!toolName && event.message) {
                const toolMatch = event.message.match(/Tool:\s*(\w+)(?:\s*\n|\s+)Arguments:\s*({[\s\S]*})/i);
                if (toolMatch) {
                  try {
                    toolName = toolMatch[1];
                    args = JSON.parse(toolMatch[2]);
                    console.log('[SSE] Extracted tool info from message:', { toolName, hasArgs: !!args });
                  } catch (e) {
                    console.warn('[SSE] Failed to parse tool arguments:', e);
                  }
                }
              }

              if (toolName) {
                // Reset current message text as we're switching to tool output
                if (currentMessageText.trim()) {
                  yield {
                    content: [{ type: "text", text: currentMessageText } as TextContent],
                    role: 'assistant',
                    id: currentMessageId
                  };
                  currentMessageText = '';
                  currentMessageId = `msg_${Date.now()}`;
                }

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
              console.log('[SSE] Processing tool output:', { 
                id: event.id || currentToolId,
                messageLength: event.message?.length,
                rawEvent: event
              });
              
              // Reset current message text as we're switching to tool output
              if (currentMessageText.trim()) {
                yield {
                  content: [{ type: "text", text: currentMessageText } as TextContent],
                  role: 'assistant',
                  id: currentMessageId
                };
                currentMessageText = '';
                currentMessageId = `msg_${Date.now()}`;
              }

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
              console.log('[SSE] Processing message chunk:', { 
                type: event.type,
                messageLength: event.message.length,
                id: event.id || currentMessageId
              });
              
              // If we have a new message ID, yield current content and reset
              if (event.id && event.id !== currentMessageId && currentMessageText.trim()) {
                yield {
                  content: [{ type: "text", text: currentMessageText } as TextContent],
                  role: 'assistant',
                  id: currentMessageId
                };
                currentMessageText = '';
                currentMessageId = event.id;
              }

              // Append new content and yield immediately
              currentMessageText += event.message;
              yield {
                content: [{ type: "text", text: currentMessageText } as TextContent],
                role: 'assistant',
                id: currentMessageId
              };
            }
          } catch (parseError) {
            console.warn('[SSE] JSON parse error:', parseError);
            
            // If JSON parsing fails, check for system message patterns
            if (content.includes('WARNING:') || content.includes('ERROR:')) {
              const text = content.replace(/^(WARNING:|ERROR:)\s*/, '').trim();
              if (text && !systemMessages.has(text)) {
                console.log('[SSE] Processing plain text system message:', { text });
                systemMessages.add(text);
                yield {
                  content: [{ type: "text", text } as TextContent],
                  role: 'system',
                  id: `system_${Date.now()}_${systemMessages.size}`
                };
              }
            } else if (!content.startsWith('{') && !content.startsWith('[')) {
              console.log('[SSE] Processing plain text chunk:', { 
                contentLength: content.length,
                content: content.substring(0, 100) + '...' // Log first 100 chars
              });
              
              // Append and yield immediately for plain text
              currentMessageText += content;
              yield {
                content: [{ type: "text", text: currentMessageText } as TextContent],
                role: 'assistant',
                id: currentMessageId
              };
            }
          }
        } catch (e) {
          console.error('[SSE] Error processing message:', e);
        }
      }
    }
  } finally {
    console.log('[SSE] Stream ended, releasing reader lock');
    reader.releaseLock();
  }
};

interface ThreadState {
  messages: any[];
  lastMessageId?: string;
  metadata: {
    teammateId: string;
    createdAt: string;
    updatedAt: string;
    title?: string;
    activeTool?: string;
  };
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

// Initialize empty thread state
const createEmptyThread = (teammateId: string): ThreadState => ({
  messages: [],
  metadata: {
    teammateId,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  }
});

// Initialize empty teammate state
const createEmptyTeammateState = (teammateId: string): TeammateState => {
  const threadId = Date.now().toString();
  return {
    sessions: [],
    currentThreadId: threadId,
    currentSessionId: threadId,
    threads: {
      [threadId]: createEmptyThread(teammateId)
    }
  };
};

// Create custom hook for runtime
const useAssistantRuntime = (adapter: ChatModelAdapter) => {
  return useLocalRuntime(adapter);
};

export const MyRuntimeProvider = ({ children }: { children: ReactNode }) => {
  const [teammateCapabilities, setTeammateCapabilities] = useState<TeammateContextType['teammateCapabilities']>({});
  const [loadingTeammateIds, setLoadingTeammateIds] = useState<Set<string>>(new Set());

  // 1. All useContext hooks first (these don't depend on state)
  const { user, isLoading: isUserLoading } = useUser();
  const { apiKey, authType } = useConfig();
  const router = useRouter();

  // 2. All useState hooks with proper initialization
  const [mounted, setMounted] = useState(false);
  const [teammates, setTeammates] = useState<any[]>([]);
  const [selectedTeammate, setSelectedTeammate] = useState<string | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isCollectingSystemMessages, setIsCollectingSystemMessages] = useState(false);
  const [teammateStates, setTeammateStates] = useState<TeammateStates>(() => {
    // Load all teammate states from localStorage on initialization
    if (typeof window === 'undefined') return {};
    
    const states: TeammateStates = {};
    for (const key of Object.keys(localStorage)) {
      if (key.startsWith('teammate_state_')) {
        const teammateId = key.replace('teammate_state_', '');
        try {
          const storedState = localStorage.getItem(key);
          if (storedState) {
            states[teammateId] = JSON.parse(storedState);
          }
        } catch (error) {
          console.error(`Error loading state for teammate ${teammateId}:`, error);
        }
      }
    }
    return states;
  });

  // Add new state for session expired
  const [isSessionExpired, setIsSessionExpired] = useState(false);

  // 3. All callbacks with safe state access
  const setTeammateState = useCallback((teammateId: string, state: TeammateState) => {
    if (!teammateId) return;
    setTeammateStates(prev => ({
      ...prev,
      [teammateId]: state
    }));
    localStorage.setItem(`teammate_state_${teammateId}`, JSON.stringify(state));
  }, []);

  const switchThread = useCallback(() => {
    if (!selectedTeammate) return;
    setTeammateStates(prev => {
      const currentState = prev[selectedTeammate] || createEmptyTeammateState(selectedTeammate);
      const updatedState = {
        ...currentState,
        currentThreadId: Date.now().toString(),
        currentSessionId: Date.now().toString(),
        threads: {
          ...currentState.threads,
          [Date.now().toString()]: currentState.threads[currentState.currentThreadId] || createEmptyThread(selectedTeammate)
        }
      };

      localStorage.setItem(`teammate_state_${selectedTeammate}`, JSON.stringify(updatedState));
      return {
        ...prev,
        [selectedTeammate]: updatedState
      };
    });
  }, [selectedTeammate]);

  const handleTeammateSelect = useCallback((teammateId: string) => {
    if (!teammateId) return;
    setSelectedTeammate(teammateId);
    
    setTeammateStates(prev => {
      if (prev[teammateId]) return prev;
      return {
        ...prev,
        [teammateId]: createEmptyTeammateState(teammateId)
      };
    });
  }, []);

  // Optimize teammate loading by moving it to a separate function
  const loadTeammates = useCallback(async () => {
    if (!user) return;
    try {
      console.log('Loading teammates for user:', user.email);
      const response = await fetch('/api/teammates', {
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });

      if (response.status === 401) {
        setIsSessionExpired(true);
        return;
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('Failed to load teammates:', {
          status: response.status,
          statusText: response.statusText,
          error: errorData
        });
        throw new Error(`Failed to load teammates: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Successfully loaded teammates:', {
        count: data.length,
        firstTeammate: data[0]
      });
      setTeammates(data);
    } catch (error) {
      console.error('Error loading teammates:', error);
      setError(error);
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  // Optimize initial loading by reducing state updates
  useEffect(() => {
    setMounted(true);
    
    // Load teammates only if we have a user
    if (user) {
      loadTeammates();
    } else {
      setIsLoading(false);
    }
  }, [user, loadTeammates]);

  // Modify the loadTeammateCapabilities to handle 401s
  const loadTeammateCapabilities = useCallback(async (teammateId: string) => {
    if (teammateCapabilities[teammateId] || isSessionExpired) return;

    setLoadingTeammateIds((prev) => new Set([...prev, teammateId]));
    try {
      // Fetch capabilities and integrations in parallel
      const [capabilitiesRes, integrationsRes] = await Promise.all([
        fetch(`/api/teammates/${teammateId}/capabilities`),
        fetch(`/api/teammates/${teammateId}/integrations`)
      ]);

      if (capabilitiesRes.status === 401 || integrationsRes.status === 401) {
        setIsSessionExpired(true);
        return;
      }

      if (!capabilitiesRes.ok) throw new Error('Failed to fetch teammate capabilities');
      if (!integrationsRes.ok) throw new Error('Failed to fetch teammate integrations');

      const capabilities = await capabilitiesRes.json();
      const integrations = await integrationsRes.json();

      setTeammateCapabilities((prev) => ({
        ...prev,
        [teammateId]: {
          tools: capabilities.tools || [],
          integrations: integrations || [],
          description: capabilities.description,
          runner: capabilities.runner,
          llm_model: capabilities.llm_model,
          instruction_type: capabilities.instruction_type
        }
      }));
    } catch (error) {
      console.error('Error loading capabilities:', error);
      toast({
        title: 'Error loading capabilities',
        description: 'Failed to load teammate capabilities. Please try again.',
      });
    } finally {
      setLoadingTeammateIds((prev) => {
        const next = new Set(prev);
        next.delete(teammateId);
        return next;
      });
    }
  }, [teammateCapabilities, isSessionExpired]);

  // Modify the adapter to handle 401s
  const adapter = useMemo<ChatModelAdapter>(() => ({
    async *run(options: ChatModelRunOptions): AsyncGenerator<MessageContent, void, unknown> {
      const customConfig = {
        ...options.config,
        teammate: selectedTeammate || '',
        threadId: teammateStates[selectedTeammate || '']?.currentThreadId || Date.now().toString(),
        sessionId: teammateStates[selectedTeammate || '']?.currentSessionId || Date.now().toString()
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
          messages: options.messages || [], 
          abortSignal: options.abortSignal, 
          config: customConfig,
          apiKey: apiKey || '',
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

        for await (const message of handleStreamEvents(stream)) {
          yield message;
        }
      } catch (error) {
        if (error instanceof Error && error.message.includes('Session expired')) {
          setIsSessionExpired(true);
          return;
        }
        
        yield {
          content: [{ type: "text", text: error instanceof Error ? error.message : "An error occurred" } as TextContent],
          role: 'system',
          id: `system_${Date.now()}`
        };
      }
    }
  }), [selectedTeammate, teammateStates, apiKey, router]);

  // 5. Create runtime using custom hook
  const runtime = useAssistantRuntime(adapter);

  // 6. Derived state with useMemo
  const currentState = useMemo(() => {
    if (!selectedTeammate) return undefined;
    const state = teammateStates[selectedTeammate];
    if (!state) {
      const newState = createEmptyTeammateState(selectedTeammate);
      setTeammateStates(prev => ({
        ...prev,
        [selectedTeammate]: newState
      }));
      return newState;
    }
    return state;
  }, [selectedTeammate, teammateStates]);

  // 7. Message submission handler with proper state preservation
  const handleSubmit = useCallback(async (message: string) => {
    if (!selectedTeammate || !currentState?.currentThreadId) {
      setError('Please select a teammate first');
      return;
    }

    if (isProcessing) return;

    setError(null);
    setIsProcessing(true);
    setIsCollectingSystemMessages(true);
    
    try {
      const threadId = currentState.currentThreadId;
      
      // Get current thread state
      const currentThread = currentState.threads[threadId] || createEmptyThread(selectedTeammate);

      // Create user message
      const userMessage = {
        id: `user_${Date.now()}`,
        role: 'user',
        content: [{ type: 'text', text: message }],
        createdAt: new Date()
      };

      // Update state atomically with user message
      setTeammateStates(prev => {
        const updatedThread = {
          ...currentThread,
          messages: [...(currentThread.messages || []), userMessage],
          metadata: {
            ...currentThread.metadata,
            updatedAt: new Date().toISOString()
          }
        };

        const updatedState = {
          ...prev[selectedTeammate],
          threads: {
            ...prev[selectedTeammate].threads,
            [threadId]: updatedThread
          }
        };

        // Store in localStorage
        localStorage.setItem(`teammate_state_${selectedTeammate}`, JSON.stringify(updatedState));

        return {
          ...prev,
          [selectedTeammate]: updatedState
        };
      });
      
      // Send message to backend
      const response = await fetch(`/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          agent_uuid: selectedTeammate,
          session_id: currentState.currentSessionId || threadId
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.details || errorData.error || 'Failed to send message');
      }

      // Handle the streaming response
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response stream available');
      }

      let collectedSystemMessages: string[] = [];

      // Read the stream
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          // Process the chunks
          const text = new TextDecoder().decode(value);
          const lines = text.split('\n');
          
          for (const line of lines) {
            if (!line.trim() || !line.startsWith('data: ')) continue;
            
            try {
              const eventData = JSON.parse(line.slice(6));
              console.log('[Chat] Processing event:', eventData);
              
              // Update state atomically with new message
              setTeammateStates(prev => {
                const currentThread = prev[selectedTeammate].threads[threadId];
                if (!currentThread) return prev;

                let newMessage = null;

                // Create new message based on event type
                switch (eventData.type) {
                  case 'system_message':
                    if (eventData.message) {
                      newMessage = {
                        id: `system_${Date.now()}`,
                        role: 'system',
                        content: [{ type: 'text', text: eventData.message }],
                        createdAt: new Date(),
                        metadata: { custom: { isSystemMessage: true } }
                      };
                      collectedSystemMessages = [...collectedSystemMessages, eventData.message];
                    }
                    break;
                  case 'msg':
                  case 'assistant':
                    if (eventData.message) {
                      newMessage = {
                        id: eventData.id || `assistant_${Date.now()}`,
                        role: 'assistant',
                        content: [{ type: 'text', text: eventData.message }],
                        createdAt: new Date()
                      };
                    }
                    break;
                  case 'tool':
                    if (eventData.tool_name) {
                      newMessage = {
                        id: eventData.id || `tool_${Date.now()}`,
                        role: 'assistant',
                        content: [],
                        tool_calls: [{
                          type: 'tool_init',
                          id: eventData.id || `tool_${Date.now()}`,
                          name: eventData.tool_name,
                          arguments: eventData.arguments,
                          timestamp: new Date().toISOString()
                        }],
                        createdAt: new Date()
                      };
                    }
                    break;
                  case 'tool_output':
                    if (eventData.message) {
                      newMessage = {
                        id: eventData.id || `tool_output_${Date.now()}`,
                        role: 'assistant',
                        content: [],
                        tool_calls: [{
                          type: 'tool_output',
                          id: eventData.id || `tool_output_${Date.now()}`,
                          message: eventData.message,
                          timestamp: new Date().toISOString()
                        }],
                        createdAt: new Date()
                      };
                    }
                    break;
                }

                if (!newMessage) return prev;

                const updatedThread = {
                  ...currentThread,
                  messages: [...(currentThread.messages || []), newMessage],
                  metadata: {
                    ...currentThread.metadata,
                    updatedAt: new Date().toISOString()
                  }
                };

                const updatedState = {
                  ...prev[selectedTeammate],
                  threads: {
                    ...prev[selectedTeammate].threads,
                    [threadId]: updatedThread
                  }
                };

                // Store in localStorage
                localStorage.setItem(`teammate_state_${selectedTeammate}`, JSON.stringify(updatedState));

                return {
                  ...prev,
                  [selectedTeammate]: updatedState
                };
              });

            } catch (e) {
              console.error('Failed to parse SSE message:', e);
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
      
    } catch (error) {
      console.error('Error sending message:', error);
      setError(error instanceof Error ? error.message : 'Failed to send message. Please try again.');
    } finally {
      setIsProcessing(false);
      setIsCollectingSystemMessages(false);
    }
  }, [selectedTeammate, currentState, isProcessing, setTeammateStates]);

  // Show session expired page if session is expired
  if (isSessionExpired) {
    return <SessionExpired />;
  }

  // Optimize loading state by showing a simpler loading indicator
  if (!mounted || isUserLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[#7C3AED] border-t-transparent"></div>
      </div>
    );
  }

  if (!apiKey || !authType || !user) {
    return <ApiKeySetup />;
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[#7C3AED] border-t-transparent"></div>
      </div>
    );
  }

  // 10. Context value with all required props
  const contextValue: TeammateContextType = {
    selectedTeammate: selectedTeammate || undefined,
    currentState: currentState || null,
    teammates,
    teammateCapabilities,
    loadingTeammateIds,
    loadTeammateCapabilities,
    switchThread,
    setTeammateState,
    handleSubmit,
    setSelectedTeammate
  };

  return (
    <TeammateContext.Provider value={contextValue}>
      <AssistantRuntimeProvider runtime={runtime}>
        <ToolProvider />
        {children}
      </AssistantRuntimeProvider>
    </TeammateContext.Provider>
  );
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

        // Update thread state with new messages
        for await (const message of handleStreamEvents(stream)) {
          if (setTeammateState && teammateState) {
            setTeammateState({
              ...teammateState,
              threads: {
                ...teammateState.threads,
                [customConfig.threadId]: {
                  messages: [...(teammateState.threads[customConfig.threadId]?.messages || []), message],
                  lastMessageId: message.id,
                  metadata: {
                    ...teammateState.threads[customConfig.threadId]?.metadata,
                    updatedAt: new Date().toISOString()
                  }
                }
              }
            });
          }
          yield message;
        }
      } catch (error) {
        if (error instanceof Error && error.message.includes('Session expired')) {
          throw error;
        }
        
        yield {
          content: [{ type: "text", text: error instanceof Error ? error.message : "An error occurred" } as TextContent],
          role: 'system',
          id: `system_${Date.now()}`
        };
      }
    }
  }), [config, token, router, setTeammateState, teammateState]);

  return useLocalRuntime(adapter);
};
