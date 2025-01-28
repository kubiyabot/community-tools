import * as React from 'react';
import { useState, useMemo, useEffect } from 'react';
import { format } from 'date-fns';
import { 
  MessageSquare, 
  Wrench, 
  CheckCircle2, 
  XCircle,
  ChevronRight,
  Users,
  Bot,
  Terminal,
  Clock,
  ArrowLeft,
  Search,
  Filter,
  ZoomIn,
  ZoomOut,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Code,
  AlertCircle,
  Loader2,
  X,
  GitBranch,
  Database,
  Globe,
  Workflow,
  ChevronLeft
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { ScrollArea } from '../ui/scroll-area';
import { 
  Tooltip, 
  TooltipContent, 
  TooltipTrigger,
  TooltipProvider 
} from '../ui/tooltip';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "../ui/collapsible";
import { Card } from '../ui/card';
import { generateAvatarUrl } from '../TeammateSelector';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import type { Components } from 'react-markdown';
import { MarkdownWithContext } from './MarkdownWithContext';

// Add CodeProps interface
interface CodeProps extends React.HTMLAttributes<HTMLElement> {
  inline?: boolean;
  className?: string;
  children: React.ReactNode;
}

interface ActivityEvent {
  id: string;
  org: string;
  email: string;
  version: number;
  category_type: string;
  category_name: string;
  resource_type: string;
  resource_text: string;
  action_type: string;
  action_successful: boolean;
  timestamp: string;
  extra: {
    is_user_message?: boolean;
    session_id?: string;
    tool_name?: string;
    tool_args?: any;
    tool_execution_status?: string;
    teammate_id?: string;
    teammate_name?: string;
  };
  scope: string;
}

export interface SessionDetailsProps {
  sessionId: string;
  events: ActivityEvent[];
  onBack: () => void;
  isLoading?: boolean;
  initialEventId?: string | null;
  onOpenInFullView?: () => void;
  teammate?: string;
}

const formatDate = (date: string) => {
  try {
    return format(new Date(date), 'MMM d, HH:mm:ss.SSS');
  } catch {
    return 'Invalid date';
  }
};

const formatTime = (timestamp: string) => {
  try {
    return format(new Date(timestamp), 'HH:mm:ss.SSS');
  } catch {
    return 'Invalid time';
  }
};

const formatTimeShort = (timestamp: string) => {
  try {
    return format(new Date(timestamp), 'HH:mm:ss');
  } catch {
    return 'Invalid time';
  }
};

const getEventIcon = (event: ActivityEvent) => {
  if (event.category_type === 'agents') {
    return (
      <div className="bg-purple-500/15 p-2 rounded-md">
        <Bot className="h-5 w-5 text-purple-400" />
      </div>
    );
  }
  if (event.resource_type === 'Message') {
    return event.extra.is_user_message ? (
      <div className="bg-blue-500/15 p-2 rounded-md">
        <Users className="h-5 w-5 text-blue-400" />
      </div>
    ) : (
      <div className="bg-indigo-500/15 p-2 rounded-md">
        <Bot className="h-5 w-5 text-indigo-400" />
      </div>
    );
  }
  if (event.resource_type === 'Tool Execution') {
    const toolName = event.extra.tool_name?.toLowerCase() || '';
    let Icon = Wrench;
    let color = "text-amber-400";
    let bgColor = "bg-amber-500/15";

    if (toolName.includes('kubernetes')) {
      Icon = Terminal;
      color = "text-cyan-400";
      bgColor = "bg-cyan-500/15";
    }
    if (toolName.includes('git')) {
      Icon = GitBranch;
      color = "text-green-400";
      bgColor = "bg-green-500/15";
    }
    if (toolName.includes('sql')) {
      Icon = Database;
      color = "text-blue-400";
      bgColor = "bg-blue-500/15";
    }
    if (toolName.includes('http')) {
      Icon = Globe;
      color = "text-purple-400";
      bgColor = "bg-purple-500/15";
    }
    if (toolName.includes('workflow')) {
      Icon = Workflow;
      color = "text-orange-400";
      bgColor = "bg-orange-500/15";
    }
    
    return (
      <div className={cn("p-2 rounded-md", bgColor)}>
        <Icon className={cn("h-5 w-5", color)} />
      </div>
    );
  }
  return (
    <div className="bg-slate-500/15 p-2 rounded-md">
      <Wrench className="h-5 w-5 text-slate-400" />
    </div>
  );
};

const getStatusIcon = (success: boolean) => {
  return success ? 
    <CheckCircle2 className="h-4 w-4 text-green-400" /> : 
    <XCircle className="h-4 w-4 text-red-400" />;
};

const getCategoryBadgeColor = (category: string) => {
  const colors: Record<string, string> = {
    agents: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30 hover:bg-indigo-500/20',
    webhooks: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30 hover:bg-cyan-500/20',
    tools: 'bg-amber-500/15 text-amber-400 border-amber-500/30 hover:bg-amber-500/20',
    default: 'bg-slate-500/15 text-slate-400 border-slate-500/30 hover:bg-slate-500/20'
  };
  return colors[category.toLowerCase()] || colors.default;
};

interface EventInspectorProps {
  event: ActivityEvent;
  onClose: () => void;
}

const LoadingSpinner = () => (
  <div className="flex items-center justify-center h-full">
    <div className="relative">
      <div className="h-24 w-24 rounded-full border-t-2 border-b-2 border-purple-500 animate-spin" />
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
        <Loader2 className="h-12 w-12 text-purple-500 animate-pulse" />
      </div>
    </div>
  </div>
);

const LoadingPulse = () => (
  <div className="space-y-4 animate-pulse">
    <div className="h-8 bg-slate-800/50 rounded-lg w-2/3" />
    <div className="h-8 bg-slate-800/50 rounded-lg w-1/2" />
    <div className="h-8 bg-slate-800/50 rounded-lg w-3/4" />
  </div>
);

const MarkdownContent: React.FC<{ content: string }> = ({ content }) => (
  <ReactMarkdown
    components={{
      code: ({ inline, className, children, ...props }: CodeProps) => {
        const language = className?.replace('language-', '');
        if (inline) {
          return <code className="bg-slate-800/50 px-1.5 py-0.5 rounded text-sm" {...props}>{children}</code>;
        }
        return (
          <SyntaxHighlighter
            language={language || 'text'}
            style={oneDark}
            customStyle={{
              background: 'rgba(15, 23, 42, 0.5)',
              padding: '1rem',
              borderRadius: '0.5rem',
              margin: '0.5rem 0'
            }}
          >
            {String(children).replace(/\n$/, '')}
          </SyntaxHighlighter>
        );
      },
      p: ({ children }) => <div className="mb-4 last:mb-0 text-slate-200">{children}</div>,
      ul: ({ children }) => <ul className="mb-4 list-disc pl-6 text-slate-200">{children}</ul>,
      ol: ({ children }) => <ol className="mb-4 list-decimal pl-6 text-slate-200">{children}</ol>,
      li: ({ children }) => <li className="mb-1">{children}</li>,
      h1: ({ children }) => <h1 className="text-xl font-bold mb-4 text-slate-100">{children}</h1>,
      h2: ({ children }) => <h2 className="text-lg font-bold mb-3 text-slate-100">{children}</h2>,
      h3: ({ children }) => <h3 className="text-base font-bold mb-2 text-slate-100">{children}</h3>,
      blockquote: ({ children }) => (
        <blockquote className="border-l-4 border-slate-700 pl-4 italic mb-4 text-slate-300">
          {children}
        </blockquote>
      ),
    } as Components}
  >
    {content}
  </ReactMarkdown>
);

const ToolExecutionDetails: React.FC<{ event: ActivityEvent }> = ({ event }) => {
  const toolIcon = useMemo(() => {
    const toolName = event.extra.tool_name?.toLowerCase() || '';
    if (toolName.includes('kubernetes')) return Terminal;
    if (toolName.includes('git')) return GitBranch;
    if (toolName.includes('sql')) return Database;
    if (toolName.includes('http')) return Globe;
    if (toolName.includes('workflow')) return Workflow;
    return Wrench;
  }, [event.extra.tool_name]);

  return (
    <Card className="bg-slate-800 border-slate-700">
      <div className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-500/10">
              {React.createElement(toolIcon, { className: "h-5 w-5 text-amber-400" })}
            </div>
            <div>
              <span className="text-sm font-medium text-slate-200">{event.extra.tool_name}</span>
              <div className="text-xs text-slate-400">Tool Execution</div>
            </div>
          </div>
          <Badge variant="outline" className={cn(
            event.action_successful 
              ? "bg-green-500/10 text-green-400 border-green-500/30"
              : "bg-red-500/10 text-red-400 border-red-500/30"
          )}>
            {event.action_successful ? 'Success' : 'Failed'}
          </Badge>
        </div>

        {event.extra.tool_args && (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Code className="h-4 w-4 text-slate-400" />
              <span className="text-sm font-medium text-slate-300">Arguments</span>
            </div>
            <SyntaxHighlighter
              language="json"
              style={oneDark}
              customStyle={{
                background: 'rgba(15, 23, 42, 0.5)',
                padding: '1rem',
                borderRadius: '0.5rem'
              }}
            >
              {JSON.stringify(event.extra.tool_args, null, 2)}
            </SyntaxHighlighter>
          </div>
        )}

        {event.resource_text && (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Terminal className="h-4 w-4 text-slate-400" />
              <span className="text-sm font-medium text-slate-300">Output</span>
            </div>
            <div className="bg-slate-900/50 rounded-lg overflow-hidden">
              <MarkdownContent content={event.resource_text} />
            </div>
          </div>
        )}

        {event.extra.tool_execution_status && (
          <div className="flex items-center gap-2 text-sm">
            <AlertCircle className="h-4 w-4 text-slate-400" />
            <span className="text-slate-300">{event.extra.tool_execution_status}</span>
          </div>
        )}
      </div>
    </Card>
  );
};

// Helper functions
const isUserMessage = (event: ActivityEvent): boolean => {
  return event.resource_type === 'Message' && 
    (event.extra?.is_user_message === true || event.category_type !== 'agents');
};

const getUniqueUsers = (events: ActivityEvent[]) => {
  const users = new Map<string, { email: string; events: number; messages: number }>();
  
  events.forEach(event => {
    if (event.email) {
      if (!users.has(event.email)) {
        users.set(event.email, { email: event.email, events: 0, messages: 0 });
      }
      const user = users.get(event.email)!;
      user.events++;
      if (isUserMessage(event)) {
        user.messages++;
      }
    }
  });
  
  return Array.from(users.values());
};

const shouldSkipMessage = (event: ActivityEvent): boolean => {
  if (event.resource_type !== 'Message') return false;
  
  // Skip messages that start with "Tool:" and contain "Arguments:"
  if (event.resource_text?.startsWith('Tool:') && event.resource_text?.includes('Arguments:')) {
    return true;
  }
  
  return false;
};

// Component definitions
const EventInspector: React.FC<EventInspectorProps> = ({ event, onClose }) => {
  const shouldShowContent = !shouldSkipMessage(event);
  
  return (
    <div className="flex flex-col h-full bg-slate-900/95 border-l border-slate-800">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/95">
        <div className="flex items-center gap-3">
          <img
            src={generateAvatarUrl({ uuid: event.email, name: event.email })}
            alt={event.email}
            className="w-8 h-8 rounded-lg"
          />
          <div>
            <h3 className="font-semibold text-slate-50">Event Details</h3>
            <p className="text-sm text-slate-400">{event.email}</p>
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {/* Basic Info Card */}
          <Card className="bg-slate-800/90 border-slate-700">
            <div className="p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Type</span>
                <Badge variant="outline" className={cn(
                  getCategoryBadgeColor(event.category_type)
                )}>
                  {event.resource_type}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Category</span>
                <div className="flex items-center gap-2">
                  {event.category_type === 'agents' ? (
                    <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/30">
                      {event.category_name}
                    </Badge>
                  ) : (
                    <Badge variant="outline" className={cn(getCategoryBadgeColor(event.category_type))}>
                      {event.category_name || event.category_type}
                    </Badge>
                  )}
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Action</span>
                <span className="text-sm text-slate-200">{event.action_type}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Time</span>
                <div className="flex items-center gap-2 text-sm text-slate-200">
                  <Clock className="h-3 w-3" />
                  {formatDate(event.timestamp)}
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Status</span>
                <Badge variant="outline" className={cn(
                  event.action_successful 
                    ? "bg-green-500/10 text-green-400 border-green-500/30"
                    : "bg-red-500/10 text-red-400 border-red-500/30"
                )}>
                  {event.action_successful ? 'Success' : 'Failed'}
                </Badge>
              </div>
              {event.scope && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Scope</span>
                  <span className="text-sm text-slate-200">{event.scope}</span>
                </div>
              )}
              {event.version && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Version</span>
                  <span className="text-sm text-slate-200">{event.version}</span>
                </div>
              )}
            </div>
          </Card>

          {/* Tool Execution Details */}
          {event.resource_type === 'Tool Execution' && (
            <Card className="bg-slate-800/90 border-slate-700">
              <div className="p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-amber-500/10">
                      <Terminal className="h-5 w-5 text-amber-400" />
                    </div>
                    <div>
                      <span className="text-sm font-medium text-slate-200">
                        {event.extra.tool_name || 'Tool Execution'}
                      </span>
                      <div className="text-xs text-slate-400">{event.category_name}</div>
                    </div>
                  </div>
                </div>

                {event.extra.tool_args && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Code className="h-4 w-4 text-slate-400" />
                      <span className="text-sm font-medium text-slate-300">Arguments</span>
                    </div>
                    <div className="bg-slate-900/50 rounded-lg p-3 text-sm font-mono text-slate-300 overflow-x-auto">
                      {typeof event.extra.tool_args === 'string' 
                        ? event.extra.tool_args
                        : JSON.stringify(event.extra.tool_args, null, 2)
                      }
                    </div>
                  </div>
                )}

                {event.resource_text && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Terminal className="h-4 w-4 text-slate-400" />
                      <span className="text-sm font-medium text-slate-300">Output</span>
                    </div>
                    <div className="bg-slate-900/50 rounded-lg overflow-hidden">
                      <MarkdownContent content={event.resource_text} />
                    </div>
                  </div>
                )}

                {event.extra.tool_execution_status && (
                  <div className="flex items-center gap-2 text-sm">
                    <AlertCircle className="h-4 w-4 text-slate-400" />
                    <span className="text-slate-300">{event.extra.tool_execution_status}</span>
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* Message Content - Only show if not a skipped message */}
          {event.resource_text && event.resource_type === 'Message' && shouldShowContent && (
            <Card className="bg-slate-800/90 border-slate-700">
              <div className="p-4 space-y-2">
                <h4 className="text-sm font-medium text-slate-400">Content</h4>
                <div className="bg-slate-900/50 rounded-lg overflow-hidden p-3">
                  <MarkdownContent content={event.resource_text} />
                </div>
              </div>
            </Card>
          )}
        </div>
      </ScrollArea>
    </div>
  );
};

interface SessionInfo {
  startTime: number;
  endTime: number;
  duration: number;
  totalEvents: number;
  successfulEvents: number;
  user: string;
  category: string;
  success: boolean;
  users: number;
  teammates: number;
}

// Update the getTeammatesFromEvents function
const getTeammatesFromEvents = (events: ActivityEvent[]) => {
  const teammates = new Map<string, { id: string; name: string; events: number }>();
  
  events.forEach(event => {
    if (event.category_type === 'agents') {
      const id = event.extra?.teammate_id || event.category_name;
      const name = event.category_name;
      if (!teammates.has(id)) {
        teammates.set(id, { id, name, events: 0 });
      }
      teammates.get(id)!.events++;
    }
  });
  
  return Array.from(teammates.values());
};

// Update the useSessionInfo hook to count teammates correctly
const useSessionInfo = (events: ActivityEvent[]): SessionInfo => {
  return useMemo(() => {
    const sortedEvents = [...events].sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
    
    const startTime = new Date(sortedEvents[0].timestamp).getTime();
    const endTime = new Date(sortedEvents[sortedEvents.length - 1].timestamp).getTime();
    const duration = endTime - startTime;
    const totalEvents = events.length;
    const successfulEvents = events.filter(e => e.action_successful).length;

    // Count unique users and teammates
    const uniqueUsers = new Set<string>();
    const uniqueTeammates = new Set<string>();
    
    events.forEach(event => {
      uniqueUsers.add(event.email);
      if (event.category_type === 'agents') {
        uniqueTeammates.add(event.category_name);
      }
    });
    
    return {
      startTime,
      endTime,
      duration,
      totalEvents,
      successfulEvents,
      user: sortedEvents[0].email,
      category: sortedEvents[0].category_type,
      success: sortedEvents.some(e => e.action_successful),
      users: uniqueUsers.size,
      teammates: uniqueTeammates.size
    };
  }, [events]);
};

// Add new type for view mode
type ViewMode = 'timeline' | 'conversation';

// Add timeline positioning function
const useTimelinePositions = (events: ActivityEvent[], startTime: number, duration: number) => {
  return useMemo(() => {
    const PADDING = 8; // Percentage padding from edges
    const MIN_GAP = 48; // Minimum gap in pixels between events
    const AVAILABLE_WIDTH = 100 - (2 * PADDING); // Available width percentage

    const positions = events.map(event => {
      const time = new Date(event.timestamp).getTime();
      // Scale position to available width and add padding
      const rawPosition = PADDING + ((time - startTime) / duration) * AVAILABLE_WIDTH;
      return { event, position: rawPosition };
    }).sort((a, b) => a.position - b.position);

    // Adjust positions to ensure minimum gap
    const adjustedPositions = new Map<ActivityEvent, number>();
    let lastPosition = -MIN_GAP;

    positions.forEach(({ event, position }) => {
      const pixelPosition = (position / 100) * window.innerWidth;
      const minPosition = (lastPosition + MIN_GAP) / window.innerWidth * 100;
      
      if (position < minPosition) {
        // Ensure we don't go below padding
        const newPosition = Math.max(PADDING, minPosition);
        adjustedPositions.set(event, newPosition);
        lastPosition = (newPosition / 100) * window.innerWidth;
      } else {
        // Ensure we don't exceed (100 - padding)
        const newPosition = Math.min(100 - PADDING, position);
        adjustedPositions.set(event, newPosition);
        lastPosition = (newPosition / 100) * window.innerWidth;
      }
    });

    return adjustedPositions;
  }, [events, startTime, duration]);
};

// Add isTeammateMessage helper
const isTeammateMessage = (event: ActivityEvent): boolean => {
  return event.category_type === 'agents' && !!event.extra.teammate_name;
};

// Update TimelineEvent component
const TimelineEvent: React.FC<{
  event: ActivityEvent;
  position: number;
  isSelected: boolean;
  onClick: () => void;
  showLabel?: boolean;
}> = ({ event, position, isSelected, onClick, showLabel = true }) => (
  <Tooltip>
    <TooltipTrigger asChild>
      <button
        className={cn(
          "absolute top-1/2 group",
          "flex flex-col items-center",
          "focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:ring-offset-2 focus:ring-offset-slate-900",
          position < 0 || position > 100 ? "opacity-0 pointer-events-none" : "opacity-100"
        )}
        style={{ 
          left: `${position}%`,
          transform: 'translate(-50%, -50%)',
          zIndex: isSelected ? 30 : 'auto'
        }}
        onClick={onClick}
      >
        <div className="relative">
          <div className={cn(
            "w-12 h-12 rounded-xl flex items-center justify-center transition-all",
            "hover:scale-110 hover:shadow-lg group-hover:z-10",
            isSelected 
              ? "bg-indigo-500/20 ring-2 ring-indigo-400 ring-offset-2 ring-offset-slate-900 scale-110 shadow-lg shadow-indigo-500/20" 
              : event.action_successful 
                ? "bg-slate-800/90 shadow-sm shadow-green-500/10 hover:shadow-green-500/20" 
                : "bg-slate-800/90 shadow-sm shadow-red-500/10 hover:shadow-red-500/20"
          )}>
            {getEventIcon(event)}
          </div>
          
          {/* Action Indicator */}
          <div className={cn(
            "absolute -bottom-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center",
            "bg-slate-800 ring-2 ring-slate-900",
            event.action_successful ? "text-green-400" : "text-red-400"
          )}>
            {isTeammateMessage(event) ? (
              <Bot className="h-3 w-3 text-purple-400" />
            ) : event.resource_type === 'Message' ? (
              event.extra.is_user_message ? (
                <Users className="h-3 w-3" />
              ) : (
                <Bot className="h-3 w-3" />
              )
            ) : event.resource_type === 'Tool Execution' ? (
              <Terminal className="h-3 w-3" />
            ) : (
              <Wrench className="h-3 w-3" />
            )}
          </div>
        </div>

        {showLabel && (
          <div className={cn(
            "absolute top-full mt-2 transition-all z-10",
            isSelected ? "opacity-100" : "opacity-0 group-hover:opacity-100",
            "text-[10px] font-medium text-slate-400 whitespace-nowrap",
            "bg-slate-800 px-2 py-1 rounded-md shadow-lg",
            position < 20 ? "left-0" : 
            position > 80 ? "right-0" : 
            "transform -translate-x-1/2"
          )}>
            <div className="flex items-center gap-1.5">
              <Clock className="h-3 w-3" />
              <span>{formatTimeShort(event.timestamp)}</span>
            </div>
          </div>
        )}
      </button>
    </TooltipTrigger>
    <TooltipContent 
      side="top" 
      align="center"
      className="bg-slate-800/95 border-slate-700 shadow-xl p-4 max-w-md animate-in fade-in-0 zoom-in-95"
    >
      <div className="space-y-4">
        {/* Header with user/teammate info */}
        <div className="flex items-center gap-3">
          {isTeammateMessage(event) ? (
            <>
              <div className="relative">
                <img
                  src={generateAvatarUrl({ 
                    uuid: event.extra.teammate_id || event.category_name || 'teammate',
                    name: event.extra.teammate_name || 'AI Teammate'
                  })}
                  alt={event.extra.teammate_name || 'AI Teammate'}
                  className="w-10 h-10 rounded-lg"
                />
                <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-slate-800 ring-2 ring-slate-900 flex items-center justify-center">
                  <Bot className="h-2.5 w-2.5 text-purple-400" />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-200">
                    {event.extra.teammate_name || event.category_name}
                  </span>
                  <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/30">
                    AI Teammate
                  </Badge>
                </div>
                <span className="text-xs text-slate-400">{event.category_name}</span>
              </div>
            </>
          ) : (
            <>
              <img
                src={generateAvatarUrl({ uuid: event.email, name: event.email })}
                alt={event.email}
                className="w-10 h-10 rounded-lg"
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-200">
                    {formatUserName(event.email)}
                  </span>
                  {event.extra?.is_user_message && (
                    <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/30">
                      User
                    </Badge>
                  )}
                </div>
                <span className="text-xs text-slate-400">{event.email}</span>
              </div>
            </>
          )}
          <Badge variant="outline" className={cn(
            event.action_successful 
              ? "bg-green-500/10 text-green-400 border-green-500/30"
              : "bg-red-500/10 text-red-400 border-red-500/30"
          )}>
            {event.action_successful ? 'Success' : 'Failed'}
          </Badge>
        </div>

        {/* Event type and category */}
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            {getEventIcon(event)}
            <div>
              <span className="text-sm font-medium text-slate-200">
                {event.resource_type}
              </span>
              <div className="flex items-center gap-1 mt-0.5">
                <span className="text-xs text-slate-400">{event.action_type}</span>
              </div>
            </div>
          </div>
          <Badge variant="outline" className={cn(getCategoryBadgeColor(event.category_type))}>
            {event.category_name}
          </Badge>
        </div>

        {/* Content preview */}
        {event.resource_text && (
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <MessageSquare className="h-3 w-3" />
              Content Preview
            </div>
            <div className="bg-slate-900/50 rounded-lg p-2">
              <MarkdownWithContext 
                content={event.resource_text} 
                className="line-clamp-3 text-sm text-slate-300"
              />
            </div>
          </div>
        )}

        {/* Timestamp */}
        <div className="flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {formatDate(event.timestamp)}
          </div>
          {isTeammateMessage(event) && (
            <div className="flex items-center gap-1">
              <Bot className="h-3 w-3 text-purple-400" />
              <span className="text-purple-400">{event.extra.teammate_name}</span>
            </div>
          )}
        </div>
      </div>
    </TooltipContent>
  </Tooltip>
);

// Helper function to format user name
const formatUserName = (email: string) => {
  const [namepart] = email.split('@');
  const parts = namepart.split('.');
  return parts.map(part => 
    part.charAt(0).toUpperCase() + part.slice(1)
  ).join(' ');
};

// Unified session info panel
const SessionInfoPanel: React.FC<{ sessionInfo: SessionInfo; events: ActivityEvent[]; sessionId: string }> = ({ 
  sessionInfo, 
  events,
  sessionId 
}) => {
  const teammates = getTeammatesFromEvents(events);
  const users = getUniqueUsers(events);

  return (
    <div className="space-y-4">
      {/* Top Row - Core Info */}
      <div className="grid grid-cols-[2fr,1fr] gap-4">
        {/* Session ID and Status */}
        <div className="bg-slate-800/50 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 min-w-0">
              <div className="p-2 rounded-lg bg-slate-700/50">
                <Code className="h-4 w-4 text-slate-300" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-slate-200 font-mono truncate">{sessionId}</p>
                <div className="flex items-center gap-2 mt-1">
                  <MessageSquare className="h-3 w-3 text-blue-400" />
                  <span className="text-xs text-slate-400">Chat Gateway</span>
                </div>
              </div>
            </div>
            <Badge variant="outline" className={cn(
              "px-3 py-1 ml-4",
              sessionInfo.success 
                ? "bg-green-500/10 text-green-400 border-green-500/30"
                : "bg-red-500/10 text-red-400 border-red-500/30"
            )}>
              {sessionInfo.success ? 'Completed' : 'Failed'}
            </Badge>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-2 bg-slate-800/50 rounded-lg p-3">
          <div>
            <span className="text-xs text-slate-400">Duration</span>
            <p className="text-sm font-medium text-slate-200">
              {sessionInfo.duration < 60000 
                ? `${Math.round(sessionInfo.duration / 1000)}s`
                : `${Math.round(sessionInfo.duration / 60000)}m`}
            </p>
          </div>
          <div>
            <span className="text-xs text-slate-400">Events</span>
            <p className="text-sm font-medium text-slate-200">{sessionInfo.totalEvents}</p>
          </div>
          <div>
            <span className="text-xs text-slate-400">Success</span>
            <p className="text-sm font-medium text-slate-200">{Math.round((sessionInfo.successfulEvents / sessionInfo.totalEvents) * 100)}%</p>
          </div>
        </div>
      </div>

      {/* Bottom Row - Participants */}
      <div className="grid grid-cols-[1fr,2fr] gap-4">
        {/* Users */}
        <div className="bg-slate-800/50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-blue-400" />
              <span className="text-sm font-medium text-slate-200">Conversation Participants</span>
            </div>
            <Badge variant="outline" className="bg-slate-700/50 text-slate-400 text-xs">
              User Messages Tracing Disabled
            </Badge>
          </div>
          <div className="space-y-2">
            {users.map((user) => (
              <div
                key={user.email}
                className="flex items-center gap-3 p-3 rounded-lg bg-slate-800 border border-slate-700/50"
              >
                <div className="relative shrink-0">
                  <img
                    src={generateAvatarUrl({ uuid: user.email, name: user.email })}
                    alt={formatUserName(user.email)}
                    className="w-8 h-8 rounded-lg"
                  />
                  <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-slate-800 ring-2 ring-slate-900 flex items-center justify-center">
                    <Users className="h-2.5 w-2.5 text-blue-400" />
                  </div>
                </div>
                <div className="flex flex-col min-w-0 flex-1">
                  <span className="text-sm font-medium text-slate-200">
                    {formatUserName(user.email)}
                  </span>
                  <div className="flex flex-col gap-1">
                    <span className="text-xs text-slate-400">{user.email}</span>
                    <div className="flex items-center gap-1.5">
                      <MessageSquare className="h-3 w-3 text-blue-400" />
                      <span className="text-xs text-slate-400">Conversation Initiator</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Teammates */}
        <div className="bg-slate-800/50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Bot className="h-4 w-4 text-purple-400" />
              <span className="text-sm font-medium text-slate-200">Active Teammates</span>
            </div>
            <Badge variant="outline" className="bg-purple-500/10 text-purple-400 text-xs">
              Handling Actions
            </Badge>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {teammates.map((teammate) => (
              <div
                key={teammate.id}
                className="flex items-center gap-3 p-2 rounded-lg bg-slate-800 border border-slate-700/50 hover:bg-slate-700/50 transition-colors"
              >
                <div className="relative shrink-0">
                  <img
                    src={generateAvatarUrl({ uuid: teammate.id, name: teammate.name })}
                    alt={teammate.name}
                    className="w-8 h-8 rounded-lg"
                  />
                  <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-slate-800 ring-2 ring-slate-900 flex items-center justify-center">
                    <Bot className="h-2.5 w-2.5 text-purple-400" />
                  </div>
                </div>
                <div className="flex flex-col min-w-0 flex-1">
                  <span className="text-sm font-medium text-slate-200 truncate">{teammate.name}</span>
                  <div className="flex items-center gap-1.5">
                    <Terminal className="h-3 w-3 text-purple-400" />
                    <span className="text-xs text-slate-400">{teammate.events} tool executions</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export const SessionDetails: React.FC<SessionDetailsProps> = ({ 
  sessionId, 
  events,
  onBack,
  isLoading = false,
  initialEventId,
  onOpenInFullView,
  teammate
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [viewMode, setViewMode] = useState<ViewMode>('timeline');
  const [selectedEvent, setSelectedEvent] = useState<ActivityEvent | null>(null);
  const sessionInfo = useSessionInfo(events);

  // Set initial selected event based on initialEventId
  useEffect(() => {
    if (initialEventId) {
      const event = events.find(e => e.id === initialEventId || e.timestamp === initialEventId);
      if (event) {
        setSelectedEvent(event);
        setViewMode('timeline');  // Ensure we're in timeline view to show the event details
      }
    }
  }, [initialEventId, events]);

  // Extract first name and last name if available
  const [firstName, lastName] = sessionInfo.user.split('@')[0].split('.');
  const displayName = firstName && lastName 
    ? `${firstName.charAt(0).toUpperCase() + firstName.slice(1)} ${lastName.charAt(0).toUpperCase() + lastName.slice(1)}`
    : sessionInfo.user;

  // Filter events based on search and filters
  const filteredEvents = useMemo(() => {
    return events.filter(event => {
      const matchesSearch = searchTerm === '' || 
        event.resource_text?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        event.category_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        event.resource_type?.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesCategory = categoryFilter === 'all' || 
        event.category_type?.toLowerCase() === categoryFilter.toLowerCase();
      
      const matchesStatus = statusFilter === 'all' || 
        (statusFilter === 'success' && event.action_successful) ||
        (statusFilter === 'failed' && !event.action_successful);
      
      return matchesSearch && matchesCategory && matchesStatus;
    });
  }, [events, searchTerm, categoryFilter, statusFilter]);

  // Get conversation messages
  const conversationMessages = useMemo(() => {
    return events
      .filter(event => 
        (event.resource_type === 'Message' && !shouldSkipMessage(event)) || 
        (event.resource_type === 'Tool Execution' && event.resource_text)
      )
      .map(event => ({
        ...event,
        isUser: event.extra.is_user_message,
        isTeammate: isTeammateMessage(event),
        isTool: event.resource_type === 'Tool Execution',
        content: event.resource_text
      }));
  }, [events]);

  // Get adjusted positions for timeline events
  const timelinePositions = useTimelinePositions(
    filteredEvents,
    sessionInfo.startTime,
    sessionInfo.duration
  );

  const uniqueTeammates = useMemo(() => {
    const teammates = new Map<string, { id: string; name: string; events: number }>();
    
    events.forEach(event => {
      if (event.extra?.teammate_id && event.extra?.teammate_name) {
        if (!teammates.has(event.extra.teammate_id)) {
          teammates.set(event.extra.teammate_id, {
            id: event.extra.teammate_id,
            name: event.extra.teammate_name,
            events: 0
          });
        }
        teammates.get(event.extra.teammate_id)!.events++;
      }
    });

    return Array.from(teammates.values());
  }, [events]);

  if (isLoading) {
    return (
      <div className="flex flex-col h-screen max-h-screen bg-slate-900">
        <div className="flex items-center justify-between p-6 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <Button 
              variant="ghost" 
              size="sm" 
              disabled
              className="hover:bg-slate-800"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <LoadingPulse />
          </div>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <LoadingSpinner />
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="flex flex-col h-full max-h-full bg-slate-900 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={onBack} className="shrink-0">
              <ChevronLeft className="h-4 w-4 mr-1" />
              Back
            </Button>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold text-slate-50">Session Details</h2>
              {teammate && (
                <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/30">
                  {teammate}
                </Badge>
              )}
            </div>
          </div>
          {onOpenInFullView && (
            <Button
              variant="outline"
              size="sm"
              className="bg-slate-800 border-slate-700 hover:bg-slate-700"
              onClick={onOpenInFullView}
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Open in Full View
            </Button>
          )}
        </div>

        {/* Session Info */}
        <div className="py-3 px-6 border-b border-slate-800">
          <SessionInfoPanel 
            sessionInfo={sessionInfo} 
            events={events}
            sessionId={sessionId}
          />
        </div>

        {/* Main Content */}
        <div className="flex-1 flex min-h-0 overflow-hidden">
          <div className={cn(
            "flex-1 flex flex-col min-h-0",
            selectedEvent ? "w-2/3" : "w-full"
          )}>
            {viewMode === 'timeline' ? (
              <>
                {/* Timeline View */}
                <div className="relative h-48 border-b border-slate-800 overflow-hidden">
                  <div className="absolute inset-x-12 top-6 flex justify-between">
                    <div className="flex flex-col items-start">
                      <span className="text-xs font-medium text-slate-300">Start</span>
                      <span className="text-xs text-slate-500">{formatTimeShort(events[0].timestamp)}</span>
                    </div>
                    <div className="flex flex-col items-end">
                      <span className="text-xs font-medium text-slate-300">End</span>
                      <span className="text-xs text-slate-500">{formatTimeShort(events[events.length - 1].timestamp)}</span>
                    </div>
                  </div>
                  
                  <div className="absolute inset-x-12 top-1/2 h-0.5 bg-gradient-to-r from-slate-800 via-indigo-500/10 to-slate-800" />
                  
                  <div className="absolute inset-0 px-12">
                    {filteredEvents.map((event, index) => {
                      const position = timelinePositions.get(event) || 0;
                      // Only render if the event is within the visible area (with some padding)
                      if (position >= -10 && position <= 110) {
                        return (
                          <TimelineEvent
                            key={index}
                            event={event}
                            position={position}
                            isSelected={event === selectedEvent}
                            onClick={() => setSelectedEvent(event)}
                            showLabel={filteredEvents.length <= 10}
                          />
                        );
                      }
                      return null;
                    })}
                  </div>
                </div>

                {/* Event List */}
                <ScrollArea className="flex-1">
                  <div className="py-2 px-4 space-y-2">
                    {filteredEvents.map((event, index) => (
                      <div
                        key={index}
                        className={cn(
                          "group flex items-start gap-4 p-3 rounded-xl transition-all cursor-pointer",
                          "hover:bg-slate-800/50 hover:shadow-lg",
                          event === selectedEvent 
                            ? "bg-slate-800 ring-2 ring-indigo-500/20 shadow-lg shadow-indigo-500/10" 
                            : "bg-slate-800/20"
                        )}
                        onClick={() => setSelectedEvent(event)}
                      >
                        <div className="flex items-center gap-2 min-w-[120px] text-xs text-slate-400">
                          <Clock className="h-3 w-3" />
                          {formatTime(event.timestamp)}
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            {getEventIcon(event)}
                            <span className="font-medium text-slate-200">
                              {event.resource_type}
                            </span>
                            <Badge variant="outline" className={cn(
                              getCategoryBadgeColor(event.category_type)
                            )}>
                              {event.category_type}
                            </Badge>
                          </div>
                          
                          {event.resource_text && (
                            <p className="text-sm text-slate-400 line-clamp-2 group-hover:text-slate-300">
                              {event.resource_text}
                            </p>
                          )}
                          
                          {event.extra && (
                            <div className="flex flex-wrap gap-2 mt-2">
                              {event.extra.tool_name && (
                                <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/30">
                                  <Terminal className="h-3 w-3 mr-1" />
                                  {event.extra.tool_name}
                                </Badge>
                              )}
                            </div>
                          )}
                        </div>
                        
                        <ChevronRight className="h-4 w-4 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </>
            ) : (
              // Conversation View
              <ScrollArea className="flex-1">
                <div className="py-4 px-6 space-y-6">
                  {conversationMessages.map((message, index) => {
                    const avatarInfo = message.isTeammate ? {
                      uuid: message.extra.teammate_id || message.category_name || 'teammate',
                      name: message.extra.teammate_name || 'AI Teammate'
                    } : {
                      uuid: message.isUser ? message.email : 'assistant',
                      name: message.isUser ? message.email : 'Assistant'
                    };

                    return (
                      <div
                        key={index}
                        className={cn(
                          "flex gap-4",
                          message.isUser ? "flex-row" : "flex-row-reverse"
                        )}
                      >
                        <div className="flex-shrink-0">
                          {message.isTeammate ? (
                            <div className="relative">
                              <img
                                src={generateAvatarUrl(avatarInfo)}
                                alt={avatarInfo.name}
                                className="w-8 h-8 rounded-lg"
                              />
                              <div className="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full bg-slate-800 ring-2 ring-slate-900 flex items-center justify-center">
                                <Bot className="h-2 w-2 text-purple-400" />
                              </div>
                            </div>
                          ) : (
                            <img
                              src={generateAvatarUrl(avatarInfo)}
                              alt={avatarInfo.name}
                              className="w-8 h-8 rounded-lg"
                            />
                          )}
                        </div>
                        <div className={cn(
                          "flex-1 max-w-[80%] p-4 rounded-lg",
                          message.isUser 
                            ? "bg-blue-500/10 text-blue-50" 
                            : message.isTeammate
                              ? "bg-purple-500/10 text-purple-50"
                              : message.isTool
                                ? "bg-amber-500/10 text-amber-50"
                                : "bg-indigo-500/10 text-indigo-50"
                        )}>
                          {message.isTeammate && (
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-xs font-medium text-purple-400">
                                {message.extra.teammate_name || message.category_name}
                              </span>
                              <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/30 text-[10px]">
                                AI Teammate
                              </Badge>
                            </div>
                          )}
                          {message.isTool && (
                            <div className="flex items-center gap-2 mb-2 text-xs font-medium text-amber-400">
                              <Terminal className="h-3 w-3" />
                              {message.extra.tool_name}
                            </div>
                          )}
                          <MarkdownWithContext content={message.content} />
                          <div className="mt-2 flex items-center gap-2 text-xs">
                            <Clock className="h-3 w-3" />
                            <span className="text-slate-400">{formatTime(message.timestamp)}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            )}
          </div>

          {/* Event Inspector */}
          {selectedEvent && viewMode === 'timeline' && (
            <div className="w-1/3 border-l border-slate-800 flex flex-col min-h-0">
              <EventInspector 
                event={selectedEvent}
                onClose={() => setSelectedEvent(null)}
              />
            </div>
          )}
        </div>
      </div>
    </TooltipProvider>
  );
}; 