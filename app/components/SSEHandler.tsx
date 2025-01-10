'use client'

import React, { useEffect, useRef } from 'react'
import { useRuntime } from './RuntimeProvider'

export function SSEHandler() {
  const { processMessage } = useRuntime()
  const messageBuffer = useRef<{[key: string]: string}>({})

  useEffect(() => {
    const handleSSEMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        console.log('SSE message received:', data)

        // If it's a tool message, accumulate until complete
        if (data.type === 'tool') {
          const currentBuffer = messageBuffer.current[data.id] || ''
          const newBuffer = currentBuffer + data.message

          // Check if the message is complete (has closing brace)
          if (newBuffer.includes('}')) {
            // Process complete message
            processMessage({
              ...data,
              message: newBuffer.trim()
            })
            // Clear buffer for this message ID
            delete messageBuffer.current[data.id]
          } else {
            // Store incomplete message
            messageBuffer.current[data.id] = newBuffer
          }
        } else {
          // For non-tool messages, process immediately
          processMessage(data)
        }
      } catch (error) {
        console.error('Error processing SSE message:', error)
      }
    }

    // Set up event source for SSE
    const eventSource = new EventSource('/api/converse')
    
    eventSource.onmessage = handleSSEMessage
    eventSource.onerror = (error) => {
      console.error('SSE error:', error)
      eventSource.close()
    }

    return () => {
      eventSource.close()
    }
  }, [processMessage])

  return null // This component doesn't render anything
} 