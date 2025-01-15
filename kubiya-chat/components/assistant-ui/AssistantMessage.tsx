"use client";

import { MessagePrimitive } from "@assistant-ui/react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { MarkdownText } from "@/components/assistant-ui/markdown-text";
import { Copy, Check } from "lucide-react";
import { useState } from "react";
import type { ReactNode } from "react";
import { ToolExecution } from './ToolExecution';

interface CodeBlockProps {
  children?: ReactNode;
  className?: string;
}

export const AssistantMessage = ({ 
  isTyping,
  teammate,
  content
}: { 
  isTyping?: boolean;
  teammate?: { 
    name: string; 
    avatar: string;
    type?: string;
  };
  content?: string;
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (content) {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const CodeBlock = ({ children, className }: CodeBlockProps) => (
    <pre className={`relative group/code ${className}`}>
      <button
        onClick={() => {
          const code = children?.toString() || '';
          navigator.clipboard.writeText(code);
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        }}
        className="absolute right-2 top-2 opacity-0 group-hover/code:opacity-100 transition-opacity"
        title="Copy code"
      >
        {copied ? (
          <Check className="h-4 w-4 text-green-500" />
        ) : (
          <Copy className="h-4 w-4 text-gray-400 hover:text-gray-600" />
        )}
      </button>
      {children}
    </pre>
  );

  const InlineCode = ({ children, className }: CodeBlockProps) => (
    <code className={`bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800 ${className || ''}`}>
      {children}
    </code>
  );

  return (
    <div className="px-4 py-2.5 flex items-start gap-4 group hover:bg-gray-50/50 transition-colors">
      <div className="flex-none pt-1">
        <Avatar className="h-10 w-10 select-none ring-2 ring-[#7C3AED] ring-offset-2 ring-offset-white shadow-sm">
          {teammate ? (
            <>
              <AvatarImage src={teammate.avatar} className="object-cover" />
              <AvatarFallback className="bg-gradient-to-br from-[#7C3AED] to-[#5B21B6] text-white font-medium">
                {teammate.name[0].toUpperCase()}
              </AvatarFallback>
            </>
          ) : (
            <>
              <AvatarImage src="/images/kubiya-logo.png" className="object-contain bg-white p-1.5" />
              <AvatarFallback className="bg-gradient-to-br from-[#7C3AED] to-[#5B21B6] text-white">
                K
              </AvatarFallback>
            </>
          )}
        </Avatar>
      </div>
      <div className="min-w-0 flex-1">
        {/* Teammate Info */}
        {teammate && (
          <div className="flex items-center gap-2 mb-1.5">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-gray-900">{teammate.name}</span>
              <div className="flex items-center gap-1.5">
                <span className="text-xs px-2 py-0.5 rounded-full bg-[#7C3AED]/10 text-[#7C3AED] font-medium">
                  Assistant
                </span>
                {teammate.type && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-[#3B82F6]/10 text-[#3B82F6] font-medium">
                    {teammate.type}
                  </span>
                )}
              </div>
            </div>
            <span className="text-xs text-gray-400">•</span>
            <span className="text-xs text-gray-500 font-medium">{new Date().toLocaleTimeString()}</span>
          </div>
        )}
        
        <div className="relative rounded-2xl rounded-tl-sm bg-white px-5 py-3.5 text-sm text-gray-900 shadow-sm ring-1 ring-gray-900/5 hover:shadow-md transition-all duration-200">
          {/* Message Status - Typing */}
          {isTyping ? (
            <div className="flex items-center gap-2.5 min-h-[24px]">
              <div className="flex gap-1">
                <div className="w-1.5 h-1.5 rounded-full bg-[#7C3AED] animate-pulse"></div>
                <div className="w-1.5 h-1.5 rounded-full bg-[#7C3AED] animate-pulse [animation-delay:0.2s]"></div>
                <div className="w-1.5 h-1.5 rounded-full bg-[#7C3AED] animate-pulse [animation-delay:0.4s]"></div>
              </div>
              <span className="text-gray-500 text-xs font-medium">
                {teammate ? teammate.name : 'Kubiya'} is typing...
              </span>
            </div>
          ) : (
            <>
              {/* Copy Button */}
              <button
                onClick={handleCopy}
                className="absolute right-4 top-3.5 opacity-0 group-hover:opacity-100 transition-all duration-200 hover:scale-105"
                title="Copy message"
              >
                {copied ? (
                  <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-green-50 text-green-600">
                    <Check className="h-3.5 w-3.5" />
                    <span className="text-xs font-medium">Copied!</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 px-2 py-1 rounded-md hover:bg-gray-50 text-gray-400 hover:text-gray-600">
                    <Copy className="h-3.5 w-3.5" />
                    <span className="text-xs font-medium">Copy</span>
                  </div>
                )}
              </button>

              {/* Message Content */}
              <div className="prose prose-sm max-w-none prose-p:leading-relaxed prose-headings:font-semibold prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gray-900 prose-strong:font-semibold prose-code:text-[#7C3AED] prose-code:font-medium">
                <div className="prose-pre:bg-gray-50 prose-pre:p-4 prose-pre:rounded-lg prose-pre:ring-1 prose-pre:ring-gray-900/5 prose-pre:my-3 prose-pre:shadow-sm">
                  <MessagePrimitive.Content 
                    components={{ 
                      Text: MarkdownText,
                      tools: {
                        by_name: {
                          ToolExecution: ToolExecution
                        }
                      }
                    }} 
                  />
                </div>
              </div>

              {/* Message Footer - Metadata */}
              <div className="mt-3 pt-2 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                    Completed
                  </span>
                  {content && (
                    <span className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-gray-300"></span>
                      {content.length} characters
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 font-medium">
                  <button className="hover:text-[#7C3AED] transition-colors" title="React to message">
                    😊
                  </button>
                  <button className="hover:text-[#7C3AED] transition-colors" title="More options">
                    •••
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}; 