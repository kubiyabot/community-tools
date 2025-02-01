"use client";

import { useEffect, useState, useCallback, useMemo } from 'react';
import { useUser } from '@auth0/nextjs-auth0/client';
import { useRouter } from 'next/navigation';
import { useTeammateContext } from '../../MyRuntimeProvider';
import { ChatInput } from './ChatInput';
import { ChatMessages } from './ChatMessages';
import { ThreadsSidebar } from './ThreadsSidebar';
import { SystemMessages } from './SystemMessages';
import { ToolExecution } from './ToolExecution';
import { Info, Clock, Calendar, CheckCircle2, RotateCcw, AlertCircle, ChevronRight, ListTodo, Trello, Webhook } from 'lucide-react';
import { Button } from '@/app/components/button';
import { TeammateDetailsModal } from '../shared/TeammateDetailsModal';
import { TaskSchedulingModal } from '../TaskSchedulingModal';
import { cn } from '@/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../../components/ui/tooltip";
import { format, isToday } from "date-fns";
import { toast } from "@/app/components/ui/use-toast";
import { ScheduledTasksModal } from '../ScheduledTasksModal';
import { Badge } from "@/app/components/ui/badge";
import { MessageSquare } from 'lucide-react';
import { ActivityHub } from '../activity/ActivityHub';
import { Task } from '../activity/types';
import { TeammateInfo } from '@/app/types/teammate';
import type { TeammateDetails } from '@/app/components/shared/teammate-details/types';

interface ThreadInfo {
  id: string;
  title: string;
  lastMessage?: string;
  createdAt: string;
  updatedAt: string;
  teammateId: string;
}

interface MessageContent {
  type: string;
  text: string;
}

interface Teammate {
  uuid: string;
  name: string;
  description?: string;
}

interface TeammateState {
  sessions: any[];
  currentThreadId?: string;
  currentSessionId?: string;
  threads: Record<string, {
    messages: Array<{
      id: string;
      role: string;
      content: Array<{ type: string; text: string }>;
      createdAt: Date;
      metadata?: {
        custom?: {
          isSystemMessage?: boolean;
        };
        activeTool?: string;
      };
    }>;
    lastMessageId?: string;
    metadata: {
      teammateId: string;
      createdAt: string;
      updatedAt: string;
      title?: string;
      preview?: string;
      activeTool?: string;
    };
  }>;
}

interface ToolCall {
  type: 'tool_init' | 'tool_output';
  id: string;
  name?: string;
  arguments?: Record<string, unknown>;
  message?: string;
  timestamp?: string;
  tool_description?: string;
  status?: string;
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
    context?: string;
  };
  status: string;
  created_at: string;
  updated_at: string | null;
}

// Add new helper functions for task stats
const getTaskStats = (tasks: ScheduledTask[]) => {
  const now = new Date();
  return {
    total: tasks.length,
    completed: tasks.filter(task => task.status === 'completed').length,
    pending: tasks.filter(task => task.status === 'scheduled').length,
    recurring: tasks.filter(task => !!task.parameters.cron_string).length,
    today: tasks.filter(task => {
      const taskDate = new Date(task.scheduled_time);
      return isToday(taskDate) && task.status === 'scheduled';
    }).length,
    sources: {
      chat: tasks.filter(task => task.task_type === 'chat_activity').length,
      jira: tasks.filter(task => task.task_type === 'jira_ticket').length,
      webhook: tasks.filter(task => task.task_type === 'webhook').length
    }
  };
};

// Add interface for tool arguments
interface ToolArguments {
  [key: string]: unknown;
}

// Add task mapping function
const mapScheduledTasksToTasks = (scheduledTasks: ScheduledTask[]): Task[] => {
  return scheduledTasks.map(task => ({
    ...task,
    status: task.status as "completed" | "scheduled" | "pending" | "failed",
    task_type: task.task_type || 'chat_activity'
  }));
};

interface ScheduleTaskPayload {
  schedule_time: string;
  channel_id: string;
  task_description: string;
  selected_agent: string;
  cron_string: string;
}

interface ScheduleTaskResult {
  task_id: string;
  task_uuid: string;
}

export const Chat = () => {
  const { user, isLoading: userLoading } = useUser();
  const router = useRouter();
  const { selectedTeammate, currentState, switchThread, teammates, setTeammateState } = useTeammateContext();
  const [isProcessing, setIsProcessing] = useState(false);
  const [systemMessages, setSystemMessages] = useState<string[]>([]);
  const [isCollectingSystemMessages, setIsCollectingSystemMessages] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [capabilities, setCapabilities] = useState<any>(null);
  const [teammate, setTeammate] = useState<any>(null);
  const [isSchedulingModalOpen, setIsSchedulingModalOpen] = useState(false);
  const [scheduledTasks, setScheduledTasks] = useState<ScheduledTask[]>([]);
  const [isScheduledTasksModalOpen, setIsScheduledTasksModalOpen] = useState(false);
  const [isLoadingTasks, setIsLoadingTasks] = useState(false);
  const [schedulingInitialData, setSchedulingInitialData] = useState<{
    description?: string;
    slackTarget?: string;
    scheduleType?: 'quick' | 'custom';
    repeatOption?: string;
    date?: Date;
  } | undefined>(undefined);
  const [isActivityHubOpen, setIsActivityHubOpen] = useState(false);
  const [selectedTeammateForDetails, setSelectedTeammateForDetails] = useState<TeammateDetails | null>(null);
  const [isTeammateDetailsOpen, setIsTeammateDetailsOpen] = useState(false);

  // Get task stats
  const taskStats = useMemo(() => getTaskStats(scheduledTasks), [scheduledTasks]);

  // Track system messages
  useEffect(() => {
    if (!currentState?.currentThreadId) return;
    const thread = currentState.threads[currentState.currentThreadId];
    if (!thread?.messages) return;
    
    const newSystemMessages = thread.messages
      .filter(msg => msg.role === 'system' || msg.metadata?.custom?.isSystemMessage)
      .map(msg => {
        const textContent = msg.content.find((c: MessageContent) => c.type === 'text' && 'text' in c);
        return textContent && 'text' in textContent ? textContent.text : '';
      })
      .filter(Boolean);

    if (newSystemMessages.length > 0 && JSON.stringify(newSystemMessages) !== JSON.stringify(systemMessages)) {
      setSystemMessages(newSystemMessages);
    }
  }, [currentState?.currentThreadId, currentState?.threads, systemMessages]);

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
      const teammate = teammates.find((t: Teammate) => t.uuid === selectedTeammate);
      setTeammate(teammate);
      fetchDetails();
    }
  }, [selectedTeammate, teammates]);

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

  const handleSubmit = async (message: string) => {
    if (!selectedTeammate || !currentState?.currentThreadId) {
      setError('Please select a teammate first');
      return;
    }

    if (isProcessing) return;

    // Add message counter for unique IDs
    let messageCounter = 0;
    const generateUniqueId = (prefix: string) => `${prefix}_${Date.now()}_${messageCounter++}`;

    setError(null);
    setIsProcessing(true);
    setIsCollectingSystemMessages(true);
    setSystemMessages([]); // Reset system messages
    
    try {
      const threadId = currentState.currentThreadId;
      
      // Immediately add user message to the UI
      const userMessage = {
        id: generateUniqueId('user'),
        role: 'user',
        content: [{ type: 'text', text: message }],
        createdAt: new Date()
      };

      // Get current thread state
      const currentThread = currentState.threads[threadId] || {
        messages: [],
        metadata: {
          teammateId: selectedTeammate,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          title: message.slice(0, 50) + (message.length > 50 ? '...' : '') // Add title for new threads
        }
      };

      // Update thread with user message
      const updatedThread = {
        ...currentThread,
        messages: [...currentThread.messages, userMessage],
        metadata: {
          ...currentThread.metadata,
          updatedAt: new Date().toISOString()
        }
      };

      // Update state with user message
      const initialUpdatedState = {
        ...currentState,
        threads: {
          ...currentState.threads,
          [threadId]: updatedThread
        }
      };
      setTeammateState(selectedTeammate, initialUpdatedState);

      // Send message to backend
      const response = await fetch(`/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          agent_uuid: selectedTeammate,
          session_id: currentState.currentSessionId || threadId
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.details || errorData.error || 'Failed to send message');
      }

      // Handle the streaming response
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response stream available');
      }

      let collectedSystemMessages: string[] = [];
      let currentMessages = [...updatedThread.messages]; // Track messages locally
      let partialMessage = ''; // Track partial message
      let currentAssistantMessageId: string | null = null;
      let lastEventId: string | null = null;

      // Read the stream
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          // Process the chunks
          const text = new TextDecoder().decode(value);
          const lines = text.split('\n');
          
          for (const line of lines) {
            if (!line.trim() || !line.startsWith('data: ')) continue;
            
            try {
              const eventData = JSON.parse(line.slice(6));
              console.log('[Chat] Processing event:', eventData);
              
              // Handle different event types
              switch (eventData.type) {
                case 'msg':
                case 'assistant':
                  if (eventData.message) {
                    // If this is a new message or a different message ID
                    if (!currentAssistantMessageId || lastEventId !== eventData.id) {
                      currentAssistantMessageId = eventData.id || generateUniqueId('assistant');
                      lastEventId = eventData.id;
                      
                      // Create new message or update existing one
                      const existingMessageIndex = currentMessages.findIndex(msg => msg.id === currentAssistantMessageId);
                      if (existingMessageIndex === -1) {
                        // Create new message
                        const assistantMessage = {
                          id: currentAssistantMessageId,
                          role: 'assistant',
                          content: [{ type: 'text', text: eventData.message }],
                          createdAt: new Date()
                        };
                        currentMessages = [...currentMessages, assistantMessage];
                      } else {
                        // Update existing message with complete new content
                        currentMessages = currentMessages.map((msg, index) => 
                          index === existingMessageIndex
                            ? {
                                ...msg,
                                content: [{ type: 'text', text: eventData.message }]
                              }
                            : msg
                        );
                      }
                    } else {
                      // Update existing message with complete content
                      currentMessages = currentMessages.map(msg => 
                        msg.id === currentAssistantMessageId
                          ? {
                              ...msg,
                              content: [{ type: 'text', text: eventData.message }]
                            }
                          : msg
                      );
                    }

                    // If there's an active tool, mark it as complete
                    if (currentThread.metadata.activeTool) {
                      const toolMessage = [...currentMessages].reverse().find(msg => 
                        msg.tool_calls?.some((call: ToolCall) => 
                          call.name === currentThread.metadata.activeTool
                        )
                      );

                      if (toolMessage) {
                        currentMessages = currentMessages.map(msg => 
                          msg.id === toolMessage.id
                            ? {
                                ...msg,
                                tool_calls: msg.tool_calls?.map((call: ToolCall) => ({
                                  ...call,
                                  status: 'complete'
                                }))
                              }
                            : msg
                        );
                      }

                      // Clear active tool
                      currentThread.metadata.activeTool = undefined;
                    }
                  }
                  break;
                case 'system_message':
                  if (eventData.messages && Array.isArray(eventData.messages)) {
                    // Handle array of system messages
                    const uniqueSystemMessages = eventData.messages.filter((message: string) => 
                      !currentMessages.some(msg => 
                        msg.role === 'system' && 
                        msg.content[0]?.text === message
                      )
                    );

                    uniqueSystemMessages.forEach((message: string) => {
                      const systemMessage = {
                        id: generateUniqueId('system'),
                        role: 'system',
                        content: [{ type: 'text', text: message }],
                        createdAt: new Date(),
                        metadata: { custom: { isSystemMessage: true } }
                      };
                      currentMessages = [...currentMessages, systemMessage];
                      collectedSystemMessages = [...collectedSystemMessages, message];
                      setSystemMessages(prev => [...prev, message]);

                      // Add an assistant message for task completion
                      if (message.includes('✅')) {
                        const assistantMessage = {
                          id: generateUniqueId('assistant'),
                          role: 'assistant',
                          content: [{ type: 'text', text: 'Task completed successfully! You can delete this task or schedule it for later.' }],
                          createdAt: new Date()
                        };
                        currentMessages = [...currentMessages, assistantMessage];
                      }
                    });
                  }
                  break;
                case 'tool':
                  if (eventData.message) {
                    // Extract tool information from the message more robustly
                    const toolMatch = eventData.message.match(/Tool: ([\w-]+)\nArguments: ({[\s\S]*})/);
                    if (toolMatch) {
                      const [_, toolName, argsString] = toolMatch;
                      let toolArgs: ToolArguments;
                      try {
                        // Clean up the args string before parsing
                        const cleanArgsString = argsString.trim();
                        toolArgs = JSON.parse(cleanArgsString);
                      } catch (e) {
                        console.error('Failed to parse tool arguments:', e);
                        // Try to extract just the JSON part
                        try {
                          const jsonStart = eventData.message.indexOf('{');
                          const jsonEnd = eventData.message.lastIndexOf('}') + 1;
                          if (jsonStart !== -1 && jsonEnd !== -1) {
                            const jsonString = eventData.message.slice(jsonStart, jsonEnd);
                            toolArgs = JSON.parse(jsonString);
                          } else {
                            toolArgs = {};
                          }
                        } catch (e) {
                          console.error('Failed second attempt to parse tool arguments:', e);
                          toolArgs = {};
                        }
                      }

                      const toolId = eventData.id || generateUniqueId('tool');
                      
                      // Check if we already have a message for this tool
                      const existingToolMessage = currentMessages.find(msg => 
                        msg.tool_calls?.some((call: ToolCall) => call.id === toolId)
                      );

                      if (existingToolMessage) {
                        // Only update if the message content has changed
                        const currentToolCall = existingToolMessage.tool_calls?.[0];
                        if (currentToolCall?.message !== eventData.message) {
                          currentMessages = currentMessages.map(msg => 
                            msg.id === existingToolMessage.id
                              ? {
                                  ...msg,
                                  tool_calls: [{
                                    ...msg.tool_calls[0],
                                    name: toolName,
                                    arguments: toolArgs,
                                    message: eventData.message,
                                    status: 'running'
                                  }]
                                }
                              : msg
                          );
                        }
                      } else {
                        // Create new tool message
                        const toolMessage = {
                          id: toolId,
                          role: 'assistant',
                          content: [],
                          tool_calls: [{
                            type: 'tool_init',
                            id: toolId,
                            name: toolName,
                            arguments: toolArgs,
                            message: eventData.message,
                            timestamp: new Date().toISOString(),
                            status: 'running'
                          }],
                          createdAt: new Date(),
                          metadata: {
                            activeTool: toolName
                          }
                        };
                        currentMessages = [...currentMessages, toolMessage];
                      }

                      // Update thread metadata with active tool
                      currentThread.metadata.activeTool = toolName;
                    }
                  }
                  break;
                case 'tool_output':
                  if (eventData.message) {
                    const toolId = eventData.id || currentThread.metadata.activeTool;
                    
                    // Find the last tool message to update
                    const toolMessage = [...currentMessages].reverse().find(msg => 
                      msg.tool_calls?.some((call: ToolCall) => 
                        call.id === toolId || 
                        call.name === currentThread.metadata.activeTool ||
                        msg.metadata?.activeTool === currentThread.metadata.activeTool
                      )
                    );
                    
                    if (toolMessage) {
                      // Check if this is a completion message or if we received a regular message after
                      const isComplete = eventData.message.includes('✅') || 
                        eventData.status === 'complete' || 
                        eventData.type === 'msg' || 
                        eventData.type === 'assistant';

                      // Only update if the message content has actually changed
                      const currentOutput = toolMessage.tool_calls?.[0]?.output;
                      const currentMessage = toolMessage.tool_calls?.[0]?.message;
                      
                      if (currentOutput !== eventData.message || currentMessage !== eventData.message) {
                        // Update existing tool message
                        currentMessages = currentMessages.map(msg => 
                          msg.id === toolMessage.id
                            ? {
                                ...msg,
                                tool_calls: [{
                                  ...msg.tool_calls[0],
                                  output: eventData.message,
                                  message: eventData.message,
                                  timestamp: new Date().toISOString(),
                                  status: isComplete ? 'complete' : 'running'
                                }]
                              }
                            : msg
                        );
                      }

                      // Clear active tool if complete
                      if (isComplete) {
                        currentThread.metadata.activeTool = undefined;
                      }
                    }
                  }
                  break;
              }

              // Update teammate state with latest messages immediately after each event
              const updatedState = {
                ...currentState,
                threads: {
                  ...currentState.threads,
                  [threadId]: {
                    ...currentThread,
                    messages: currentMessages,
                    metadata: {
                      ...currentThread.metadata,
                      updatedAt: new Date().toISOString()
                    }
                  }
                }
              };
              setTeammateState(selectedTeammate, updatedState);
            } catch (error) {
              console.error('[Chat] Error processing event:', error);
            }
          }
        }
      } finally {
        reader.releaseLock();
        // Reset message tracking at the end
        currentAssistantMessageId = null;
        partialMessage = '';
      }
      
    } catch (error) {
      console.error('Error sending message:', error);
      setError(error instanceof Error ? error.message : 'Failed to send message. Please try again.');
    } finally {
      setIsProcessing(false);
      setIsCollectingSystemMessages(false);
    }
  };

  const handleScheduleTask = async (taskData: ScheduleTaskPayload): Promise<ScheduleTaskResult> => {
    try {
      const response = await fetch('/api/scheduled_tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(taskData)
      });

      if (!response.ok) {
        throw new Error('Failed to schedule task');
      }

      const result = await response.json();
      setScheduledTasks(prev => [...prev, result]);

      // Return the expected ScheduleTaskResult
      return {
        task_id: result.task_id,
        task_uuid: result.task_uuid
      };
    } catch (error) {
      console.error('Error scheduling task:', error);
      throw error;
    }
  };

  const handleScheduleSimilar = (initialData: {
    description: string;
    slackTarget: string;
    scheduleType: 'quick' | 'custom';
    repeatOption: string;
  }) => {
    setIsScheduledTasksModalOpen(false);
    setIsSchedulingModalOpen(true);
    setSchedulingInitialData({
      description: initialData.description,
      slackTarget: initialData.slackTarget,
      scheduleType: initialData.scheduleType,
      repeatOption: initialData.repeatOption,
      date: new Date() // Set a default date
    });
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

  const handleTeammateClick = (teammate: TeammateInfo) => {
    if (!teammate) return;
    const teammateDetails = {
      ...teammate,
      status: teammate.status === 'busy' ? 'active' : teammate.status || 'active'
    } as TeammateDetails;
    setSelectedTeammateForDetails(teammateDetails);
    setIsTeammateDetailsOpen(true);
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
          </div>
          
          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsSchedulingModalOpen(true)}
              className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-lg",
                "bg-purple-500/10 hover:bg-purple-500/20",
                "text-purple-400 hover:text-purple-300",
                "transition-all duration-200",
                "border border-purple-500/20 hover:border-purple-500/30",
                "cursor-pointer"
              )}
            >
              <ListTodo className="h-4 w-4" />
              <span>Assign Task</span>
            </Button>
            
            <TooltipProvider>
              <Tooltip delayDuration={0}>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsActivityHubOpen(true)}
                    className={cn(
                      "flex items-center gap-2 px-3 py-2 rounded-lg",
                      "bg-blue-500/10 hover:bg-blue-500/20",
                      "text-blue-400 hover:text-blue-300",
                      "transition-all duration-200",
                      "border border-blue-500/20 hover:border-blue-500/30",
                      "cursor-pointer"
                    )}
                  >
                    <div className="flex items-center gap-2 flex-1">
                      <Calendar className="h-4 w-4" />
                      <span className="flex-1 text-left">Tasks</span>
                      {scheduledTasks.length > 0 && (
                        <div className="flex items-center justify-center min-w-[20px] h-5 rounded-full bg-blue-500 text-white text-xs font-medium px-1.5">
                          {scheduledTasks.length}
                        </div>
                      )}
                    </div>
                  </Button>
                </TooltipTrigger>
                <TooltipContent 
                  side="bottom" 
                  className="max-w-[300px] p-4 bg-[#1E293B] border-[#2D3B4E] text-slate-200"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between gap-2 text-sm font-medium">
                      <span className="text-slate-200">Task Summary</span>
                      <Badge variant="outline" className="border-blue-500/30 text-blue-400">
                        {taskStats.total} total
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="flex items-center gap-2 text-sm">
                        <Clock className="h-3.5 w-3.5 text-blue-400" />
                        <span className="text-slate-400">{taskStats.pending} pending</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <CheckCircle2 className="h-3.5 w-3.5 text-green-400" />
                        <span className="text-slate-400">{taskStats.completed} completed</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <RotateCcw className="h-3.5 w-3.5 text-purple-400" />
                        <span className="text-slate-400">{taskStats.recurring} recurring</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <AlertCircle className="h-3.5 w-3.5 text-yellow-400" />
                        <span className="text-slate-400">{taskStats.today} today</span>
                      </div>
                    </div>
                    <div className="pt-2 border-t border-[#2D3B4E]">
                      <div className="text-xs font-medium text-slate-400 mb-2">Task Sources</div>
                      <div className="grid grid-cols-3 gap-2">
                        <div className="flex items-center gap-1.5 text-xs">
                          <MessageSquare className="h-3 w-3 text-purple-400" />
                          <span className="text-slate-400">{taskStats.sources.chat}</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-xs">
                          <Trello className="h-3 w-3 text-blue-400" />
                          <span className="text-slate-400">{taskStats.sources.jira}</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-xs">
                          <Webhook className="h-3 w-3 text-green-400" />
                          <span className="text-slate-400">{taskStats.sources.webhook}</span>
                        </div>
                      </div>
                    </div>
                    {taskStats.total > 0 && (
                      <div className="pt-2 mt-2 border-t border-[#2D3B4E] text-xs text-slate-400">
                        Click to view and manage all tasks
                      </div>
                    )}
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
          onCloseAction={async () => {
            setIsDetailsModalOpen(false);
          }}
          teammate={teammate}
        />

        <TaskSchedulingModal
          isOpen={isSchedulingModalOpen}
          onClose={() => setIsSchedulingModalOpen(false)}
          teammate={teammate}
          onSchedule={handleScheduleTask}
          initialData={schedulingInitialData}
        />

        <ScheduledTasksModal
          isOpen={isScheduledTasksModalOpen}
          onClose={() => setIsScheduledTasksModalOpen(false)}
          tasks={scheduledTasks.map(task => ({
            ...task,
            status: task.status as 'pending' | 'completed' | 'failed' | 'scheduled' | undefined
          }))}
          onDelete={handleDeleteTask}
          isLoading={isLoadingTasks}
          teammate={teammate ? {
            uuid: teammate.uuid,
            name: teammate.name,
            email: teammate.email
          } : undefined}
          onScheduleSimilar={handleScheduleSimilar}
        />

        <ActivityHub
          isOpen={isActivityHubOpen}
          onClose={() => setIsActivityHubOpen(false)}
          tasks={mapScheduledTasksToTasks(scheduledTasks)}
          webhooks={[]}
          isLoading={isLoadingTasks}
          teammates={teammates}
        />
      </div>
    </div>
  );
};