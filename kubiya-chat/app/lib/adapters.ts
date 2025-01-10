export interface Message {
  type: 'tool' | 'msg' | 'system_message'
  id: string
  message: string
  session_id?: string
}

export interface ModelAdapter {
  id: string
  type: string
  processMessage: (message: Message) => Promise<Message>
}

export function createKubiyaModelAdapter(teammate: string | undefined): ModelAdapter {
  return {
    id: teammate || '',
    type: 'kubiya',
    async processMessage(message: Message) {
      try {
        const response = await fetch('/api/converse', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message,
            teammate_id: teammate,
          }),
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        return await response.json()
      } catch (error) {
        console.error('Error processing message:', error)
        throw error
      }
    }
  }
} 