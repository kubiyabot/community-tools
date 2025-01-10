'use client'

import React, { createContext, useContext, useEffect, useState, useRef, type PropsWithChildren } from 'react'
import { AssistantRuntimeProvider, ThreadPrimitive, MessagePrimitive, ContentPart, TextContentPartProvider } from "@assistant-ui/react"
import { ToolUI, SystemMessageUI, ToolExecutionUI } from './ToolUI'
import { customRuntimeToAssistantRuntime } from '../MyRuntimeProvider'

interface RuntimeContextType {
  processMessage: (message: any) => void
  clearMessages: () => void
}

interface ToolStatus {
  type: 'running' | 'complete' | 'error'
}

export interface ToolState {
  toolName?: string
  args?: any
  status: ToolStatus
  result?: {
    output?: string
    error?: string
  }
}

interface CustomRuntime {
  config: {
    teammate: string
  }
  processMessage: (message: any) => Promise<any>
  sessions: {
    id: string
    messages: any[]
  }[]
  run?: (options: { messages: any[] }) => AsyncGenerator<any, void, unknown>
  emit?: (event: string, data: any) => void
  tool_calls?: {
    [key: string]: {
      name: string
      args: any
      status: ToolStatus
      result?: any
    }
  }
  onEvent?: (event: any) => void
}

const RuntimeContext = createContext<RuntimeContextType | null>(null)

export function RuntimeProvider({ children }: PropsWithChildren) {
  const [error, setError] = useState<string | null>(null)
  const [messages, setMessages] = useState<string[]>([])
  const [toolStates, setToolStates] = useState<{[key: string]: ToolState}>({})
  const [mounted, setMounted] = useState(false)
  const messageBufferRef = useRef<{[key: string]: string}>({})
  const toolStatesRef = useRef<{[key: string]: ToolState}>({})
  const runtime = useRef<CustomRuntime>({
    config: {
      teammate: ''
    },
    processMessage: async (message: any) => {
      console.log('Processing message:', message)
      return message
    },
    sessions: [],
    tool_calls: {},
    run: async function* ({ messages }) {
      for (const message of messages) {
        yield {
          content: [
            {
              type: 'text',
              text: message
            }
          ]
        }
      }
    },
    onEvent: (event: any) => {
      console.log('Event received:', event)
    }
  })

  useEffect(() => {
    setMounted(true)
    console.log('RuntimeProvider mounted')

    // Add emit handler
    runtime.current.emit = (event: string, data: any) => {
      console.log('Runtime emit:', event, data)

      if (event === 'content') {
        if (data.type === 'text') {
          setMessages(prev => [...prev, data.text])
        }
      } else if (event === 'tool_call') {
        runtime.current.tool_calls = runtime.current.tool_calls || {}
        runtime.current.tool_calls[data.id] = {
          name: data.name,
          args: data.args,
          status: data.status,
          result: data.result
        }
        console.log('Tool call state updated:', runtime.current.tool_calls[data.id])
        
        // Update tool states ref and state for persistence and rendering
        const newToolState: ToolState = {
          toolName: data.name,
          args: data.args,
          status: { type: 'running' as const },
          result: data.result
        }
        toolStatesRef.current[data.id] = newToolState
        setToolStates(prev => ({
          ...prev,
          [data.id]: newToolState
        }))
      }
    }

    // Setup SSE connection
    const eventSource = new EventSource('/api/sse')
    eventSource.onopen = () => {
      console.log('SSE connection opened')
    }
    eventSource.onmessage = (event) => {
      console.log('SSE message received:', event.data)
      try {
        const parsedData = JSON.parse(event.data);
        console.log('Parsed SSE message:', parsedData);
        
        // If it's a tool message, process it directly
        if (parsedData.type === 'tool' && parsedData.message) {
          const toolMatch = /Tool: (.*?)\nArguments: ({.*})/.exec(parsedData.message);
          if (toolMatch) {
            const [_, toolName, argsStr] = toolMatch;
            try {
              const args = JSON.parse(argsStr);
              console.log('Processing tool message:', { toolName, args, messageId: parsedData.id });
              
              // Update tool state
              const newToolState: ToolState = {
                toolName,
                args,
                status: { type: 'running' as const },
                result: {}
              };
              
              if (parsedData.id) {
                toolStatesRef.current[parsedData.id] = newToolState;
                // Update the state to trigger re-render
                setToolStates(prev => ({
                  ...prev,
                  [parsedData.id]: newToolState
                }));

                // Store the complete message
                setMessages(prev => [...prev, JSON.stringify({
                  type: 'tool',
                  message: parsedData.message,
                  id: parsedData.id,
                  toolState: newToolState // Include tool state in the message
                })]);

                // Emit tool call event
                runtime.current.emit?.('tool_call', {
                  id: parsedData.id,
                  name: toolName,
                  args,
                  status: { type: 'running' as const }
                });
              }
            } catch (error) {
              console.error('Error processing tool message:', error);
            }
          } else {
            // If we don't have complete arguments yet, buffer the message
            if (parsedData.id) {
              messageBufferRef.current[parsedData.id] = (messageBufferRef.current[parsedData.id] || '') + parsedData.message;
              console.log('Buffering tool message:', messageBufferRef.current[parsedData.id]);
            }
          }
        } else {
          // Process other messages normally
          handleMessage(parsedData.type, parsedData.message, parsedData.id);
        }
      } catch (error) {
        console.error('Error handling SSE message:', error);
        processMessage(event.data);
      }
    }
    eventSource.onerror = (error) => {
      console.error('SSE error:', error)
      setError('SSE connection error')
    }

    return () => {
      eventSource.close()
      console.log('SSE connection closed')
    }
  }, [])

  const clearMessages = () => {
    setError(null)
    setMessages([])
    messageBufferRef.current = {}
    toolStatesRef.current = {}
    if (runtime.current.tool_calls) {
      runtime.current.tool_calls = {}
    }
  }

  const processMessage = (message: any) => {
    console.log('Processing message:', message)

    try {
      // Try to parse if message is a string
      let parsedMessage = message;
      if (typeof message === 'string') {
        try {
          parsedMessage = JSON.parse(message);
        } catch (error) {
          console.error('Error parsing message string:', error);
          return;
        }
      }

      // Handle the message object
      if (typeof parsedMessage === 'object' && parsedMessage !== null && 'type' in parsedMessage && 'message' in parsedMessage) {
        const { type, message: messageContent, id: messageId } = parsedMessage;
        console.log('Processing parsed message:', { type, messageContent, messageId });

        // For tool messages, wait until we have a complete message
        if (type === 'tool' && typeof messageContent === 'string') {
          const toolMatch = /Tool: (.*?)\nArguments: ({.*})/.exec(messageContent);
          if (!toolMatch) {
            // If we don't have complete arguments yet, buffer the message
            if (messageId) {
              messageBufferRef.current[messageId] = (messageBufferRef.current[messageId] || '') + messageContent;
              console.log('Buffering tool message:', messageBufferRef.current[messageId]);
              return;
            }
          }
        }

        handleMessage(type, messageContent, messageId);
        return;
      }

      console.error('Invalid message format:', message);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error processing message';
      console.error('Error processing message:', errorMessage);
      setError(errorMessage);
    }
  }

  const handleMessage = (type: string, messageContent: any, messageId?: string) => {
    console.log('Handling message:', { type, messageContent, messageId });
    
    switch (type) {
      case 'tool':
        if (typeof messageContent === 'string') {
          console.log('Tool message received:', messageContent);
          // Try to get buffered content first
          const bufferedContent = messageId ? messageBufferRef.current[messageId] || messageContent : messageContent;
          const toolMatch = /Tool: (.*?)\nArguments: ({.*})/.exec(bufferedContent);
          
          if (toolMatch) {
            const [_, toolName, argsStr] = toolMatch;
            try {
              const args = JSON.parse(argsStr);
              console.log('Parsed tool arguments:', { toolName, args });
              
              // Create new tool state
              const newToolState: ToolState = {
                toolName,
                args,
                status: { type: 'running' as const },
                result: {}
              };

              // Update tool states
              if (messageId) {
                toolStatesRef.current[messageId] = newToolState;
                setToolStates(prev => ({
                  ...prev,
                  [messageId]: newToolState
                }));
                console.log('Updated tool states:', { ref: toolStatesRef.current[messageId], state: newToolState });
              }

              // Store the complete message object with tool state
              const completeMessage = {
                type,
                message: bufferedContent,
                id: messageId,
                toolState: newToolState
              };
              console.log('Storing complete message:', completeMessage);
              setMessages(prev => [...prev, JSON.stringify(completeMessage)]);
              
              // Clear the buffer
              if (messageId) {
                delete messageBufferRef.current[messageId];
              }

              // Emit tool call event
              runtime.current.emit?.('tool_call', {
                id: messageId,
                name: toolName,
                args,
                status: { type: 'running' as const }
              });
            } catch (error) {
              console.error('Error parsing tool arguments:', error, { argsStr });
            }
          } else {
            console.log('Incomplete tool message, buffering:', messageContent);
            if (messageId) {
              messageBufferRef.current[messageId] = (messageBufferRef.current[messageId] || '') + messageContent;
            }
          }
        }
        break;
      case 'tool_output':
        if (typeof messageContent === 'string') {
          console.log('Tool output message received:', messageContent);
          setMessages(prev => [...prev, `[Tool Output] ${messageContent}`]);
          
          // Update tool state with output
          if (messageId && toolStatesRef.current[messageId]) {
            toolStatesRef.current[messageId].status = { type: 'complete' };
            toolStatesRef.current[messageId].result = { output: messageContent };
            console.log('Updated tool state with output:', toolStatesRef.current[messageId]);

            // Emit tool call completion
            runtime.current.emit?.('tool_call', {
              id: messageId,
              name: toolStatesRef.current[messageId].toolName,
              args: toolStatesRef.current[messageId].args,
              status: { type: 'complete' },
              result: { output: messageContent }
            });
          }
        }
        break;
      case 'system_message':
        if (typeof messageContent === 'string') {
          console.log('System message received:', messageContent);
          setMessages(prev => [...prev, messageContent]);
        }
        break;
      case 'msg':
        if (typeof messageContent === 'string') {
          console.log('Regular message received:', messageContent);
          setMessages(prev => [...prev, messageContent]);
        }
        break;
      default:
        console.log('Unknown message type:', type);
        if (typeof messageContent === 'string') {
          setMessages(prev => [...prev, messageContent]);
        }
    }

    // Forward to runtime
    runtime.current.onEvent?.({
      type,
      content: messageContent,
      messageId,
      timestamp: new Date().toISOString()
    });
  }

  if (!mounted) return null

  // Convert CustomRuntime to AssistantRuntime
  const assistantRuntime = customRuntimeToAssistantRuntime(runtime.current)
  if (!assistantRuntime) {
    return <div>Loading runtime...</div>
  }

  // Log current messages state in render
  console.log('Rendering with messages:', messages)

  return (
    <AssistantRuntimeProvider runtime={assistantRuntime}>
      <RuntimeContext.Provider value={{ processMessage, clearMessages }}>
        <div className="flex flex-col min-h-0 relative">
          <div className="flex-1 overflow-y-auto">
            <div className="flex h-full flex-col items-center pb-3">
              <div className="flex w-full flex-grow flex-col items-center overflow-y-scroll scroll-smooth px-4 pt-12">
                <div className="space-y-4 w-full max-w-2xl">
                  {messages.map((message, index) => {
                    console.log('Rendering message:', message);
                    try {
                      const parsedMessage = JSON.parse(message);
                      console.log('Parsed message for rendering:', parsedMessage);
                      
                      if (parsedMessage.type === 'tool') {
                        const toolId = parsedMessage.id;
                        const toolState = parsedMessage.toolState || toolStates[toolId];
                        console.log('Tool state for rendering:', { toolId, toolState, fromMessage: !!parsedMessage.toolState, fromState: !!toolStates[toolId] });
                        
                        if (toolState) {
                          return (
                            <div key={`tool-${index}`} className="relative mb-6 flex w-full max-w-2xl gap-3 bg-gray-50 rounded-lg p-4">
                              <div className="mt-2 flex-grow">
                                <div className="font-medium mb-2">Running tool: {toolState.toolName}</div>
                                <pre className="text-sm mb-2 text-gray-600">
                                  {JSON.stringify(toolState.args, null, 2)}
                                </pre>
                                <ToolExecutionUI
                                  toolName={toolState.toolName || ''}
                                  args={toolState.args}
                                  status={toolState.status}
                                  result={toolState.result}
                                />
                              </div>
                            </div>
                          );
                        }
                      } else if (parsedMessage.type === 'tool_output') {
                        return (
                          <div key={`output-${index}`} className="relative mb-6 flex w-full max-w-2xl gap-3">
                            <div className="mt-2 flex-grow">
                              <p className="text-sm text-gray-800 whitespace-pre-wrap">
                                {parsedMessage.message}
                              </p>
                            </div>
                          </div>
                        );
                      } else if (parsedMessage.type === 'system_message') {
                        return (
                          <div key={`system-${index}`} className="relative mb-6 flex w-full max-w-2xl gap-3">
                            <div className="mt-2 flex-grow">
                              <SystemMessageUI message={parsedMessage.message} />
                            </div>
                          </div>
                        );
                      }
                      
                      // Default message rendering
                      return (
                        <div key={`message-${index}`} className="relative mb-6 flex w-full max-w-2xl gap-3">
                          <div className="mt-2 flex-grow">
                            <p className="text-sm text-gray-800 whitespace-pre-wrap">
                              {parsedMessage.message}
                            </p>
                          </div>
                        </div>
                      );
                    } catch (e) {
                      // If not a JSON string, render as text
                      console.log('Failed to parse message:', e);
                      return (
                        <div key={`text-${index}`} className="relative mb-6 flex w-full max-w-2xl gap-3">
                          <div className="mt-2 flex-grow">
                            <p className="text-sm text-gray-800 whitespace-pre-wrap">
                              {message}
                            </p>
                          </div>
                        </div>
                      );
                    }
                  })}
                </div>
              </div>
            </div>
          </div>
          {error && (
            <div className="sticky bottom-0 p-4 bg-red-50 border-t border-red-200">
              <div className="flex items-center space-x-2 text-red-700">
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <p className="text-sm">{error}</p>
              </div>
            </div>
          )}
        </div>
      </RuntimeContext.Provider>
    </AssistantRuntimeProvider>
  )
}

export function useRuntime() {
  const context = useContext(RuntimeContext)
  if (!context) {
    throw new Error('useRuntime must be used within a RuntimeProvider')
  }
  return context
} 