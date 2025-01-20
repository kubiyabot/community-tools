"use client";

import { useEffect, useState, useCallback } from 'react';
import { useUser } from '@auth0/nextjs-auth0/client';
import { useRouter } from 'next/navigation';
import { useAssistantRuntime, useThread, useThreadRuntime, ThreadMessage, 
  Thread, 
  ThreadWelcome, 
  Composer, 
  AssistantMessage, 
  UserMessage,
  ThreadList,
  ThreadListItem,
  AssistantActionBar,
  UserActionBar,
  type ThreadConfig 
} from '@assistant-ui/react';
import { useTeammateContext } from '../../MyRuntimeProvider';
import { ChatInput } from './ChatInput';
import { ChatMessages } from './ChatMessages';
import { ThreadsSidebar } from './ThreadsSidebar';
import { SystemMessages } from './SystemMessages';
import { ToolExecution } from './ToolExecution';

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

interface ThreadsSidebarProps {
  threads: ThreadInfo[];
  currentThreadId?: string;
  onNewThread: () => void;
  onThreadSelect: (threadId: string) => void;
}

interface ChatInputProps {
  onSubmit: (message: string) => Promise<void>;
  isDisabled?: boolean;
}

const MyThread: React.FC<ThreadConfig> = (config) => {
  return (
    <Thread.Root config={config}>
      <Thread.Viewport>
        <ThreadWelcome.Root>
          <ThreadWelcome.Center>
            <ThreadWelcome.Avatar />
            <ThreadWelcome.Message />
          </ThreadWelcome.Center>
          <ThreadWelcome.Suggestions />
        </ThreadWelcome.Root>
        <Thread.Messages 
          components={{
            AssistantMessage: MyAssistantMessage,
            UserMessage: MyUserMessage
          }}
        />
        <Thread.ViewportFooter>
          <Thread.ScrollToBottom />
          <MyComposer />
        </Thread.ViewportFooter>
      </Thread.Viewport>
    </Thread.Root>
  );
};

const MyAssistantMessage: React.FC = () => {
  return (
    <AssistantMessage.Root>
      <AssistantMessage.Avatar />
      <AssistantMessage.Content />
      <AssistantActionBar.Root>
        <AssistantActionBar.Copy />
        <AssistantActionBar.Reload />
      </AssistantActionBar.Root>
    </AssistantMessage.Root>
  );
};

const MyUserMessage: React.FC = () => {
  return (
    <UserMessage.Root>
      <UserMessage.Content />
      <UserActionBar.Root>
        <UserActionBar.Edit />
      </UserActionBar.Root>
    </UserMessage.Root>
  );
};

const MyComposer: React.FC = () => {
  return (
    <Composer.Root>
      <Composer.Input autoFocus />
      <Composer.Action />
    </Composer.Root>
  );
};

const MyThreadList: React.FC = () => {
  return (
    <ThreadList.Root>
      <ThreadList.New />
      <ThreadList.Items />
    </ThreadList.Root>
  );
};

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
  const [systemMessages, setSystemMessages] = useState<string[]>([]);
  const [pendingSystemMessages, setPendingSystemMessages] = useState<string[]>([]);
  const [isCollectingSystemMessages, setIsCollectingSystemMessages] = useState(false);
  
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

  // Track system messages from thread
  useEffect(() => {
    if (!thread?.messages) return;
    
    const newSystemMessages = thread.messages
      .filter(msg => msg.role === 'system' || msg.metadata?.custom?.isSystemMessage)
      .map(msg => {
        const textContent = msg.content.find(c => 'text' in c && c.type === 'text');
        return textContent && 'text' in textContent ? textContent.text : '';
      })
      .filter(Boolean);

    console.log('System Messages:', {
      count: newSystemMessages.length,
      messages: newSystemMessages,
      allMessages: thread.messages.map(m => ({ role: m.role, content: m.content, metadata: m.metadata }))
    });

    // Only update if we have new system messages and they're different
    if (newSystemMessages.length > 0 && JSON.stringify(newSystemMessages) !== JSON.stringify(systemMessages)) {
      setSystemMessages(newSystemMessages);
    }
  }, [thread?.messages]);

  // Handle collecting system messages
  useEffect(() => {
    if (isCollectingSystemMessages && pendingSystemMessages.length > 0) {
      console.log('Collecting system messages:', {
        pending: pendingSystemMessages,
        isCollecting: isCollectingSystemMessages
      });
      
      const timer = setTimeout(() => {
        setIsCollectingSystemMessages(false);
        
        // Filter out duplicates and empty messages
        const uniqueMessages = Array.from(new Set(pendingSystemMessages))
          .filter(msg => msg.trim());
        
        if (uniqueMessages.length > 0) {
          console.log('Appending system messages:', uniqueMessages);
          
          // Add each system message individually to maintain proper ordering
          uniqueMessages.forEach(message => {
            threadRuntime.append({
              role: 'system',
              content: [{ type: 'text', text: message }]
            });
          });
        }
        setPendingSystemMessages([]);
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [isCollectingSystemMessages, pendingSystemMessages, threadRuntime]);

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
    setIsCollectingSystemMessages(true);
    setPendingSystemMessages([]);

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

      // Send message through the runtime
      await threadRuntime.append({
        role: 'user',
        content: [{ type: 'text', text: message }]
      });

    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message. Please try again.');
    } finally {
      // Don't set isProcessing to false immediately to allow system messages to be collected
      setTimeout(() => {
        setIsProcessing(false);
        setIsCollectingSystemMessages(false);
      }, 2000); // Increased timeout to ensure all messages are collected
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
        onNewThread={handleNewThread}
        onThreadSelect={handleThreadSelect}
      />
      <div className="flex-1 flex flex-col h-full relative">
        <div className="flex-1 overflow-y-auto">
          <ChatMessages 
            messages={thread?.messages || []} 
            isCollectingSystemMessages={isCollectingSystemMessages}
            systemMessages={systemMessages}
          />
        </div>
        <ChatInput onSubmit={handleSubmit} isDisabled={isProcessing} />
        
        {/* Tool Execution Panel */}
        <div className="absolute top-0 right-0 w-80 p-4 space-y-2">
        </div>
      </div>
    </div>
  );
};