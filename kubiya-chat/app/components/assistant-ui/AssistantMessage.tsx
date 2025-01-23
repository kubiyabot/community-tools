"use client";

import { memo } from 'react';
import { ThreadMessage, ThreadAssistantContentPart, TextContentPart, ToolCallContentPart } from '@assistant-ui/react';
import { Bot, AlertTriangle, Copy, Check, Terminal, Loader2 } from 'lucide-react';
import { MarkdownText } from './MarkdownText';
import { useTeammateContext } from "../../MyRuntimeProvider";
import { useState, useEffect, useCallback } from 'react';
import { toast } from '@/app/components/use-toast';

interface ToolCall {
  type: 'tool_init' | 'tool_output';
  id: string;
  name?: string;
  arguments?: Record<string, unknown>;
  message?: string;
  timestamp?: string;
  tool_init?: boolean;
  tool_description?: string;
}

export interface AssistantMessageProps {
  message: ThreadMessage & { 
    role: 'assistant' | 'system';
    tool_calls?: ToolCall[];
  };
  isSystem?: boolean;
  isTool?: boolean;
}

function isTextContent(content: ThreadAssistantContentPart): content is TextContentPart {
  return content.type === 'text';
}

function isToolCallContent(content: ThreadAssistantContentPart): content is ToolCallContentPart<Record<string | number, unknown>, unknown> {
  return content.type === 'tool-call';
}

const CopyButton = ({ content }: { content: string }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      toast({
        description: "Copied to clipboard",
        duration: 2000,
      });
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
      toast({
        variant: "destructive",
        description: "Failed to copy to clipboard",
      });
    }
  }, [content]);

  return (
    <button
      onClick={handleCopy}
      className="opacity-0 group-hover:opacity-100 transition-opacity absolute right-2 top-2 p-1.5 rounded-md bg-[#2D3B4E] hover:bg-[#3D4B5E] text-[#94A3B8] z-10"
      title="Copy to clipboard"
    >
      {copied ? (
        <Check className="h-4 w-4 text-green-400" />
      ) : (
        <Copy className="h-4 w-4" />
      )}
    </button>
  );
};

const AssistantMessageComponent = ({ message, isSystem, isTool }: AssistantMessageProps) => {
  const { teammates, selectedTeammate } = useTeammateContext();
  const [isStreaming, setIsStreaming] = useState(false);
  const textContent = message.content.find(isTextContent);
  const toolContent = message.content.find(isToolCallContent);
  const messageText = textContent && isTextContent(textContent) ? textContent.text : '';
  const isSystemMessage = message.role === 'system';
  const hasToolCalls = 'tool_calls' in message && Array.isArray(message.tool_calls) && message.tool_calls?.length > 0;

  const currentTeammate = teammates.find(t => t.uuid === selectedTeammate);

  useEffect(() => {
    // Set streaming if this is the last message and it's still being updated
    const timestamp = new Date(message.createdAt).getTime();
    const isRecent = Date.now() - timestamp < 1000;
    setIsStreaming(isRecent);

    const timer = setTimeout(() => setIsStreaming(false), 1000);
    return () => clearTimeout(timer);
  }, [message, messageText]);

  if (!messageText.trim() && !toolContent && !hasToolCalls) {
    return null;
  }

  const warnings = isSystemMessage 
    ? messageText.split(/(?=WARNING:|ERROR:)/)
        .map((msg: string) => msg.trim())
        .filter((msg: string) => msg.length > 0)
    : [];

  if (isSystemMessage && !warnings.length && messageText) {
    warnings.push(messageText);
  }

  return (
    <div className="flex items-start gap-3">
      {isSystemMessage ? (
        <div className="w-full bg-amber-950/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
            </div>
            <div className="text-sm font-medium text-amber-200">System Messages</div>
          </div>
          <div className="space-y-3">
            {warnings.map((warning: string, index: number) => (
              <div key={index} className="flex items-start gap-2 text-sm text-amber-100 bg-amber-950/30 p-3 rounded group relative">
                <span className="mt-1 text-amber-400">•</span>
                <span className="flex-1"><MarkdownText content={warning} /></span>
                <CopyButton content={warning} />
              </div>
            ))}
          </div>
        </div>
      ) : (
        <>
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#2D3B4E] flex items-center justify-center relative">
            {currentTeammate?.avatar_url ? (
              <img 
                src={currentTeammate.avatar_url} 
                alt={currentTeammate.name || 'Assistant'} 
                className="w-full h-full rounded-full object-cover"
              />
            ) : (
              <Bot className="h-4 w-4 text-[#7C3AED]" />
            )}
            {isStreaming && (
              <span className="absolute -bottom-1 -right-1 h-2 w-2">
                <span className="absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75 animate-ping"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
              </span>
            )}
          </div>
          <div className="flex-1 space-y-1.5">
            <div className="flex items-center gap-2">
              <div className="text-sm font-medium text-white">
                {currentTeammate?.name || 'Assistant'}
              </div>
            </div>
            <div className="text-sm text-[#E2E8F0] prose prose-invert prose-sm max-w-none">
              {messageText && (
                <div className="group relative bg-[#1A1F2E]/50 rounded-lg p-3">
                  <div className="flex items-start">
                    <div className="flex-1">
                      <MarkdownText content={messageText} isStreaming={isStreaming} />
                    </div>
                  </div>
                  <CopyButton content={messageText} />
                </div>
              )}
              {(toolContent || hasToolCalls) && (
                <div className="mt-3 space-y-3">
                  {toolContent && isToolCallContent(toolContent) && (
                    <div className="bg-[#1E293B] rounded-lg border border-[#2D3B4E] overflow-hidden group relative">
                      <div className="px-4 py-2 bg-[#2D3B4E] border-b border-[#3D4B5E] flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Terminal className="h-4 w-4 text-purple-400" />
                          <p className="text-xs font-medium text-[#94A3B8]">Tool Call: {toolContent.toolName}</p>
                        </div>
                      </div>
                      <div className="relative group">
                        <pre className="p-4 text-xs overflow-x-auto">
                          <code className="text-[#E2E8F0]">
                            {JSON.stringify(toolContent.args, null, 2)}
                          </code>
                        </pre>
                        <CopyButton content={JSON.stringify(toolContent.args, null, 2)} />
                      </div>
                    </div>
                  )}
                  {hasToolCalls && message.tool_calls && message.tool_calls.map((tool: ToolCall, index: number) => (
                    <div key={`${tool.id}-${index}`} className="bg-[#1E293B] rounded-lg border border-[#2D3B4E] overflow-hidden group relative">
                      <div className="px-4 py-2 bg-[#2D3B4E] border-b border-[#3D4B5E] flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Terminal className="h-4 w-4 text-purple-400" />
                          <p className="text-xs font-medium text-[#94A3B8]">
                            {tool.type === 'tool_init' ? 'Tool Initialization' : 'Tool Output'}: {tool.name}
                          </p>
                          {tool.type === 'tool_init' && (
                            <div className="flex items-center gap-1.5 text-xs text-purple-400">
                              <Loader2 className="h-3 w-3 animate-spin" />
                              <span>Initializing</span>
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="relative group">
                        <pre className="p-4 text-xs overflow-x-auto">
                          <code className="text-[#E2E8F0]">
                            {tool.type === 'tool_init' 
                              ? tool.tool_description || 'Determining best tool for the task...'
                              : tool.message}
                            {tool.type === 'tool_init' && (
                              <span className="inline-block w-2 h-4 bg-purple-400 animate-pulse ml-1" />
                            )}
                          </code>
                        </pre>
                        <CopyButton content={tool.type === 'tool_init' 
                          ? tool.tool_description || 'Determining best tool for the task...'
                          : tool.message || ''} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export const AssistantMessage = memo(AssistantMessageComponent); 