import * as React from 'react';
import { useState } from 'react';
import { format } from 'date-fns';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../../components/ui/tooltip';
import { Calendar, CalendarClock, Info, MessageSquare, Settings, Trash2, Clock, User, RotateCcw, PenSquare, Bot, Hash, Check, X, Wrench } from 'lucide-react';
import { cn } from '@/lib/utils';
import ReactMarkdown, { Components } from 'react-markdown';
import { Slack as SlackIcon } from '../../components/icons/slack';
import { Teams as TeamsIcon } from '../../components/icons/teams';
import { GitHub as GitHubIcon } from '../../components/icons/github';
import { Jira as JiraIcon } from '../../components/icons/jira';
import type { TaskCardProps, TeammateInfo } from './types';
import { ContextVariable } from './ContextVariable';
import { Avatar, AvatarImage, AvatarFallback } from '../../components/ui/avatar';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { toast } from '@/app/components/ui/use-toast';
import type { ReactNode } from 'react';
import oneDark from 'react-syntax-highlighter/dist/cjs/styles/prism/one-dark';
import { MarkdownWithContext } from '../../components/activity/MarkdownWithContext';
import { useTeammateContext } from '@/app/MyRuntimeProvider';
import { generateAvatarUrl } from '@/app/components/TeammateSelector';
import { TeammateDetails } from '@/app/components/shared/teammate-details/TeammateDetails';
import { Dialog, DialogContent, DialogTitle } from '@/app/components/ui/dialog';
import type { TeammateDetails as TeammateDetailsType, TeammateWithCapabilities } from '@/app/types/teammate';
import type { Integration } from '@/app/components/shared/teammate-details/types';

// Custom components for markdown rendering
const MarkdownComponents = {
  p: ({ node, children, ...props }: any) => (
    <span className="text-sm text-slate-300 leading-relaxed block mb-2" {...props}>
      {children}
    </span>
  ),
  code: ({ node, inline, className, children, ...props }: any) => {
    const match = /language-(\w+)/.exec(className || '');
    const content = String(children).replace(/\n$/, '');
    
    if (!inline && match) {
      return (
        <span className="block my-2">
          <SyntaxHighlighter
            language={match[1]}
            style={oneDark}
            PreTag="div"
            customStyle={{
              margin: 0,
              padding: '0.75rem',
              background: 'rgba(30, 41, 59, 0.5)',
              border: '1px solid rgba(51, 65, 85, 0.5)',
              borderRadius: '0.375rem',
              fontSize: '0.875rem'
            }}
          >
            {content}
          </SyntaxHighlighter>
        </span>
      );
    }
    
    return (
      <code className={cn("bg-slate-800/50 px-1.5 py-0.5 rounded text-sm", className)} {...props}>
        {content}
      </code>
    );
  }
} as const;

// Helper function to normalize names for comparison
function normalizeName(name: string | undefined | null): string {
  return (name || '').toLowerCase().trim();
}

// Helper function to get teammate display info
function getTeammateDisplay(task: TaskCardProps['task'], teammates: any[]): TeammateInfo | undefined {
  console.log('Attempting to find teammate for task:', {
    taskId: task.task_id,
    teammateInfo: task.teammate,
    selectedAgent: task.parameters?.selected_agent,
    selectedAgentName: task.parameters?.selected_agent_name,
    availableTeammates: teammates.map(t => ({ uuid: t.uuid, name: t.name }))
  });

  // First try to find teammate by UUID
  let matchingTeammate;
  
  // Check task.teammate.uuid first
  if (task.teammate?.uuid) {
    matchingTeammate = teammates.find(t => t.uuid === task.teammate?.uuid);
    if (matchingTeammate) {
      console.log('Found teammate by task.teammate.uuid:', {
        uuid: matchingTeammate.uuid,
        name: matchingTeammate.name
      });
    }
  }
  
  // Then check selected_agent if it looks like a UUID
  if (!matchingTeammate && task.parameters?.selected_agent) {
    const selectedAgent = task.parameters.selected_agent;
    // Check if selected_agent is a UUID (basic validation)
    if (selectedAgent.includes('-') && selectedAgent.length > 30) {
      matchingTeammate = teammates.find(t => t.uuid === selectedAgent);
      if (matchingTeammate) {
        console.log('Found teammate by selected_agent UUID:', {
          uuid: matchingTeammate.uuid,
          name: matchingTeammate.name
        });
      }
    }
  }

  // If no UUID match, try to find by name
  if (!matchingTeammate) {
    const selectedName = task.parameters?.selected_agent_name || task.parameters?.selected_agent;
    if (selectedName) {
      const normalizedSelectedName = normalizeName(selectedName);
      matchingTeammate = teammates.find(t => 
        normalizeName(t.name) === normalizedSelectedName
      );

      if (matchingTeammate) {
        console.log('Found teammate by name match:', {
          uuid: matchingTeammate.uuid,
          name: matchingTeammate.name,
          selectedName
        });
      }
    }
  }

  // If we found a matching teammate, return the full info
  if (matchingTeammate) {
    return {
      uuid: matchingTeammate.uuid,
      name: task.parameters?.selected_agent_name || matchingTeammate.name,
      description: matchingTeammate.description || `AI Teammate - ${matchingTeammate.name}`,
      avatar: generateAvatarUrl({ 
        uuid: matchingTeammate.uuid, 
        name: matchingTeammate.name 
      })
    };
  }

  // If no match found but we have a name/id, create basic teammate info
  const selectedName = task.parameters?.selected_agent_name || task.parameters?.selected_agent;
  if (selectedName) {
    console.log('No teammate match found, creating basic info:', {
      selectedName,
      selectedAgent: task.parameters?.selected_agent
    });

    // If selected_agent looks like a UUID, use it
    const uuid = (task.parameters?.selected_agent?.includes('-') && task.parameters?.selected_agent?.length > 30) 
      ? task.parameters.selected_agent 
      : selectedName;
    const name = task.parameters?.selected_agent_name || selectedName;

    return {
      uuid,
      name,
      description: `Teammate details unavailable - ${name}`,
      avatar: generateAvatarUrl({ uuid, name })
    };
  }

  console.log('No teammate information available for task:', task.task_id);
  return undefined;
}

// Get task submitter info
function getTaskSubmitter(task: TaskCardProps['task'], currentUserEmail?: string) {
  if (!task.parameters?.user_email) return null;

  // Check if the task was submitted by the current user
  if (currentUserEmail && task.parameters.user_email === currentUserEmail) {
    return {
      email: task.parameters.user_email,
      name: 'You',
      isCurrentUser: true
    };
  }

  const name = task.parameters.user_email.split('@')[0]
    .split('.')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
  return {
    email: task.parameters.user_email,
    name,
    isCurrentUser: false
  };
}

// Helper function to detect and format JSON strings in text
function formatMessageWithJson(text: string): React.ReactNode[] {
  // Match JSON-like structures with a more precise regex
  const parts = text.split(/(\{[\s\S]*?\}|\[[\s\S]*?\])/);
  return parts.map((part, index) => {
    if (!part.trim()) return null;
    try {
      // Try to parse as JSON
      const parsed = JSON.parse(part);
      return (
        <div key={index} className="my-2 rounded-md overflow-hidden">
          <SyntaxHighlighter
            language="json"
            style={vscDarkPlus}
            customStyle={{ margin: 0, padding: '0.75rem' }}
          >
            {JSON.stringify(parsed, null, 2)}
          </SyntaxHighlighter>
        </div>
      );
    } catch {
      // If not JSON, return as regular text or markdown
      return (
        <div key={index} className="prose prose-invert max-w-none">
          <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
            {part.split('\n').map((line, i) => (
              <div key={i} className="mb-2">
                {line}
              </div>
            ))}
          </div>
        </div>
      );
    }
  }).filter(Boolean);
}

// Get communication method icon and label
const getCommunicationInfo = (channelId: string) => {
  if (!channelId) return { icon: <MessageSquare className="h-4 w-4" />, label: 'Direct Message' };
  
  if (channelId.startsWith('#') || channelId.startsWith('C')) {
    return { 
      icon: <SlackIcon className="h-4 w-4" />, 
      label: channelId.startsWith('#') ? channelId : `#${channelId}` 
    };
  }
  
  if (channelId.startsWith('teams:')) {
    return { 
      icon: <TeamsIcon className="h-4 w-4" />, 
      label: channelId.replace('teams:', '') 
    };
  }

  return { 
    icon: <Hash className="h-4 w-4" />, 
    label: channelId 
  };
};

// Helper function to get integration icon
const getIcon = (integration: string | undefined) => {
  if (!integration) return <Bot className="h-4 w-4" />;
  
  switch (integration.toLowerCase()) {
    case 'slack':
      return <SlackIcon className="h-4 w-4" />;
    case 'teams':
      return <TeamsIcon className="h-4 w-4" />;
    case 'github':
      return <GitHubIcon className="h-4 w-4" />;
    case 'jira':
      return <JiraIcon className="h-4 w-4" />;
    default:
      return <Bot className="h-4 w-4" />;
  }
};

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onDelete,
  badges = [],
  onTeammateClick,
  currentUserEmail
}) => {
  const [isLoading, setIsLoading] = React.useState(true);
  const [teammate, setTeammate] = React.useState<TeammateInfo | undefined>();
  const [isDeleting, setIsDeleting] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const { teammates } = useTeammateContext();

  // Find teammate details on mount or when task/teammates change
  React.useEffect(() => {
    setIsLoading(true);
    const matchedTeammate = getTeammateDisplay(task, teammates);
    setTeammate(matchedTeammate);
    setIsLoading(false);
  }, [task, teammates]);

  const handleTeammateClick = () => {
    if (teammate && onTeammateClick) {
      // Find full teammate data
      const fullTeammate = teammates.find(t => t.uuid === teammate.uuid) as TeammateWithCapabilities;
      if (fullTeammate) {
        const teammateData: TeammateDetailsType = {
          uuid: fullTeammate.uuid,
          name: fullTeammate.name,
          description: fullTeammate.description || teammate.description || '',
          avatar_url: fullTeammate.avatar_url || teammate.avatar,
          llm_model: fullTeammate.capabilities?.llm_model,
          instruction_type: fullTeammate.capabilities?.instruction_type,
          tools: fullTeammate.tools || [],
          runners: fullTeammate.runners || [],
          integrations: (fullTeammate.integrations || []).map(integration => {
            if (typeof integration === 'string') {
              return {
                id: integration,
                name: integration,
                type: integration,
                icon_url: undefined,
                managed_by: 'kubiya',
                configs: [],
                kubiya_metadata: {},
                integration_type: integration,
                auth_type: 'none'
              };
            }
            return {
              id: integration.id || integration.name,
              name: integration.name,
              type: integration.type || integration.name,
              icon_url: integration.icon_url,
              managed_by: 'kubiya',
              configs: [],
              kubiya_metadata: {},
              integration_type: integration.type || integration.name,
              auth_type: 'none'
            };
          }),
          sources: fullTeammate.sources || [],
          metadata: {
            created_at: fullTeammate.metadata?.created_at || new Date().toISOString(),
            last_updated: fullTeammate.metadata?.last_updated || new Date().toISOString(),
            tools_count: fullTeammate.tools?.length || 0,
            integrations_count: fullTeammate.integrations?.length || 0,
            sources_count: fullTeammate.sources?.length || 0
          }
        };
        onTeammateClick(teammateData);
      }
    }
  };

  const isRecurring = !!task.parameters.cron_string;
  const scheduledDate = new Date(task.scheduled_time);
  const [editData, setEditData] = useState({
    message_text: task.parameters.message_text || '',
    channel_id: task.channel_id || '',
    scheduled_time: task.scheduled_time,
    cron_string: task.parameters.cron_string || ''
  });

  const submitter = getTaskSubmitter(task, currentUserEmail);
  const communicationInfo = getCommunicationInfo(task.channel_id);
  const createdDate = task.created_at ? new Date(task.created_at) : null;

  const handleDelete = async () => {
    if (!isDeleting) {
      setIsDeleting(true);
      return;
    }

    try {
      console.log('Deleting task:', { taskId: task.task_id });
      
      const response = await fetch(`/api/scheduled_tasks?taskId=${task.task_id}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        let errorMessage = 'Failed to delete task. Please try again.';
        
        // Try to get detailed error message
        try {
          const errorData = await response.json();
          errorMessage = errorData.details || errorData.error || errorMessage;
          
          // Handle specific error cases
          if (response.status === 404) {
            errorMessage = 'This task no longer exists. The list will be refreshed.';
          } else if (response.status === 401) {
            errorMessage = 'Your session has expired. Please log in again.';
          }
        } catch (e) {
          console.error('Error parsing delete response:', e);
        }

        toast({
          title: "Error",
          description: errorMessage,
          variant: "destructive",
        });

        // If task doesn't exist, trigger delete callback anyway to refresh the list
        if (response.status === 404 && onDelete) {
          await onDelete(task.task_id);
        }
        return;
      }

      if (onDelete) {
        await onDelete(task.task_id);
      }

      toast({
        title: "Success",
        description: "Task deleted successfully",
      });
    } catch (error) {
      console.error('Error deleting task:', {
        taskId: task.task_id,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      
      toast({
        title: "Error",
        description: "Failed to delete task. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const cancelDelete = () => {
    setIsDeleting(false);
  };

  // Render teammate tooltip content
  const renderTeammateTooltip = () => {
    if (!teammate) {
      return (
        <div className="space-y-1">
          <p className="text-red-200">Could not detect the teammate</p>
          <p className="text-xs text-red-300/80">This could be a configuration issue or the teammate no longer exists</p>
        </div>
      );
    }

    // Get full teammate data
    const fullTeammate = teammates.find(t => t.uuid === teammate.uuid) as TeammateWithCapabilities;
    if (!fullTeammate) return null;

    return (
      <div className="space-y-2 min-w-[300px]">
        {/* Header with Avatar */}
        <div className="flex items-start gap-3">
          <Avatar className="h-10 w-10">
            {teammate.avatar ? (
              <AvatarImage src={teammate.avatar} alt={teammate.name} />
            ) : (
              <AvatarFallback className="bg-purple-500/20 text-purple-200">
                {teammate.name.charAt(0).toUpperCase()}
              </AvatarFallback>
            )}
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-white text-lg">{teammate.name}</p>
            <p className="text-xs text-slate-400 truncate">ID: {teammate.uuid}</p>
          </div>
        </div>

        {/* Description */}
        <p className="text-sm text-slate-300">{fullTeammate.description || teammate.description}</p>
        
        {/* Tools Count */}
        {(fullTeammate.tools?.length ?? 0) > 0 && (
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Wrench className="h-3.5 w-3.5" />
            <span>{fullTeammate.tools?.length || 0} tools available</span>
          </div>
        )}

        {/* Integrations */}
        {(fullTeammate.integrations?.length ?? 0) > 0 && (
          <div className="space-y-1.5">
            <p className="text-xs font-medium text-slate-400">Connected Platforms</p>
            <div className="flex flex-wrap gap-2">
              {(fullTeammate.integrations || []).map((integration, index) => {
                const integrationName = typeof integration === 'string' ? integration : integration.name;
                const icon = getIcon(integrationName);
                return (
                  <div key={index} className="flex items-center gap-1.5 bg-purple-500/10 rounded-full px-2 py-1">
                    <div className="w-4 h-4">{icon}</div>
                    <span className="text-[10px] text-purple-300">{integrationName}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="pt-1 text-xs text-purple-300/70 flex items-center gap-1.5">
          <Info className="h-3 w-3" />
          Click for full details
        </div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className={cn(
        "p-4 rounded-lg border bg-slate-900/50",
        "border-slate-800/60",
        "animate-pulse"
      )}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-3">
              <div className="flex items-center gap-2 bg-purple-500/10 border border-purple-500/20 px-2 py-1 rounded-md">
                <div className="w-5 h-5 rounded-full bg-purple-500/20" />
                <div className="w-24 h-4 bg-purple-500/20 rounded" />
              </div>
              <div className="w-20 h-5 bg-slate-800 rounded" />
            </div>
            <div className="space-y-2">
              <div className="w-3/4 h-4 bg-slate-800 rounded" />
              <div className="w-1/2 h-4 bg-slate-800 rounded" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className={cn(
        "p-4 rounded-lg border bg-slate-900/50",
        "border-slate-800/60 hover:border-slate-700/60",
        "transition-all duration-200"
      )}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            {/* Header with Status Badge and Teammate */}
            <div className="flex items-center gap-3 mb-3 flex-wrap">
              {/* Teammate Info */}
              <TooltipProvider delayDuration={100}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleTeammateClick}
                      className={cn(
                        "flex items-center gap-2 px-2 py-1 rounded-md",
                        teammate ? "bg-purple-500/10 border border-purple-500/20 hover:bg-purple-500/20" :
                        "bg-red-500/10 border border-red-500/20 hover:bg-red-500/20"
                      )}
                    >
                      <Avatar className="h-5 w-5">
                        {teammate?.avatar ? (
                          <AvatarImage src={teammate.avatar} alt={teammate.name} />
                        ) : (
                          <AvatarFallback className={cn(
                            teammate ? "bg-purple-500/20 text-purple-200" :
                            "bg-red-500/20 text-red-200"
                          )}>
                            {teammate?.name.charAt(0).toUpperCase() || '?'}
                          </AvatarFallback>
                        )}
                      </Avatar>
                      <span className={cn(
                        "text-sm",
                        teammate ? "text-purple-200" : "text-red-200"
                      )}>
                        {teammate?.name || 'Unknown Teammate'}
                      </span>
                      <Info className={cn(
                        "h-3 w-3 opacity-50",
                        teammate ? "text-purple-300" : "text-red-300"
                      )} />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" sideOffset={5}>
                    {renderTeammateTooltip()}
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>

              {/* Communication Method */}
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Badge variant="outline" className="bg-blue-500/10 text-blue-300 border-blue-500/30">
                      {communicationInfo.icon}
                      <span className="ml-1">{communicationInfo.label}</span>
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Communication Channel</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>

              {/* Status Badge */}
              <Badge
                variant="outline"
                className={cn(
                  task.status === 'pending' && "bg-yellow-500/10 text-yellow-300 border-yellow-500/30",
                  task.status === 'completed' && "bg-green-500/10 text-green-300 border-green-500/30",
                  task.status === 'failed' && "bg-red-500/10 text-red-300 border-red-500/30"
                )}
              >
                {task.status.charAt(0).toUpperCase() + task.status.slice(1)}
              </Badge>

              {/* Recurring Badge */}
              {task.parameters.cron_string && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Badge variant="outline" className="bg-purple-500/10 text-purple-300 border-purple-500/30">
                        <RotateCcw className="h-3 w-3 mr-1" />
                        Recurring
                      </Badge>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Pattern: {task.parameters.cron_string}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </div>

            {/* Task Details */}
            <div className="space-y-2">
              {/* Message with JSON and Markdown Support */}
              <div className="text-sm text-slate-300">
                <MarkdownWithContext
                  content={task.parameters.message_text}
                  className="line-clamp-2"
                />
              </div>

              {/* Schedule Info */}
              <div className="flex items-center gap-4 text-xs text-slate-400">
                <div className="flex items-center gap-1.5">
                  <Calendar className="h-3.5 w-3.5" />
                  <span>{format(scheduledDate, 'MMM d, yyyy')}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5" />
                  <span>{format(scheduledDate, 'h:mm a')}</span>
                </div>
                {createdDate && (
                  <div className="flex items-center gap-1.5">
                    <Info className="h-3.5 w-3.5" />
                    <span>Created {format(createdDate, 'MMM d')}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsEditing(true)}
              className={cn(
                "text-slate-400 hover:text-white",
                "bg-slate-800/50 hover:bg-slate-800"
              )}
            >
              <PenSquare className="h-4 w-4" />
            </Button>
            {isDeleting ? (
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleDelete}
                  className="text-red-400 hover:bg-red-500/20"
                >
                  <Check className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={cancelDelete}
                  className="text-slate-400 hover:bg-slate-800"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDelete}
                className={cn(
                  "text-red-400 hover:text-red-300",
                  "bg-red-500/10 hover:bg-red-500/20"
                )}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Edit Form */}
        {isEditing && (
          <div className="mt-4 space-y-4 border-t border-slate-800 pt-4">
            <div>
              <label className="text-sm font-medium text-slate-300 mb-2 block">Message</label>
              <textarea
                value={editData.message_text}
                onChange={(e) => setEditData({ ...editData, message_text: e.target.value })}
                className={cn(
                  "w-full px-4 py-3 bg-slate-900/50 border border-slate-800",
                  "rounded-lg text-slate-300 min-h-[120px] resize-y",
                  "focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500/30",
                  "transition-all duration-200"
                )}
                placeholder="Enter your task message..."
              />
            </div>

            <div className="flex items-center gap-4">
              <Button
                onClick={() => setIsEditing(false)}
                className="bg-purple-500 hover:bg-purple-600 text-white"
              >
                Save Changes
              </Button>
              <Button
                variant="ghost"
                onClick={() => setIsEditing(false)}
                className="text-slate-400 hover:text-white"
              >
                Cancel
              </Button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}; 