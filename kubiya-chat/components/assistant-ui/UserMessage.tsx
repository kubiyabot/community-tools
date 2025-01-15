"use client";

import { MessagePrimitive } from "@assistant-ui/react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { MarkdownText } from "@/components/assistant-ui/markdown-text";
import { useUser } from '@auth0/nextjs-auth0/client';

export const UserMessage = ({ isStreaming }: { isStreaming?: boolean }) => {
  const { user } = useUser();
  
  return (
    <div className="px-4 py-2 flex flex-row-reverse items-start gap-3 group">
      <div className="flex-none">
        <Avatar className="h-8 w-8 select-none ring-1 ring-blue-100">
          {user?.picture && <AvatarImage src={user.picture} className="object-cover" />}
          <AvatarFallback className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
            {user?.name?.[0] || 'U'}
          </AvatarFallback>
        </Avatar>
      </div>
      <div className="min-w-0 flex-1 flex justify-end">
        <div className={`relative rounded-2xl rounded-tr-sm bg-blue-500 px-4 py-2.5 text-sm text-white shadow-sm ${isStreaming ? 'opacity-80' : 'animate-in fade-in-0 duration-150'}`}>
          <div className="prose prose-invert prose-sm max-w-none prose-p:my-1 prose-p:leading-relaxed prose-pre:my-2 prose-pre:bg-blue-600/50 prose-pre:p-3 prose-pre:ring-1 prose-pre:ring-white/10 whitespace-pre-wrap">
            <MessagePrimitive.Content components={{ Text: MarkdownText }} />
          </div>
        </div>
      </div>
    </div>
  );
}; 