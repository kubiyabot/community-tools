"use client";

import { useEffect, useRef } from 'react';
import { ThreadMessage } from '@assistant-ui/react';
import { UserMessage } from './UserMessage';
import { AssistantMessage } from './AssistantMessage';

interface ChatMessagesProps {
  messages: ThreadMessage[];
}

export const ChatMessages = ({ messages }: ChatMessagesProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  if (!messages.length) {
    return (
      <div className="flex-1 flex items-center justify-center p-4 text-center text-[#94A3B8]">
        <div>
          <h3 className="text-lg font-medium mb-2">Welcome to the Chat!</h3>
          <p className="text-sm">Start the conversation by typing a message below.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-4xl mx-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div key={index}>
            {message.role === 'user' ? (
              <UserMessage message={message} />
            ) : (
              <AssistantMessage message={message} />
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}; 