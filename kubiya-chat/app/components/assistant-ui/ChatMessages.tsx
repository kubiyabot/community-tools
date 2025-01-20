"use client";

import { useEffect, useRef, useMemo, useCallback } from 'react';
import { ThreadMessage } from '@assistant-ui/react';
import { UserMessage } from './UserMessage';
import { AssistantMessage } from './AssistantMessage';
import { SystemMessages } from './SystemMessages';

interface ToolCall {
  type: 'tool_init' | 'tool_output';
  id: string;
  name?: string;
  arguments?: Record<string, unknown>;
  message?: string;
  timestamp?: string;
}

type SystemMessage = ThreadMessage & { 
  role: 'system';
  tool_calls?: ToolCall[];
};

type AssistantMessage = ThreadMessage & { 
  role: 'assistant';
  tool_calls?: ToolCall[];
};

type UserThreadMessage = ThreadMessage & { 
  role: 'user';
  tool_calls?: ToolCall[];
};

interface ChatMessagesProps {
  messages: readonly ThreadMessage[];
  isCollectingSystemMessages: boolean;
  systemMessages?: string[];
}

interface TextContent {
  type: 'text';
  text: string;
}

// Type guards with proper type assertions
function isAssistantMessage(message: ThreadMessage): message is AssistantMessage {
  return message.role === 'assistant';
}

function isUserMessage(message: ThreadMessage): message is UserThreadMessage {
  return message.role === 'user';
}

function isSystemMessage(message: ThreadMessage): message is SystemMessage {
  return message.role === 'system' || (message.metadata?.custom?.isSystemMessage === true);
}

const isTextContent = (content: any): content is TextContent => {
  return content?.type === 'text' && typeof content?.text === 'string';
};

const getMessageKey = (message: ThreadMessage): string => {
  const textContent = message.content.find(isTextContent);
  return message.id || `${message.role}-${textContent?.text || Date.now()}`;
};

const hasToolCalls = (msg: ThreadMessage & { tool_calls?: ToolCall[] }): boolean => {
  return 'tool_calls' in msg && 
    Array.isArray(msg.tool_calls) && 
    msg.tool_calls.length > 0;
};

export const ChatMessages = ({ messages, isCollectingSystemMessages, systemMessages = [] }: ChatMessagesProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const processedMessagesRef = useRef<Map<string, ThreadMessage & { tool_calls?: ToolCall[] }>>(new Map());

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  const { systemMessageTexts, conversationMessages } = useMemo(() => {
    console.log('[ChatMessages] Processing messages:', {
      inputCount: messages.length,
      isCollecting: isCollectingSystemMessages,
      messageTypes: messages.map(m => m.role).join(', '),
      messagesWithTools: messages.filter(hasToolCalls).length,
      systemCount: messages.filter(m => m.role === 'system' || m.metadata?.custom?.isSystemMessage).length,
      rawMessages: messages.map(m => ({
        id: m.id,
        role: m.role,
        content: m.content.map(c => c.type === 'text' ? c.text : c.type),
        metadata: m.metadata
      }))
    });

    // Create maps to store the latest version of each message by ID
    const messageMap = new Map<string, ThreadMessage>();
    const systemMessageMap = new Map<string, ThreadMessage>();
    
    // Process messages in reverse to get the latest version first
    [...messages].reverse().forEach(msg => {
      const textContent = msg.content.find(isTextContent);
      const messageText = textContent?.text || '';
      const msgToolCalls = hasToolCalls(msg);
      const isSystem = isSystemMessage(msg);
      const hasSystemMetadata = msg.metadata?.custom?.isSystemMessage;
      const originalId = msg.metadata?.custom?.originalId;
      
      console.log('[ChatMessages] Processing message:', {
        id: msg.id,
        role: msg.role,
        text: messageText,
        hasText: !!messageText,
        hasToolCalls: msgToolCalls,
        isSystem,
        isSystemMetadata: hasSystemMetadata,
        originalId,
        isCollecting: isCollectingSystemMessages,
        content: msg.content,
        metadata: msg.metadata
      });
      
      // Handle system messages
      if (isSystem || hasSystemMetadata) {
        // Always keep system messages with content
        const messageKey = (originalId || msg.id || Date.now().toString()) as string;
        if (!systemMessageMap.has(messageKey) && messageText.trim()) {
          systemMessageMap.set(messageKey, msg);
          console.log('[ChatMessages] Added system message:', {
            id: msg.id,
            key: messageKey,
            text: messageText,
            metadata: msg.metadata,
            isSystemMetadata: hasSystemMetadata,
            originalId
          });
        }
        return;
      }
      
      // Skip empty non-system messages unless they have tool calls
      if (!messageText && !msgToolCalls) {
        console.log('[ChatMessages] Skipping empty message:', msg.id);
        return;
      }
      
      // Use message ID or content as key
      const key = getMessageKey(msg);
      if (!messageMap.has(key)) {
        messageMap.set(key, msg);
      }
    });

    const processedSystemMessages = Array.from(systemMessageMap.values());
    const processedConversationMessages = Array.from(messageMap.values()).reverse();
    
    // Extract system message texts
    const processedSystemMessageTexts = processedSystemMessages
      .map(msg => {
        const textContent = msg.content.find(isTextContent);
        return textContent?.text || '';
      })
      .filter(text => text.trim().length > 0);

    console.log('[ChatMessages] Processed result:', {
      totalMessages: processedConversationMessages.length + processedSystemMessages.length,
      systemMessages: processedSystemMessages.length,
      messageTypes: [...processedSystemMessages, ...processedConversationMessages].map(m => m.role).join(', '),
      systemMessageIds: processedSystemMessages.map(m => m.id),
      systemMessageTexts: processedSystemMessageTexts
    });

    return {
      systemMessageTexts: processedSystemMessageTexts,
      conversationMessages: processedConversationMessages
    };
  }, [messages, isCollectingSystemMessages]);

  // Scroll to bottom when messages change
  useEffect(() => {
    if (conversationMessages.length > 0) {
      scrollToBottom();
    }
  }, [conversationMessages.length, scrollToBottom]);

  // Log messages for debugging only when they change
  useEffect(() => {
    const messageKeys = conversationMessages.map(m => m.id).join(',');
    console.log('[ChatMessages] Render update:', {
      totalMessages: messages.length,
      processedMessages: conversationMessages.length,
      systemMessages: systemMessageTexts.length,
      assistantMessages: conversationMessages.filter(m => m.role === 'assistant').length,
      userMessages: conversationMessages.filter(m => m.role === 'user').length,
      messageKeys
    });
  }, [messages.length, conversationMessages, systemMessageTexts]);

  // Use systemMessages prop if provided, otherwise use processed ones
  const displaySystemMessages = systemMessages.length > 0 ? systemMessages : systemMessageTexts;

  // Render system messages
  if (systemMessages.length > 0) {
    return (
      <div className="system-messages">
        <SystemMessages messages={systemMessages} />
      </div>
    );
  }

  if (!conversationMessages.length) {
    return (
      <div className="flex-1 flex items-center justify-center p-4 text-center text-[#94A3B8]">
        <div className="text-center">
          <h3 className="text-lg font-medium mb-2">Welcome to the Teammate Chat!</h3>
          <p className="text-sm">Start the conversation by typing a message below.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-4xl mx-auto p-4 space-y-4">
        {/* Render conversation messages in order */}
        {conversationMessages.map((message) => {
          const key = getMessageKey(message);

          if (message.role === 'system') {
            return (
              <AssistantMessage
                key={key}
                message={message}
                isSystem
              />
            );
          }

          if (message.role === 'assistant') {
            return (
              <AssistantMessage
                key={key}
                message={message}
              />
            );
          }

          if (message.role === 'user') {
            return (
              <UserMessage
                key={key}
                message={message}
              />
            );
          }

          return null; // skip any other roles
        })}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}; 