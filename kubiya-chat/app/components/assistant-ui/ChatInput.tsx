"use client";

import { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';

interface ChatInputProps {
  onSubmit: (message: string) => void;
  isDisabled?: boolean;
}

export const ChatInput = ({ onSubmit, isDisabled }: ChatInputProps) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isDisabled) return;
    
    onSubmit(message.trim());
    setMessage('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  }, [message]);

  return (
    <div className="border-t border-[#3D4B5E] bg-[#1A1F2E] p-4">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isDisabled ? "Please select a teammate to start chatting..." : "Type your message..."}
            disabled={isDisabled}
            className="w-full bg-[#2D3B4E] text-white rounded-lg pl-4 pr-12 py-3 min-h-[52px] max-h-[200px] text-sm focus:outline-none focus:ring-1 focus:ring-[#7C3AED] disabled:opacity-50 disabled:cursor-not-allowed resize-none"
            rows={1}
          />
          <button
            type="submit"
            disabled={!message.trim() || isDisabled}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-white bg-[#7C3AED] rounded-md hover:bg-[#6D31D0] disabled:opacity-50 disabled:hover:bg-[#7C3AED] transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </form>
    </div>
  );
}; 