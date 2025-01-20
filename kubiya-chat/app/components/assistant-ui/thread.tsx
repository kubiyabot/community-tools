"use client";

import {
  ThreadWelcome,
  Composer,
  type ThreadConfig,
  ThreadPrimitive,
  ComposerPrimitive
} from "@assistant-ui/react";
import { Avatar, AvatarFallback } from "@/app/components/avatar";
import { Button } from "@/app/components/button";
import { ArrowDownIcon, SendHorizontalIcon, StopCircleIcon, Terminal, Box, Cloud, Wrench, GitBranch, Database, Code } from "lucide-react";
import { useTeammateContext } from "../../MyRuntimeProvider";
import { useMemo, useEffect, useState, useCallback } from "react";

interface TeammateCapabilities {
  tools: any[];
  integrations: string[];
  starters: Array<{
    command: string;
    display_name: string;
    icon?: string;
  }>;
  instruction_type: string;
  llm_model: string;
  description: string;
}

interface Suggestion {
  text: string;
  command?: string;
  icon: JSX.Element | string;
}

const WelcomeMessage = () => {
  const { teammates, selectedTeammate } = useTeammateContext();
  const teammate = useMemo(() => teammates.find(t => t.uuid === selectedTeammate), [teammates, selectedTeammate]);
  const [capabilities, setCapabilities] = useState<TeammateCapabilities | null>(null);

  useEffect(() => {
    const fetchCapabilities = async () => {
      if (!selectedTeammate) return;
      try {
        const response = await fetch(`/api/teammates/${selectedTeammate}/capabilities`);
        if (response.ok) {
          const data = await response.json();
          setCapabilities(data);
        }
      } catch (error) {
        console.error('Failed to fetch capabilities:', error);
      }
    };

    fetchCapabilities();
  }, [selectedTeammate]);

  if (!teammate) return null;

  // Get icon based on integration or instruction type
  const getIcon = (type: string) => {
    type = type.toLowerCase();
    // Integration-specific icons
    if (type.includes('aws')) return <img src="/icons/aws.svg" alt="AWS" className="h-full w-full object-contain" />;
    if (type.includes('github')) return <img src="/icons/github.svg" alt="GitHub" className="h-full w-full object-contain" />;
    if (type.includes('slack')) return <img src="/icons/slack.svg" alt="Slack" className="h-full w-full object-contain" />;
    if (type.includes('jira')) return <img src="/icons/jira.svg" alt="Jira" className="h-full w-full object-contain" />;
    
    // Other icons
    if (type.includes('terraform')) return <img src="/icons/terraform.svg" alt="Terraform" className="h-full w-full object-contain" />;
    if (type.includes('kubernetes')) return <img src="/icons/kubernetes.svg" alt="Kubernetes" className="h-full w-full object-contain" />;
    if (type.includes('tool')) return <Wrench className="h-4 w-4" />;
    if (type.includes('workflow')) return <GitBranch className="h-4 w-4" />;
    if (type.includes('database')) return <Database className="h-4 w-4" />;
    if (type.includes('code')) return <Code className="h-4 w-4" />;
    return <Terminal className="h-4 w-4" />;
  };

  return (
    <div className="flex flex-col h-full bg-[#0F1629] text-gray-200">
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-6 py-12">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-2xl font-semibold mb-3">Welcome to {teammate.name}</h1>
            <p className="text-gray-400 text-sm max-w-2xl mx-auto leading-relaxed">
              {teammate.description}
            </p>
            {teammate.llm_model && (
              <div className="flex items-center justify-center gap-2 mt-3 text-xs text-gray-500">
                <Terminal className="h-3 w-3" />
                <span>Powered by {teammate.llm_model}</span>
              </div>
            )}
          </div>

          {/* Suggestions Section (formerly Quick Start Commands) */}
          {capabilities?.starters && capabilities.starters.length > 0 && (
            <div className="mb-6">
              <h2 className="text-xs font-medium text-gray-400 mb-3 uppercase tracking-wider">
                Here's what you can try
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-w-full">
                {capabilities.starters.map((starter, index) => (
                  <div
                    key={index}
                    className="group relative"
                  >
                    <button
                      onClick={() => {
                        const composer = document.querySelector('[role="textbox"]') as HTMLTextAreaElement;
                        if (composer) {
                          composer.value = starter.command;
                          composer.focus();
                          const event = new Event('input', { bubbles: true });
                          composer.dispatchEvent(event);
                          
                          // Simulate Enter key press to send the message
                          const enterEvent = new KeyboardEvent('keydown', {
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            which: 13,
                            bubbles: true
                          });
                          composer.dispatchEvent(enterEvent);
                        }
                      }}
                      className="group flex items-start w-full max-w-full bg-[#1B2236] hover:bg-[#232B42] rounded-md border border-[#2A3347] transition-colors"
                    >
                      <div className="flex-shrink-0 p-2">
                        <div className="w-5 h-5 flex items-center justify-center rounded-md bg-[#2A3347] group-hover:bg-[#323E5B] transition-colors">
                          {getIcon(capabilities.instruction_type)}
                        </div>
                      </div>
                      <div className="flex-1 min-w-0 p-2 pr-3">
                        <div className="font-medium text-xs text-gray-200 truncate">
                          {starter.display_name}
                        </div>
                        <div className="text-[11px] text-gray-500 font-mono truncate">
                          {starter.command}
                        </div>
                      </div>
                    </button>
                    {/* Hover Preview */}
                    <div className="absolute left-0 right-0 bottom-full mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-10">
                      <div className="bg-[#2A3347] rounded-md p-2 shadow-lg border border-[#3D4B5E] max-w-sm">
                        <div className="text-xs text-gray-200 font-medium mb-1">{starter.display_name}</div>
                        <div className="text-[11px] text-gray-400 leading-relaxed">{starter.command}</div>
                      </div>
                      <div className="absolute bottom-0 left-4 w-2 h-2 bg-[#2A3347] transform rotate-45 translate-y-1 border-r border-b border-[#3D4B5E]"></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Available Integrations */}
          {capabilities?.integrations && capabilities.integrations.length > 0 && (
            <div className="mb-6">
              <h2 className="text-xs font-medium text-gray-400 mb-3 uppercase tracking-wider">
                Available Integrations
              </h2>
              <div className="flex flex-wrap gap-1.5">
                {capabilities.integrations.map((integration, index) => (
                  <div
                    key={index}
                    className="inline-flex items-center gap-1.5 px-2 py-1 bg-[#1B2236] rounded-md border border-[#2A3347]"
                  >
                    <div className="flex-shrink-0 w-4 h-4 flex items-center justify-center">
                      {getIcon(integration)}
                    </div>
                    <span className="text-[11px] text-gray-300">{integration}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tools Section */}
          {capabilities?.tools && capabilities.tools.length > 0 && (
            <div>
              <h2 className="text-xs font-medium text-gray-400 mb-3 uppercase tracking-wider">
                Available Tools
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {capabilities.tools.map((tool: any, index: number) => (
                  <div
                    key={index}
                    className="p-2 bg-[#1B2236] rounded-md border border-[#2A3347] overflow-hidden"
                  >
                    <div className="flex items-center gap-1.5 mb-1">
                      <div className="w-3.5 h-3.5 flex items-center justify-center">
                        <Wrench className="w-3 h-3 text-gray-400" />
                      </div>
                      <h3 className="text-xs font-medium text-gray-200 truncate">{tool.name}</h3>
                    </div>
                    <p className="text-[11px] text-gray-400 leading-relaxed pl-5 line-clamp-2">{tool.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const MyComposer = () => {
  const { teammates, selectedTeammate } = useTeammateContext();
  const teammate = teammates.find(t => t.uuid === selectedTeammate);

  return (
    <ComposerPrimitive.Root className="flex w-full items-end rounded-xl border border-[#1E293B] bg-[#0A0F1E] px-3 shadow-lg transition-colors ease-in focus-within:border-[#7C3AED]/30">
      <ComposerPrimitive.Input
        autoFocus
        placeholder={`Message ${teammate?.name || 'Kubiya'}...`}
        rows={1}
        className="max-h-40 flex-grow resize-none border-none bg-transparent px-2 py-4 text-sm text-white placeholder:text-slate-500 outline-none focus:ring-0 disabled:cursor-not-allowed"
      />
      <ThreadPrimitive.If running={false}>
        <ComposerPrimitive.Send asChild>
          <Button size="icon" className="my-2.5 bg-[#7C3AED] hover:bg-[#6D28D9] text-white">
            <SendHorizontalIcon className="h-4 w-4" />
          </Button>
        </ComposerPrimitive.Send>
      </ThreadPrimitive.If>
      <ThreadPrimitive.If running>
        <ComposerPrimitive.Cancel asChild>
          <Button size="icon" variant="destructive" className="my-2.5">
            <StopCircleIcon className="h-4 w-4" />
          </Button>
        </ComposerPrimitive.Cancel>
      </ThreadPrimitive.If>
    </ComposerPrimitive.Root>
  );
};

const ChatMessages = ({ messages, isCollectingSystemMessages }: { messages: any[], isCollectingSystemMessages: boolean }) => {
  return (
    <div className="flex-1 overflow-y-auto p-4">
      {messages.map((message, index) => (
        <div key={index} className="mb-4">
          {message.role === 'user' ? (
            <div className="flex justify-end">
              <div className="bg-indigo-600 text-white rounded-lg px-4 py-2 max-w-[80%]">
                {message.content[0]?.text}
              </div>
            </div>
          ) : message.role === 'assistant' ? (
            <div className="flex justify-start">
              <div className="bg-gray-800 text-white rounded-lg px-4 py-2 max-w-[80%]">
                {message.content[0]?.text}
              </div>
            </div>
          ) : null}
        </div>
      ))}
      {isCollectingSystemMessages && (
        <div className="flex justify-center">
          <div className="animate-pulse text-gray-400">Processing...</div>
        </div>
      )}
    </div>
  );
};

export const Thread = () => {
  const { selectedTeammate, currentState } = useTeammateContext();
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Get current thread messages from teammate state
  const currentThreadMessages = useMemo(() => {
    if (!currentState || !currentState.currentThreadId) return [];
    return currentState.threads[currentState.currentThreadId]?.messages || [];
  }, [currentState]);

  // Show welcome message if no messages
  if (!currentThreadMessages.length) {
    return <WelcomeMessage />;
  }

  return (
    <div className="flex flex-col h-full">
      <ChatMessages 
        messages={currentThreadMessages} 
        isCollectingSystemMessages={false} 
      />
      <div className="p-4 border-t border-gray-700">
        <div className="flex items-end gap-4">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (inputValue.trim()) {
                  // TODO: Implement message sending
                  setInputValue('');
                }
              }
            }}
            placeholder={`Message ${selectedTeammate ? currentState?.threads[currentState.currentThreadId]?.metadata.title : 'Kubiya'}...`}
            className="flex-1 min-h-[44px] max-h-[200px] bg-gray-800 rounded-lg p-2 text-white resize-none"
            disabled={isLoading || !selectedTeammate}
          />
          <button
            onClick={() => {
              if (inputValue.trim()) {
                // TODO: Implement message sending
                setInputValue('');
              }
            }}
            disabled={isLoading || !inputValue.trim() || !selectedTeammate}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}; 