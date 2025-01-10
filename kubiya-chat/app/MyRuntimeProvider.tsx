"use client";

import React, { useState, useEffect, type ReactNode, useMemo, useCallback } from "react";
import Image from "next/image";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
  type ModelConfig,
  type LocalRuntimeOptions,
  type ChatModelRunOptions,
} from "@assistant-ui/react";
import { getKubiyaConfig } from "./config";
import { ToolUI } from "./components/ToolUI";
import { Search } from 'lucide-react';

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

interface AgentData {
  uuid: string;
  name: string;
  description?: string;
  is_debug_mode?: boolean;
}

interface Tool {
  name: string;
  description: string;
  type: string;
  sourceId: string;
  icon_url?: string;
  metadata?: {
    arguments?: {
      name: string;
      type: string;
      description: string;
      required: boolean;
    }[];
    returns?: {
      type: string;
      description: string;
    };
    examples?: string[];
    files?: string[];
    image?: string;
    version?: string;
  };
}

interface Session {
  id: string;
  title?: string;
}

interface SourceMetadata {
  id: string;
  name: string;
  url: string;
  uuid: string;
  runner: string;
  description?: string;
  icon?: string;
  tools: Tool[];
  source_meta?: {
    id: string;
    url: string;
    commit: string;
    committer: string;
    branch: string;
  };
  kubiya_metadata?: {
    created_at: string;
    last_updated: string;
    user_created: string;
    user_last_updated: string;
  };
}

interface SourceInfo {
  uuid: string;
  name?: string;
  description?: string;
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

// First, create a proper interface for the runtime
interface RuntimeWithConfig {
  config?: TeammateConfig;
  [key: string]: unknown;
}

interface SourceTools {
  sourceId: string;
  sourceName?: string;
  icon: string;
  url: string;
  runner: string;
  tools: Tool[];
  metadata?: {
    kubiya_metadata?: {
      created_at: string;
      last_updated: string;
      user_created: string;
      user_last_updated: string;
    };
  };
}

interface Starter {
  command: string;
  display_name: string;
}

interface StreamEvent {
  type: string;
  message?: string;
  content?: string;
  id?: string;
  session_id?: string;
  name?: string;
}

const formatName = (name: string | undefined) => {
  if (!name) return '';
  return name
    .split(/[_-]/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
};

const getDefaultToolIcon = (type: string) => {
  switch (type?.toLowerCase()) {
    case 'kubernetes':
      return '⎈';
    case 'aws':
      return '☁️';
    case 'gcp':
      return '☁️';
    case 'azure':
      return '☁️';
    case 'docker':
      return '🐳';
    case 'git':
      return '📦';
    case 'database':
      return '🗄️';
    case 'monitoring':
      return '📊';
    case 'security':
      return '🔒';
    case 'network':
      return '🌐';
    case 'storage':
      return '💾';
    case 'compute':
      return '💻';
    case 'automation':
      return '🤖';
    default:
      return '🛠️';
  }
};

const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>, type: string) => {
  const target = e.target as HTMLImageElement;
  const parentNode = target.parentNode;
  if (parentNode) {
    const span = document.createElement('span');
    span.className = 'text-xl select-none';
    span.setAttribute('role', 'img');
    span.textContent = getDefaultToolIcon(type);
    parentNode.replaceChild(span, target);
  }
};

function ToolRegistrationWrapper({ children }: { children: ReactNode }) {
  return <ToolUI>{children}</ToolUI>;
}

const getSourceIcon = (source: SourceMetadata): string => {
  // If source has an icon, use it
  if (source.icon) return source.icon;

  // Default icons based on source type/name
  if (!source.name) return '📦';
  
  const sourceNameLower = source.name.toLowerCase();
  if (sourceNameLower.includes('aws')) return '☁️';
  if (sourceNameLower.includes('kubernetes') || sourceNameLower.includes('k8s')) return '⚓️';
  if (sourceNameLower.includes('github')) return '📝';
  if (sourceNameLower.includes('docker')) return '🐳';
  if (sourceNameLower.includes('terraform')) return '🏗️';
  if (sourceNameLower.includes('jira')) return '📋';
  if (sourceNameLower.includes('slack')) return '💬';
  if (sourceNameLower.includes('git')) return '📝';
  if (sourceNameLower.includes('jenkins')) return '🔧';
  if (sourceNameLower.includes('database')) return '💾';
  if (sourceNameLower.includes('monitoring')) return '📊';
  if (sourceNameLower.includes('security')) return '🔒';
  return '🧰';
};

const groupToolsBySource = (tools: Tool[], sources: SourceMetadata[]): SourceTools[] => {
  // First, create a map of tools by sourceId
  const toolsBySource = tools.reduce((acc, tool) => {
    const sourceId = tool.sourceId;
    if (!acc[sourceId]) {
      acc[sourceId] = [];
    }
    acc[sourceId].push(tool);
    return acc;
  }, {} as Record<string, Tool[]>);

  // Then map sources to SourceTools format
  const groupedTools = sources
    .map(source => {
      const sourceTools = toolsBySource[source.id] || toolsBySource[source.uuid] || [];
      if (sourceTools.length === 0) return null;

      const sourceGroup: SourceTools = {
        sourceId: source.id || source.uuid,
        sourceName: source.name,
        icon: getSourceIcon(source),
        url: source.url || '',
        runner: source.runner || '',
        tools: sourceTools,
        metadata: source.kubiya_metadata ? {
          kubiya_metadata: source.kubiya_metadata
        } : undefined
      };
      return sourceGroup;
    })
    .filter((group): group is SourceTools => group !== null);

  return groupedTools;
};

const createKubiyaModelAdapter = (
  selectedTeammate: string | undefined,
): ChatModelAdapter => ({
  async *run(options: ChatModelRunOptionsWithSessions) {
    const kubiyaConfig = getKubiyaConfig();
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
          session_id: sessionId // Always include session ID
        };

        console.log('Sending conversation request:', {
          url: '/api/converse',
          payload,
          apiKey: kubiyaConfig.apiKey ? 'present' : 'missing',
          sessionId,
          retryAttempt: retryCount + 1
        });

        const response = await fetch('/api/converse', {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
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

        console.log('Starting to read SSE stream...');

        let currentEvent: StreamEvent | undefined;

        try {
          while (!aborted) {
            // Check for timeout
            if (Date.now() - lastActivityTime > TIMEOUT_MS) {
              console.log('Stream timeout - no activity for 30 seconds');
              break;
            }

            const { done, value } = await reader.read();
            
            if (done) {
              console.log('SSE stream complete');
              break;
            }

            // Reset activity timer
            lastActivityTime = Date.now();

            const chunk = decoder.decode(value, { stream: true });
            console.log('Raw chunk received:', {
              chunk,
              chunkLength: chunk.length,
              timestamp: new Date().toISOString()
            });

            buffer += chunk;
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (!line.trim()) continue;

              try {
                currentEvent = JSON.parse(line) as StreamEvent;
                console.log('Processing event:', {
                  type: currentEvent.type,
                  content: currentEvent.content || currentEvent.message,
                  messageId: currentEvent.id,
                  timestamp: new Date().toISOString()
                });

                // Handle session initialization
                if (currentEvent.type === 'session_init' && currentEvent.session_id) {
                  console.log('Storing session ID:', currentEvent.session_id);
                  localStorage.setItem(`chat_session_${selectedTeammate}`, currentEvent.session_id);
                  continue;
                }

                // Handle different message types
                if (currentEvent.type === 'assistant' || currentEvent.type === 'msg') {
                  const messageText = currentEvent.message || currentEvent.content || '';
                  const isComplete = messageText.endsWith('?');
                  
                  yield {
                    content: [{
                      type: "text",
                      text: messageText,
                    }],
                  };

                  if (isComplete) {
                    console.log('Message complete, ending stream');
                    break;
                  }
                } else if (currentEvent.type === 'tool' || currentEvent.type === 'tool_output') {
                  const toolContent = currentEvent.content || currentEvent.message;
                  const toolName = currentEvent.name || 'unknown';
                  
                  console.log('Tool event:', {
                    type: currentEvent.type,
                    name: toolName,
                    content: toolContent,
                    timestamp: new Date().toISOString()
                  });

                  if (currentEvent.type === 'tool') {
                    // Tool execution started
                    yield {
                      content: [],
                      tool_calls: [{
                        type: 'tool_preview',
                        name: toolName,
                        content: toolContent,
                        status: { type: 'running' }
                      }]
                    };
                  } else {
                    // Tool execution completed
                    yield {
                      content: [],
                      tool_calls: [{
                        type: 'tool_output',
                        name: toolName,
                        content: toolContent,
                        status: { type: 'complete' }
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
                console.error("Failed to parse or process event:", {
                  error: e,
                  line,
                  timestamp: new Date().toISOString()
                });
                
                if (e instanceof Error && e.message.startsWith('ERROR:')) {
                  throw e;
                }
              }
            }
          }
        } catch (streamError) {
          console.error("Stream error:", streamError);
          throw streamError;
        } finally {
          aborted = true;
          reader.releaseLock();
          controller.abort();
        }

        if (!aborted) {
          // Only break if we've received a complete message
          if (currentEvent?.type === 'msg' && (currentEvent.message?.endsWith('?') || currentEvent.content?.endsWith('?'))) {
            console.log('Message complete, ending stream');
            break;
          }
          yield {
            content: [{
              type: "text",
              text: currentEvent?.message || currentEvent?.content || '',
            }],
          };
        } else {
          console.log('Stream aborted');
          break;
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

// Update the custom hook to properly handle runtime creation
function useKubiyaRuntime(
  selectedTeammate: string | undefined,
  sessions: Session[],
  setSessions: React.Dispatch<React.SetStateAction<Session[]>>
) {
  // Create the runtime configuration first
  const runtimeConfig = useMemo<TeammateConfig>(() => ({
    teammate: selectedTeammate || '',
  }), [selectedTeammate]);

  // Create the runtime options with the config
  const runtimeOptions = useMemo<CustomRuntimeOptions>(() => ({
    config: runtimeConfig,
    sessions,
    setSessions,
  }), [runtimeConfig, sessions, setSessions]);

  // Create the adapter with proper teammate
  const modelAdapter = useMemo(
    () => createKubiyaModelAdapter(selectedTeammate),
    [selectedTeammate]
  );

  // Create the runtime with proper options
  const runtime = useLocalRuntime(modelAdapter, runtimeOptions);

  // Log runtime creation for debugging
  useEffect(() => {
    console.log('Runtime creation:', {
      selectedTeammate,
      runtimeConfig,
      runtimeOptions,
      hasSessions: sessions.length > 0,
      hasTeammate: !!selectedTeammate,
      hasRuntime: !!runtime,
      modelAdapter: !!modelAdapter,
    });
  }, [selectedTeammate, runtimeConfig, runtimeOptions, sessions, runtime, modelAdapter]);

  return selectedTeammate ? runtime : null;
}

export default function MyRuntimeProvider({ children }: { children: ReactNode }) {
  const [teammates, setTeammates] = useState<Teammate[]>([]);
  const [selectedTeammate, setSelectedTeammate] = useState<string>();
  const [error, setError] = useState<string>();
  const [isLoading, setIsLoading] = useState(true);
  const [tools, setTools] = useState<Tool[]>([]);
  const [starters, setStarters] = useState<Starter[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [sourcesData, setSourcesData] = useState<SourceMetadata[]>([]);
  const [isToolsModalOpen, setIsToolsModalOpen] = useState(false);
  const toolsPerPage = 5;
  const [searchQuery, setSearchQuery] = useState('');

  // Use the custom hook to manage runtime
  const runtime = useKubiyaRuntime(selectedTeammate, sessions, setSessions);

  // Add debug logging
  useEffect(() => {
    console.log('Runtime state:', {
      selectedTeammate,
      hasRuntime: !!runtime,
      runtimeConfig: runtime ? (runtime as unknown as RuntimeWithConfig).config : null,
      sessions,
    });
  }, [selectedTeammate, runtime, sessions]);

  useEffect(() => {
    const fetchTeammates = async () => {
      setIsLoading(true);
      const config = getKubiyaConfig();
      try {
        console.log('Fetching teammates...');
        const response = await fetch(`${config.baseUrl}/agents?mode=all`, {
          headers: {
            "Content-Type": "application/json",
            "Authorization": `UserKey ${config.apiKey}`,
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch teammates: ${response.statusText}`);
        }

        const data = await response.json();
        console.log('Received teammates data:', data);

        const validTeammates = data
          .filter((agent: AgentData) => agent.uuid && agent.name)
          .map((agent: AgentData) => ({
            id: agent.uuid,
            name: agent.name,
            description: agent.description || '',
            uuid: agent.uuid,
          }));

        console.log('Valid teammates:', validTeammates);
        setTeammates(validTeammates);

        // Initialize teammate selection
        const storedTeammate = localStorage.getItem('selectedTeammate');
        const validStoredTeammate = storedTeammate && validTeammates.some((t: Teammate) => t.id === storedTeammate);
        
        if (validStoredTeammate) {
          console.log('Restoring stored teammate:', storedTeammate);
          setSelectedTeammate(storedTeammate);
          // Load stored sessions
          const storedSessions = localStorage.getItem(`sessions_${storedTeammate}`);
          if (storedSessions) {
            setSessions(JSON.parse(storedSessions));
          }
        } else if (validTeammates.length > 0) {
          console.log('Setting first teammate:', validTeammates[0].id);
          setSelectedTeammate(validTeammates[0].id);
          localStorage.setItem('selectedTeammate', validTeammates[0].id);
          setSessions([]); // Reset sessions for new teammate
        }
      } catch (err) {
        console.error("Failed to fetch teammates:", err);
        setError(err instanceof Error ? err.message : "Failed to fetch teammates");
      } finally {
        setIsLoading(false);
      }
    };

    fetchTeammates();
  }, []);

  // Add an effect to handle teammate selection changes
  useEffect(() => {
    console.log('Selected teammate changed:', selectedTeammate);
    if (selectedTeammate) {
      localStorage.setItem('selectedTeammate', selectedTeammate);
    }
  }, [selectedTeammate]);

  useEffect(() => {
    if (selectedTeammate) {
      console.log('Selected teammate changed:', selectedTeammate);
      // Load sessions from localStorage
      const storedSessions = localStorage.getItem(`sessions_${selectedTeammate}`);
      if (storedSessions) {
        setSessions(JSON.parse(storedSessions));
      }

      const fetchTeammateData = async () => {
        const config = getKubiyaConfig();
        console.log('Fetching teammate data for:', selectedTeammate);
        try {
          // First fetch teammate metadata
          const response = await fetch(`${config.baseUrl}/agents/${selectedTeammate}`, {
            headers: {
              "Content-Type": "application/json",
              "Authorization": `UserKey ${config.apiKey}`,
            },
          });

          if (!response.ok) throw new Error("Failed to fetch teammate metadata");
          const metadata = await response.json();
          console.log('Received teammate metadata:', metadata);

          setStarters(metadata.starters || []);
          
          // Then fetch all sources
          const sourcesResponse = await fetch(`${config.baseUrl}/sources`, {
            headers: {
              "Content-Type": "application/json",
              "Authorization": `UserKey ${config.apiKey}`,
            },
          });
          
          if (!sourcesResponse.ok) throw new Error("Failed to fetch sources");
          const allSources = await sourcesResponse.json();
          console.log('Fetched all sources:', allSources);
          
          // Filter and fetch tools only for sources that belong to this teammate
          if (metadata.sources && metadata.sources.length > 0) {
            console.log('Teammate sources:', metadata.sources);
            
            const sourcesPromises = metadata.sources
              .map((sourceId: string) => {
                const sourceInfo = allSources.find((s: SourceInfo) => s.uuid === sourceId);
                if (!sourceInfo) {
                  console.log('Source not found:', sourceId);
                  return null;
                }
                
                console.log('Fetching tools for source:', sourceInfo.name || sourceId);
                return fetch(`${config.baseUrl}/sources/${sourceId}/metadata`, {
                  headers: {
                    "Content-Type": "application/json",
                    "Authorization": `UserKey ${config.apiKey}`,
                  },
                })
                .then(res => {
                  if (!res.ok) throw new Error(`Failed to fetch source metadata for ${sourceId}`);
                  return res.json();
                })
                .then(sourceData => {
                  console.log('Received source data:', sourceData);
                  return {
                    ...sourceData,
                    id: sourceId, // Make sure we set the id properly
                    name: sourceInfo.name || sourceData.name,
                    description: sourceInfo.description || sourceData.description,
                    uuid: sourceId,
                    tools: sourceData.tools?.map((tool: Tool) => ({
                      ...tool,
                      sourceId: sourceId
                    })) || []
                  };
                })
                .catch(error => {
                  console.error(`Error fetching source ${sourceId}:`, error);
                  return null;
                });
              })
              .filter(Boolean);

            const sourcesData = await Promise.all(sourcesPromises);
            const validSourcesData = sourcesData.filter((source): source is SourceMetadata => source !== null);
            console.log('Fetched sources data:', validSourcesData);
            
            setSourcesData(validSourcesData);

            const allTools = validSourcesData.flatMap((source: SourceMetadata) => 
              (source.tools || []).map(tool => ({
                ...tool,
                sourceId: source.id || source.uuid
              }))
            );
            
            console.log('Processed tools:', allTools);
            setTools(allTools);
          } else {
            console.log('No sources found for teammate');
            setTools([]);
            setSourcesData([]);
          }
        } catch (err) {
          console.error("Failed to fetch teammate data:", err);
          setTools([]);
          setSourcesData([]);
        }
      };

      fetchTeammateData();
    }
  }, [selectedTeammate]);

  const handleTeammateSelect = useCallback((teammate: Teammate) => {
    console.log('Selecting teammate:', teammate);
    setSelectedTeammate(teammate.id);
    localStorage.setItem('selectedTeammate', teammate.id);
    
    const storedSessions = localStorage.getItem(`sessions_${teammate.id}`);
    if (storedSessions) {
      setSessions(JSON.parse(storedSessions));
    } else {
      setSessions([]);
    }
  }, [setSessions]);

  const handleNewThread = useCallback(() => {
    if (selectedTeammate) {
      // Clear the current session ID
      localStorage.removeItem(`chat_session_${selectedTeammate}`);
      
      // Create a new session using UnixNano format (exactly matching Go's implementation)
      const timestamp = BigInt(Date.now()) * BigInt(1000000); // Convert to nanoseconds
      const newSessionId = timestamp.toString();
      const newSession = { id: newSessionId, title: 'New Thread' };
      const updatedSessions = [newSession, ...sessions].slice(0, 5);
      setSessions(updatedSessions);
      localStorage.setItem(`sessions_${selectedTeammate}`, JSON.stringify(updatedSessions));
      
      // Force a re-render of the chat by clearing and setting the teammate
      const currentTeammate = selectedTeammate;
      setSelectedTeammate(undefined);
      setTimeout(() => setSelectedTeammate(currentTeammate), 0);
    }
  }, [selectedTeammate, sessions]);

  // Add debug logging for the modal
  useEffect(() => {
    if (isToolsModalOpen) {
      console.log('Modal opened with:', {
        tools: tools.length,
        sources: sourcesData.length,
        groupedTools: groupToolsBySource(tools, sourcesData)
      });
    }
  }, [isToolsModalOpen, tools, sourcesData]);

  const filteredTeammates = teammates.filter(teammate => 
    teammate.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    teammate.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0A0F1E]">
        <div className="w-full max-w-md space-y-4 rounded-xl bg-[#1E293B] p-8 shadow-lg">
          <div className="text-center text-red-400">
            <h3 className="text-lg font-medium">Error</h3>
            <p className="mt-1 text-sm">{error}</p>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="w-full rounded-lg bg-[#7C3AED] px-4 py-2 text-sm font-medium text-white hover:bg-[#6D28D9]"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0A0F1E]">
        <div className="animate-spin h-8 w-8 border-4 border-[#7C3AED] rounded-full border-t-transparent"></div>
      </div>
    );
  }

  if (!selectedTeammate && teammates.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0A0F1E]">
        <div className="w-full max-w-md space-y-4 rounded-xl bg-[#1E293B] p-8 shadow-lg">
          <div className="text-center text-red-400">
            <h3 className="text-lg font-medium">Error</h3>
            <p className="mt-1 text-sm">No teammates available</p>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="w-full rounded-lg bg-[#7C3AED] px-4 py-2 text-sm font-medium text-white hover:bg-[#6D28D9]"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!selectedTeammate && teammates.length > 0) {
    console.log('No teammate selected but teammates available:', teammates);
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0A0F1E]">
        <div className="w-full max-w-md space-y-4 rounded-xl bg-[#1E293B] p-8 shadow-lg">
          <div className="text-center text-yellow-400">
            <h3 className="text-lg font-medium">Debug Info</h3>
            <p className="mt-1 text-sm">Available teammates: {teammates.length}</p>
            <p className="mt-1 text-sm">Selected teammate: {selectedTeammate || 'none'}</p>
          </div>
          <button
            onClick={() => {
              const firstTeammate = teammates[0];
              console.log('Manually selecting first teammate:', firstTeammate);
              setSelectedTeammate(firstTeammate.id);
            }}
            className="w-full rounded-lg bg-[#7C3AED] px-4 py-2 text-sm font-medium text-white hover:bg-[#6D28D9]"
          >
            Select First Teammate
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full">
      {runtime && selectedTeammate ? (
        <AssistantRuntimeProvider runtime={runtime}>
          <ToolRegistrationWrapper>
            <div className="flex h-screen">
              <div className="w-72 flex-shrink-0 flex flex-col bg-[#0A0F1E] border-r border-[#1E293B]">
                <div className="flex flex-col p-4 border-b border-[#1E293B] space-y-4">
                  <div className="flex items-center justify-between">
                    <h2 className="text-sm font-medium text-white">Teammates</h2>
                    <button
                      onClick={handleNewThread}
                      className="p-2 rounded-lg hover:bg-[#1E293B] text-[#7C3AED] transition-colors"
                      title="New Thread"
                    >
                      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M12 5v14M5 12h14" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </button>
                  </div>
                  
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Search className="h-4 w-4 text-[#94A3B8]" />
                    </div>
                    <input
                      type="text"
                      placeholder="Search teammates..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 bg-[#1E293B] border border-[#2D3B4E] rounded-lg text-sm text-white placeholder-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#7C3AED] focus:border-transparent"
                    />
                  </div>
                </div>
                
                <div className="flex-1 overflow-y-auto p-4 space-y-2">
                  {filteredTeammates.length === 0 ? (
                    <div className="text-center py-4 text-[#94A3B8] text-sm">
                      No teammates found
                    </div>
                  ) : (
                    filteredTeammates.map((teammate) => (
                      <button
                        key={teammate.id}
                        onClick={() => handleTeammateSelect(teammate)}
                        className={`w-full text-left p-3 rounded-lg transition-colors ${
                          selectedTeammate === teammate.id
                            ? 'bg-[#7C3AED] text-white'
                            : 'text-[#94A3B8] hover:bg-[#1E293B]'
                        }`}
                      >
                        <div className="flex items-center space-x-3">
                          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#7C3AED]/20 flex items-center justify-center">
                            <span className={`text-sm font-medium ${
                              selectedTeammate === teammate.id ? 'text-white' : 'text-[#7C3AED]'
                            }`}>
                              {teammate.name.charAt(0)}
                            </span>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">{teammate.name}</p>
                            {teammate.description && (
                              <p className={`text-xs truncate ${
                                selectedTeammate === teammate.id ? 'text-white/75' : 'text-[#94A3B8]'
                              }`}>
                                {teammate.description}
                              </p>
                            )}
                          </div>
                          {selectedTeammate === teammate.id && (
                            <div className="flex-shrink-0">
                              <div className="w-2 h-2 rounded-full bg-white"></div>
                            </div>
                          )}
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </div>

              <div className="flex-1 flex flex-col min-h-0 bg-[#0A0F1E]">
                {selectedTeammate ? (
                  <>
                    <div className="flex items-center justify-between p-4 border-b border-[#1E293B]">
                      <div className="flex items-center space-x-4">
                        <Image 
                          src="https://kubiya-public-20221113173935726800000003.s3.amazonaws.com/kubiya-ai-logo-2024_NEW_Bot-05.png"
                          alt="Kubiya Logo"
                          width={32}
                          height={32}
                          style={{ width: 'auto', height: '32px' }}
                          priority
                          unoptimized
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            const parentNode = target.parentNode;
                            if (parentNode) {
                              const span = document.createElement('span');
                              span.className = 'text-2xl';
                              span.textContent = '🤖';
                              parentNode.replaceChild(span, target);
                            }
                          }}
                        />
                        <h1 className="text-sm font-medium text-white">Kubiya Chat</h1>
                      </div>
                      <div className="flex items-center space-x-4">
                        <a href="/docs" className="text-[#7C3AED] text-sm hover:text-[#6D28D9] transition-colors">Docs</a>
                        <a href="/system-health" className="text-[#7C3AED] text-sm hover:text-[#6D28D9] transition-colors">System Health</a>
                      </div>
                    </div>

                    <div className="flex-1 flex">
                      <div className="flex-1 flex flex-col">
                        <div className="p-4 bg-[#1E293B]/30">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <div className="w-10 h-10 rounded-full bg-[#7C3AED] flex items-center justify-center">
                                <span className="text-white text-lg font-medium">
                                  {teammates.find(t => t.id === selectedTeammate)?.name.charAt(0)}
                                </span>
                              </div>
                              <div>
                                <h2 className="text-white font-medium">
                                  {teammates.find(t => t.id === selectedTeammate)?.name}
                                </h2>
                                <p className="text-[#94A3B8] text-sm">
                                  {teammates.find(t => t.id === selectedTeammate)?.description}
                                </p>
                              </div>
                            </div>
                            <button
                              onClick={() => setIsToolsModalOpen(true)}
                              className="px-3 py-1.5 rounded-lg bg-[#7C3AED] text-white text-sm hover:bg-[#6D28D9] transition-colors flex items-center space-x-2"
                            >
                              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                              </svg>
                              <span>View Tools</span>
                            </button>
                          </div>
                        </div>

                        <div className="flex-1 overflow-y-auto p-4">
                          <div className="max-w-4xl mx-auto">
                            {children}
                          </div>
                        </div>
                      </div>

                      <div className="w-80 border-l border-[#1E293B] overflow-y-auto">
                        <div className="p-4 space-y-6">
                          {/* Threads Section */}
                          <div className="space-y-4">
                            <div className="flex items-center justify-between">
                              <h3 className="text-white text-sm font-medium">Recent Threads</h3>
                              <button
                                onClick={handleNewThread}
                                className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-[#7C3AED] text-white text-sm hover:bg-[#6D28D9] transition-colors"
                              >
                                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                  <path d="M12 5v14M5 12h14" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                </svg>
                                <span>New Thread</span>
                              </button>
                            </div>

                            {sessions.length > 0 ? (
                              <div className="space-y-2">
                                {sessions.map((session) => (
                                  <button
                                    key={session.id}
                                    onClick={() => {
                                      localStorage.setItem(`chat_session_${selectedTeammate}`, session.id);
                                    }}
                                    className={`w-full flex items-center space-x-3 p-3 rounded-lg transition-colors ${
                                      localStorage.getItem(`chat_session_${selectedTeammate}`) === session.id
                                        ? 'bg-[#1E293B] text-[#7C3AED]'
                                        : 'text-white hover:bg-[#1E293B]/50'
                                    }`}
                                  >
                                    <div className="flex-shrink-0">
                                      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                      </svg>
                                    </div>
                                    <div className="flex-1 min-w-0 text-left">
                                      <div className="font-medium truncate">
                                        {session.title || 'Untitled Thread'}
                                      </div>
                                      <div className="text-xs text-[#94A3B8] mt-0.5">
                                        {new Date(parseInt(session.id)).toLocaleString()}
                                      </div>
                                    </div>
                                    <div className="flex-shrink-0">
                                      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                        <path d="M9 5l7 7-7 7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                      </svg>
                                    </div>
                                  </button>
                                ))}
                              </div>
                            ) : (
                              <div className="text-center p-4">
                                <div className="w-12 h-12 rounded-full bg-[#1E293B] flex items-center justify-center mx-auto mb-4">
                                  <svg className="w-6 h-6 text-[#94A3B8]" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                    <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                  </svg>
                                </div>
                                <h3 className="text-white font-medium mb-2">No Threads Yet</h3>
                                <p className="text-[#94A3B8] text-sm">Start a new conversation to create a thread</p>
                              </div>
                            )}
                          </div>

                          {/* Tools Section */}
                          {tools.length > 0 && (
                            <div className="space-y-6" key="tools-container">
                              <div className="flex items-center justify-between">
                                <h3 className="text-white text-sm font-medium">Available Tools</h3>
                                <div className="flex space-x-2">
                                  <button
                                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                                    className="p-1 rounded hover:bg-[#1E293B] text-[#94A3B8] disabled:opacity-50"
                                    disabled={currentPage === 1}
                                  >
                                    ←
                                  </button>
                                  <span className="text-[#94A3B8] text-sm">
                                    {currentPage}
                                  </span>
                                  <button
                                    onClick={() => setCurrentPage(prev => prev + 1)}
                                    className="p-1 rounded hover:bg-[#1E293B] text-[#94A3B8] disabled:opacity-50"
                                    disabled={currentPage * toolsPerPage >= tools.length}
                                  >
                                    →
                                  </button>
                                </div>
                              </div>

                              <div className="space-y-4" key="tools-list">
                                {groupToolsBySource(tools, sourcesData)
                                  .slice((currentPage - 1) * toolsPerPage, currentPage * toolsPerPage)
                                  .map((sourceGroup, sourceIndex) => (
                                    <div key={`${sourceGroup.sourceId}-${sourceIndex}`} className="bg-[#1E293B]/20 rounded-lg p-4 space-y-4">
                                      <div 
                                        className="flex items-center space-x-3 cursor-pointer hover:bg-[#1E293B]/30 p-2 rounded-lg transition-colors"
                                        onClick={async () => {
                                          const source = sourcesData.find(s => s.id === sourceGroup.sourceId);
                                          if (source) {
                                            const config = getKubiyaConfig();
                                            try {
                                              // Fetch complete source metadata
                                              const response = await fetch(`${config.baseUrl}/sources/${source.uuid}/metadata`, {
                                                headers: {
                                                  "Content-Type": "application/json",
                                                  "Authorization": `UserKey ${config.apiKey}`,
                                                },
                                              });
                                              
                                              if (!response.ok) throw new Error("Failed to fetch source metadata");
                                              console.log('Source metadata fetched successfully');
                                            } catch (err) {
                                              console.error("Failed to fetch source metadata:", err);
                                            }
                                          }
                                        }}
                                      >
                                        <div className="flex-shrink-0">
                                          <span className="text-xl select-none" role="img" aria-label="toolbox">🧰</span>
                                        </div>
                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-center space-x-2">
                                            <h4 className="text-white text-sm font-medium">
                                              {(sourceGroup.sourceName || 'Unknown Source').split('/').pop()?.replace(/\.ya?ml$/, '')}
                                            </h4>
                                            {sourceGroup.runner && (
                                              <span className="px-2 py-0.5 text-xs rounded-full bg-[#7C3AED]/20 text-[#7C3AED]">
                                                {sourceGroup.runner}
                                              </span>
                                            )}
                                          </div>
                                          {sourceGroup.metadata?.kubiya_metadata && (
                                            <p className="text-[#94A3B8] text-xs mt-1">
                                              Updated {new Date(sourceGroup.metadata.kubiya_metadata.last_updated).toLocaleDateString()}
                                            </p>
                                          )}
                                        </div>
                                        <div className="flex-shrink-0">
                                          <svg className="w-4 h-4 text-[#94A3B8]" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                            <path d="M9 5l7 7-7 7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                          </svg>
                                        </div>
                                      </div>

                                      <div className="pl-8 space-y-2">
                                        {sourceGroup.tools.map((tool: Tool, toolIndex: number) => (
                                          <div
                                            key={`${tool.name}-${toolIndex}-${sourceGroup.sourceId}`}
                                            className="bg-[#1E293B]/30 rounded-lg p-3 hover:bg-[#1E293B]/40 transition-colors group cursor-pointer"
                                          >
                                            <div className="flex items-start justify-between">
                                              <div className="flex-1">
                                                <div className="flex items-center space-x-2">
                                                  {tool.icon_url ? (
                                                    <Image 
                                                      src={tool.icon_url || ''}
                                                      alt={`${tool.name} icon`}
                                                      width={20}
                                                      height={20}
                                                      className="w-5 h-5 rounded"
                                                      onError={(e) => handleImageError(e, tool.type)}
                                                      unoptimized
                                                    />
                                                  ) : (
                                                    <span className="text-xl select-none" role="img">{getDefaultToolIcon(tool.type)}</span>
                                                  )}
                                                  <h4 className="text-white text-sm font-medium">{formatName(tool.name)}</h4>
                                                </div>
                                                <p className="text-[#94A3B8] text-xs mt-1 line-clamp-2">{tool.description}</p>
                                              </div>
                                              <button
                                                className="opacity-0 group-hover:opacity-100 p-2 rounded-full hover:bg-[#7C3AED] transition-all"
                                                onClick={(e) => {
                                                  e.stopPropagation();
                                                  // Handle tool execution
                                                }}
                                              >
                                                <svg className="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                                  <path d="M5 3l14 9-14 9V3z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                                </svg>
                                              </button>
                                            </div>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  ))}
                              </div>
                            </div>
                          )}

                          {/* Quick Actions Section */}
                          {starters.length > 0 && (
                            <div className="space-y-4">
                              <h3 className="text-white text-sm font-medium">Quick Actions</h3>
                              <div className="space-y-2">
                                {starters.map((starter, index) => (
                                  <button 
                                    key={starter.command + index} 
                                    className="w-full text-left bg-[#1E293B]/30 hover:bg-[#1E293B]/40 rounded-lg p-3 transition-colors"
                                  >
                                    <p className="text-white text-sm font-medium">{starter.display_name}</p>
                                    <p className="text-[#94A3B8] text-xs mt-1">Command: {starter.command}</p>
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="flex-1 flex items-center justify-center">
                    <div className="text-center text-[#94A3B8]">
                      <h3 className="text-lg font-medium">Select a Teammate</h3>
                      <p className="mt-2 text-sm">Choose a teammate from the sidebar to start chatting</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </ToolRegistrationWrapper>
        </AssistantRuntimeProvider>
      ) : (
        <div className="flex min-h-screen items-center justify-center bg-[#0A0F1E]">
          <div className="w-full max-w-md space-y-4 rounded-xl bg-[#1E293B] p-8 shadow-lg">
            <div className="text-center text-yellow-400">
              <h3 className="text-lg font-medium">Initializing Chat</h3>
              <p className="mt-1 text-sm">
                {!selectedTeammate 
                  ? 'Waiting for teammate selection...' 
                  : 'Setting up chat environment...'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Add the modal */}
      {isToolsModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1E293B] rounded-xl max-w-4xl w-full max-h-[80vh] flex flex-col">
            <div className="p-4 border-b border-[#2D3748] flex items-center justify-between">
              <h3 className="text-lg font-medium text-white">Available Tools ({tools.length})</h3>
              <button
                onClick={() => setIsToolsModalOpen(false)}
                className="p-2 rounded-lg hover:bg-[#2D3748] text-[#94A3B8] transition-colors"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path d="M6 18L18 6M6 6l12 12" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              <div className="space-y-4">
                {groupToolsBySource(tools, sourcesData).map((sourceGroup, sourceIndex) => (
                  <div key={`${sourceGroup.sourceId}-${sourceIndex}`} className="bg-[#0A0F1E] rounded-lg p-4 space-y-4">
                    <div className="flex items-center space-x-3">
                      <span className="text-xl select-none" role="img">{sourceGroup.icon}</span>
                      <div>
                        <h4 className="text-white font-medium">
                          {(sourceGroup.sourceName || 'Unknown Source').split('/').pop()?.replace(/\.ya?ml$/, '')}
                        </h4>
                        {sourceGroup.metadata?.kubiya_metadata && (
                          <p className="text-[#94A3B8] text-sm">
                            Updated {new Date(sourceGroup.metadata.kubiya_metadata.last_updated).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="space-y-2">
                      {sourceGroup.tools.map((tool: Tool, toolIndex: number) => (
                        <div
                          key={`${tool.name}-${toolIndex}`}
                          className="bg-[#1E293B] rounded-lg p-3 hover:bg-[#2D3748] transition-colors"
                        >
                          <div className="flex items-start space-x-3">
                            {tool.icon_url ? (
                              <Image 
                                src={tool.icon_url}
                                alt={`${tool.name} icon`}
                                width={20}
                                height={20}
                                className="w-5 h-5 rounded"
                                onError={(e) => handleImageError(e, tool.type)}
                                unoptimized
                              />
                            ) : (
                              <span className="text-xl select-none" role="img">{getDefaultToolIcon(tool.type)}</span>
                            )}
                            <div className="flex-1">
                              <h5 className="text-white font-medium">{formatName(tool.name)}</h5>
                              <p className="text-[#94A3B8] text-sm mt-1">{tool.description}</p>
                              {tool.metadata?.arguments && (
                                <div className="mt-2 space-y-1">
                                  <p className="text-[#94A3B8] text-xs font-medium">Arguments:</p>
                                  {tool.metadata.arguments.map((arg: { name: string; type: string; description: string; required: boolean }, i: number) => (
                                    <div key={i} className="text-[#94A3B8] text-xs pl-2">
                                      • {arg.name} ({arg.type}){arg.required ? ' *' : ''}: {arg.description}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 