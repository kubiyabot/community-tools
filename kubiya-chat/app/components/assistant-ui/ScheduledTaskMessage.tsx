"use client";

import { memo } from 'react';
import { Clock, Calendar, Bell, Trash2, AlertCircle, CheckCircle2, ExternalLink, Slack } from 'lucide-react';
import { Button } from "@/app/components/button";
import { toast } from '@/app/components/use-toast';
import { MarkdownText } from './MarkdownText';
import { ContextVariable } from '../activity/ContextVariable';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/app/components/ui/tooltip";

interface ScheduledTaskMessageProps {
  task: {
    id: string;
    task_id: string;
    task_uuid: string;
    scheduled_time: string;
    parameters: {
      message_text: string;
      cron_string?: string;
      team_id: string;
      user_email: string;
      channel_id?: string;
    };
    status: string;
    created_at: string;
  };
}

const ScheduledTaskMessageComponent = ({ task }: ScheduledTaskMessageProps) => {
  const handleDelete = async () => {
    try {
      const response = await fetch(`/api/scheduled_tasks/${task.task_uuid}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete task');
      }

      toast({
        title: "Task Deleted",
        description: "The scheduled task has been successfully deleted.",
        variant: "default",
      });
    } catch (error) {
      console.error('Error deleting task:', error);
      toast({
        title: "Error",
        description: "Failed to delete the scheduled task. Please try again.",
        variant: "destructive",
      });
    }
  };

  const formatScheduleTime = (dateString?: string) => {
    if (!dateString) return 'No date specified';

    try {
      const date = new Date(dateString);
      
      if (isNaN(date.getTime())) {
        return 'Invalid date';
      }

      return new Intl.DateTimeFormat('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short'
      }).format(date);
    } catch (error) {
      return 'Invalid date';
    }
  };

  const getStatusColor = (status?: string) => {
    if (!status) return 'text-gray-400 bg-gray-400/10';
    
    switch (status.toLowerCase()) {
      case 'scheduled':
        return 'text-blue-400 bg-blue-400/10';
      case 'completed':
        return 'text-green-400 bg-green-400/10';
      case 'failed':
        return 'text-red-400 bg-red-400/10';
      case 'running':
        return 'text-purple-400 bg-purple-400/10';
      default:
        return 'text-gray-400 bg-gray-400/10';
    }
  };

  const getStatusIcon = (status?: string) => {
    if (!status) return <Bell className="h-4 w-4" />;
    
    switch (status.toLowerCase()) {
      case 'scheduled':
        return <Clock className="h-4 w-4" />;
      case 'completed':
        return <CheckCircle2 className="h-4 w-4" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <Bell className="h-4 w-4" />;
    }
  };

  const getSlackUrl = (channelId: string) => {
    // This is a placeholder. Replace with actual Slack deep link format
    return `slack://channel?team=${task.parameters.team_id}&id=${channelId.replace('#', '')}`;
  };

  const formatPromptWithContext = (text: string) => {
    // Replace context variables with formatted components
    const formattedText = text.replace(
      /{{([^}]+)}}/g,
      (match, variable) => `<var>${variable.trim()}</var>`
    );

    return (
      <div className="space-y-4">
        <MarkdownText content={formattedText} />
        <div className="flex flex-wrap gap-2 pt-2 border-t border-[#2A3347]">
          {Array.from(text.matchAll(/{{([^}]+)}}/g)).map(([_, variable], index) => (
            <ContextVariable key={index} variable={variable.trim()} />
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="flex items-start gap-3">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#2D3B4E] flex items-center justify-center">
        <Calendar className="h-4 w-4 text-[#7C3AED]" />
      </div>
      <div className="flex-1 space-y-1.5">
        <div className="flex items-center gap-2">
          <div className="text-sm font-medium text-white">Scheduled Task</div>
          <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs ${getStatusColor(task.status)}`}>
            {getStatusIcon(task.status)}
            <span>{task.status}</span>
          </div>
        </div>
        <div className="bg-[#1A1F2E]/50 rounded-lg p-4 space-y-4">
          {/* Destination */}
          <div className="flex items-center gap-2 p-2 rounded-lg bg-[#2A3347]/50 border border-[#3D4B5E]">
            <Slack className="h-5 w-5 text-[#36C5F0]" />
            <div className="flex-1">
              <div className="text-xs text-slate-400">Destination</div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-200 font-medium">
                  {task.parameters.channel_id || '#general'}
                </span>
                <a
                  href={getSlackUrl(task.parameters.channel_id || '#general')}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                >
                  <ExternalLink className="h-3 w-3" />
                  Open in Slack
                </a>
              </div>
            </div>
          </div>

          {/* Scheduled Prompt */}
          <div className="space-y-2">
            <div className="text-xs font-medium text-slate-400">Scheduled Prompt</div>
            <div className="bg-[#2A3347] rounded-lg p-3">
              {formatPromptWithContext(task.parameters.message_text)}
            </div>
          </div>

          {/* Schedule Details */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <div className="text-xs font-medium text-slate-400">Scheduled For</div>
              <div className="flex items-center gap-2 text-sm text-[#E2E8F0]">
                <Clock className="h-4 w-4 text-purple-400" />
                {formatScheduleTime(task.scheduled_time)}
              </div>
            </div>
            {task.parameters.cron_string && (
              <div className="space-y-1">
                <div className="text-xs font-medium text-slate-400">Recurrence</div>
                <div className="flex items-center gap-2 text-sm text-[#E2E8F0]">
                  <Bell className="h-4 w-4 text-purple-400" />
                  <code className="text-xs bg-[#2A3347] px-2 py-1 rounded">
                    {task.parameters.cron_string}
                  </code>
                </div>
              </div>
            )}
          </div>

          {/* Context Variables */}
          <div className="space-y-2">
            <div className="text-xs font-medium text-slate-400">Available Context</div>
            <div className="flex flex-wrap gap-2">
              <ContextVariable variable=".user.email" />
              <ContextVariable variable=".time.scheduled" />
              <ContextVariable variable=".source.slack" />
            </div>
          </div>

          {/* Task ID and Created At */}
          <div className="pt-3 border-t border-[#2A3347] space-y-2">
            <div className="flex items-center justify-between">
              <div className="text-xs text-slate-400">
                Task ID: <span className="font-mono">{task.task_uuid}</span>
              </div>
              <div className="text-xs text-slate-400">
                Created: {new Date(task.created_at).toLocaleString()}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-2 pt-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={handleDelete}
                    className="bg-red-500/10 text-red-400 hover:bg-red-500/20"
                  >
                    <Trash2 className="h-4 w-4" />
                    <span className="ml-1.5">Delete Task</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="top">
                  <p>Delete this scheduled task</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>
      </div>
    </div>
  );
};

export const ScheduledTaskMessage = memo(ScheduledTaskMessageComponent); 