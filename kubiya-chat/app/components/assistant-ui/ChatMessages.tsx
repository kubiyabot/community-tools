"use client";

import { useEffect, useRef, useMemo, useCallback, useState } from 'react';
import { ThreadMessage, ThreadAssistantContentPart, TextContentPart } from '@assistant-ui/react';
import { UserMessage } from './UserMessage';
import { AssistantMessage } from './AssistantMessage';
import { SystemMessages } from './SystemMessages';
import { useTeammateContext } from "../../MyRuntimeProvider";
import { 
  Terminal, Box, Cloud, Wrench, GitBranch, Database, Code, 
  Settings, Search, ChevronDown, Bot, Workflow, Globe, Loader2,
  Clock, Plus, Calendar, Bell, X, MoreHorizontal, ListTodo
} from "lucide-react";
import { Button } from "@/app/components/button";
import { toolRegistry, CustomToolUI } from './ToolRegistry';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "../../components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../../components/ui/tooltip";
import { cn } from "@/lib/utils";
import { toast } from "../../components/ui/use-toast";
import { ScheduledTasksModal } from '../ScheduledTasksModal';
import mermaid from 'mermaid';
import { TaskSchedulingModal } from '@/app/components/task';

interface ToolCall {
  type: 'tool_init' | 'tool_output';
  id: string;
  name?: string;
  arguments?: Record<string, unknown>;
  message?: string;
  timestamp?: string;
  tool_description?: string;
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
  tools?: any[];
  integrations?: Array<string | Integration>;
  starters?: Array<Starter>;
  instruction_type?: string;
  llm_model?: string;
  description?: string;
  runner?: string;
}

interface SourceMetadata {
  sourceId: string;
  metadata: {
    tools?: Array<{
      name: string;
      description: string;
      type?: string;
      icon_url?: string;
      metadata?: {
        git_url?: string;
        git_branch?: string;
        git_path?: string;
        docker_image?: string;
      };
      parameters?: Array<{
        name: string;
        type: string;
        description?: string;
        required?: boolean;
      }>;
    }>;
  };
}

interface Source {
  sourceId: string;
  name?: string;
}

interface ChatMessagesProps {
  messages: readonly ThreadMessage[];
  isCollectingSystemMessages: boolean;
  systemMessages?: string[];
  capabilities?: TeammateCapabilities;
  teammate?: {
    name?: string;
    description?: string;
    uuid?: string;
    avatar_url?: string;
    team_id?: string;
    user_id?: string;
    org_id?: string;
    email?: string;
    context?: string;
    integrations?: Array<Integration | string>;
  };
  showTeammateDetails?: () => void;
  onStarterCommand?: (command: string) => void;
  onScheduleTask?: () => void;
}

interface TextContent {
  type: 'text';
  text: string;
}

interface ToolMetadata {
  name: string;
  description: string;
  icon: string | React.ComponentType<any>;
  category?: string;
  version?: string;
}

interface IntegrationData {
  tools: Record<string, ToolMetadata>;
  categories: string[];
}

interface ScheduledTask {
  id: string;
  task_id: string;
  task_uuid: string;
  task_type: string;
  scheduled_time: string;
  channel_id: string;
  parameters: {
    message_text: string;
    team_id: string;
    user_email: string;
    cron_string?: string;
  };
  status: string;
  created_at: string;
  updated_at: string | null;
}

interface TaskData {
  channel_id: string;
  channel_name: string;
  created_at: string;
  next_schedule_time: string | null;
  parameters: {
    action_context_data: Record<string, any>;
    body: {
      team: {
        id: string;
      };
      user: {
        id: string;
      };
    };
    channel_id: string;
    context: string;
    cron_string: string;
    existing_session: boolean;
    message_text: string;
    organization_name: string;
    repeat: boolean;
    task_uuid: string;
    team_id: string;
    user_email: string;
  };
  scheduled_time: string;
  status: string;
  task_id: string;
  task_uuid: string;
  updated_at: string | null;
  user_email: string;
}

const defaultIcons = {
  kubernetes: Terminal,
  git: GitBranch,
  sql: Database,
  http: Globe,
  workflow: Workflow,
};

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

function isTextContentPart(content: any): content is TextContentPart {
  return content?.type === 'text' && typeof content?.text === 'string';
}

const getMessageKey = (message: string | ThreadMessage): string => {
  if (typeof message === 'string') return `string-${message}`;
  return message.id || `${message.role}-${Date.now()}`;
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

interface QuickAction {
  icon: React.ComponentType<any>;
  label: string;
  description: string;
  action: () => void;
  color: string;
  badge?: number;
}

// Add MermaidDiagram component before ChatMessages component
const MermaidDiagram = ({ code }: { code: string }) => {
  const [svg, setSvg] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const elementId = useMemo(() => `mermaid-${Math.random().toString(36).substr(2, 9)}`, []);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: true,
      theme: 'dark',
      securityLevel: 'loose',
      themeVariables: {
        darkMode: true,
        background: '#1A1F2E',
        primaryColor: '#7C3AED',
        primaryTextColor: '#E2E8F0',
        secondaryColor: '#4B5563',
        lineColor: '#4B5563',
        textColor: '#E2E8F0',
      }
    });

    const renderDiagram = async () => {
      try {
        const { svg } = await mermaid.render(elementId, code);
        setSvg(svg);
        setError(null);
      } catch (err) {
        console.error('Failed to render mermaid diagram:', err);
        setError('Failed to render diagram');
      }
    };

    renderDiagram();
  }, [code, elementId]);

  if (error) {
    return (
      <div className="text-red-400 bg-red-400/10 rounded-lg p-3 text-sm">
        {error}
        <pre className="mt-2 text-xs">{code}</pre>
      </div>
    );
  }

  return (
    <div 
      className="mermaid-diagram bg-[#1A1F2E] rounded-lg p-4 my-4"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
};

export const ChatMessages = ({ 
  messages, 
  isCollectingSystemMessages, 
  systemMessages = [],
  capabilities,
  teammate,
  showTeammateDetails,
  onStarterCommand,
  onScheduleTask
}: ChatMessagesProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { selectedTeammate, currentState, teammates } = useTeammateContext();
  const [sourceMetadata, setSourceMetadata] = useState<SourceMetadata | null>(null);
  const [isToolsExpanded, setIsToolsExpanded] = useState(false);
  const [toolsFilter, setToolsFilter] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [integrations, setIntegrations] = useState<IntegrationData | null>(null);
  const [showTaskModal, setShowTaskModal] = useState(false);

  // Helper function to extract Mermaid diagrams
  const extractMermaidDiagrams = (text: string): { diagrams: string[], remainingText: string } => {
    const mermaidPattern = /```mermaid\n([\s\S]*?)```/g;
    const diagrams: string[] = [];
    const remainingText = text.replace(mermaidPattern, (match, diagramCode) => {
      diagrams.push(diagramCode.trim());
      return '{{MERMAID_DIAGRAM}}';
    });
    
    return { diagrams, remainingText };
  };

  // Render message with Mermaid support
  const renderMessage = (message: ThreadMessage) => {
    if (isUserMessage(message)) {
      return <UserMessage key={getMessageKey(message)} message={message} />;
    }
    
    if (isAssistantMessage(message)) {
      // Process text content for Mermaid diagrams
      const processedContent = message.content.map(content => {
        if (isTextContentPart(content)) {
          const { diagrams, remainingText } = extractMermaidDiagrams(content.text);
          if (diagrams.length > 0) {
            // Split text by diagram placeholders and interleave with Mermaid components
            const parts = remainingText.split('{{MERMAID_DIAGRAM}}');
            const processedText = parts.reduce((acc, part, index) => {
              if (index === 0) return part;
              const diagram = diagrams[index - 1];
              return acc + `\n\n\`\`\`mermaid\n${diagram}\n\`\`\`\n\n` + part;
            }, '');
            
            return {
              type: 'text' as const,
              text: processedText
            };
          }
        }
        return content;
      }) as ThreadAssistantContentPart[];

      // Group tool calls by their ID to maintain execution context
      const toolCallsById = new Map<string, ToolCall[]>();
      
      // Process all tool calls
      message.tool_calls?.forEach(call => {
        const existingCalls = toolCallsById.get(call.id) || [];
        toolCallsById.set(call.id, [...existingCalls, call]);
      });

      // Convert the grouped calls back to a flat array, maintaining order
      const groupedToolCalls = Array.from(toolCallsById.values()).flat();
      
      return (
        <AssistantMessage 
          key={getMessageKey(message)} 
          message={{
            ...message,
            content: processedContent,
            tool_calls: groupedToolCalls
          }}
          isSystem={false}
          sourceMetadata={sourceMetadata || undefined}
        />
      );
    }
    
    if (isSystemMessage(message)) {
      return (
        <AssistantMessage 
          key={getMessageKey(message)} 
          message={message} 
          isSystem={true}
          sourceMetadata={sourceMetadata || undefined}
        />
      );
    }
    
    return null;
  };

  useEffect(() => {
    const fetchSourcesAndMetadata = async () => {
      if (!teammate?.uuid) {
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      try {
        const sourcesRes = await fetch(`/api/teammates/${teammate.uuid}/sources`);
        if (!sourcesRes.ok) {
          console.error('Failed to fetch teammate sources:', {
            status: sourcesRes.status,
            statusText: sourcesRes.statusText
          });
          return;
        }

        const sources = await sourcesRes.json();
        if (!sources || !sources.length) {
          console.log('No sources found for teammate:', teammate.uuid);
          return;
        }

        const metadataPromises = sources.map(async (source: Source) => {
          const metadataRes = await fetch(`/api/teammates/${teammate.uuid}/sources/${source.sourceId}/metadata`);
          if (!metadataRes.ok) {
            console.error('Failed to fetch metadata:', {
              sourceId: source.sourceId,
              status: metadataRes.status
            });
            return null;
          }

          const metadata = await metadataRes.json();
          return metadata;
        });

        const metadataResults = await Promise.all(metadataPromises);
        const validMetadata = metadataResults.filter(result => result !== null);

        if (validMetadata.length > 0) {
          const combinedMetadata = {
            sourceId: 'combined',
            metadata: {
              tools: validMetadata.flatMap(metadata => metadata?.metadata?.tools || [])
            }
          };

          setSourceMetadata(combinedMetadata);
        }

        setIsLoading(false);
      } catch (error) {
        console.error('Error fetching source metadata:', error);
        setIsLoading(false);
      }
    };

    fetchSourcesAndMetadata();
  }, [teammate?.uuid]);

  useEffect(() => {
    // Load integrations and tool metadata on mount
    const loadIntegrations = async () => {
      try {
        const response = await fetch('/api/integrations');
        const data: IntegrationData = await response.json();
        
        // Process tool metadata and register tools
        const tools = data?.tools || {};
        if (Object.keys(tools).length > 0) {
          Object.entries(tools).forEach(([toolName, metadata]) => {
            // Convert icon URL to component if it's a string URL
            let icon = metadata.icon;
            if (typeof icon === 'string') {
              // If it's a URL, create an img component
              const IconComponent = (props: any) => (
                <img 
                  src={icon as string} 
                  alt={`${toolName} icon`}
                  className="w-4 h-4"
                  {...props}
                />
              );
              icon = IconComponent;
            } else {
              // Use default icon based on category or name
              icon = defaultIcons[toolName.toLowerCase() as keyof typeof defaultIcons] || Terminal;
            }

            // Register tool with processed metadata
            const toolUI: CustomToolUI = {
              name: metadata.name,
              description: metadata.description,
              icon: icon as React.ComponentType<any>,
              metadata: {
                category: metadata.category || 'Other',
                version: metadata.version || '1.0'
              }
            };
            
            toolRegistry[toolName] = toolUI;
          });
        }

        setIntegrations(data);
      } catch (err) {
        console.error('Failed to load integrations:', err);
      }
    };

    loadIntegrations();
  }, []);

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

  // Group tools by category
  const toolsByCategory = useMemo(() => {
    if (!sourceMetadata?.metadata?.tools) return {};
    
    return sourceMetadata.metadata.tools.reduce((acc: Record<string, any[]>, tool) => {
      const category = tool.type || 'Other';
      if (!acc[category]) acc[category] = [];
      acc[category].push(tool);
      return acc;
    }, {});
  }, [sourceMetadata?.metadata?.tools]);

  // Filter tools based on search and category
  const filteredTools = useMemo(() => {
    if (!sourceMetadata?.metadata?.tools) return [];
    
    return sourceMetadata.metadata.tools.filter(tool => {
      const matchesSearch = !toolsFilter || 
        tool.name.toLowerCase().includes(toolsFilter.toLowerCase()) ||
        tool.description.toLowerCase().includes(toolsFilter.toLowerCase());
      
      const matchesCategory = !selectedCategory || tool.type === selectedCategory;
      
      return matchesSearch && matchesCategory;
    });
  }, [sourceMetadata?.metadata?.tools, toolsFilter, selectedCategory]);

  // Show welcome message if no messages and we have capabilities
  if (!groupedMessages.length && (capabilities || sourceMetadata)) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center">
        <div className="w-full max-w-4xl mx-auto space-y-6 p-4">
          {/* Teammate Info */}
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-white mb-3">
              {teammate?.name || 'Welcome'}
            </h2>
            <p className="text-slate-400 text-lg max-w-2xl mx-auto">
              {teammate?.description || capabilities?.description}
            </p>
            <div className="flex items-center justify-center gap-3 mt-4">
              <Button
                variant="outline"
                size="lg"
                onClick={() => setShowTaskModal(true)}
                className="bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20"
              >
                <ListTodo className="h-4 w-4 mr-1.5" />
                Assign Task
              </Button>
            </div>
          </div>

          {isLoading ? (
            // Loading skeleton
            <div className="space-y-4">
              <div className="bg-[#1E293B] rounded-xl p-6 animate-pulse">
                <div className="h-8 w-48 bg-[#2A3347] rounded mb-4"></div>
                <div className="grid grid-cols-2 gap-3">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="h-24 bg-[#2A3347] rounded"></div>
                  ))}
                </div>
              </div>
              <div className="bg-[#1E293B] rounded-xl p-6 animate-pulse">
                <div className="h-8 w-48 bg-[#2A3347] rounded mb-4"></div>
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-12 bg-[#2A3347] rounded"></div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Tools Preview Section */}
              {sourceMetadata?.metadata?.tools && sourceMetadata.metadata.tools.length > 0 && (
                <div className={`bg-[#1E293B] rounded-xl p-4 transition-all ${isToolsExpanded ? 'h-auto' : 'h-[250px]'}`}>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="p-1.5 rounded-lg bg-purple-500/10">
                        <Wrench className="h-5 w-5 text-purple-400" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white">Available Tools</h3>
                        <p className="text-sm text-slate-400">
                          {isToolsExpanded ? 'All available tools' : 'Most commonly used tools'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm px-3 py-1 rounded-full bg-[#2A3347] text-purple-400 font-medium">
                        {sourceMetadata.metadata.tools.length} tools
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-slate-400 hover:text-white"
                        onClick={() => setIsToolsExpanded(!isToolsExpanded)}
                      >
                        <ChevronDown className={`h-4 w-4 mr-1.5 transition-transform ${isToolsExpanded ? 'rotate-180' : ''}`} />
                        {isToolsExpanded ? 'Show Less' : 'Show More'}
                      </Button>
                    </div>
                  </div>

                  {/* Tools Grid with smooth height transition */}
                  <div className={`grid grid-cols-2 gap-2 overflow-hidden transition-all duration-300 ${
                    isToolsExpanded ? 'max-h-[600px]' : 'max-h-[180px]'
                  }`}>
                    {(isToolsExpanded ? filteredTools : filteredTools.slice(0, 4)).map((tool, index) => (
                      <div 
                        key={index}
                        className="group bg-[#2A3347] rounded-lg p-2.5 hover:bg-[#374151] transition-all cursor-pointer hover:shadow-lg border border-transparent hover:border-purple-500/30"
                        onClick={showTeammateDetails}
                      >
                        <div className="flex items-center gap-2">
                          <div className="p-1.5 rounded-lg bg-[#1A1F2E] group-hover:bg-[#2A3347]">
                            {tool.icon_url ? (
                              <img src={tool.icon_url} alt={tool.name} className="h-5 w-5 object-contain" />
                            ) : (
                              getIcon(tool.type || 'tool')
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <h4 className="text-sm font-medium text-white truncate">{tool.name}</h4>
                              {tool.type && (
                                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#1A1F2E] text-purple-400 flex-shrink-0">
                                  {tool.type}
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-slate-400 line-clamp-1">{tool.description}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Quick Actions Row */}
              <div className="space-y-4">
                {/* Quick Start Commands */}
                {capabilities?.starters && capabilities.starters.length > 0 && (
                  <div className="bg-[#1E293B] rounded-xl p-4">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="p-2 rounded-lg bg-blue-500/10">
                        <Terminal className="h-5 w-5 text-blue-400" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white">Quick Start</h3>
                        <p className="text-sm text-slate-400">Common commands</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2 max-h-[160px] overflow-y-auto pr-2">
                      {capabilities.starters.map((starter: Starter, index: number) => (
                        <button
                          key={index}
                          className="group relative w-full flex items-center gap-3 p-3 bg-[#2A3347] rounded-lg text-left hover:bg-[#374151] transition-all border border-transparent hover:border-blue-500/30 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                          onClick={() => {
                            if (onStarterCommand) {
                              onStarterCommand(starter.command);
                            }
                          }}
                        >
                          <div className="p-2 rounded-lg bg-[#1A1F2E] group-hover:bg-[#2A3347] transition-colors">
                            {starter.icon ? (
                              <img src={starter.icon} alt="" className="h-4 w-4" />
                            ) : (
                              <Terminal className="h-4 w-4 text-blue-400" />
                            )}
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="font-medium text-white text-sm truncate">{starter.display_name}</div>
                            <div className="text-xs text-slate-400 font-mono truncate mt-0.5">{starter.command}</div>
                          </div>
                          
                          {/* Hover tooltip */}
                          <div className="absolute left-0 right-0 bottom-full mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-10">
                            <div className="bg-[#374151] rounded-lg p-2 shadow-lg border border-blue-500/20">
                              <div className="text-xs text-white font-medium mb-1">{starter.display_name}</div>
                              <div className="text-xs text-slate-300 font-mono break-all">{starter.command}</div>
                            </div>
                            <div className="absolute bottom-0 left-4 w-2 h-2 bg-[#374151] transform rotate-45 translate-y-1 border-r border-b border-blue-500/20"></div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Connected Platforms */}
                {capabilities?.integrations && capabilities.integrations.length > 0 && (
                  <div className="bg-[#1E293B] rounded-xl p-4">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="p-2 rounded-lg bg-green-500/10">
                        <Cloud className="h-5 w-5 text-green-400" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white">Connected Platforms</h3>
                        <p className="text-sm text-slate-400">Active integrations</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-2 max-h-[120px] overflow-y-auto pr-2">
                      {capabilities.integrations.map((integration, index) => {
                        const integrationName = typeof integration === 'string' ? integration : integration.name;
                        const integrationType = typeof integration === 'string' ? integration : integration.type || integration.name;
                        
                        return (
                          <div
                            key={index}
                            className="bg-[#2A3347] rounded-lg p-2.5 flex items-center gap-2 group hover:bg-[#374151] transition-all border border-transparent hover:border-green-500/30"
                          >
                            <div className="p-1.5 rounded-lg bg-[#1A1F2E] group-hover:bg-[#2A3347]">
                              {getIcon(integrationType)}
                            </div>
                            <div className="min-w-0">
                              <div className="text-sm font-medium text-white truncate">{integrationName}</div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto relative">
      <div className="max-w-4xl mx-auto p-4 space-y-6">
        {groupedMessages.map(renderMessage)}

        {isCollectingSystemMessages && (
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#2D3B4E] flex items-center justify-center relative">
              {teammate?.avatar_url ? (
                <img 
                  src={teammate.avatar_url} 
                  alt={teammate.name || 'Assistant'} 
                  className="w-full h-full rounded-full object-cover"
                />
              ) : (
                <Bot className="h-4 w-4 text-[#7C3AED]" />
              )}
              <span className="absolute -bottom-1 -right-1 h-2 w-2">
                <span className="absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75 animate-ping"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
              </span>
            </div>
            <div className="flex-1 space-y-1.5">
              <div className="flex items-center gap-2">
                <div className="text-sm font-medium text-white">
                  {teammate?.name || 'Assistant'}
                </div>
                <div className="flex items-center gap-1 text-xs text-purple-400">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  <span>thinking</span>
                </div>
              </div>
              <div className="text-sm text-[#E2E8F0] prose prose-invert prose-sm max-w-none">
                <div className="group relative bg-[#1A1F2E]/50 rounded-lg p-3">
                  <div className="flex items-start">
                    <div className="flex-1">
                      <div className="h-4 w-12 bg-purple-400/10 rounded animate-pulse"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} className="h-4" />
      </div>

      {/* Task Scheduling Modal */}
      {showTaskModal && teammate?.uuid && (
        <TaskSchedulingModal
          isOpen={showTaskModal}
          onClose={() => setShowTaskModal(false)}
          teammate={{
            uuid: teammate.uuid,
            name: teammate.name || 'Unknown',
            team_id: teammate.team_id || '',
            user_id: teammate.user_id || '',
            org_id: teammate.org_id || '',
            email: teammate.email || '',
            context: teammate.context || teammate.uuid,
            integrations: teammate.integrations || []
          }}
          onSchedule={async (data) => {
            try {
              await fetch('/api/tasks', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
              });
              toast({
                title: "Task Scheduled",
                description: "The task has been scheduled successfully.",
              });
              setShowTaskModal(false);
            } catch (error) {
              console.error('Failed to schedule task:', error);
              toast({
                variant: "destructive",
                title: "Error",
                description: "Failed to schedule task. Please try again.",
              });
            }
          }}
        />
      )}
    </div>
  );
}; 