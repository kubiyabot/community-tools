"use client";

import { useState } from 'react';
import { MessageSquare, Plus, Search, X, AlertCircle } from 'lucide-react';
import { useTeammateContext } from '../../MyRuntimeProvider';

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
  onThreadSelect: (threadId: string) => void;
  onNewThread: () => void;
}

export const ThreadsSidebar = ({ threads, currentThreadId, onThreadSelect, onNewThread }: ThreadsSidebarProps) => {
  const [searchQuery, setSearchQuery] = useState('');
  const { teammates, error } = useTeammateContext();

  const filteredThreads = threads.filter(thread => {
    const matchesSearch = thread.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         thread.lastMessage?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const getTeammateName = (teammateId: string) => {
    return teammates.find(t => t.uuid === teammateId)?.name || 'Unknown Teammate';
  };

  const handleSupportClick = () => {
    if (error?.supportInfo) {
      const { email, subject, body } = error.supportInfo;
      window.location.href = `mailto:${email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    }
  };

  if (error) {
    return (
      <div className="w-80 h-full bg-[#1A1F2E] border-r border-[#3D4B5E] flex flex-col">
        <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
          <h3 className="text-white font-medium mb-2">{error.error}</h3>
          <p className="text-[#94A3B8] text-sm mb-4">{error.details}</p>
          <button
            onClick={handleSupportClick}
            className="px-4 py-2 bg-[#7C3AED] hover:bg-[#6D31D0] text-white rounded-md transition-colors"
          >
            Contact Support
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-80 h-full bg-[#1A1F2E] border-r border-[#3D4B5E] flex flex-col">
      <div className="p-4 border-b border-[#3D4B5E]">
        <button
          onClick={onNewThread}
          className="w-full flex items-center gap-2 px-4 py-2 bg-[#7C3AED] hover:bg-[#6D31D0] text-white rounded-md transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>New Chat</span>
        </button>
      </div>

      <div className="p-3 border-b border-[#3D4B5E]">
        <div className="relative">
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#2D3B4E] text-white rounded-md pl-9 pr-8 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[#7C3AED] border border-[#3D4B5E]"
          />
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-[#94A3B8]" />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2 top-2 p-1 hover:bg-[#1A1F2E] rounded-sm transition-colors"
            >
              <X className="h-3 w-3 text-[#94A3B8]" />
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {filteredThreads.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-[#94A3B8] p-4 text-center">
            <MessageSquare className="h-8 w-8 mb-2 opacity-50" />
            {searchQuery ? (
              <p className="text-sm">No conversations found matching your search</p>
            ) : (
              <p className="text-sm">No conversations yet. Start a new chat to begin!</p>
            )}
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {filteredThreads.map((thread) => (
              <button
                key={thread.id}
                onClick={() => onThreadSelect(thread.id)}
                className={`w-full text-left p-3 rounded-md transition-colors ${
                  currentThreadId === thread.id
                    ? 'bg-[#7C3AED] text-white'
                    : 'hover:bg-[#2D3B4E] text-[#94A3B8]'
                }`}
              >
                <div className="flex flex-col gap-1">
                  <span className="font-medium text-sm truncate">{thread.title}</span>
                  <span className="text-xs opacity-75 truncate">{getTeammateName(thread.teammateId)}</span>
                  {thread.lastMessage && (
                    <span className="text-xs opacity-75 truncate">{thread.lastMessage}</span>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}; 