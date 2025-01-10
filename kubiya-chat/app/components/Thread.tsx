"use client";

import React, { useState, useEffect } from 'react';
import { Edit2, Plus } from 'lucide-react';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: Date;
}

interface Thread {
  id: string;
  name: string;
  messages: Message[];
  createdAt: Date;
  lastUpdated: Date;
}

export function Thread() {
  const [threads, setThreads] = useState<Thread[]>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('chat-threads');
      return saved ? JSON.parse(saved) : [];
    }
    return [];
  });
  
  const [currentThreadId, setCurrentThreadId] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('current-thread-id') || '';
    }
    return '';
  });

  const [threadName, setThreadName] = useState('');
  const [isEditingName, setIsEditingName] = useState(false);

  useEffect(() => {
    localStorage.setItem('chat-threads', JSON.stringify(threads));
  }, [threads]);

  useEffect(() => {
    localStorage.setItem('current-thread-id', currentThreadId);
  }, [currentThreadId]);

  const createNewThread = () => {
    const newThread: Thread = {
      id: Date.now().toString(),
      name: `Thread ${threads.length + 1}`,
      messages: [],
      createdAt: new Date(),
      lastUpdated: new Date()
    };
    setThreads(prev => [...prev, newThread]);
    setCurrentThreadId(newThread.id);
    setThreadName(newThread.name);
  };

  const updateThreadName = (threadId: string, newName: string) => {
    setThreads(prev => prev.map(thread => 
      thread.id === threadId 
        ? { ...thread, name: newName, lastUpdated: new Date() }
        : thread
    ));
    setIsEditingName(false);
  };

  const currentThread = threads.find(t => t.id === currentThreadId);

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-background border rounded-lg overflow-hidden">
      {/* Thread Header */}
      <div className="flex items-center justify-between p-4 border-b bg-muted/50">
        <div className="flex items-center gap-2">
          {isEditingName ? (
            <input
              type="text"
              value={threadName}
              onChange={(e) => setThreadName(e.target.value)}
              onBlur={() => currentThreadId && updateThreadName(currentThreadId, threadName)}
              onKeyDown={(e) => e.key === 'Enter' && currentThreadId && updateThreadName(currentThreadId, threadName)}
              className="px-2 py-1 rounded border bg-background"
              autoFocus
            />
          ) : (
            <>
              <h2 className="font-semibold">{currentThread?.name || 'Select a thread'}</h2>
              {currentThread && (
                <button
                  onClick={() => {
                    setThreadName(currentThread.name);
                    setIsEditingName(true);
                  }}
                  className="p-1 hover:bg-muted rounded"
                >
                  <Edit2 className="h-4 w-4" />
                </button>
              )}
            </>
          )}
        </div>
        <button
          onClick={createNewThread}
          className="flex items-center gap-2 px-3 py-1 rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          New Thread
        </button>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {currentThread?.messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              }`}
            >
              <p className="text-sm">{message.content}</p>
              <p className="text-xs opacity-70 mt-1">
                {new Date(message.timestamp).toLocaleString()}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Composer */}
      <div className="p-4 border-t bg-muted/50">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Type your message..."
            className="flex-1 px-3 py-2 rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button className="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90">
            Send
          </button>
        </div>
      </div>
    </div>
  );
} 