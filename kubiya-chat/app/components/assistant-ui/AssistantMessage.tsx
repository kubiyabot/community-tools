"use client";

import { memo } from 'react';
import { ThreadMessage, ThreadAssistantContentPart, TextContentPart, ToolCallContentPart } from '@assistant-ui/react';
import { Bot, AlertTriangle } from 'lucide-react';
import { MarkdownText } from './MarkdownText';

interface ToolCall {
  type: 'tool_init' | 'tool_output';
  id: string;
  name?: string;
  arguments?: Record<string, unknown>;
  message?: string;
  timestamp?: string;
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

const AssistantMessageComponent = ({ message, isSystem, isTool }: AssistantMessageProps) => {
  const textContent = message.content.find(isTextContent);
  const toolContent = message.content.find(isToolCallContent);
  const messageText = textContent && isTextContent(textContent) ? textContent.text : '';
  const isSystemMessage = message.role === 'system';
  const hasToolCalls = 'tool_calls' in message && Array.isArray(message.tool_calls) && message.tool_calls?.length > 0;

  // Ensure tool calls are rendered
  if (!messageText.trim() && !toolContent && !hasToolCalls) {
    console.log('[AssistantMessage] Skipping empty message:', { id: message.id });
    return null;
  }

  // Enhanced logging for debugging
  console.log('[AssistantMessage] Rendering message:', {
    id: message.id,
    role: message.role,
    isSystem: isSystemMessage,
    hasText: !!messageText,
    textLength: messageText.length,
    contentParts: message.content.length,
    contentTypes: message.content.map(c => c.type).join(', '),
    hasToolContent: !!toolContent,
    hasToolCalls,
    toolCallsCount: hasToolCalls && message.tool_calls ? message.tool_calls.length : 0,
    fullText: messageText // Log the full text for debugging
  });

  // Split system messages into individual warnings and filter out empty ones
  const warnings: string[] = isSystemMessage 
    ? messageText.split(/(?=WARNING:|ERROR:)/)
        .map((msg: string) => msg.trim())
        .filter((msg: string) => msg.length > 0)
    : [];

  if (isSystemMessage && !warnings.length && messageText) {
    warnings.push(messageText);
  }

  if (isSystemMessage) {
    console.log('[AssistantMessage] Processing system message:', {
      id: message.id,
      warningsCount: warnings.length,
      warnings
    });
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
              <div key={index} className="flex items-start gap-2 text-sm text-amber-100 bg-amber-950/30 p-3 rounded">
                <span className="mt-1 text-amber-400">•</span>
                <span className="flex-1"><MarkdownText content={warning} /></span>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <>
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#2D3B4E] flex items-center justify-center">
            <Bot className="h-4 w-4 text-[#7C3AED]" />
          </div>
          <div className="flex-1 space-y-2">
            <div className="text-sm font-medium text-white">Assistant</div>
            <div className="text-sm text-[#E2E8F0] prose prose-invert prose-sm max-w-none whitespace-pre-wrap break-words">
              {messageText && <MarkdownText content={messageText} />}
              {(toolContent || hasToolCalls) && (
                <div className="mt-4 space-y-3">
                  {toolContent && isToolCallContent(toolContent) && (
                    <div className="bg-[#1E293B] rounded-lg border border-[#2D3B4E] overflow-hidden">
                      <div className="px-4 py-2 bg-[#2D3B4E] border-b border-[#3D4B5E]">
                        <p className="text-xs font-medium text-[#94A3B8]">Tool Call: {toolContent.toolName}</p>
                      </div>
                      <pre className="p-4 text-xs overflow-x-auto">
                        <code className="text-[#E2E8F0]">
                          {JSON.stringify(toolContent.args, null, 2)}
                        </code>
                      </pre>
                    </div>
                  )}
                  {hasToolCalls && message.tool_calls && message.tool_calls.map((tool: ToolCall, index: number) => (
                    <div key={`${tool.id}-${index}`} className="bg-[#1E293B] rounded-lg border border-[#2D3B4E] overflow-hidden">
                      <div className="px-4 py-2 bg-[#2D3B4E] border-b border-[#3D4B5E]">
                        <p className="text-xs font-medium text-[#94A3B8]">
                          {tool.type === 'tool_init' ? 'Tool Call' : 'Tool Output'}: {tool.type === 'tool_init' ? tool.name : ''}
                        </p>
                      </div>
                      <pre className="p-4 text-xs overflow-x-auto">
                        <code className="text-[#E2E8F0]">
                          {tool.type === 'tool_init' 
                            ? JSON.stringify(tool.arguments, null, 2)
                            : tool.message}
                        </code>
                      </pre>
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

// Export without memoization to ensure all updates are rendered
export const AssistantMessage = AssistantMessageComponent; 