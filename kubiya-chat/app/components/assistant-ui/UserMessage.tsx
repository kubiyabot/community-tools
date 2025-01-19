"use client";

import { ThreadMessage } from '@assistant-ui/react';
import { User } from 'lucide-react';

interface UserMessageProps {
  message: ThreadMessage & { role: 'user' };
}

export const UserMessage = ({ message }: UserMessageProps) => {
  const textContent = message.content.find(c => c.type === 'text');
  const messageText = textContent && 'text' in textContent ? textContent.text : '';

  return (
    <div className="flex items-start gap-3">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#7C3AED] flex items-center justify-center">
        <User className="h-4 w-4 text-white" />
      </div>
      <div className="flex-1 space-y-1">
        <div className="text-sm font-medium text-white">You</div>
        <div className="text-sm text-[#E2E8F0] whitespace-pre-wrap">{messageText}</div>
      </div>
    </div>
  );
}; 