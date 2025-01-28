"use client";

import { useEffect, useState, useCallback } from 'react';
import { useUser } from '@auth0/nextjs-auth0/client';
import { useRouter } from 'next/navigation';
import { useTeammateContext } from '@/app/MyRuntimeProvider';
import { ChatInput } from '@/app/components/assistant-ui/ChatInput';
import { ChatMessages } from '@/app/components/assistant-ui/ChatMessages';
import { ThreadsSidebar } from '@/app/components/assistant-ui/ThreadsSidebar';
import { SystemMessages } from '@/app/components/assistant-ui/SystemMessages';
import { ToolExecution } from '@/app/components/assistant-ui/ToolExecution';
import { Info, Clock, Calendar } from 'lucide-react';
import { Button } from '@/app/components/ui/button';
import { TeammateDetailsModal } from '@/app/components/shared/TeammateDetailsModal';
import { TaskSchedulingModal } from '@/app/components/TaskSchedulingModal';
import { ScheduledTasksModal } from '@/app/components/ScheduledTasksModal';
import { cn } from '@/lib/utils';
import { toast } from '@/app/components/ui/use-toast';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/app/components/ui/tooltip";
import { format } from "date-fns";

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

export const Chat = () => {
  const { user, isLoading: userLoading } = useUser();
  const router = useRouter();
  const { selectedTeammate, currentState, teammates } = useTeammateContext();
  const [isProcessing, setIsProcessing] = useState(false);
  const [systemMessages, setSystemMessages] = useState<string[]>([]);
  const [isCollectingSystemMessages, setIsCollectingSystemMessages] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [isSchedulingModalOpen, setIsSchedulingModalOpen] = useState(false);
  const [isScheduledTasksModalOpen, setIsScheduledTasksModalOpen] = useState(false);
  const [capabilities, setCapabilities] = useState<any>(null);
  const [teammate, setTeammate] = useState<any>(null);
  const [scheduledTasks, setScheduledTasks] = useState<ScheduledTask[]>([]);
  const [isLoadingTasks, setIsLoadingTasks] = useState(false);

  // Fetch scheduled tasks
  useEffect(() => {
    const fetchScheduledTasks = async () => {
      if (!teammate?.uuid) return;
      
      setIsLoadingTasks(true);
      try {
        const response = await fetch('/api/scheduled_tasks');
        if (!response.ok) {
          throw new Error('Failed to fetch scheduled tasks');
        }
        const tasks = await response.json();
        setScheduledTasks(tasks);
      } catch (error) {
        console.error('Error fetching scheduled tasks:', error);
        toast({
          variant: "destructive",
          title: "Error",
          description: "Failed to load scheduled tasks",
        });
      } finally {
        setIsLoadingTasks(false);
      }
    };

    fetchScheduledTasks();
  }, [teammate?.uuid]);

  // Fetch teammate details and capabilities
  useEffect(() => {
    const fetchDetails = async () => {
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

    if (selectedTeammate) {
      const teammate = teammates.find((t: any) => t.uuid === selectedTeammate);
      setTeammate(teammate);
      fetchDetails();
    }
  }, [selectedTeammate, teammates]);

  // Handle message submission
  const handleSubmit = async (message: string) => {
    if (!selectedTeammate || !currentState?.currentThreadId) {
      setError('Please select a teammate first');
      return;
    }

    if (isProcessing) return;

    setError(null);
    setIsProcessing(true);
    setIsCollectingSystemMessages(true);
    setSystemMessages([]);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          agent_uuid: selectedTeammate,
          session_id: currentState.currentSessionId || currentState.currentThreadId
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      // Handle streaming response...
    } catch (error) {
      console.error('Error sending message:', error);
      setError(error instanceof Error ? error.message : 'Failed to send message');
    } finally {
      setIsProcessing(false);
      setIsCollectingSystemMessages(false);
    }
  };

  // Handle task scheduling with feedback
  const handleScheduleTask = async (taskData: any) => {
    try {
      const response = await fetch('/api/scheduled_tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(taskData),
      });

      if (!response.ok) {
        throw new Error('Failed to schedule task');
      }

      const result = await response.json();
      setScheduledTasks(prev => [...prev, result]);
      setIsSchedulingModalOpen(false);
      toast({
        title: "Task Scheduled",
        description: "Your task has been scheduled successfully.",
      });
    } catch (error) {
      console.error('Error scheduling task:', error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to schedule task. Please try again.",
      });
      throw error;
    }
  };

  // Handle task deletion with feedback
  const handleDeleteTask = async (taskId: string) => {
    try {
      const response = await fetch(`/api/scheduled_tasks?taskId=${taskId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete task');
      }

      setScheduledTasks(prev => prev.filter(task => task.task_id !== taskId));
      toast({
        title: "Task Deleted",
        description: "The scheduled task has been cancelled.",
      });
    } catch (error) {
      console.error('Error deleting task:', error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to delete task. Please try again.",
      });
      throw error;
    }
  };

  // Get preview text for tasks tooltip
  const getTasksPreview = () => {
    if (scheduledTasks.length === 0) return "No scheduled tasks";
    
    const previewTasks = scheduledTasks.slice(0, 3);
    const remainingCount = scheduledTasks.length - 3;
    
    const preview = previewTasks.map(task => (
      `• ${task.parameters.message_text.slice(0, 50)}${task.parameters.message_text.length > 50 ? '...' : ''}\n  ${format(new Date(task.scheduled_time), 'MMM d, h:mm a')}`
    )).join('\n');

    return `${preview}${remainingCount > 0 ? `\n\n+ ${remainingCount} more task${remainingCount > 1 ? 's' : ''}` : ''}`;
  };

  // Show loading state
  if (userLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[#7C3AED] border-t-transparent"></div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className="flex h-full">
      <ThreadsSidebar />
      <div className="flex-1 flex flex-col h-full relative">
        {/* Header with Actions */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-[#2A3347] bg-[#1E293B] z-10">
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-medium text-white">{teammate?.name}</h1>
            <Button
              variant="ghost"
                size="sm"
                className="text-slate-400 hover:text-white p-1 h-auto"
                onClick={() => setIsDetailsModalOpen(true)}
              >
                <Info className="h-4 w-4" />
              </Button>
            <TooltipProvider>
              <Tooltip delayDuration={300}>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      console.log('Opening tasks modal');
                      setIsScheduledTasksModalOpen(true);
                    }}
                    className={cn(
                      "flex items-center gap-2 px-3 py-2 rounded-lg",
                      "bg-blue-500/10 hover:bg-blue-500/20",
                      "text-blue-400 hover:text-blue-300",
                      "transition-all duration-200",
                      "border border-blue-500/20 hover:border-blue-500/30",
                      "cursor-pointer"
                    )}
                  >
                    <Calendar className="h-4 w-4" />
                    <span>Tasks</span>
                    {scheduledTasks.length > 0 && (
                      <div className="flex items-center justify-center min-w-[20px] h-5 rounded-full bg-blue-500 text-white text-xs font-medium px-1.5">
                        {scheduledTasks.length}
                      </div>
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent 
                  side="bottom" 
                  className="max-w-[400px] p-3 bg-[#1E293B] border-[#2D3B4E] text-slate-200"
                >
                  <div className="space-y-1 whitespace-pre-line text-sm">
                    <p className="font-medium mb-2">Scheduled Tasks:</p>
                    {getTasksPreview()}
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 overflow-hidden relative">
          <div className="absolute inset-0 overflow-y-auto">
            <ChatMessages 
              messages={currentState?.threads[currentState.currentThreadId]?.messages || []} 
              isCollectingSystemMessages={isCollectingSystemMessages}
              systemMessages={systemMessages}
              capabilities={capabilities}
              teammate={teammate}
              showTeammateDetails={() => setIsDetailsModalOpen(true)}
              onStarterCommand={handleSubmit}
              onScheduleTask={() => setIsSchedulingModalOpen(true)}
            />
          </div>
        </div>

        {/* Chat Input */}
        <div className="border-t border-[#2A3347] bg-[#1E293B] z-10">
          <ChatInput onSubmit={handleSubmit} isDisabled={isProcessing} />
        </div>

        {/* Modals */}
        <TeammateDetailsModal
          isOpen={isDetailsModalOpen}
          onClose={() => setIsDetailsModalOpen(false)}
          teammate={teammate}
          capabilities={capabilities}
        />

        <TaskSchedulingModal
          isOpen={isSchedulingModalOpen}
          onClose={() => setIsSchedulingModalOpen(false)}
          teammate={teammate}
          onSchedule={handleScheduleTask}
        />

        <ScheduledTasksModal
          isOpen={isScheduledTasksModalOpen}
          onClose={() => setIsScheduledTasksModalOpen(false)}
          tasks={scheduledTasks}
          onDelete={handleDeleteTask}
          isLoading={isLoadingTasks}
          teammate={teammate}
        />
      </div>
    </div>
  );
}; 