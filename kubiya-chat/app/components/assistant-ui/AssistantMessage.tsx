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

  // Render tool execution content
  if (hasToolCalls && message.tool_calls) {
    return (
      <div className="tool-execution">
        {message.tool_calls.map((toolCall, index) => (
          <div key={index} className="tool-call">
            <span>{toolCall.name}</span>
            <span>{toolCall.message || 'No output available'}</span>
          </div>
        ))}
      </div>
    );
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
    toolCallsCount: hasToolCalls && message.tool_calls ? message.tool_calls.length : 0
  });

  // Split system messages into individual warnings and filter out empty ones
  const warnings: string[] = isSystemMessage 
    ? messageText.split(/WARNING:|ERROR:/)
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
        <div className="w-full bg-amber-950/50 rounded-lg p-4 my-2">
          <div className="flex items-center gap-2 mb-2">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
            </div>
            <div className="text-sm font-medium text-amber-200">System Messages</div>
          </div>
          <div className="space-y-3">
            {warnings.map((warning: string, index: number) => (
              <div key={index} className="flex items-start gap-2 text-sm text-amber-100 bg-amber-950/30 p-3 rounded">
                <span className="mt-1 text-amber-400">•</span>
                <span className="flex-1">{warning}</span>
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
              {(toolContent || hasToolCalls) && (
                <div className="mt-2 p-2 bg-gray-800 rounded">
                  {toolContent && isToolCallContent(toolContent) && (
                    <>
                      <p className="text-xs text-gray-400">Tool Call: {toolContent.toolName}</p>
                      <pre className="text-xs mt-1">{JSON.stringify(toolContent.args, null, 2)}</pre>
                    </>
                  )}
                  {hasToolCalls && message.tool_calls && message.tool_calls.map((tool: ToolCall, index: number) => (
                    <div key={`${tool.id}-${index}`} className="mt-2">
                      <p className="text-xs text-gray-400">
                        Tool {tool.type === 'tool_init' ? 'Call' : 'Output'}: {tool.type === 'tool_init' ? tool.name : ''}
                      </p>
                      <pre className="text-xs mt-1">
                        {tool.type === 'tool_init' 
                          ? JSON.stringify(tool.arguments, null, 2)
                          : tool.message}
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

export const AssistantMessage = memo(AssistantMessageComponent, (prevProps, nextProps) => {
  const prevContent = prevProps.message.content.find(isTextContent);
  const nextContent = nextProps.message.content.find(isTextContent);
  return (prevContent && nextContent && isTextContent(prevContent) && isTextContent(nextContent)) 
    ? prevContent.text === nextContent.text 
    : prevContent === nextContent;
}); 