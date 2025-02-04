"use client";

import { useEffect, useRef, useMemo, useCallback, useState } from 'react';
import { ThreadMessage, ThreadAssistantContentPart, TextContentPart, Tool } from '@assistant-ui/react';
import { UserMessage } from './UserMessage';
import { AssistantMessage } from './AssistantMessage';
import { SystemMessages } from './SystemMessages';
import { useTeammateContext } from "../../MyRuntimeProvider";
import { 
  Terminal, Box, Cloud, Wrench, GitBranch, Database, Code, 
  Settings, Search, ChevronDown, Bot, Workflow, Globe, Loader2,
  Clock, Plus, Calendar, Bell, X, MoreHorizontal, ListTodo, User
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
import { lazy, Suspense } from 'react';
import mermaid from 'mermaid';
import { TaskSchedulingModal } from '../TaskSchedulingModal';
import type { Integration, SimpleIntegration, IntegrationType } from '@/app/types/integration';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { SourceInfo } from '@/app/types/source';

interface ToolCall {
  type: 'tool_init' | 'tool_output';
  id: string;
  name?: string;
  arguments?: Record<string, unknown>;
  message?: string;
  timestamp?: string;
  tool_description?: string;
}

export interface SystemMessage {
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

type AssistantMessage = ThreadMessage & { 
  role: 'assistant';
  tool_calls?: ToolCall[];
};

type UserThreadMessage = ThreadMessage & { 
  role: 'user';
  tool_calls?: ToolCall[];
};

interface Teammate {
  name?: string;
  description?: string;
  uuid?: string;
  avatar_url?: string;
  team_id?: string;
  user_id?: string;
  org_id?: string;
  email?: string;
  context?: string;
  integrations?: Array<string | SimpleIntegration>;
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
    }>;
  };
}

interface Source {
  sourceId: string;
  uuid?: string;
  name?: string;
}

interface ChatMessagesProps {
  messages: readonly ThreadMessage[];
  isCollectingSystemMessages: boolean;
  systemMessages?: string[];
  capabilities?: TeammateCapabilities;
  teammate?: Teammate;
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

function isSystemMessage(message: ThreadMessage): message is ThreadMessage & { role: 'system' } {
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
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const elementId = useMemo(() => `mermaid-${Math.random().toString(36).substr(2, 9)}`, []);
  const retryCount = useRef(0);
  const maxRetries = 3;

  useEffect(() => {
    const initializeMermaid = async () => {
      try {
        await mermaid.initialize({
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
          },
          flowchart: {
            curve: 'basis',
            padding: 20,
          },
          sequence: {
            actorMargin: 50,
            boxMargin: 10,
            mirrorActors: false,
            bottomMarginAdj: 1,
          }
        });
        return true;
      } catch (err) {
        console.warn('Failed to initialize mermaid:', err);
        return false;
      }
    };

    const renderDiagram = async () => {
      setStatus('loading');
      
      try {
        // Initialize mermaid first
        const initialized = await initializeMermaid();
        if (!initialized) {
          throw new Error('Failed to initialize mermaid');
        }

        // Parse the diagram to validate syntax
        await mermaid.parse(code);
        
        // Render the diagram
        const { svg: renderedSvg } = await mermaid.render(elementId, code);
        
        // If successful, update state
        setSvg(renderedSvg);
        setStatus('success');
        retryCount.current = 0;
      } catch (err) {
        console.warn('Mermaid render attempt failed:', err);
        
        // Implement retry logic
        if (retryCount.current < maxRetries) {
          retryCount.current += 1;
          setTimeout(renderDiagram, 1000); // Retry after 1 second
        } else {
          setStatus('error');
          console.error('Failed to render mermaid diagram after retries:', err);
        }
      }
    };

    renderDiagram();
  }, [code, elementId]);

  // Only show the diagram when it's successfully rendered
  if (status === 'success' && svg) {
    return (
      <div 
        className="mermaid-diagram bg-[#1A1F2E] rounded-lg p-4 my-4 shadow-lg border border-purple-500/10"
        dangerouslySetInnerHTML={{ __html: svg }}
      />
    );
  }

  // Show loading state
  if (status === 'loading') {
    return (
      <div className="mermaid-diagram-loading bg-[#1A1F2E] rounded-lg p-4 my-4 border border-purple-500/10 flex items-center justify-center h-20">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <div className="animate-spin h-4 w-4 border-2 border-purple-500/20 border-t-purple-500 rounded-full" />
          <span>Rendering diagram...</span>
        </div>
      </div>
    );
  }

  // Don't show anything on error
  return null;
};

// Define interfaces locally instead of importing
interface ToolDetailsModalProps {
  teammateId?: string;
  toolId?: string;
  isOpen: boolean;
  onCloseAction: () => void;
  tool: Tool;
  source?: SourceInfo;
}

interface ScheduledTasksModalProps {
  isOpen: boolean;
  onClose: () => void;
  tasks: ScheduledTask[];
  onDelete: (taskId: string) => Promise<void>;
  isLoading: boolean;
  teammate?: {
    email?: string;
    name?: string;
    uuid?: string;
  };
  onScheduleSimilar?: (initialData: {
    description: string;
    slackTarget: string;
    scheduleType: 'quick' | 'custom';
    repeatOption: string;
  }) => void;
}

// Fix lazy loading by using default imports
const LazyToolDetailsModal = lazy(() => import('@/app/components/shared/tool-details/ToolDetailsModal').then(mod => ({ default: mod.ToolDetailsModal })));

const LazyScheduledTasksModal = lazy(() => import('@/app/components/ScheduledTasksModal').then(mod => ({ default: mod.ScheduledTasksModal })));

// Optimize message rendering with virtualization
const MessageVirtualizer = ({ messages, renderMessage }: { messages: ThreadMessage[], renderMessage: (message: ThreadMessage) => React.ReactNode }) => {
  const parentRef = useRef<HTMLDivElement>(null);
  
  const rowVirtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100,
    overscan: 5,
    getItemKey: (index) => {
      const msg = messages[index];
      const id = msg?.id;
      return typeof id === 'string' || typeof id === 'number' ? String(id) : `msg-${index}`;
    }
  });

  return (
    <div ref={parentRef} className="flex-1 overflow-y-auto relative">
      <div
        className="relative w-full"
        style={{ height: `${rowVirtualizer.getTotalSize()}px` }}
      >
        {rowVirtualizer.getVirtualItems().map((virtualItem) => {
          const key = typeof virtualItem.key === 'string' || typeof virtualItem.key === 'number' 
            ? String(virtualItem.key) 
            : `msg-${virtualItem.index}`;
            
          return (
            <div
              key={key}
              className="absolute top-0 left-0 w-full"
              style={{
                height: `${virtualItem.size}px`,
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              {renderMessage(messages[virtualItem.index])}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// Optimize source metadata fetching
const useSourceMetadata = (teammate?: Teammate) => {
  const [sourceMetadata, setSourceMetadata] = useState<SourceMetadata | null>(null);
  const [isLoading, setIsLoading] = useState(true);

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
        if (!sources?.length) {
          setIsLoading(false);
          return;
        }

        // Fetch metadata in parallel
        const metadataResults = await Promise.all(
          sources.map(async (source: Source) => {
            const effectiveSourceId = source.sourceId || source.uuid;
            if (!effectiveSourceId) return null;
            
            try {
              const metadataRes = await fetch(`/api/teammates/${teammate.uuid}/sources/${effectiveSourceId}/metadata`);
              if (!metadataRes.ok) return null;
              return await metadataRes.json();
            } catch (error) {
              console.error('Error fetching metadata:', error);
              return null;
            }
          })
        );

        const validMetadata = metadataResults.filter(Boolean);
        if (validMetadata.length > 0) {
          setSourceMetadata({
            sourceId: 'combined',
            metadata: {
              tools: validMetadata.flatMap(metadata => metadata?.metadata?.tools || [])
            }
          });
        }
      } catch (error) {
        console.error('Error fetching source metadata:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSourcesAndMetadata();
  }, [teammate?.uuid]);

  return { 
    sourceMetadata: sourceMetadata as SourceMetadata | null,
    isLoading 
  };
};

// Update the interface definition with proper types
interface MessageStatus {
  readonly type: 'running' | 'requires-action' | 'complete' | 'incomplete';
  readonly reason?: 'tool-calls' | 'stop' | 'unknown' | 'error' | 'cancelled' | 'length' | 'content-filter' | 'other';
  readonly error?: unknown;
}

interface ThreadStep {
  id: string;
  type: string;
  status: string;
  details?: Record<string, unknown>;
}

type ThreadMessageStatus = 
  | { readonly type: 'running' }
  | { readonly type: 'requires-action'; readonly reason: 'tool-calls' }
  | { readonly type: 'complete'; readonly reason: 'stop' | 'unknown' }
  | { readonly type: 'incomplete'; readonly reason: 'tool-calls' | 'error' | 'cancelled' | 'length' | 'content-filter' | 'other'; readonly error?: unknown };

interface ThreadMetadata {
  readonly unstable_data: readonly unknown[];
  readonly steps: readonly ThreadStep[];
  readonly custom: Record<string, unknown>;
}

interface AssistantMessageWithTools extends Omit<ThreadMessage, 'role' | 'metadata' | 'status'> {
  role: 'assistant';
  tool_calls?: ToolCall[];
  metadata: ThreadMetadata;
  status: ThreadMessageStatus;
  content: readonly ThreadAssistantContentPart[];
}

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
  const { sourceMetadata, isLoading } = useSourceMetadata(teammate);
  const [isToolsExpanded, setIsToolsExpanded] = useState(false);
  const [toolsFilter, setToolsFilter] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showTeammateSelectionModal, setShowTeammateSelectionModal] = useState(false);
  const [showSystemMessages, setShowSystemMessages] = useState(true);

  // Group messages by type and time
  const groupedMessages = useMemo(() => {
    const systemMsgs: SystemMessage[] = [];
    const otherMsgs: ThreadMessage[] = [];
    const seenWarnings = new Set<string>();

    messages.forEach(msg => {
      if (isSystemMessage(msg)) {
        const textContent = msg.content.find((c): c is TextContentPart => c.type === 'text');
        if (textContent?.text) {
          const warnings = textContent.text
            .split(/(?=WARNING:|ERROR:)/)
            .map(warning => warning.trim())
            .filter(warning => warning.length > 0);

          warnings.forEach(warning => {
            if (!seenWarnings.has(warning)) {
              seenWarnings.add(warning);
              systemMsgs.push({
                id: `system-${msg.id}`,
                role: 'system',
                content: [{ type: 'text', text: warning }] as const,
                metadata: {
                  unstable_data: [],
                  steps: [],
                  custom: { isSystemMessage: true }
                },
                createdAt: new Date().toISOString()
              });
            }
          });
        }
      } else {
        otherMsgs.push(msg);
      }
    });

    return {
      systemMessages: systemMsgs,
      chatMessages: otherMsgs
    };
  }, [messages]);

  // Scroll to bottom effect
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [groupedMessages]);

  return (
    <div className="flex-1 overflow-y-auto relative">
      <div className="max-w-4xl mx-auto px-4">
        {!groupedMessages.chatMessages.length && (capabilities || sourceMetadata) ? (
          <div className="flex flex-col items-center justify-center min-h-[calc(100vh-12rem)]">
            <div className="w-full space-y-8 backdrop-blur-sm bg-[#1E293B]/30 rounded-2xl p-8 border border-white/5">
              {/* Teammate Info */}
              <div className="text-center space-y-4">
                <h2 className="text-3xl font-bold text-white">
                  {teammate?.name || 'Welcome'}
                </h2>
                <p className="text-slate-400 text-lg max-w-2xl mx-auto">
                  {teammate?.description || capabilities?.description}
                </p>
                <div className="flex items-center justify-center gap-3 mt-6">
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="outline"
                          size="lg"
                          onClick={() => {
                            if (teammate?.uuid) {
                              setShowTaskModal(true);
                            } else {
                              setShowTeammateSelectionModal(true);
                              if (showTeammateDetails) {
                                showTeammateDetails();
                              }
                              toast({
                                title: "Select a Teammate",
                                description: "Please select a teammate to assign tasks to.",
                                variant: "default"
                              });
                            }
                          }}
                          className="bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20"
                        >
                          <ListTodo className="h-4 w-4 mr-2" />
                          Assign Task
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent side="bottom" className="max-w-xs">
                        <p>Assign tasks to your teammate to be executed on schedule or in response to events. Perfect for automation and recurring tasks.</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
              </div>

              {isLoading ? (
                // Loading skeleton with improved spacing
                <div className="space-y-6">
                  <div className="bg-[#1E293B] rounded-xl p-6 animate-pulse">
                    <div className="h-8 w-48 bg-[#2A3347] rounded mb-6"></div>
                    <div className="grid grid-cols-2 gap-4">
                      {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="h-28 bg-[#2A3347] rounded"></div>
                      ))}
                    </div>
                  </div>
                  <div className="bg-[#1E293B] rounded-xl p-6 animate-pulse">
                    <div className="h-8 w-48 bg-[#2A3347] rounded mb-6"></div>
                    <div className="space-y-4">
                      {[1, 2, 3].map((i) => (
                        <div key={i} className="h-14 bg-[#2A3347] rounded"></div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Tools Preview Section */}
                  {sourceMetadata?.metadata?.tools && sourceMetadata.metadata.tools.length > 0 && (
                    <div className={cn(
                      "bg-[#1E293B] rounded-xl p-6 transition-all duration-300",
                      isToolsExpanded ? "h-auto" : "h-[300px]"
                    )}>
                      <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-4">
                          <div className="p-2 rounded-lg bg-purple-500/10">
                            <Wrench className="h-5 w-5 text-purple-400" />
                          </div>
                          <div>
                            <h3 className="text-lg font-semibold text-white">Available Tools</h3>
                            <p className="text-sm text-slate-400 mt-1">
                              {isToolsExpanded ? "All available tools" : "Most commonly used tools"}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="text-sm px-4 py-1.5 rounded-full bg-[#2A3347] text-purple-400 font-medium">
                            {sourceMetadata.metadata.tools.length} tools
                          </span>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-slate-400 hover:text-white"
                            onClick={() => setIsToolsExpanded(!isToolsExpanded)}
                          >
                            <ChevronDown className={cn(
                              "h-4 w-4 mr-2 transition-transform",
                              isToolsExpanded ? "rotate-180" : ""
                            )} />
                            {isToolsExpanded ? "Show Less" : "Show More"}
                          </Button>
                        </div>
                      </div>

                      {/* Tools Grid */}
                      <div className={cn(
                        "grid grid-cols-2 gap-4 overflow-hidden transition-all duration-300",
                        isToolsExpanded ? "max-h-[800px]" : "max-h-[200px]"
                      )}>
                        {(isToolsExpanded ? sourceMetadata.metadata.tools : sourceMetadata.metadata.tools.slice(0, 4)).map((tool, index) => (
                          <div 
                            key={index}
                            className="group bg-[#2A3347] rounded-lg p-4 hover:bg-[#374151] transition-all cursor-pointer hover:shadow-lg border border-transparent hover:border-purple-500/30"
                            onClick={showTeammateDetails}
                          >
                            <div className="flex items-center gap-3">
                              <div className="p-2 rounded-lg bg-[#1A1F2E] group-hover:bg-[#2A3347]">
                                {tool.icon_url ? (
                                  <img src={tool.icon_url} alt={tool.name} className="h-5 w-5 object-contain" />
                                ) : (
                                  getIcon(tool.type || "tool")
                                )}
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <h4 className="text-sm font-medium text-white truncate">{tool.name}</h4>
                                  {tool.type && (
                                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#1A1F2E] text-purple-400 flex-shrink-0">
                                      {tool.type}
                                    </span>
                                  )}
                                </div>
                                <p className="text-xs text-slate-400 line-clamp-2">{tool.description}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Quick Actions Section with improved spacing */}
                  <div className="space-y-6">
                    {/* Quick Start Commands */}
                    {capabilities?.starters && capabilities.starters.length > 0 && (
                      <div className="bg-[#1E293B] rounded-xl p-6">
                        <div className="flex items-center gap-4 mb-6">
                          <div className="p-2 rounded-lg bg-blue-500/10">
                            <Terminal className="h-5 w-5 text-blue-400" />
                          </div>
                          <div>
                            <h3 className="text-lg font-semibold text-white">Quick Start</h3>
                            <p className="text-sm text-slate-400 mt-1">Common commands</p>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4 max-h-[200px] overflow-y-auto pr-2">
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

                    {/* Connected Platforms with improved spacing */}
                    {teammate?.integrations && teammate.integrations.length > 0 && (
                      <div className="bg-[#1E293B] rounded-xl p-6">
                        <div className="flex items-center gap-4 mb-6">
                          <div className="p-2 rounded-lg bg-green-500/10">
                            <Cloud className="h-5 w-5 text-green-400" />
                          </div>
                          <div>
                            <h3 className="text-lg font-semibold text-white">Connected Platforms</h3>
                            <p className="text-sm text-slate-400 mt-1">Active integrations</p>
                          </div>
                        </div>
                        <div className="grid grid-cols-3 gap-4 max-h-[160px] overflow-y-auto pr-2">
                          {teammate.integrations.map((integration, index) => {
                            const integrationName = typeof integration === 'string' ? integration : integration.name;
                            const integrationType = typeof integration === 'string' ? integration : integration.integration_type;
                            
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
                                  <div className="text-xs text-slate-400 truncate">{integrationType}</div>
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
        ) : (
          <div className="flex flex-col min-h-full py-4">
            {/* System Messages Toggle Button */}
            {groupedMessages.systemMessages.length > 0 && (
              <div className="fixed bottom-24 right-8 z-50">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => setShowSystemMessages(!showSystemMessages)}
                        className={cn(
                          "h-10 w-10 rounded-full shadow-lg border-white/10 backdrop-blur-sm",
                          showSystemMessages 
                            ? "bg-purple-500/10 hover:bg-purple-500/20" 
                            : "bg-[#1E293B]/50 hover:bg-[#2D3B4E]/50"
                        )}
                      >
                        <Bot className={cn(
                          "h-5 w-5 transition-colors",
                          showSystemMessages ? "text-purple-400" : "text-slate-400"
                        )} />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>{showSystemMessages ? "Hide" : "Show"} system messages</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            )}

            {/* System Messages Panel */}
            {showSystemMessages && groupedMessages.systemMessages.length > 0 && (
              <div className="sticky top-0 z-10 backdrop-blur-xl bg-gradient-to-b from-[#0F1117]/95 to-[#1A1F2E]/95 border-b border-white/5 shadow-lg mb-4">
                <div className="max-w-4xl mx-auto py-3">
                  <SystemMessages messages={groupedMessages.systemMessages} />
                </div>
              </div>
            )}

            {/* Main Chat Messages */}
            <div className="flex-1 space-y-3">
              {groupedMessages.chatMessages.map((message, index, filteredMessages) => {
                const isFirstInGroup = index === 0 || 
                  filteredMessages[index - 1]?.role !== message.role;
                const isLastInGroup = index === filteredMessages.length - 1 || 
                  filteredMessages[index + 1]?.role !== message.role;

                return (
                  <div
                    key={message.id}
                    className={cn(
                      "group relative transition-all duration-200",
                      isFirstInGroup ? "mt-4" : "mt-1",
                      isLastInGroup ? "mb-4" : "mb-1"
                    )}
                  >
                    {isUserMessage(message) && (
                      <UserMessage message={message} />
                    )}
                    {isAssistantMessage(message) && (
                      <AssistantMessage 
                        message={message}
                        isSystem={false}
                        sourceMetadata={sourceMetadata || undefined}
                      />
                    )}
                  </div>
                );
              })}

              {/* Thinking State */}
              {isCollectingSystemMessages && (
                <div className="mt-3">
                  <div className="backdrop-blur-sm bg-[#1E293B]/30 rounded-2xl p-4 border border-white/5">
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#2D3B4E] ring-1 ring-white/10 flex items-center justify-center relative">
                        {teammate?.avatar_url ? (
                          <img 
                            src={teammate.avatar_url} 
                            alt={teammate.name || 'Assistant'} 
                            className="w-full h-full rounded-full object-cover"
                          />
                        ) : (
                          <Bot className="h-4 w-4 text-purple-400" />
                        )}
                        <span className="absolute -bottom-1 -right-1 h-2.5 w-2.5">
                          <span className="absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75 animate-ping"></span>
                          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-purple-500"></span>
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-2">
                          <div className="text-sm font-medium text-white">
                            {teammate?.name || 'Assistant'}
                          </div>
                          <div className="flex items-center gap-1.5 text-xs text-purple-400">
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            <span>thinking</span>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="animate-pulse flex space-x-2">
                            <div className="h-3 w-24 bg-purple-400/10 rounded"></div>
                            <div className="h-3 w-32 bg-purple-400/10 rounded"></div>
                          </div>
                          <div className="animate-pulse flex space-x-2">
                            <div className="h-3 w-20 bg-purple-400/10 rounded"></div>
                            <div className="h-3 w-16 bg-purple-400/10 rounded"></div>
                            <div className="h-3 w-28 bg-purple-400/10 rounded"></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} className="h-4" />
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      {showTaskModal && teammate?.uuid && (
        <Suspense fallback={null}>
          <TaskSchedulingModal
            isOpen={showTaskModal}
            onClose={() => setShowTaskModal(false)}
            teammate={{
              uuid: teammate?.uuid || '',
              name: teammate?.name || 'Unknown',
              team_id: teammate?.team_id || '',
              user_id: teammate?.user_id || '',
              org_id: teammate?.org_id || '',
              email: teammate?.email || '',
              context: teammate?.context || teammate?.uuid || '',
            }}
            onSchedule={async (data) => {
              try {
                const response = await fetch('/api/tasks', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(data),
                });
                
                if (!response.ok) throw new Error('Failed to schedule task');
                const result = await response.json();
                return {
                  task_id: result.task_id,
                  task_uuid: result.task_uuid
                };
              } catch (error) {
                console.error('Failed to schedule task:', error);
                throw error;
              }
            }}
          />
        </Suspense>
      )}
    </div>
  );
}; 