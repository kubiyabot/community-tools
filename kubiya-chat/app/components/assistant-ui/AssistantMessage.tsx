"use client";

import { ThreadMessage } from '@assistant-ui/react';
import { Bot } from 'lucide-react';
import { MarkdownText } from './MarkdownText';

interface AssistantMessageProps {
  message: ThreadMessage & { role: 'assistant' | 'system' };
}

export const AssistantMessage = ({ message }: AssistantMessageProps) => {
  const textContent = message.content.find(c => c.type === 'text');
  const messageText = textContent && 'text' in textContent ? textContent.text : '';
  const isSystemMessage = message.role === 'system';

  // Split system messages into individual warnings
  const warnings = isSystemMessage 
    ? messageText.split('WARNING:')
        .map(msg => msg.trim())
        .filter(msg => msg.length > 0)
    : [];

  return (
    <div className="flex items-start gap-3">
      {isSystemMessage ? (
        <div className="w-full bg-amber-950/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center">
              <Bot className="h-4 w-4 text-amber-500" />
            </div>
            <div className="text-sm font-medium text-amber-200">System Warnings</div>
          </div>
          <div className="space-y-2">
            {warnings.map((warning, index) => (
              <div key={index} className="flex items-start gap-2 text-sm text-amber-100">
                <span className="mt-1">•</span>
                <span>{warning}</span>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <>
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#2D3B4E] flex items-center justify-center">
            <Bot className="h-4 w-4 text-[#7C3AED]" />
          </div>
          <div className="flex-1 space-y-1">
            <div className="text-sm font-medium text-white">Assistant</div>
            <div className="text-sm text-[#E2E8F0] prose prose-invert prose-sm max-w-none">
              {messageText}
            </div>
          </div>
        </>
      )}
    </div>
  );
}; 