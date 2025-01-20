"use client";

import { useEffect, useState, useCallback } from 'react';
import { useUser } from '@auth0/nextjs-auth0/client';
import { useRouter } from 'next/navigation';
import { useTeammateContext } from '../../MyRuntimeProvider';
import { ChatInput } from './ChatInput';
import { ChatMessages } from './ChatMessages';
import { ThreadsSidebar } from './ThreadsSidebar';
import { SystemMessages } from './SystemMessages';
import { ToolExecution } from './ToolExecution';
import { Info } from 'lucide-react';
import { Button } from '@/app/components/button';

interface ThreadInfo {
  id: string;
  title: string;
  lastMessage?: string;
  createdAt: string;
  updatedAt: string;
  teammateId: string;
}

interface MessageContent {
  type: string;
  text: string;
}

interface Teammate {
  uuid: string;
  name: string;
  description?: string;
}

interface TeammateState {
  sessions: any[];
  currentThreadId?: string;
  currentSessionId?: string;
  threads: Record<string, {
    messages: Array<{
      id: string;
      role: string;
      content: Array<{ type: string; text: string }>;
      createdAt: Date;
      metadata?: {
        custom?: {
          isSystemMessage?: boolean;
        };
        activeTool?: string;
      };
    }>;
    lastMessageId?: string;
    metadata: {
      teammateId: string;
      createdAt: string;
      updatedAt: string;
      title?: string;
      preview?: string;
      activeTool?: string;
    };
  }>;
}

interface TeammateDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  teammate: Teammate | null;
  capabilities: any;
}

const TeammateDetailsModal = ({ isOpen, onClose, teammate, capabilities }: TeammateDetailsModalProps) => {
  if (!isOpen) return null;

  const getIcon = (integration: string | { name: string; type: string }) => {
    // Handle both string and object with type
    const name = typeof integration === 'string' ? integration : integration.name;
    const type = typeof integration === 'string' ? integration : integration.type;
    
    const checkType = (keyword: string) => {
      return name.toLowerCase().includes(keyword) || type.toLowerCase().includes(keyword);
    };

    if (checkType('slack')) return <img src="https://cdn4.iconfinder.com/data/icons/logos-and-brands/512/306_Slack_logo-512.png" alt="Slack" className="h-5 w-5 object-contain" />;
    if (checkType('aws')) return <img src="https://uxwing.com/wp-content/themes/uxwing/download/brands-and-social-media/aws-icon.png" alt="AWS" className="h-5 w-5 object-contain" />;
    if (checkType('github')) return <img src="https://cdn-icons-png.flaticon.com/512/25/25231.png" alt="GitHub" className="h-5 w-5 object-contain" />;
    if (checkType('jira')) return <img src="https://cdn-icons-png.flaticon.com/512/5968/5968875.png" alt="Jira" className="h-5 w-5 object-contain" />;
    if (checkType('kubernetes')) return <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Kubernetes_logo_without_workmark.svg/2109px-Kubernetes_logo_without_workmark.svg.png" alt="Kubernetes" className="h-5 w-5 object-contain" />;
    return <div className="h-5 w-5 bg-purple-400 rounded-full" />;
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-[#0F1629] rounded-lg max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">
                {teammate?.name || 'Teammate Details'}
              </h2>
              <p className="text-slate-400">
                {teammate?.description}
              </p>
            </div>
            <Button
              variant="ghost"
              className="text-slate-400 hover:text-white"
              onClick={onClose}
            >
              ✕
            </Button>
          </div>

          {/* Capabilities */}
          {capabilities && (
            <div className="space-y-6">
              {/* Runner Info */}
              {capabilities.runner && (
                <div className="bg-[#1E293B] rounded-lg p-4">
                  <h3 className="text-sm font-medium text-slate-300 mb-2">Runtime Environment</h3>
                  <div className="flex items-center gap-2 text-sm text-slate-400">
                    <img 
                      src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Kubernetes_logo_without_workmark.svg/2109px-Kubernetes_logo_without_workmark.svg.png" 
                      alt="Kubernetes" 
                      className="h-4 w-4 object-contain"
                    />
                    <span>{capabilities.runner}</span>
                  </div>
                </div>
              )}

              {/* Integrations */}
              {capabilities.integrations?.length > 0 && (
                <div className="bg-[#1E293B] rounded-lg p-4">
                  <h3 className="text-sm font-medium text-slate-300 mb-3">Available Integrations</h3>
                  <div className="flex flex-wrap gap-2">
                    {capabilities.integrations.map((integration: any, index: number) => (
                      <div
                        key={index}
                        className="flex items-center gap-2 px-3 py-2 bg-[#2A3347] rounded-md border border-[#3D4B5E]"
                      >
                        {getIcon(integration)}
                        <span className="text-sm text-slate-300">
                          {typeof integration === 'string' ? integration : integration.name}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tools */}
              {capabilities.tools?.length > 0 && (
                <div className="bg-[#1E293B] rounded-lg p-4">
                  <h3 className="text-sm font-medium text-slate-300 mb-3">Available Tools</h3>
                  <div className="space-y-2">
                    {capabilities.tools.map((tool: any, index: number) => (
                      <div key={index} className="bg-[#2A3347] rounded-md p-3 border border-[#3D4B5E]">
                        <div className="font-medium text-sm text-slate-300 mb-1">{tool.name}</div>
                        <div className="text-xs text-slate-400">{tool.description}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Model Info */}
              <div className="bg-[#1E293B] rounded-lg p-4">
                <h3 className="text-sm font-medium text-slate-300 mb-2">Model Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs text-slate-400">Language Model</div>
                    <div className="text-sm text-slate-300">{capabilities.llm_model}</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400">Instruction Type</div>
                    <div className="text-sm text-slate-300">{capabilities.instruction_type}</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export const Chat = () => {
  const { user, isLoading: userLoading } = useUser();
  const router = useRouter();
  const { selectedTeammate, currentState, switchThread, teammates, setTeammateState } = useTeammateContext();
  const [isProcessing, setIsProcessing] = useState(false);
  const [systemMessages, setSystemMessages] = useState<string[]>([]);
  const [isCollectingSystemMessages, setIsCollectingSystemMessages] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [capabilities, setCapabilities] = useState<any>(null);
  const [teammate, setTeammate] = useState<any>(null);

  // Track system messages
  useEffect(() => {
    if (!currentState?.currentThreadId) return;
    const thread = currentState.threads[currentState.currentThreadId];
    if (!thread?.messages) return;
    
    const newSystemMessages = thread.messages
      .filter(msg => msg.role === 'system' || msg.metadata?.custom?.isSystemMessage)
      .map(msg => {
        const textContent = msg.content.find((c: MessageContent) => c.type === 'text' && 'text' in c);
        return textContent && 'text' in textContent ? textContent.text : '';
      })
      .filter(Boolean);

    if (newSystemMessages.length > 0 && JSON.stringify(newSystemMessages) !== JSON.stringify(systemMessages)) {
      setSystemMessages(newSystemMessages);
    }
  }, [currentState?.currentThreadId, currentState?.threads, systemMessages]);

  // Fetch teammate details and capabilities
  useEffect(() => {
    const fetchDetails = async () => {
      if (!selectedTeammate) return;
      try {
        const response = await fetch(`/api/teammates/${selectedTeammate}/capabilities`);
        if (response.ok) {
          const data = await response.json();
          setCapabilities(data);
        }
      } catch (error) {
        console.error('Failed to fetch capabilities:', error);
      }
    };

    if (selectedTeammate) {
      const teammate = teammates.find((t: Teammate) => t.uuid === selectedTeammate);
      setTeammate(teammate);
      fetchDetails();
    }
  }, [selectedTeammate, teammates]);

  const handleSubmit = async (message: string) => {
    if (!selectedTeammate || !currentState?.currentThreadId) {
      setError('Please select a teammate first');
      return;
    }

    if (isProcessing) return;

    // Add message counter for unique IDs
    let messageCounter = 0;
    const generateUniqueId = (prefix: string) => `${prefix}_${Date.now()}_${messageCounter++}`;

    setError(null);
    setIsProcessing(true);
    setIsCollectingSystemMessages(true);
    setSystemMessages([]); // Reset system messages
    
    try {
      const threadId = currentState.currentThreadId;
      
      // Immediately add user message to the UI
      const userMessage = {
        id: generateUniqueId('user'),
        role: 'user',
        content: [{ type: 'text', text: message }],
        createdAt: new Date()
      };

      // Get current thread state
      const currentThread = currentState.threads[threadId] || {
        messages: [],
        metadata: {
          teammateId: selectedTeammate,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          title: message.slice(0, 50) + (message.length > 50 ? '...' : '') // Add title for new threads
        }
      };

      // Update thread with user message
      const updatedThread = {
        ...currentThread,
        messages: [...currentThread.messages, userMessage],
        metadata: {
          ...currentThread.metadata,
          updatedAt: new Date().toISOString()
        }
      };

      // Update state with user message
      const initialUpdatedState = {
        ...currentState,
        threads: {
          ...currentState.threads,
          [threadId]: updatedThread
        }
      };
      setTeammateState(selectedTeammate, initialUpdatedState);

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
      let currentMessages = [...updatedThread.messages]; // Track messages locally
      let partialMessage = ''; // Track partial message
      let currentAssistantMessageId: string | null = null;
      let lastEventId: string | null = null;

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
              
              // Handle different event types
              switch (eventData.type) {
                case 'msg':
                case 'assistant':
                  if (eventData.message) {
                    // If this is a new message or a different message ID
                    if (!currentAssistantMessageId || lastEventId !== eventData.id) {
                      currentAssistantMessageId = eventData.id || generateUniqueId('assistant');
                      lastEventId = eventData.id;
                      
                      // Create new message or update existing one
                      const existingMessageIndex = currentMessages.findIndex(msg => msg.id === currentAssistantMessageId);
                      if (existingMessageIndex === -1) {
                        // Create new message
                        const assistantMessage = {
                          id: currentAssistantMessageId,
                          role: 'assistant',
                          content: [{ type: 'text', text: eventData.message }],
                          createdAt: new Date()
                        };
                        currentMessages = [...currentMessages, assistantMessage];
                      } else {
                        // Update existing message with complete new content
                        currentMessages = currentMessages.map((msg, index) => 
                          index === existingMessageIndex
                            ? {
                                ...msg,
                                content: [{ type: 'text', text: eventData.message }]
                              }
                            : msg
                        );
                      }

                      // Update teammate state immediately with new message
                      const updatedState = {
                        ...currentState,
                        threads: {
                          ...currentState.threads,
                          [threadId]: {
                            ...currentThread,
                            messages: currentMessages,
                            metadata: {
                              ...currentThread.metadata,
                              updatedAt: new Date().toISOString()
                            }
                          }
                        }
                      };
                      setTeammateState(selectedTeammate, updatedState);
                    } else {
                      // Update existing message with complete content
                      currentMessages = currentMessages.map(msg => 
                        msg.id === currentAssistantMessageId
                          ? {
                              ...msg,
                              content: [{ type: 'text', text: eventData.message }]
                            }
                          : msg
                      );

                      // Update teammate state with complete message
                      const updatedState = {
                        ...currentState,
                        threads: {
                          ...currentState.threads,
                          [threadId]: {
                            ...currentThread,
                            messages: currentMessages,
                            metadata: {
                              ...currentThread.metadata,
                              updatedAt: new Date().toISOString()
                            }
                          }
                        }
                      };
                      setTeammateState(selectedTeammate, updatedState);
                    }

                    // Log for debugging
                    console.log('[Chat] Message update:', {
                      id: currentAssistantMessageId,
                      text: eventData.message,
                      messageCount: currentMessages.length,
                      fullMessage: true
                    });
                  }
                  break;
                case 'system_message':
                  if (eventData.messages && Array.isArray(eventData.messages)) {
                    // Handle array of system messages
                    eventData.messages.forEach((message: string) => {
                      const systemMessage = {
                        id: generateUniqueId('system'),
                        role: 'system',
                        content: [{ type: 'text', text: message }],
                        createdAt: new Date(),
                        metadata: { custom: { isSystemMessage: true } }
                      };
                      currentMessages = [...currentMessages, systemMessage];
                      collectedSystemMessages = [...collectedSystemMessages, message];
                      setSystemMessages(prev => [...prev, message]);
                    });

                    // Update teammate state with latest messages including system messages
                    const updatedState = {
                      ...currentState,
                      threads: {
                        ...currentState.threads,
                        [threadId]: {
                          ...currentThread,
                          messages: currentMessages,
                          metadata: {
                            ...currentThread.metadata,
                            updatedAt: new Date().toISOString()
                          }
                        }
                      }
                    };
                    setTeammateState(selectedTeammate, updatedState);
                  }
                  break;
                case 'tool':
                  if (eventData.tool_name) {
                    currentAssistantMessageId = null; // Reset message tracking
                    partialMessage = ''; // Reset partial message
                    const toolId = generateUniqueId('tool');
                    const toolMessage = {
                      id: toolId,
                      role: 'assistant',
                      content: [],
                      tool_calls: [{
                        type: 'tool_init',
                        id: toolId,
                        name: eventData.tool_name,
                        arguments: eventData.arguments,
                        timestamp: new Date().toISOString()
                      }],
                      createdAt: new Date()
                    };
                    currentMessages = [...currentMessages, toolMessage];
                  }
                  break;
                case 'tool_output':
                  if (eventData.message) {
                    currentAssistantMessageId = null; // Reset message tracking
                    partialMessage = ''; // Reset partial message
                    const outputId = generateUniqueId('tool_output');
                    const toolOutputMessage = {
                      id: outputId,
                      role: 'assistant',
                      content: [],
                      tool_calls: [{
                        type: 'tool_output',
                        id: outputId,
                        message: eventData.message,
                        timestamp: new Date().toISOString()
                      }],
                      createdAt: new Date()
                    };
                    currentMessages = [...currentMessages, toolOutputMessage];
                  }
                  break;
              }

              // Update teammate state with latest messages
              const updatedState = {
                ...currentState,
                threads: {
                  ...currentState.threads,
                  [threadId]: {
                    ...currentThread,
                    messages: currentMessages,
                    metadata: {
                      ...currentThread.metadata,
                      updatedAt: new Date().toISOString()
                    }
                  }
                }
              };
              setTeammateState(selectedTeammate, updatedState);
            } catch (error) {
              console.error('[Chat] Error processing event:', error);
            }
          }
        }
      } finally {
        reader.releaseLock();
        // Reset message tracking at the end
        currentAssistantMessageId = null;
        partialMessage = '';
      }
      
    } catch (error) {
      console.error('Error sending message:', error);
      setError(error instanceof Error ? error.message : 'Failed to send message. Please try again.');
    } finally {
      setIsProcessing(false);
      setIsCollectingSystemMessages(false);
    }
  };

  // Show loading state
  if (userLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[#7C3AED] border-t-transparent"></div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className="flex h-full">
      <ThreadsSidebar />
      <div className="flex-1 flex flex-col h-full relative">
        {/* Header with Info Button */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-[#2A3347]">
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-medium text-white">{teammate?.name}</h1>
            <Button
              variant="ghost"
              size="sm"
              className="text-slate-400 hover:text-white p-1 h-auto"
              onClick={() => setIsDetailsModalOpen(true)}
            >
              <Info className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          <ChatMessages 
            messages={currentState?.threads[currentState.currentThreadId]?.messages || []} 
            isCollectingSystemMessages={isCollectingSystemMessages}
            systemMessages={systemMessages}
            capabilities={capabilities}
            teammate={teammate}
          />
        </div>
        <ChatInput onSubmit={handleSubmit} isDisabled={isProcessing} />
        
        {/* Tool Execution Panel */}
        <div className="absolute top-0 right-0 w-80 p-4 space-y-2">
          {/* Only render ToolExecution when there's an active tool */}
          {currentState?.threads[currentState.currentThreadId]?.metadata?.activeTool && (
            <ToolExecution 
              toolName={currentState.threads[currentState.currentThreadId].metadata.activeTool || ''} 
            />
          )}
        </div>

        {/* Teammate Details Modal */}
        <TeammateDetailsModal
          isOpen={isDetailsModalOpen}
          onClose={() => setIsDetailsModalOpen(false)}
          teammate={teammate}
          capabilities={capabilities}
        />
      </div>
    </div>
  );
};