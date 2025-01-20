"use client";

import { useEffect, useRef, useMemo, useCallback, useState } from 'react';
import { ThreadMessage, ThreadAssistantContentPart, TextContentPart } from '@assistant-ui/react';
import { UserMessage } from './UserMessage';
import { AssistantMessage } from './AssistantMessage';
import { SystemMessages } from './SystemMessages';
import { useTeammateContext } from "../../MyRuntimeProvider";
import { Terminal, Box, Cloud, Wrench, GitBranch, Database, Code } from "lucide-react";
import { Button } from "@/app/components/button";

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

interface Integration {
  name: string;
  type?: string;
}

interface Starter {
  command: string;
  display_name: string;
  icon?: string;
}

interface TeammateCapabilities {
  tools: any[];
  integrations: Array<string | Integration>;
  starters: Array<Starter>;
  instruction_type: string;
  llm_model: string;
  description: string;
  runner?: string;
}

interface ChatMessagesProps {
  messages: readonly ThreadMessage[];
  isCollectingSystemMessages: boolean;
  systemMessages?: string[];
  capabilities?: TeammateCapabilities;
  teammate?: {
    name?: string;
    description?: string;
  };
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

// Update type guard to handle string messages
function isThreadMessage(message: string | ThreadMessage): message is ThreadMessage {
  return typeof message !== 'string' && 'role' in message;
}

const getMessageKey = (message: string | ThreadMessage): string => {
  if (!isThreadMessage(message)) return `string-${message}`;
  const textContent = message.content.find((c): c is TextContentPart => c.type === 'text');
  return message.id || `${message.role}-${textContent?.text || Date.now()}`;
};

const isTextContent = (content: any): content is TextContent => {
  return content?.type === 'text' && typeof content?.text === 'string';
};

const hasToolCalls = (msg: ThreadMessage & { tool_calls?: ToolCall[] }): boolean => {
  return 'tool_calls' in msg && 
    Array.isArray(msg.tool_calls) && 
    msg.tool_calls.length > 0;
};

// Helper function to get the appropriate icon for an integration
const getIcon = (type: string) => {
  const checkType = (keyword: string) => type.toLowerCase().includes(keyword);

  // Integration-specific icons with direct URLs
  if (checkType('slack')) return <img src="https://cdn4.iconfinder.com/data/icons/logos-and-brands/512/306_Slack_logo-512.png" alt="Slack" className="h-5 w-5 object-contain" />;
  if (checkType('aws')) return <img src="https://uxwing.com/wp-content/themes/uxwing/download/brands-and-social-media/aws-icon.png" alt="AWS" className="h-5 w-5 object-contain" />;
  if (checkType('github')) return <img src="https://cdn-icons-png.flaticon.com/512/25/25231.png" alt="GitHub" className="h-5 w-5 object-contain" />;
  if (checkType('jira')) return <img src="https://cdn-icons-png.flaticon.com/512/5968/5968875.png" alt="Jira" className="h-5 w-5 object-contain" />;
  if (checkType('kubernetes')) return <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Kubernetes_logo_without_workmark.svg/2109px-Kubernetes_logo_without_workmark.svg.png" alt="Kubernetes" className="h-5 w-5 object-contain" />;
  
  // Other icons
  if (checkType('terraform')) return <img src="/icons/terraform.svg" alt="Terraform" className="h-5 w-5" />;
  if (checkType('tool')) return <Wrench className="h-5 w-5 text-purple-400" />;
  if (checkType('workflow')) return <GitBranch className="h-5 w-5 text-blue-400" />;
  if (checkType('database')) return <Database className="h-5 w-5 text-green-400" />;
  if (checkType('code')) return <Code className="h-5 w-5 text-yellow-400" />;
  return <Terminal className="h-5 w-5 text-purple-400" />;
};

export const ChatMessages = ({ 
  messages, 
  isCollectingSystemMessages, 
  systemMessages = [],
  capabilities,
  teammate
}: ChatMessagesProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { selectedTeammate, currentState } = useTeammateContext();

  // Group and deduplicate system messages
  const groupedMessages = useMemo(() => {
    const systemMsgs: SystemMessage[] = [];
    const otherMsgs: ThreadMessage[] = [];
    const seenWarnings = new Set<string>();

    messages.forEach(msg => {
      if (isSystemMessage(msg)) {
        // Extract warnings from message text
        const textContent = msg.content.find((c): c is TextContentPart => c.type === 'text');
        if (textContent?.text) {
          const warnings = textContent.text
            .split(/(?=WARNING:|ERROR:)/)
            .map(warning => warning.trim())
            .filter(warning => warning.length > 0);

          // Add unique warnings
          warnings.forEach(warning => {
            if (!seenWarnings.has(warning)) {
              seenWarnings.add(warning);
              systemMsgs.push({
                ...msg,
                content: [{ type: 'text', text: warning }]
              });
            }
          });
        }
      } else {
        otherMsgs.push(msg);
      }
    });

    // Combine system messages into a single message if there are any
    if (systemMsgs.length > 0) {
      const combinedWarnings = Array.from(seenWarnings).join('\n\n');
      return [
        {
          id: 'system-warnings',
          role: 'system',
          content: [{ type: 'text', text: combinedWarnings }],
          metadata: {
            custom: {
              isSystemMessage: true
            }
          },
          createdAt: new Date()
        } as SystemMessage,
        ...otherMsgs
      ];
    }

    return otherMsgs;
  }, [messages]);

  // Scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [groupedMessages]);

  // Show welcome message if no messages and we have capabilities
  if (!groupedMessages.length && capabilities) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
        <div className="max-w-2xl w-full space-y-8">
          {/* Teammate Info */}
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-white">
              {teammate?.name || 'Welcome'}
            </h2>
            <p className="text-slate-400">
              {teammate?.description || capabilities.description}
            </p>
          </div>

          {/* Tools */}
          {capabilities.tools?.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-white">Available Tools</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {capabilities.tools.map((tool, index) => (
                  <div key={index} className="bg-[#1E293B] rounded-lg p-4 flex items-center gap-3">
                    <Wrench className="h-5 w-5 text-purple-400" />
                    <span className="text-sm text-slate-300">{tool.name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Integrations */}
          {capabilities.integrations?.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-white">Available Integrations</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {capabilities.integrations.map((integration: string | Integration, index: number) => {
                  const type = typeof integration === 'string' ? integration : integration.type || integration.name;
                  const name = typeof integration === 'string' ? integration : integration.name;
                  return (
                    <div key={index} className="bg-[#1E293B] rounded-lg p-4 flex items-center gap-3">
                      {getIcon(type)}
                      <span className="text-sm text-slate-300">{name}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Starters */}
          {capabilities.starters?.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-white">Quick Start Commands</h3>
              <div className="grid grid-cols-1 gap-4">
                {capabilities.starters.map((starter: Starter, index: number) => (
                  <Button
                    key={index}
                    variant="outline"
                    className="w-full justify-start bg-[#1E293B] border-[#2D3B4E] hover:bg-[#2D3B4E] text-slate-300"
                    onClick={() => {
                      // Handle starter command
                      console.log('Starter command:', starter.command);
                    }}
                  >
                    <Code className="h-4 w-4 text-[#7C3AED]" />
                    <span className="truncate">{starter.display_name}</span>
                  </Button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-4xl mx-auto p-4 space-y-6">
        {groupedMessages.map((message) => {
          if (isUserMessage(message)) {
            return <UserMessage key={message.id} message={message} />;
          }
          
          if (isAssistantMessage(message)) {
            return (
              <AssistantMessage 
                key={message.id} 
                message={message} 
                isSystem={false}
              />
            );
          }
          
          if (isSystemMessage(message)) {
            return (
              <AssistantMessage 
                key={message.id} 
                message={message} 
                isSystem={true}
              />
            );
          }
          
          return null;
        })}

        {isCollectingSystemMessages && (
          <div className="flex justify-center py-4">
            <div className="animate-pulse flex items-center space-x-2">
              <div className="h-2 w-2 bg-purple-500 rounded-full"></div>
              <div className="h-2 w-2 bg-purple-500 rounded-full animation-delay-200"></div>
              <div className="h-2 w-2 bg-purple-500 rounded-full animation-delay-400"></div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} className="h-4" />
      </div>
    </div>
  );
}; 