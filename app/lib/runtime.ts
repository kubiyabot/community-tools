import React, { useCallback, useEffect, useRef } from 'react'
import { ModelAdapter } from './adapters'

export interface Session {
  id: string
  messages: any[]
}

export interface RuntimeOptions {
  config: any
  sessions: Session[]
  setSessions: React.Dispatch<React.SetStateAction<Session[]>>
}

export interface Runtime {
  config: any
  processMessage: (message: any) => Promise<any>
  sessions: Session[]
}

export interface CustomRuntime extends Runtime {
  emit?: (event: string, data: any) => void
  tool_calls?: {
    [key: string]: {
      name: string
      args: any
      status: { type: 'running' | 'complete' | 'error' }
      result?: any
    }
  }
  onEvent?: (event: any) => void
}

export function useLocalRuntime(adapter: ModelAdapter, options: RuntimeOptions): CustomRuntime {
  const { config, sessions, setSessions } = options
  const eventSourceRef = useRef<EventSource | null>(null)

  const processMessage = useCallback(async (message: any) => {
    try {
      const response = await adapter.processMessage(message)
      return response
    } catch (error) {
      console.error('Error processing message:', error)
      throw error
    }
  }, [adapter])

  useEffect(() => {
    // Clean up any existing event source
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    // Create new event source if we have a teammate
    if (adapter.id) {
      const eventSource = new EventSource(`/api/stream?teammate=${adapter.id}`)
      eventSourceRef.current = eventSource

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          // Update sessions with new message
          setSessions((prev: Session[]) => {
            const currentSession = prev[prev.length - 1] || { id: Date.now().toString(), messages: [] }
            return [
              ...prev.slice(0, -1),
              {
                ...currentSession,
                messages: [...currentSession.messages, data]
              }
            ]
          })
        } catch (error) {
          console.error('Error processing SSE message:', error)
        }
      }

      eventSource.onerror = (error) => {
        console.error('SSE error:', error)
        eventSource.close()
      }

      return () => {
        eventSource.close()
      }
    }
  }, [adapter.id, setSessions])

  const runtime: CustomRuntime = {
    config,
    processMessage,
    sessions,
    emit: undefined,
    tool_calls: {},
    onEvent: undefined
  }

  return runtime
} 