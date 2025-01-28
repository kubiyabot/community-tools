import * as React from 'react';
import { useState } from 'react';
import { format } from 'date-fns';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../../components/ui/tooltip';
import { Calendar, CalendarClock, Info, MessageSquare, Settings, Trash2, Clock, User, RotateCcw, PenSquare, Bot, Hash } from 'lucide-react';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import { Slack as SlackIcon } from '../../components/icons/slack';
import { Teams as TeamsIcon } from '../../components/icons/teams';
import type { TaskCardProps } from './types';
import { ContextVariable } from './ContextVariable';
import { Avatar, AvatarImage, AvatarFallback } from '../../components/ui/avatar';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

// Helper function to get teammate display info
function getTeammateDisplay(task: TaskCardProps['task']) {
  // First try to get teammate from the teammate object
  if (task.teammate?.uuid) {
    return {
      uuid: task.teammate.uuid,
      name: task.teammate.name,
      avatar: task.teammate.avatar,
      description: task.teammate.description
    };
  }

  // If no teammate object but we have selected_agent info
  if (task.parameters?.selected_agent) {
    return {
      uuid: task.parameters.selected_agent,
      name: task.parameters.selected_agent_name || task.parameters.selected_agent.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' '),
      avatar: undefined,
      description: 'Assigned Teammate'
    };
  }

  return null;
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
        <ReactMarkdown
          key={index}
          className={cn(
            "prose prose-invert max-w-none",
            "prose-p:leading-relaxed prose-p:my-2",
            "prose-code:px-1 prose-code:py-0.5 prose-code:rounded-md",
            "prose-code:bg-slate-800 prose-code:text-slate-200"
          )}
        >
          {part}
        </ReactMarkdown>
      );
    }
  }).filter(Boolean);
}

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onDelete,
  badges = []
}) => {
  const isRecurring = !!task.parameters.cron_string;
  const scheduledDate = new Date(task.scheduled_time);
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    message_text: task.parameters.message_text || '',
    channel_id: task.channel_id || '',
    scheduled_time: task.scheduled_time,
    cron_string: task.parameters.cron_string || ''
  });

  const teammate = getTeammateDisplay(task);


  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-500/10 text-yellow-300 border-yellow-500/30';
      case 'completed':
        return 'bg-green-500/10 text-green-300 border-green-500/30';
      case 'failed':
        return 'bg-red-500/10 text-red-300 border-red-500/30';
      default:
        return 'bg-slate-500/10 text-slate-300 border-slate-500/30';
    }
  };

  // Get communication method icon and label
  const getCommunicationInfo = () => {
    const channelId = task.channel_id;
    if (!channelId) return { icon: <MessageSquare className="h-4 w-4" />, label: 'Direct Message' };
    
    if (channelId.startsWith('#') || channelId.startsWith('C')) {
      return { 
        icon: <SlackIcon className="h-4 w-4" />, 
        label: channelId.startsWith('#') ? channelId : `Slack Channel ${channelId}` 
      };
    }
    
    if (channelId.startsWith('teams:')) {
      return { 
        icon: <TeamsIcon className="h-4 w-4" />, 
        label: channelId.replace('teams:', 'Teams: ') 
      };
    }

    return { 
      icon: <Hash className="h-4 w-4" />, 
      label: channelId 
    };
  };

  const communicationInfo = getCommunicationInfo();
  const createdDate = task.created_at ? new Date(task.created_at) : null;

  return (
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
            {teammate ? (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="flex items-center gap-2 px-2 py-1 rounded-md bg-purple-500/10 border border-purple-500/20">
                      <Avatar className="h-5 w-5">
                        {teammate.avatar ? (
                          <AvatarImage src={teammate.avatar} alt={teammate.name} />
                        ) : (
                          <AvatarFallback className="bg-purple-500/20 text-purple-200">
                            {teammate.name.charAt(0)}
                          </AvatarFallback>
                        )}
                      </Avatar>
                      <span className="text-sm text-purple-200">{teammate.name}</span>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{teammate.description || 'Assigned Teammate'}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            ) : (
              <Badge variant="outline" className="bg-yellow-500/10 text-yellow-300 border-yellow-500/30">
                <Bot className="h-3 w-3 mr-1" />
                No Teammate Assigned
              </Badge>
            )}

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

            {/* Additional Badges */}
            {badges.map((badge, index) => (
              <Badge
                key={index}
                variant={badge.variant}
                className={badge.className}
              >
                {badge.icon}
                {badge.text}
              </Badge>
            ))}
          </div>

          {/* Task Details */}
          <div className="space-y-2">
            {/* Message with JSON and Markdown Support */}
            <div className="text-sm text-slate-300">
              {formatMessageWithJson(task.parameters.message_text)}
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
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onDelete(task.task_id)}
            className={cn(
              "text-red-400 hover:text-red-300",
              "bg-red-500/10 hover:bg-red-500/20"
            )}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
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
  );
}; 