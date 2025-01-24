"use client";

import { useState, useMemo } from 'react';
import { MessageCircle, PlusCircle, Search, X, MoreHorizontal, Pencil, Trash2 } from 'lucide-react';
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
  const { selectedTeammate, currentState, switchThread, setTeammateState } = useTeammateContext();
  const [searchQuery, setSearchQuery] = useState('');
  const [editingThreadId, setEditingThreadId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);

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

  const handleEditClick = (thread: any, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingThreadId(thread.id);
    setEditingTitle(thread.metadata.title || 'New Conversation');
    setActiveDropdown(null);
  };

  const handleTitleSave = async (threadId: string) => {
    if (!selectedTeammate || !currentState) return;
    
    const updatedState = {
      ...currentState,
      threads: {
        ...currentState.threads,
        [threadId]: {
          ...currentState.threads[threadId],
          metadata: {
            ...currentState.threads[threadId].metadata,
            title: editingTitle,
            updatedAt: new Date().toISOString()
          }
        }
      }
    };

    // Update state and persist to localStorage
    setTeammateState(selectedTeammate, updatedState);
    setEditingThreadId(null);
  };

  const handleDeleteThread = async (threadId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!selectedTeammate || !currentState) return;

    if (confirm('Are you sure you want to delete this conversation?')) {
      // Create new state without the deleted thread
      const { [threadId]: deletedThread, ...remainingThreads } = currentState.threads;
      
      const updatedState = {
        ...currentState,
        threads: remainingThreads,
        // If we're deleting the current thread, switch to the most recent one
        currentThreadId: currentState.currentThreadId === threadId 
          ? Object.keys(remainingThreads)[0] || Date.now().toString()
          : currentState.currentThreadId
      };

      // Update state and persist to localStorage
      setTeammateState(selectedTeammate, updatedState);
      
      // If we deleted the current thread, switch to another one
      if (currentState.currentThreadId === threadId) {
        switchThread(selectedTeammate, updatedState.currentThreadId);
      }
    }
    setActiveDropdown(null);
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
    <div className="flex flex-col h-full bg-gray-900/95 border-r border-gray-800/60 backdrop-blur-sm w-[280px]">
      <div className="flex-shrink-0 p-3 border-b border-gray-800/60">
        <button
          onClick={handleNewThread}
          className="w-full flex items-center justify-center gap-2 py-2.5 bg-purple-600/90 hover:bg-purple-600 
                   text-white rounded-xl transition-all duration-200 font-medium tracking-wide
                   hover:shadow-lg hover:shadow-purple-500/20 active:scale-[0.98]"
        >
          <PlusCircle className="h-4 w-4" />
          <span>New Conversation</span>
        </button>
      </div>

      {teammateThreads.length > 0 && (
        <div className="flex-shrink-0 p-3 border-b border-gray-800/60">
          <div className="relative group">
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2.5 bg-gray-800/80 text-white rounded-xl placeholder-gray-400 
                       focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:bg-gray-800/95
                       transition-all duration-200 group-hover:bg-gray-800/95"
            />
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 
                            group-hover:text-purple-400 transition-colors duration-200" />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 opacity-60 
                         hover:opacity-100 transition-all duration-200"
              >
                <X className="h-3.5 w-3.5 text-gray-400 hover:text-purple-400" />
              </button>
            )}
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto min-h-0 scrollbar-thin scrollbar-thumb-gray-800 scrollbar-track-transparent">
        {filteredThreads.length > 0 ? (
          <div className="p-2 space-y-1">
            {filteredThreads.map((thread) => (
              <div
                key={thread.id}
                onClick={() => switchThread(selectedTeammate, thread.id)}
                className={`w-full flex items-start gap-3 p-3 rounded-lg transition-all duration-200 cursor-pointer
                         hover:bg-gray-800/80 group relative
                         ${currentState?.currentThreadId === thread.id 
                           ? 'bg-gray-800/90 shadow-lg shadow-purple-500/5' 
                           : ''}`}
              >
                <div className="relative flex-shrink-0">
                  <MessageCircle className="h-5 w-5 text-gray-400 flex-shrink-0 
                                        group-hover:text-purple-400 transition-colors duration-200" />
                  {currentState?.currentThreadId === thread.id && (
                    <div className="absolute -bottom-0.5 -right-0.5 w-1.5 h-1.5 
                                 bg-purple-500 rounded-full animate-pulse" />
                  )}
                </div>

                <div className="flex-1 text-left min-w-0">
                  {editingThreadId === thread.id ? (
                    <input
                      type="text"
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onBlur={() => handleTitleSave(thread.id)}
                      onKeyDown={(e) => e.key === 'Enter' && handleTitleSave(thread.id)}
                      onClick={(e) => e.stopPropagation()}
                      className="w-full bg-gray-800 text-white text-sm px-2 py-1 rounded 
                               focus:outline-none focus:ring-1 focus:ring-purple-500"
                      autoFocus
                    />
                  ) : (
                    <div className="text-sm font-medium text-white truncate group-hover:text-purple-100">
                      {thread.metadata.title || 'New Conversation'}
                    </div>
                  )}
                  {thread.messages.length > 0 && (
                    <p className="text-sm text-gray-400 truncate mt-1 group-hover:text-gray-300
                              transition-colors duration-200">
                      {thread.messages[thread.messages.length - 1]?.content[0]?.text?.slice(0, 50) + 
                        (thread.messages[thread.messages.length - 1]?.content[0]?.text?.length > 50 ? '...' : '')}
                    </p>
                  )}
                  <div className="text-xs text-gray-500 mt-1.5 group-hover:text-gray-400">
                    {new Date(thread.metadata.updatedAt).toLocaleDateString()}
                  </div>
                </div>

                <div className="relative flex items-center ml-2" onClick={(e) => e.stopPropagation()}>
                  <div
                    role="button"
                    tabIndex={0}
                    onClick={(e) => {
                      e.stopPropagation();
                      setActiveDropdown(activeDropdown === thread.id ? null : thread.id);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        setActiveDropdown(activeDropdown === thread.id ? null : thread.id);
                      }
                    }}
                    className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-gray-700/50
                             transition-all duration-200 cursor-pointer"
                  >
                    <MoreHorizontal className="h-4 w-4 text-gray-400 hover:text-purple-400" />
                  </div>

                  {activeDropdown === thread.id && (
                    <div className="absolute right-0 top-0 mt-8 w-36 py-1 bg-gray-800 rounded-lg shadow-xl
                                  border border-gray-700/50 z-50">
                      <div
                        role="button"
                        tabIndex={0}
                        onClick={(e) => handleEditClick(thread, e)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            handleEditClick(thread, e as any);
                          }
                        }}
                        className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-gray-300
                                 hover:bg-gray-700/50 hover:text-purple-400 transition-colors cursor-pointer"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                        Rename
                      </div>
                      <div
                        role="button"
                        tabIndex={0}
                        onClick={(e) => handleDeleteThread(thread.id, e)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            handleDeleteThread(thread.id, e as any);
                          }
                        }}
                        className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-red-400
                                 hover:bg-gray-700/50 hover:text-red-300 transition-colors cursor-pointer"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        Delete
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 p-6 text-center">
            <MessageCircle className="h-10 w-10 mb-3 text-gray-500/80" />
            <p className="font-medium text-gray-300">No conversations yet</p>
            <p className="text-sm mt-1.5 text-gray-500">Start a new one to begin chatting</p>
          </div>
        )}
      </div>
    </div>
  );
}; 