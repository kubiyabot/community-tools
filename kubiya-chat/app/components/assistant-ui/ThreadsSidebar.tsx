"use client";

import { useState, useMemo } from 'react';
import { MessageCircle, PlusCircle, Search, X } from 'lucide-react';
import { useTeammateContext } from '../../MyRuntimeProvider';

interface ThreadState {
  messages: any[];
  lastMessageId?: string;
  metadata: {
    teammateId: string;
    createdAt: string;
    updatedAt: string;
    title?: string;
    preview?: string;
    activeTool?: string;
  };
}

export const ThreadsSidebar = () => {
  const { selectedTeammate, currentState, switchThread } = useTeammateContext();
  const [searchQuery, setSearchQuery] = useState('');

  // Get threads for the selected teammate
  const teammateThreads = useMemo(() => {
    if (!selectedTeammate || !currentState?.threads) return [];
    
    return Object.entries(currentState.threads)
      .filter(([_, thread]) => thread.metadata.teammateId === selectedTeammate)
      .sort((a, b) => new Date(b[1].metadata.updatedAt).getTime() - new Date(a[1].metadata.updatedAt).getTime())
      .map(([id, thread]) => ({
        id,
        ...thread
      }));
  }, [selectedTeammate, currentState?.threads]);

  // Filter threads based on search
  const filteredThreads = useMemo(() => {
    if (!searchQuery) return teammateThreads;
    
    const query = searchQuery.toLowerCase();
    return teammateThreads.filter(thread => 
      thread.metadata.title?.toLowerCase().includes(query) ||
      thread.messages[thread.messages.length - 1]?.content[0]?.text?.toLowerCase().includes(query)
    );
  }, [teammateThreads, searchQuery]);

  const handleNewThread = () => {
    if (!selectedTeammate) return;
    const newThreadId = Date.now().toString();
    switchThread(selectedTeammate, newThreadId);
  };

  if (!selectedTeammate) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 p-4 text-center">
        <MessageCircle className="h-8 w-8 mb-2" />
        <p>Select a teammate to start a conversation</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-900">
      <div className="p-3 border-b border-gray-700">
        <button
          onClick={handleNewThread}
          className="w-full flex items-center justify-center gap-2 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
        >
          <PlusCircle className="h-4 w-4" />
          <span>New Conversation</span>
        </button>
      </div>

      {teammateThreads.length > 0 && (
        <div className="p-3 border-b border-gray-700">
          <div className="relative">
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-gray-800 text-white rounded-lg placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-purple-500"
            />
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2"
              >
                <X className="h-4 w-4 text-gray-400 hover:text-white" />
              </button>
            )}
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        {filteredThreads.length > 0 ? (
          <div className="p-2 space-y-1">
            {filteredThreads.map((thread) => (
              <button
                key={thread.id}
                onClick={() => switchThread(selectedTeammate, thread.id)}
                className={`w-full flex items-start gap-3 p-3 rounded-lg hover:bg-gray-800 transition-colors ${
                  currentState?.currentThreadId === thread.id ? 'bg-gray-800' : ''
                }`}
              >
                <MessageCircle className="h-5 w-5 text-gray-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1 text-left min-w-0">
                  <div className="text-sm font-medium text-white truncate">
                    {thread.metadata.title || 'New Conversation'}
                  </div>
                  {thread.messages.length > 0 && (
                    <p className="text-sm text-gray-400 truncate mt-0.5">
                      {thread.messages[thread.messages.length - 1]?.content[0]?.text?.slice(0, 50) + 
                        (thread.messages[thread.messages.length - 1]?.content[0]?.text?.length > 50 ? '...' : '')}
                    </p>
                  )}
                  <div className="text-xs text-gray-500 mt-1">
                    {new Date(thread.metadata.updatedAt).toLocaleDateString()}
                  </div>
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 p-4 text-center">
            <MessageCircle className="h-8 w-8 mb-2" />
            <p>No conversations yet</p>
            <p className="text-sm mt-1">Start a new one to begin chatting</p>
          </div>
        )}
      </div>
    </div>
  );
}; 