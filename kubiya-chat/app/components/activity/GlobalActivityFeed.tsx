import React, { useState, useMemo } from 'react';
import { format, subHours, subDays } from 'date-fns';
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
  Webhook,
  Settings,
  Shield,
  Database,
  AlertCircle,
  Info,
  Link,
  Loader2,
  ExternalLink
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { ScrollArea } from '../ui/scroll-area';
import { 
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../ui/tooltip';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { MarkdownWithContext } from './MarkdownWithContext';
import { generateAvatarUrl } from '../../lib/utils/avatar';

type TimeRange = '1h' | '24h' | '7d' | '30d' | 'all';

interface ActivityEvent {
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

interface GlobalActivityFeedProps {
  events: ActivityEvent[];
  timeRange: TimeRange;
  isLoading?: boolean;
  onViewSession?: (sessionId: string) => void;
}

interface SessionGroup {
  sessionId: string;
  events: ActivityEvent[];
  startTime: string;
  endTime: string;
  participants: {
    users: Array<{ email: string; events: number }>;
    teammates: Array<{ id: string; name: string; events: number }>;
  };
  success: boolean;
}

const formatDate = (date: string) => {
  try {
    return format(new Date(date), 'MMM d, HH:mm:ss');
  } catch {
    return 'Invalid date';
  }
};

const getEventNarrative = (event: ActivityEvent, isFirst: boolean = false): string => {
  // Handle user messages
  if (event.extra.is_user_message) {
    if (isFirst) {
      return 'started a conversation';
    }
    return 'sent a message';
  }
  
  // Handle teammate/agent actions
  if (isTeammateEvent(event)) {
    if (event.extra.tool_name) {
      return `executed ${event.extra.tool_name}`;
    }
    return 'responded';
  }
  
  // Handle system actions
  switch (event.resource_type) {
    case 'Webhook':
      if (event.extra.teammate_name) {
        return `assigned to ${event.extra.teammate_name}`;
      }
      if (event.extra.tool_name) {
        return `triggered webhook ${event.extra.tool_name}`;
      }
      return 'triggered webhook';
      
    case 'Tool Execution':
      if (event.extra.tool_name) {
        return `executed ${event.extra.tool_name}`;
      }
      return 'executed tool';
      
    case 'Configuration':
      return 'updated configuration';
      
    case 'Security':
      return 'performed security action';
      
    case 'Message':
      if (event.extra.tool_args) {
        return 'performed automated action';
      }
      return 'processed message';
      
    default:
      if (event.action_type) {
        return event.action_type.toLowerCase();
      }
      return 'performed action';
  }
};

const getEventIcon = (event: ActivityEvent) => {
  if (event.extra.tool_name) {
    return <Wrench className="h-4 w-4 text-amber-400" />;
  }

  const iconMap: Record<string, React.ReactNode> = {
    'Message': event.extra.is_user_message ? 
      <MessageSquare className="h-4 w-4 text-blue-400" /> : 
      <Bot className="h-4 w-4 text-purple-400" />,
    'Tool Execution': <Terminal className="h-4 w-4 text-amber-400" />,
    'Webhook': <Webhook className="h-4 w-4 text-green-400" />,
    'Configuration': <Settings className="h-4 w-4 text-yellow-400" />,
    'Security': <Shield className="h-4 w-4 text-red-400" />,
    'Data': <Database className="h-4 w-4 text-cyan-400" />,
    'System': <Wrench className="h-4 w-4 text-slate-400" />
  };

  return iconMap[event.resource_type] || <Info className="h-4 w-4 text-slate-400" />;
};

const getStatusIcon = (success: boolean) => {
  return success ? 
    <CheckCircle2 className="h-4 w-4 text-green-400" /> : 
    <XCircle className="h-4 w-4 text-red-400" />;
};

const getCategoryBadgeColor = (category: string) => {
  const colors: Record<string, string> = {
    'agents': 'bg-purple-500/10 text-purple-400 border-purple-500/30',
    'webhooks': 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    'tools': 'bg-orange-500/10 text-orange-400 border-orange-500/30',
    'security': 'bg-red-500/10 text-red-400 border-red-500/30',
    'system': 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
    'default': 'bg-slate-500/10 text-slate-400 border-slate-500/30'
  };
  return colors[category.toLowerCase()] || colors.default;
};

const getUserInitials = (email: string) => {
  const parts = email.split('@')[0].split(/[._-]/);
  return parts.map(part => part[0].toUpperCase()).join('').slice(0, 2);
};

const getTimeRangeDate = (timeRange: TimeRange) => {
  const now = new Date();
  switch (timeRange) {
    case '1h':
      return subHours(now, 1);
    case '24h':
      return subHours(now, 24);
    case '7d':
      return subDays(now, 7);
    case '30d':
      return subDays(now, 30);
    default:
      return new Date(0); // beginning of time for 'all'
  }
};

const isTeammateEvent = (event: ActivityEvent): boolean => {
  return event.category_type === 'agents' && !!event.extra.teammate_name;
};

// Add helper function for user avatar URL
const getUserAvatarUrl = (email: string) => {
  const [namepart] = email.split('@');
  const parts = namepart.split(/[._-]/);
  const name = parts.map(part => part.charAt(0).toUpperCase() + part.slice(1)).join('+');
  return `https://ui-avatars.com/api/?name=${name}&background=1e293b&color=94a3b8&bold=true`;
};

const getEventAvatar = (event: ActivityEvent) => {
  if (isTeammateEvent(event)) {
    return (
      <div className="relative">
        <Avatar className="w-6 h-6">
          <AvatarImage src={generateAvatarUrl({ uuid: event.extra.teammate_id || event.category_name, name: event.extra.teammate_name || 'AI Teammate' })} />
          <AvatarFallback>{event.extra.teammate_name?.slice(0, 2).toUpperCase()}</AvatarFallback>
        </Avatar>
        <div className="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full bg-slate-800 ring-2 ring-slate-900 flex items-center justify-center">
          <Bot className="h-2 w-2 text-purple-400" />
        </div>
      </div>
    );
  }

  return (
    <Avatar className="w-6 h-6">
      <AvatarImage src={getUserAvatarUrl(event.email)} />
      <AvatarFallback>{getUserInitials(event.email)}</AvatarFallback>
    </Avatar>
  );
};

const getEventSender = (event: ActivityEvent): { name: string; description: string } => {
  if (isTeammateEvent(event)) {
    return {
      name: event.extra.teammate_name || event.category_name,
      description: 'AI Teammate'
    };
  }

  const name = event.email.split('@')[0].split(/[._-]/).map(part => 
    part.charAt(0).toUpperCase() + part.slice(1)
  ).join(' ');

  return {
    name,
    description: event.email
  };
};

// Add helper to group events by session
const groupEventsBySession = (events: ActivityEvent[]): SessionGroup[] => {
  const sessionMap = new Map<string, ActivityEvent[]>();
  
  // First, group events by session ID
  events.forEach(event => {
    if (event.extra.session_id) {
      const events = sessionMap.get(event.extra.session_id) || [];
      events.push(event);
      sessionMap.set(event.extra.session_id, events);
    }
  });

  // Then create session groups with participant info
  return Array.from(sessionMap.entries()).map(([sessionId, events]) => {
    const sortedEvents = [...events].sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    // Get unique participants
    const users = new Map<string, { email: string; events: number }>();
    const teammates = new Map<string, { id: string; name: string; events: number }>();

    events.forEach(event => {
      if (isTeammateEvent(event)) {
        const id = event.extra.teammate_id || event.category_name;
        if (!teammates.has(id)) {
          teammates.set(id, { 
            id, 
            name: event.extra.teammate_name || event.category_name,
            events: 0 
          });
        }
        teammates.get(id)!.events++;
      } else if (!event.extra.is_user_message) {
        // Skip system messages
        return;
      } else {
        if (!users.has(event.email)) {
          users.set(event.email, { email: event.email, events: 0 });
        }
        users.get(event.email)!.events++;
      }
    });

    return {
      sessionId,
      events: sortedEvents,
      startTime: sortedEvents[0].timestamp,
      endTime: sortedEvents[sortedEvents.length - 1].timestamp,
      participants: {
        users: Array.from(users.values()),
        teammates: Array.from(teammates.values())
      },
      success: events.some(e => e.action_successful)
    };
  }).sort((a, b) => new Date(b.startTime).getTime() - new Date(a.startTime).getTime());
};

export const GlobalActivityFeed: React.FC<GlobalActivityFeedProps> = ({ 
  events, 
  timeRange, 
  isLoading,
  onViewSession 
}) => {
  const [selectedEvent, setSelectedEvent] = useState<ActivityEvent | null>(null);
  const [expandedSessions, setExpandedSessions] = useState<Set<string>>(new Set());

  // Filter and group events based on time range
  const sessionGroups = useMemo(() => {
    const cutoffDate = getTimeRangeDate(timeRange);
    const filteredEvents = events.filter(event => new Date(event.timestamp) > cutoffDate);
    return groupEventsBySession(filteredEvents);
  }, [events, timeRange]);

  const toggleSession = (sessionId: string) => {
    setExpandedSessions(prev => {
      const next = new Set(prev);
      if (next.has(sessionId)) {
        next.delete(sessionId);
      } else {
        next.add(sessionId);
      }
      return next;
    });
  };

  if (isLoading) {
    return (
      <div className="h-full w-full flex items-center justify-center text-slate-400">
        <div className="flex flex-col items-center gap-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <p>Loading activity...</p>
        </div>
      </div>
    );
  }

  if (!events || events.length === 0) {
    return (
      <div className="h-full w-full flex items-center justify-center text-slate-400">
        <div className="flex flex-col items-center gap-2">
          <AlertCircle className="h-6 w-6" />
          <p>No activity found</p>
          <p className="text-sm text-slate-500">Try adjusting the time range</p>
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="h-full w-full flex flex-col">
        <ScrollArea className="flex-1">
          <div className="space-y-3 px-2 py-3">
            {sessionGroups.map((group) => {
              const isExpanded = expandedSessions.has(group.sessionId);
              const displayEvents = isExpanded ? group.events : group.events.slice(0, 3);
              const firstUser = group.participants.users[0];
              const mainTeammate = group.participants.teammates[0];

              return (
                <div
                  key={group.sessionId}
                  className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden"
                >
                  {/* Session Header */}
                  <div 
                    className="p-3 flex items-start gap-3 border-b border-slate-700/50 cursor-pointer hover:bg-slate-800/70"
                    onClick={() => toggleSession(group.sessionId)}
                  >
                    <div className="flex-shrink-0 relative">
                      {firstUser && (
                        <div className="w-8 h-8 rounded-full bg-blue-500/10 flex items-center justify-center ring-2 ring-slate-900">
                          <Users className="h-4 w-4 text-blue-400" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-slate-200">
                          {firstUser ? firstUser.email.split('@')[0] : 'System'} started a conversation
                        </span>
                        <Badge variant="outline" className={cn(
                          "text-[10px] px-1.5 py-0.5",
                          group.success 
                            ? "bg-green-500/10 text-green-400 border-green-500/30"
                            : "bg-red-500/10 text-red-400 border-red-500/30"
                        )}>
                          {group.success ? 'Completed' : 'Failed'}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatDate(group.startTime)}
                        </div>
                        <span>•</span>
                        <div className="flex items-center gap-1">
                          <Bot className="h-3 w-3" />
                          with {mainTeammate?.name || 'AI Teammate'}
                        </div>
                        <span>•</span>
                        <div className="flex items-center gap-1">
                          <MessageSquare className="h-3 w-3" />
                          {group.events.length} interactions
                        </div>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2"
                      onClick={(e) => {
                        e.stopPropagation();
                        onViewSession?.(group.sessionId);
                      }}
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                    </Button>
                  </div>

                  {/* Timeline of Events */}
                  <div className="divide-y divide-slate-700/50">
                    {displayEvents.map((event, index) => (
                      <div
                        key={`${event.timestamp}-${index}`}
                        className="p-2.5 pl-12 relative hover:bg-slate-800/50 cursor-pointer"
                        onClick={() => setSelectedEvent(event)}
                      >
                        {/* Timeline connector */}
                        <div className="absolute left-[1.4rem] top-0 bottom-0 w-px bg-slate-700/50" />
                        
                        {/* Event dot */}
                        <div className={cn(
                          "absolute left-5 top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full ring-2 ring-slate-900",
                          isTeammateEvent(event) ? "bg-purple-500" :
                          event.extra.is_user_message ? "bg-blue-500" :
                          event.extra.tool_name ? "bg-amber-500" : "bg-slate-500"
                        )} />
                        
                        <div className="flex items-start gap-2.5">
                          <div className={cn(
                            "flex-shrink-0 p-1 rounded-md",
                            isTeammateEvent(event) ? "bg-purple-500/10" :
                            event.extra.is_user_message ? "bg-blue-500/10" :
                            event.extra.tool_name ? "bg-amber-500/10" : "bg-slate-800"
                          )}>
                            {getEventIcon(event)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-slate-300">
                                {isTeammateEvent(event) ? (
                                  <span className="text-purple-400">{event.extra.teammate_name}</span>
                                ) : event.extra.is_user_message ? (
                                  <span className="text-blue-400">{event.email.split('@')[0]}</span>
                                ) : event.resource_type === 'Webhook' && event.extra.teammate_name ? (
                                  <span className="text-purple-400">{event.extra.teammate_name}</span>
                                ) : (
                                  <span className="text-amber-400">System</span>
                                )}
                                {' '}
                                <span className="text-slate-500">{getEventNarrative(event)}</span>
                              </span>
                              {event.extra.tool_name && (
                                <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/30 text-[10px] px-1.5">
                                  {event.extra.tool_name}
                                </Badge>
                              )}
                              {event.resource_type === 'Webhook' && !event.extra.teammate_name && (
                                <Badge variant="outline" className="bg-red-500/10 text-red-400 border-red-500/30 text-[10px] px-1.5">
                                  No Teammate Selected
                                </Badge>
                              )}
                            </div>
                            {event.resource_text && (
                              <div className="text-sm text-slate-400 mt-1">
                                <MarkdownWithContext 
                                  content={event.resource_text} 
                                  className="line-clamp-2"
                                />
                              </div>
                            )}
                            <div className="flex items-center gap-2 mt-1.5">
                              <span className="text-xs text-slate-500">{formatDate(event.timestamp)}</span>
                              {event.action_successful !== undefined && (
                                <>
                                  <span className="text-xs text-slate-500">•</span>
                                  <span className={cn(
                                    "text-xs",
                                    event.action_successful ? "text-green-400" : "text-red-400"
                                  )}>
                                    {event.action_successful ? 'Succeeded' : 'Failed'}
                                  </span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Show more/less button */}
                  {group.events.length > 3 && (
                    <div className="p-1.5 bg-slate-800/50 border-t border-slate-700/50">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full h-7 text-xs text-slate-400 hover:text-slate-300"
                        onClick={() => toggleSession(group.sessionId)}
                      >
                        {isExpanded ? (
                          <>Show less<ChevronRight className="h-3 w-3 ml-1 rotate-90" /></>
                        ) : (
                          <>Show {group.events.length - 3} more events<ChevronRight className="h-3 w-3 ml-1 -rotate-90" /></>
                        )}
                      </Button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </ScrollArea>

        {/* Event Details Dialog */}
        <Dialog open={!!selectedEvent} onOpenChange={() => setSelectedEvent(null)}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col bg-slate-900 border-slate-800">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-slate-800">
                  {selectedEvent && getEventIcon(selectedEvent)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-slate-400">
                      {selectedEvent && formatDate(selectedEvent.timestamp)}
                    </span>
                    {selectedEvent?.extra.session_id && (
                      <>
                        <span className="text-sm text-slate-500">•</span>
                        <Button
                          variant="link"
                          size="sm"
                          className="h-auto p-0 text-sm text-indigo-400 hover:text-indigo-300"
                          onClick={() => selectedEvent.extra.session_id && onViewSession?.(selectedEvent.extra.session_id)}
                        >
                          View Full Session
                          <ExternalLink className="h-3 w-3 ml-1" />
                        </Button>
                      </>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <h2 className="text-lg font-semibold text-slate-100">
                      {selectedEvent?.resource_type}
                    </h2>
                    {selectedEvent?.extra.tool_name && (
                      <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/30">
                        {selectedEvent.extra.tool_name}
                      </Badge>
                    )}
                  </div>
                </div>
                {selectedEvent && getStatusIcon(selectedEvent.action_successful)}
              </DialogTitle>
            </DialogHeader>

            <ScrollArea className="flex-1">
              <div className="p-6 space-y-6">
                {/* Sender Info */}
                {selectedEvent && (
                  <div className="flex items-center gap-4 p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                    <div className="relative">
                      {isTeammateEvent(selectedEvent) ? (
                        <>
                          <img
                            src={generateAvatarUrl({ 
                              uuid: selectedEvent.extra.teammate_id || selectedEvent.category_name, 
                              name: selectedEvent.extra.teammate_name || 'AI Teammate'
                            })}
                            alt={selectedEvent.extra.teammate_name || 'AI Teammate'}
                            className="w-10 h-10 rounded-lg"
                          />
                          <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-slate-800 ring-2 ring-slate-900 flex items-center justify-center">
                            <Bot className="h-2.5 w-2.5 text-purple-400" />
                          </div>
                        </>
                      ) : (
                        <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                          <Users className="h-5 w-5 text-blue-400" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1">
                      {isTeammateEvent(selectedEvent) ? (
                        <>
                          <div className="flex items-center gap-2">
                            <div className="font-medium text-slate-200">{selectedEvent.extra.teammate_name}</div>
                            <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/30">
                              AI Teammate
                            </Badge>
                          </div>
                          <div className="text-sm text-slate-400">
                            {selectedEvent.category_name} • Handling Actions
                          </div>
                        </>
                      ) : (
                        <>
                          <div className="font-medium text-slate-200">
                            {selectedEvent.email.split('@')[0]}
                          </div>
                          <div className="text-sm text-slate-400">
                            User • {selectedEvent.email}
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                )}

                {/* Content */}
                {selectedEvent?.resource_text && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-medium text-slate-400">Content</h3>
                    <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                      <MarkdownWithContext content={selectedEvent.resource_text} />
                    </div>
                  </div>
                )}

                {/* Tool Details */}
                {selectedEvent?.extra.tool_name && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-medium text-slate-400">Tool Details</h3>
                    <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Terminal className="h-4 w-4 text-amber-400" />
                          <span className="text-slate-200 font-medium">{selectedEvent.extra.tool_name}</span>
                        </div>
                        {selectedEvent.extra.tool_execution_status && (
                          <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/30">
                            {selectedEvent.extra.tool_execution_status}
                          </Badge>
                        )}
                      </div>
                      {selectedEvent.extra.tool_args && (
                        <div>
                          <h4 className="text-sm text-slate-400 mb-2">Arguments</h4>
                          <pre className="p-3 rounded-lg bg-slate-900 overflow-x-auto text-sm text-slate-300 font-mono">
                            {JSON.stringify(selectedEvent.extra.tool_args, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
          </DialogContent>
        </Dialog>
      </div>
    </TooltipProvider>
  );
}; 