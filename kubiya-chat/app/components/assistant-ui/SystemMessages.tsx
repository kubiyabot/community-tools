import React from 'react';
import { Bot, AlertTriangle } from 'lucide-react';
import { ThreadMessage, TextContentPart } from '@assistant-ui/react';
import { cn } from '@/lib/utils';

interface SystemMessage {
  id: string;
  role: 'system';
  content: readonly [TextContentPart];
  metadata: {
    readonly unstable_data?: readonly unknown[];
    readonly steps?: readonly {
      id: string;
      type: string;
      status: string;
      details?: Record<string, unknown>;
    }[];
    readonly custom: Record<string, unknown>;
  };
  createdAt: string;
}

interface SystemMessagesProps {
  messages: SystemMessage[];
}

export const SystemMessages = ({ messages }: SystemMessagesProps) => {
  return (
    <div className="space-y-2">
      {messages.map((message) => {
        const textContent = message.content[0]?.text || '';
        const isError = textContent.toLowerCase().includes("error");
        const isWarning = textContent.toLowerCase().includes("warning");
        
        return (
          <div
            key={message.id}
            className={cn(
              "flex items-start gap-3 p-3 rounded-xl transition-colors",
              "backdrop-blur-sm border border-white/5",
              isError 
                ? "bg-red-500/10 hover:bg-red-500/15" 
                : isWarning 
                  ? "bg-yellow-500/10 hover:bg-yellow-500/15"
                  : "bg-[#1E293B]/30 hover:bg-[#2D3B4E]/30"
            )}
          >
            <div className={cn(
              "flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center",
              isError 
                ? "bg-red-500/20" 
                : isWarning 
                  ? "bg-yellow-500/20"
                  : "bg-purple-500/20"
            )}>
              {isError || isWarning ? (
                <AlertTriangle className={cn(
                  "h-3.5 w-3.5",
                  isError ? "text-red-400" : "text-yellow-400"
                )} />
              ) : (
                <Bot className="h-3.5 w-3.5 text-purple-400" />
              )}
            </div>
            <div className={cn(
              "text-sm",
              isError 
                ? "text-red-200" 
                : isWarning 
                  ? "text-yellow-200"
                  : "text-slate-200"
            )}>
              {textContent}
            </div>
          </div>
        );
      })}
    </div>
  );
}; 