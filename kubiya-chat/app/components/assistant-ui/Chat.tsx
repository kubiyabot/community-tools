"use client";

import { useEffect, useState } from 'react';
import { useUser } from '@auth0/nextjs-auth0/client';
import { useRouter } from 'next/navigation';
import { useAssistantRuntime, useThread, useThreadRuntime, ThreadMessage } from '@assistant-ui/react';
import { useTeammateContext } from '../../MyRuntimeProvider';
import { ChatInput } from './ChatInput';
import { ChatMessages } from './ChatMessages';
import { ThreadsSidebar } from './ThreadsSidebar';

interface StoredState {
  threadId?: string;
  threads: ThreadInfo[];
  lastSelectedTeammate?: string;
}

interface ThreadInfo {
  id: string;
  title: string;
  lastMessage?: string;
  createdAt: string;
  updatedAt: string;
  teammateId: string;
}

export const Chat = () => {
  const { user, isLoading } = useUser();
  const router = useRouter();
  const runtime = useAssistantRuntime();
  const { selectedTeammate, setSelectedTeammate } = useTeammateContext();
  const thread = useThread();
  const threadRuntime = useThreadRuntime();
  const [storedState, setStoredState] = useState<StoredState>({
    threads: [],
  });
  
  // Load stored state on mount
  useEffect(() => {
    const stored = localStorage.getItem('chatState');
    if (stored) {
      const parsedState = JSON.parse(stored);
      setStoredState(parsedState);
      
      // If there's a last selected teammate, restore it
      if (parsedState.lastSelectedTeammate) {
        setSelectedTeammate(parsedState.lastSelectedTeammate);
      }
    }
  }, [setSelectedTeammate]);

  // Save state changes to localStorage
  useEffect(() => {
    if (storedState.threadId || storedState.threads.length > 0) {
      localStorage.setItem('chatState', JSON.stringify({
        ...storedState,
        lastSelectedTeammate: selectedTeammate
      }));
    }
  }, [storedState, selectedTeammate]);

  // Update thread info when messages change
  useEffect(() => {
    if (!thread?.messages.length || !selectedTeammate || !storedState.threadId) return;
    
    const lastMessage = thread.messages[thread.messages.length - 1];
    const lastMessageText = lastMessage.content.find(c => 'text' in c && c.type === 'text')?.text || '';
    const now = new Date().toISOString();
    
    setStoredState(prev => {
      const existingThreadIndex = prev.threads.findIndex(t => t.id === prev.threadId);
      const updatedThread: ThreadInfo = {
        id: prev.threadId!,
        title: prev.threads[existingThreadIndex]?.title || 'New Conversation',
        lastMessage: lastMessageText,
        createdAt: prev.threads[existingThreadIndex]?.createdAt || now,
        updatedAt: now,
        teammateId: selectedTeammate
      };

      const updatedThreads = [...prev.threads];
      if (existingThreadIndex >= 0) {
        updatedThreads[existingThreadIndex] = updatedThread;
      } else {
        updatedThreads.unshift(updatedThread);
      }

      return {
        ...prev,
        threads: updatedThreads
      };
    });
  }, [thread?.messages, selectedTeammate, storedState.threadId]);

  const handleSubmit = async (message: string) => {
    if (!thread || !threadRuntime || !selectedTeammate) return;

    // Add message to thread
    await threadRuntime.append({
      role: 'user',
      content: [{ type: 'text', text: message }]
    });

    try {
      // Generate a unique session ID if none exists
      if (!storedState.threadId) {
        const newThreadId = Date.now().toString();
        setStoredState(prev => ({ ...prev, threadId: newThreadId }));
      }

      const response = await fetch('/api/converse', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive'
        },
        credentials: 'same-origin',
        body: JSON.stringify({
          message,
          agent_uuid: selectedTeammate,
          session_id: storedState.threadId || Date.now().toString()
        })
      });

      if (!response.ok) {
        const errorText = await response.text().catch(() => null);
        throw new Error(`API error: ${response.status}${errorText ? ` - ${errorText}` : ''}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      try {
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (!line.trim() || !line.startsWith('data: ')) continue;
            
            const data = line.slice(6);
            if (data === '[DONE]') break;
            
            try {
              console.log('[Chat] Received event:', data);
              const event = JSON.parse(data);
              if (event.type === 'assistant' || event.type === 'msg' || event.type === 'system_message') {
                console.log('[Chat] Processing message:', event);
                await threadRuntime.append({
                  role: 'assistant',
                  content: [{ 
                    type: 'text', 
                    text: event.message || event.content || '' 
                  }]
                });
              } else if (event.error) {
                console.error('[Chat] Stream error:', event.error);
                throw new Error(event.error);
              }
            } catch (e) {
              console.error('[Chat] Failed to parse event:', e, 'Raw data:', data);
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      // Add error message to thread
      await threadRuntime.append({
        role: 'assistant',
        content: [{ 
          type: 'text', 
          text: 'Sorry, there was an error sending your message. Please try again.' 
        }]
      });
    }
  };

  const handleNewThread = () => {
    const newThreadId = Date.now().toString();
    setStoredState(prev => ({
      ...prev,
      threadId: newThreadId,
      threads: [{
        id: newThreadId,
        title: 'New Conversation',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        teammateId: selectedTeammate || ''
      }, ...prev.threads]
    }));
  };

  const handleThreadSelect = (threadId: string) => {
    setStoredState(prev => ({
      ...prev,
      threadId
    }));
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        Loading...
      </div>
    );
  }

  if (!user) {
    router.push('/api/auth/login');
    return null;
  }

  return (
    <div className="flex h-full">
      <ThreadsSidebar
        threads={storedState.threads}
        currentThreadId={storedState.threadId}
        onThreadSelect={handleThreadSelect}
        onNewThread={handleNewThread}
      />
      <div className="flex-1 flex flex-col h-full">
        <ChatMessages messages={thread?.messages as ThreadMessage[]} />
        <ChatInput onSubmit={handleSubmit} isDisabled={!selectedTeammate} />
      </div>
    </div>
  );
}; 