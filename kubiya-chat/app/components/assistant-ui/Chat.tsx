"use client";

import { useEffect, useState, useCallback } from 'react';
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
  const { user, isLoading: userLoading } = useUser();
  const router = useRouter();
  const runtime = useAssistantRuntime();
  const { selectedTeammate, setSelectedTeammate, isLoading: teammateLoading } = useTeammateContext();
  const thread = useThread();
  const threadRuntime = useThreadRuntime();
  const [storedState, setStoredState] = useState<StoredState>({
    threads: [],
  });
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Load stored state on mount only
  useEffect(() => {
    const stored = localStorage.getItem('chatState');
    if (!stored) return;

    try {
      const parsedState = JSON.parse(stored);
      setStoredState(parsedState);
      
      // If we have a stored teammate but none selected, restore it
      if (parsedState.lastSelectedTeammate && !selectedTeammate) {
        setSelectedTeammate(parsedState.lastSelectedTeammate);
      }
    } catch (e) {
      console.error('Failed to parse stored chat state:', e);
    }
  }, [selectedTeammate, setSelectedTeammate]);

  // Save teammate selection
  useEffect(() => {
    if (selectedTeammate) {
      const stored = localStorage.getItem('chatState');
      const parsedState = stored ? JSON.parse(stored) : { threads: [] };
      const updatedState = {
        ...parsedState,
        lastSelectedTeammate: selectedTeammate
      };
      localStorage.setItem('chatState', JSON.stringify(updatedState));
    }
  }, [selectedTeammate]);

  // Save state changes to localStorage
  useEffect(() => {
    if (!storedState.threadId && storedState.threads.length === 0) return;

    const stateToStore = {
      ...storedState,
      lastSelectedTeammate: selectedTeammate
    };
    localStorage.setItem('chatState', JSON.stringify(stateToStore));
  }, [storedState.threadId, storedState.threads, selectedTeammate]);

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
    if (!selectedTeammate) {
      setError('Please select a teammate first');
      return;
    }

    if (isProcessing) {
      return;
    }

    setError(null);
    setIsProcessing(true);

    try {
      // Create or get thread ID
      const threadId = storedState.threadId || Date.now().toString();
      if (!storedState.threadId) {
        setStoredState(prev => ({
          ...prev,
          threadId,
          threads: [{
            id: threadId,
            title: 'New Conversation',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            teammateId: selectedTeammate
          }, ...prev.threads]
        }));
      }

      // Log the request details for debugging
      console.log('[Chat] Sending message:', {
        message,
        teammate: selectedTeammate,
        threadId,
        sessionId: threadId
      });

      // Append user message to thread
      await threadRuntime.append({
        role: 'user',
        content: [{ type: 'text', text: message }]
      });
      
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive'
        },
        body: JSON.stringify({
          message: message.trim(),
          agent_uuid: selectedTeammate,
          thread_id: threadId,
          session_id: threadId
        })
      });

      if (!response.ok) {
        let errorMessage = 'Failed to send message';
        try {
          const errorData = await response.json();
          errorMessage = errorData.details || errorData.error || response.statusText;
          console.error('Chat error:', errorData);

          if (response.status === 401) {
            router.push('/api/auth/login');
            return;
          }
        } catch (e) {
          console.error('Failed to parse error response:', e);
        }
        setError(errorMessage);
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        setError('No response from assistant');
        return;
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
                const messageText = event.message || event.content || '';
                
                // Append each chunk as a new message
                await threadRuntime.append({
                  role: 'assistant',
                  content: [{ 
                    type: 'text', 
                    text: messageText
                  }]
                });
              } else if (event.error) {
                console.error('[Chat] Stream error:', event.error);
                setError(event.error);
                throw new Error(event.error);
              }
            } catch (e) {
              console.error('[Chat] Failed to parse event:', e, 'Raw data:', data);
              setError('Failed to process assistant response');
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (e) {
      console.error('Chat error:', e);
      setError(e instanceof Error ? e.message : 'An unexpected error occurred');
    } finally {
      setIsProcessing(false);
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

  // Show loading state
  if (userLoading || teammateLoading) {
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

  // Show teammate selection prompt if none selected
  if (!selectedTeammate) {
    return (
      <div className="flex flex-col items-center justify-center h-full space-y-4">
        <p className="text-lg text-gray-600">Please select a teammate to start chatting</p>
      </div>
    );
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
        <ChatMessages messages={thread?.messages || []} />
        <ChatInput 
          onSubmit={handleSubmit} 
          isDisabled={!selectedTeammate || isProcessing} 
        />
      </div>
    </div>
  );
};