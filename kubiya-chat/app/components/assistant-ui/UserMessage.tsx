"use client";

import { memo } from 'react';
import { ThreadMessage } from '@assistant-ui/react';
import { User } from 'lucide-react';
import { MarkdownText } from './MarkdownText';

interface UserMessageProps {
  message: ThreadMessage & { role: 'user' };
}

const UserMessageComponent = ({ message }: UserMessageProps) => {
  const textContent = message.content.find(c => c.type === 'text');
  const messageText = textContent && 'text' in textContent ? textContent.text : '';

  // Log for debugging
  console.log('[UserMessage] Rendering:', {
    id: message.id,
    hasText: !!messageText,
    textLength: messageText.length,
    content: message.content
  });

  if (!messageText.trim()) {
    console.log('[UserMessage] Skipping empty message');
    return null;
  }

  return (
    <div className="flex items-start gap-3">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#7C3AED] flex items-center justify-center">
        <User className="h-4 w-4 text-white" />
      </div>
      <div className="flex-1 space-y-2">
        <div className="text-sm font-medium text-white">You</div>
        <div className="text-sm text-[#E2E8F0] prose prose-invert prose-sm max-w-none">
          <MarkdownText content={messageText} />
        </div>
      </div>
    </div>
  );
};

// Memoize the component to prevent unnecessary re-renders
export const UserMessage = memo(UserMessageComponent, (prevProps, nextProps) => {
  const prevContent = prevProps.message.content.find(c => c.type === 'text');
  const nextContent = nextProps.message.content.find(c => c.type === 'text');
  return prevContent === nextContent;
}); 