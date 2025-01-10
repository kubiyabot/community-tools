'use client'

import React, { createContext, useContext, useEffect, useState, useCallback, useMemo, useRef } from 'react'
import { createKubiyaModelAdapter } from './lib/adapters'
import { useLocalRuntime, type Session, type Runtime, type CustomRuntime } from './lib/runtime'
import { AssistantRuntimeProvider } from "@assistant-ui/react"
import { AssistantRuntime, ThreadState, ThreadListState, ThreadListItemRuntime, ModelConfigProvider, ThreadRuntime, ThreadListRuntime, ThreadListItemState, ThreadMessage, ThreadSuggestion, ThreadComposerState } from "@assistant-ui/react"
import { ToolUI, SystemMessageUI, ToolExecutionUI } from './components/ToolUI'
import { ToolState } from './components/RuntimeProvider'

interface TeammateConfig {
  teammate: string
}

interface CustomRuntimeOptions {
  config: TeammateConfig
  sessions: Session[]
  setSessions: React.Dispatch<React.SetStateAction<Session[]>>
}

interface Teammate {
  id: string
  name: string
}

interface Tool {
  id: string
  name: string
}

interface SourceMetadata {
  id: string
  name: string
}

interface Starter {
  id: string
  name: string
  description: string
}

interface RuntimeWithConfig extends Runtime {
  config: TeammateConfig
}

interface RuntimeContextType {
  processMessage: (message: any) => void
  clearMessages: () => void
}

const RuntimeContext = createContext<RuntimeContextType | null>(null)

// Create the runtime configuration first
function useKubiyaRuntime(
  selectedTeammate: string | undefined,
  sessions: Session[],
  setSessions: React.Dispatch<React.SetStateAction<Session[]>>
): CustomRuntime | null {
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
  const runtime = useLocalRuntime(modelAdapter, runtimeOptions) as CustomRuntime;

  return selectedTeammate ? runtime : null;
}

// Export the conversion function
export const customRuntimeToAssistantRuntime = (customRuntime: CustomRuntime | null): AssistantRuntime | undefined => {
  if (!customRuntime) return undefined;
  
  const threadListItemState: ThreadListItemState = {
    isMain: true,
    id: customRuntime.config.teammate,
    remoteId: customRuntime.config.teammate,
    externalId: customRuntime.config.teammate,
    threadId: customRuntime.config.teammate,
    status: 'regular',
    title: customRuntime.config.teammate,
  };

  const threadState: ThreadState = {
    threadId: customRuntime.config.teammate,
    metadata: threadListItemState,
    isDisabled: false,
    isRunning: false,
    messages: customRuntime.sessions[0]?.messages || [],
    capabilities: {
      switchToBranch: false,
      edit: false,
      reload: false,
      cancel: false,
      unstable_copy: false,
      speech: false,
      attachments: false,
      feedback: false,
    },
    suggestions: [],
    extras: {},
    speech: undefined,
  };

  const threadListState: ThreadListState = {
    mainThreadId: customRuntime.config.teammate,
    newThread: customRuntime.config.teammate,
    threads: customRuntime.sessions.map(session => session.id),
    archivedThreads: [],
  };

  const threadRuntime: ThreadRuntime = {
    ...threadState,
    getState: () => threadState,
    subscribe: () => () => {},
    path: { ref: 'thread', threadSelector: { type: 'main' } },
    composer: {
      path: { ref: 'composer', threadSelector: { type: 'main' }, composerSource: 'thread' },
      type: 'thread' as const,
      getState: () => ({
        canCancel: false,
        isEditing: false,
        isEmpty: true,
        text: '',
        isDisabled: false,
        isFocused: false,
        isLoading: false,
        role: 'user',
        attachments: [],
        type: 'thread' as const,
        runConfig: { custom: {} },
      }),
      getAttachmentAccept: () => '',
      addAttachment: async () => {},
      setText: () => {},
      setRole: () => {},
      setRunConfig: () => {},
      reset: async () => Promise.resolve(),
      clearAttachments: async () => Promise.resolve(),
      send: async () => Promise.resolve(),
      cancel: async () => Promise.resolve(),
      subscribe: () => () => {},
      getAttachmentByIndex: () => ({
        path: { ref: 'attachment', threadSelector: { type: 'main' }, attachmentSource: 'thread-composer', attachmentSelector: { type: 'index', index: 0 } },
        source: 'thread-composer' as const,
        getState: () => ({
          id: '',
          type: 'file',
          name: '',
          contentType: 'application/octet-stream',
          status: { type: 'running', reason: 'uploading', progress: 0 },
          file: new File([], ''),
          source: 'thread-composer',
        }),
        subscribe: () => () => {},
        remove: async () => Promise.resolve(),
      }),
    },
    append: async () => Promise.resolve(),
    startRun: async () => Promise.resolve(),
    cancelRun: async () => Promise.resolve(),
    getModelConfig: () => ({}),
    export: () => ({ messages: [] }),
    import: () => {},
    getMesssageByIndex: () => ({
      path: { 
        ref: 'message', 
        threadSelector: { type: 'main' },
        messageSelector: { type: 'index', index: 0 }
      },
      composer: {
        path: { ref: 'composer', threadSelector: { type: 'main' }, composerSource: 'edit', messageSelector: { type: 'index', index: 0 } },
        type: 'edit' as const,
        getState: () => ({
          canCancel: false,
          isEditing: false,
          isEmpty: true,
          text: '',
          isDisabled: false,
          isFocused: false,
          isLoading: false,
          role: 'user',
          attachments: [],
          type: 'edit' as const,
          runConfig: { custom: {} },
        }),
        getAttachmentAccept: () => '',
        addAttachment: async () => Promise.resolve(),
        setText: () => {},
        setRole: () => {},
        setRunConfig: () => {},
        reset: async () => Promise.resolve(),
        clearAttachments: async () => Promise.resolve(),
        send: async () => Promise.resolve(),
        cancel: async () => Promise.resolve(),
        subscribe: () => () => {},
        getAttachmentByIndex: () => ({
          path: { ref: 'attachment', threadSelector: { type: 'main' }, messageSelector: { type: 'index', index: 0 }, attachmentSource: 'edit-composer', attachmentSelector: { type: 'index', index: 0 } },
          source: 'edit-composer' as const,
          getState: () => ({
            id: '',
            type: 'file',
            name: '',
            contentType: 'application/octet-stream',
            status: { type: 'running', reason: 'uploading', progress: 0 },
            file: new File([], ''),
            source: 'edit-composer',
          }),
          subscribe: () => () => {},
          remove: async () => Promise.resolve(),
        }),
        beginEdit: () => {},
      },
      getState: () => ({
        id: '',
        createdAt: new Date(),
        role: 'user',
        content: [],
        attachments: [],
        metadata: {
          custom: {},
        },
        parentId: null,
        isLast: false,
        branchNumber: 0,
        branchCount: 0,
        speech: undefined,
        submittedFeedback: undefined,
      }),
      reload: async () => Promise.resolve(),
      subscribe: () => () => {},
      unstable_on: () => () => {},
      speak: async () => Promise.resolve(),
      stopSpeaking: () => {},
      submitFeedback: async () => Promise.resolve(),
      switchToBranch: async () => Promise.resolve(),
      unstable_copy: async () => Promise.resolve(),
      unstable_edit: async () => Promise.resolve(),
      unstable_getAttachmentByIndex: () => ({
        path: { ref: 'attachment', threadSelector: { type: 'main' }, messageSelector: { type: 'index', index: 0 }, attachmentSource: 'message', attachmentSelector: { type: 'index', index: 0 } },
        source: 'message' as const,
        getState: () => ({
          id: '',
          type: 'file',
          name: '',
          contentType: 'application/octet-stream',
          status: { type: 'running', reason: 'uploading', progress: 0 },
          file: new File([], ''),
          source: 'message',
        }),
        subscribe: () => () => {},
        remove: async () => Promise.resolve(),
      }),
      unstable_reload: async () => Promise.resolve(),
      unstable_getCopyText: () => '',
      getContentPartByIndex: () => ({
        type: 'text',
        text: '',
        addToolResult: async () => Promise.resolve(),
        path: { ref: 'content-part', threadSelector: { type: 'main' }, messageSelector: { type: 'index', index: 0 }, contentPartSelector: { type: 'index', index: 0 } },
        getState: () => ({
          type: 'text',
          text: '',
          status: { type: 'complete' } as const,
        }),
        subscribe: () => () => {},
      }),
      getContentPartByToolCallId: () => ({
        type: 'text',
        text: '',
        addToolResult: async () => Promise.resolve(),
        path: { ref: 'content-part', threadSelector: { type: 'main' }, messageSelector: { type: 'index', index: 0 }, contentPartSelector: { type: 'toolCallId', toolCallId: '' } },
        getState: () => ({
          type: 'text',
          text: '',
          status: { type: 'complete' } as const,
        }),
        subscribe: () => () => {},
      }),
      getAttachmentByIndex: () => ({
        path: { ref: 'attachment', threadSelector: { type: 'main' }, messageSelector: { type: 'index', index: 0 }, attachmentSource: 'message', attachmentSelector: { type: 'index', index: 0 } },
        source: 'message' as const,
        getState: () => ({
          id: '',
          type: 'file',
          name: '',
          contentType: 'application/octet-stream',
          status: { type: 'complete' } as const,
          content: [],
          file: new File([], ''),
          source: 'message',
        }),
        subscribe: () => () => {},
        remove: async () => Promise.resolve(),
      }),
    }),
    getMesssageById: () => ({
      path: { 
        ref: 'message', 
        threadSelector: { type: 'main' },
        messageSelector: { type: 'messageId', messageId: '' }
      },
      composer: {
        path: { ref: 'composer', threadSelector: { type: 'main' }, composerSource: 'edit', messageSelector: { type: 'messageId', messageId: '' } },
        type: 'edit' as const,
        getState: () => ({
          canCancel: false,
          isEditing: false,
          isEmpty: true,
          text: '',
          isDisabled: false,
          isFocused: false,
          isLoading: false,
          role: 'user',
          attachments: [],
          type: 'edit' as const,
          runConfig: { custom: {} },
        }),
        getAttachmentAccept: () => '',
        addAttachment: async () => Promise.resolve(),
        setText: () => {},
        setRole: () => {},
        setRunConfig: () => {},
        reset: async () => Promise.resolve(),
        clearAttachments: async () => Promise.resolve(),
        send: async () => Promise.resolve(),
        cancel: async () => Promise.resolve(),
        subscribe: () => () => {},
        getAttachmentByIndex: () => ({
          path: { ref: 'attachment', threadSelector: { type: 'main' }, messageSelector: { type: 'messageId', messageId: '' }, attachmentSource: 'edit-composer', attachmentSelector: { type: 'index', index: 0 } },
          source: 'edit-composer' as const,
          getState: () => ({
            id: '',
            type: 'file',
            name: '',
            contentType: 'application/octet-stream',
            status: { type: 'running', reason: 'uploading', progress: 0 },
            file: new File([], ''),
            source: 'edit-composer',
          }),
          subscribe: () => () => {},
          remove: async () => Promise.resolve(),
        }),
        beginEdit: () => {},
      },
      getState: () => ({
        id: '',
        createdAt: new Date(),
        role: 'user',
        content: [],
        attachments: [],
        metadata: {
          custom: {},
        },
        parentId: null,
        isLast: false,
        branchNumber: 0,
        branchCount: 0,
        speech: undefined,
        submittedFeedback: undefined,
      }),
      reload: async () => Promise.resolve(),
      subscribe: () => () => {},
      unstable_on: () => () => {},
      speak: async () => Promise.resolve(),
      stopSpeaking: () => {},
      submitFeedback: async () => Promise.resolve(),
      switchToBranch: async () => Promise.resolve(),
      unstable_copy: async () => Promise.resolve(),
      unstable_edit: async () => Promise.resolve(),
      unstable_getAttachmentByIndex: () => ({
        path: { ref: 'attachment', threadSelector: { type: 'main' }, messageSelector: { type: 'messageId', messageId: '' }, attachmentSource: 'message', attachmentSelector: { type: 'index', index: 0 } },
        source: 'message' as const,
        getState: () => ({
          id: '',
          type: 'file',
          name: '',
          contentType: 'application/octet-stream',
          status: { type: 'running', reason: 'uploading', progress: 0 },
          file: new File([], ''),
          source: 'message',
        }),
        subscribe: () => () => {},
        remove: async () => Promise.resolve(),
      }),
      unstable_reload: async () => Promise.resolve(),
      unstable_getCopyText: () => '',
      getContentPartByIndex: () => ({
        type: 'text',
        text: '',
        addToolResult: async () => Promise.resolve(),
        path: { ref: 'content-part', threadSelector: { type: 'main' }, messageSelector: { type: 'messageId', messageId: '' }, contentPartSelector: { type: 'index', index: 0 } },
        getState: () => ({
          type: 'text',
          text: '',
          status: { type: 'complete' } as const,
        }),
        subscribe: () => () => {},
      }),
      getContentPartByToolCallId: () => ({
        type: 'text',
        text: '',
        addToolResult: async () => Promise.resolve(),
        path: { ref: 'content-part', threadSelector: { type: 'main' }, messageSelector: { type: 'messageId', messageId: '' }, contentPartSelector: { type: 'toolCallId', toolCallId: '' } },
        getState: () => ({
          type: 'text',
          text: '',
          status: { type: 'complete' } as const,
        }),
        subscribe: () => () => {},
      }),
      getAttachmentByIndex: () => ({
        path: { ref: 'attachment', threadSelector: { type: 'main' }, messageSelector: { type: 'messageId', messageId: '' }, attachmentSource: 'message', attachmentSelector: { type: 'index', index: 0 } },
        source: 'message' as const,
        getState: () => ({
          id: '',
          type: 'file',
          name: '',
          contentType: 'application/octet-stream',
          status: { type: 'complete' } as const,
          content: [],
          file: new File([], ''),
          source: 'message',
        }),
        subscribe: () => () => {},
        remove: async () => Promise.resolve(),
      }),
    }),
    stopSpeaking: () => {},
    unstable_on: () => () => {},
  };

  const threadListRuntime: ThreadListRuntime = {
    ...threadListState,
    getState: () => threadListState,
    subscribe: () => () => {},
    mainItem: {
      ...threadListItemState,
      getState: () => threadListItemState,
      subscribe: () => () => {},
      path: { ref: 'thread-list-item', threadSelector: { type: 'main' } },
      switchTo: async () => Promise.resolve(),
      rename: async () => Promise.resolve(),
      archive: async () => Promise.resolve(),
      unarchive: async () => Promise.resolve(),
      delete: async () => Promise.resolve(),
      unstable_on: () => () => {},
    },
    getItemById: (threadId: string): ThreadListItemRuntime => {
      const session = customRuntime.sessions.find(session => session.id === threadId);
      const item: ThreadListItemRuntime = {
        getState: () => threadListItemState,
        subscribe: () => () => {},
        path: { ref: 'thread-list-item', threadSelector: { type: 'threadId', threadId: session?.id || threadId } },
        switchTo: async () => Promise.resolve(),
        rename: async () => Promise.resolve(),
        archive: async () => Promise.resolve(),
        unarchive: async () => Promise.resolve(),
        delete: async () => Promise.resolve(),
        unstable_on: () => () => {},
      };
      return item;
    },
    getItemByIndex: (index: number): ThreadListItemRuntime => {
      const session = customRuntime.sessions[index];
      const item: ThreadListItemRuntime = {
        getState: () => threadListItemState,
        subscribe: () => () => {},
        path: { ref: 'thread-list-item', threadSelector: { type: 'index', index } },
        switchTo: async () => Promise.resolve(),
        rename: async () => Promise.resolve(),
        archive: async () => Promise.resolve(),
        unarchive: async () => Promise.resolve(),
        delete: async () => Promise.resolve(),
        unstable_on: () => () => {},
      };
      return item;
    },
    getArchivedItemByIndex: (index: number): ThreadListItemRuntime => {
      const item: ThreadListItemRuntime = {
        getState: () => threadListItemState,
        subscribe: () => () => {},
        path: { ref: 'thread-list-item', threadSelector: { type: 'archiveIndex', index } },
        switchTo: async () => Promise.resolve(),
        rename: async () => Promise.resolve(),
        archive: async () => Promise.resolve(),
        unarchive: async () => Promise.resolve(),
        delete: async () => Promise.resolve(),
        unstable_on: () => () => {},
      };
      return item;
    },
  };

  const assistantRuntime: AssistantRuntime = {
    thread: threadRuntime,
    threadList: threadListRuntime,
    switchToNewThread: async () => Promise.resolve(),
    switchToThread: async () => Promise.resolve(),
    registerModelConfigProvider: () => () => {},
  };

  return assistantRuntime;
};

export default function MyRuntimeProvider({ children }: { children: React.ReactNode }) {
  const [teammates, setTeammates] = useState<Teammate[]>([])
  const [selectedTeammate, setSelectedTeammate] = useState<string>()
  const [error, setError] = useState<string | null>()
  const [isLoading, setIsLoading] = useState(true)
  const [tools, setTools] = useState<Tool[]>([])
  const [starters, setStarters] = useState<Starter[]>([])
  const [sessions, setSessions] = useState<Session[]>([])
  const [currentPage, setCurrentPage] = useState(1)
  const [sourcesData, setSourcesData] = useState<SourceMetadata[]>([])
  const [isToolsModalOpen, setIsToolsModalOpen] = useState(false)
  const toolsPerPage = 5
  const [searchQuery, setSearchQuery] = useState('')
  const [messages, setMessages] = useState<string[]>([])
  const messageBufferRef = useRef<{[key: string]: string}>({})
  const toolStatesRef = useRef<{[key: string]: ToolState}>({})

  // Use the custom hook to manage runtime
  const customRuntime = useKubiyaRuntime(selectedTeammate, sessions, setSessions);
  const assistantRuntime = customRuntimeToAssistantRuntime(customRuntime);

  if (!assistantRuntime) {
    return null;
  }

  const clearMessages = () => {
    setError(null);
    setMessages([]);
    messageBufferRef.current = {};
    toolStatesRef.current = {};
    if (customRuntime && customRuntime.tool_calls) {
      customRuntime.tool_calls = {};
    }
  };

  const processMessage = (message: any) => {
    if (!customRuntime) return;
    console.log('Processing message:', message);

    try {
      // Buffer incoming chunks
      const messageId = typeof message === 'object' && message !== null ? message.id : undefined;
      if (messageId) {
        messageBufferRef.current[messageId] = (messageBufferRef.current[messageId] || '') + message;
        console.log('Buffered message:', messageBufferRef.current[messageId]);

        // Check if the message is complete (e.g., ends with a specific delimiter)
        if (!message.endsWith('}')) return;

        // Parse the complete message
        let parsedMessage = messageBufferRef.current[messageId];
        delete messageBufferRef.current[messageId]; // Clear the buffer for this message ID

        if (typeof parsedMessage === 'string') {
          try {
            parsedMessage = JSON.parse(parsedMessage);
          } catch (error) {
            console.error('Error parsing message:', error, { message: parsedMessage });
            return;
          }
        }

        console.log('Parsed message:', parsedMessage);

        // Handle different message types explicitly
        if (typeof parsedMessage === 'object' && parsedMessage !== null && 'type' in parsedMessage && 'message' in parsedMessage && 'id' in parsedMessage) {
          const { type, message: messageContent, id } = parsedMessage;
          switch (type) {
            case 'tool':
              if (typeof messageContent === 'string') {
                console.log('Tool message received:', messageContent);
                const toolMatch = /Tool: (.*?)\nArguments: (.*)/.exec(messageContent);
                if (toolMatch) {
                  const [_, toolName, argsStr] = toolMatch;
                  try {
                    const args = JSON.parse(argsStr);
                    console.log('Parsed tool arguments:', args);
                    setMessages(prev => [...prev, `[Tool] ${messageContent}`]);
                    // Update tool states ref for persistence
                    if (typeof id === 'string') {
                      toolStatesRef.current[id] = {
                        toolName,
                        args,
                        status: { type: 'running' },
                        result: {}
                      };
                    }
                  } catch (error) {
                    console.error('Error parsing tool arguments:', error, { argsStr });
                  }
                } else {
                  console.error('Tool message format mismatch:', messageContent);
                }
              }
              break;
            case 'tool_init':
              if (typeof messageContent === 'string') {
                console.log('Tool initialization message received:', messageContent);
              }
              break;
            case 'tool_output':
              if (typeof messageContent === 'string') {
                console.log('Tool output message received:', messageContent);
              }
              // Update tool state with output
              if (typeof id === 'string' && toolStatesRef.current[id]) {
                toolStatesRef.current[id].result = messageContent;
                console.log('Tool output updated:', toolStatesRef.current[id]);
              }
              break;
            case 'msg':
              if (typeof messageContent === 'string') {
                console.log('Regular message received:', messageContent);
                setMessages(prev => [...prev, messageContent]);
              }
              break;
            case 'system_message':
              if (typeof messageContent === 'string') {
                console.log('System message received:', messageContent);
                setMessages(prev => [...prev, `[System] ${messageContent}`]);
              }
              break;
            default:
              console.log('Unknown message type:', type);
              if (typeof messageContent === 'string') {
                setMessages(prev => [...prev, `[Unknown] ${messageContent}`]);
              }
          }

          customRuntime.onEvent?.({
            type,
            content: messageContent,
            messageId: id,
            timestamp: new Date().toISOString()
          });
        }
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error processing message';
      console.error('Error processing message:', errorMessage, { message });
      setError(errorMessage);
    }
  };

  return (
    <AssistantRuntimeProvider runtime={assistantRuntime}>
      <RuntimeContext.Provider 
        value={{
          processMessage,
          clearMessages
        }}
      >
        <div className="relative">
          {isLoading && (
            <div className="fixed inset-0 bg-white/50 flex items-center justify-center z-50">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
          )}
          {error && (
            <div className="fixed top-4 right-4 bg-red-50 text-red-700 px-4 py-2 rounded-lg shadow-lg">
              {error}
            </div>
          )}
          <ToolUI>
            {children}
            {/* Show text messages */}
            <div className="space-y-4 p-4">
              {messages.length === 0 ? (
                <div className="text-sm text-gray-500">No messages yet</div>
              ) : (
                messages.map((msg, i) => {
                  console.log('Rendering message:', msg)
                  let parsedMsg = msg;
                  if (typeof msg === 'string') {
                    try {
                      parsedMsg = JSON.parse(msg);
                    } catch (error) {
                      console.error('Error parsing message:', error);
                    }
                  }
                  if (typeof parsedMsg === 'object' && parsedMsg !== null && 'type' in parsedMsg && 'message' in parsedMsg && 'id' in parsedMsg) {
                    const { type, message: messageContent, id } = parsedMsg;
                    if (type === 'system_message') {
                      return (
                        <div key={i}>
                          <SystemMessageUI message={messageContent} />
                        </div>
                      );
                    } else if (type === 'tool') {
                      const toolMatch = typeof messageContent === 'string' ? /Tool: (.*?)\nArguments: (.*)/.exec(messageContent) : null;
                      if (toolMatch) {
                        const [_, toolName, argsStr] = toolMatch;
                        const args = JSON.parse(argsStr);
                        const toolState = typeof id === 'string' ? toolStatesRef.current[id] : undefined;
                        return (
                          <div key={i}>
                            <ToolExecutionUI 
                              toolName={toolName} 
                              args={args}
                              status={toolState?.status}
                              result={toolState?.result}
                            />
                          </div>
                        );
                      }
                    }
                  }
                  return (
                    <div key={i.toString()}>{typeof msg === 'string' ? msg : JSON.stringify(msg)}</div>
                  );
                })
              )}
            </div>
          </ToolUI>
        </div>
      </RuntimeContext.Provider>
    </AssistantRuntimeProvider>
  );
} 