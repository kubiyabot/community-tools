import * as React from 'react';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '../../components/ui/button';
import { ScrollArea } from '../../components/ui/scroll-area';
import { Plus, Loader2, Filter as FilterIcon, Users, Clock, Calendar, MessageSquare, PenSquare, Trash2, Wrench, Check, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { TaskCard } from './TaskCard';
import { TasksTabContentProps, Task } from './types';
import { Badge } from '../../components/ui/badge';
import { useTeammateContext } from '../../MyRuntimeProvider';
import { toast } from '../../components/ui/use-toast';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { Avatar, AvatarImage, AvatarFallback } from '../../components/ui/avatar';
import { format } from 'date-fns';
import { TeammateWithCapabilities } from '@/app/types/teammate';
import { Slack as SlackIcon } from '../../components/icons/slack';
import { Teams as TeamsIcon } from '../../components/icons/teams';
import { GitHub as GitHubIcon } from '../../components/icons/github';
import { Jira as JiraIcon } from '../../components/icons/jira';
import { Bot } from 'lucide-react';

// Import avatar generation function
const AVATAR_IMAGES = [
  'Accountant.png',
  'Chemist-scientist.png',
  'Postman.png',
  'Security-guard.png',
  'builder-1.png',
  'builder-2.png',
  'builder-3.png',
  'capitan-1.png',
  'capitan-2.png',
  'capitan-3.png'
];

function generateAvatarUrl(teammate: { uuid: string; name: string }) {
  const seed = (teammate.uuid + teammate.name).split('').reduce((acc, char, i) => 
    acc + (char.charCodeAt(0) * (i + 1)), 0);
  const randomIndex = Math.abs(Math.sin(seed) * AVATAR_IMAGES.length) | 0;
  return `/images/avatars/${AVATAR_IMAGES[randomIndex]}`;
}

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

export const TasksTabContent: React.FC<TasksTabContentProps> = ({
  tasks: initialTasks,
  isLoading,
  onScheduleTask,
  onEditTask,
  onDeleteTask,
  teammates: initialTeammates = []
}) => {
  const router = useRouter();
  const [selectedTeammate, setSelectedTeammate] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>('all');
  const [isEditing, setIsEditing] = useState(false);

  // Add loading state for teammate data
  const [isTeammateDataLoading, setIsTeammateDataLoading] = useState(true);

  // Add deletion state
  const [deletingTaskId, setDeletingTaskId] = useState<string | null>(null);

  // Load teammate data on mount
  React.useEffect(() => {
    const loadTeammateData = async () => {
      setIsTeammateDataLoading(true);
      try {
        // Wait for teammates data to be fully loaded
        if (initialTeammates.length > 0) {
          setIsTeammateDataLoading(false);
        }
      } catch (error) {
        console.error('Error loading teammate data:', error);
        setIsTeammateDataLoading(false);
      }
    };

    loadTeammateData();
  }, [initialTeammates]);

  // Get task stats
  const stats = {
    total: initialTasks.length,
    byStatus: {
      pending: initialTasks.filter(t => t.status === 'pending').length,
      completed: initialTasks.filter(t => t.status === 'completed').length,
      failed: initialTasks.filter(t => t.status === 'failed').length,
    },
    byTeammate: initialTeammates.reduce((acc, teammate) => ({
      ...acc,
      [teammate.uuid]: initialTasks.filter(t => 
        t.teammate?.uuid === teammate.uuid || 
        t.parameters?.selected_agent === teammate.uuid
      ).length
    }), {} as Record<string, number>),
    recurring: initialTasks.filter(t => t.parameters?.cron_string).length,
  };

  // Map tasks to include teammate info from selected_agent and enhance metadata
  const tasksWithTeammates = initialTasks.map(task => {
    // Normalize teammate ID to lowercase for consistency
    const teammateId = task.parameters?.selected_agent?.toLowerCase();
    
    // Try to find teammate from selected_agent in parameters
    if (teammateId) {
      const teammate = initialTeammates.find(t => t.uuid.toLowerCase() === teammateId);
      if (teammate) {
        return {
          ...task,
          teammate: {
            uuid: teammate.uuid.toLowerCase(), // Ensure UUID is lowercase
            name: teammate.name.toLowerCase(),
            avatar: generateAvatarUrl({
              uuid: teammate.uuid.toLowerCase(), // Use lowercase UUID for avatar
              name: teammate.name.toLowerCase()
            })
          }
        };
      }
    }

    // If task already has teammate info, ensure UUID is lowercase
    if (task.teammate?.uuid) {
      const teammate = initialTeammates.find(t => t.uuid.toLowerCase() === task.teammate?.uuid.toLowerCase());
      if (teammate) {
        return {
          ...task,
          teammate: {
            ...task.teammate,
            uuid: task.teammate.uuid.toLowerCase(),
            avatar: task.teammate.avatar || generateAvatarUrl({
              uuid: task.teammate.uuid.toLowerCase(),
              name: task.teammate.name
            })
          }
        };
      }
    }

    // If no teammate found, return task as is
    return task;
  });

  // Filter tasks with enhanced metadata checks
  const filteredTasks = tasksWithTeammates.filter(task => {
    if (selectedTeammate !== 'all' && 
        task.teammate?.uuid !== selectedTeammate && 
        task.parameters?.selected_agent !== selectedTeammate) return false;
    if (selectedStatus !== 'all' && task.status !== selectedStatus) return false;
    if (selectedTimeframe !== 'all') {
      const taskDate = new Date(task.scheduled_time);
      const now = new Date();
      switch (selectedTimeframe) {
        case 'today':
          return taskDate.toDateString() === now.toDateString();
        case 'week':
          const weekAgo = new Date(now.setDate(now.getDate() - 7));
          return taskDate >= weekAgo;
        case 'month':
          const monthAgo = new Date(now.setMonth(now.getMonth() - 1));
          return taskDate >= monthAgo;
        default:
          return true;
      }
    }
    return true;
  });

  // Sort tasks by scheduled time
  const sortedTasks = [...filteredTasks].sort((a, b) => {
    return new Date(b.scheduled_time).getTime() - new Date(a.scheduled_time).getTime();
  });

  // Get communication stats
  const communicationStats = {
    slack: sortedTasks.filter(t => t.channel_id?.startsWith('#') || t.channel_id?.startsWith('C')).length,
    teams: sortedTasks.filter(t => t.channel_id?.startsWith('teams:')).length,
    other: sortedTasks.filter(t => !t.channel_id || (!t.channel_id.startsWith('#') && !t.channel_id.startsWith('C') && !t.channel_id.startsWith('teams:'))).length
  };

  // Add recurring and communication badges
  const getTaskBadges = (task: Task) => {
    const badges = [];
    
    // Recurring badge
    if (task.parameters?.cron_string) {
      badges.push({
        variant: "outline" as const,
        className: "bg-purple-500/10 text-purple-300 border-purple-500/30",
        icon: <Clock className="h-3 w-3 mr-1" />,
        text: "Recurring"
      });
    }
    
    // Communication badge
    if (task.channel_id) {
      if (task.channel_id.startsWith('#') || task.channel_id.startsWith('C')) {
        badges.push({
          variant: "outline" as const,
          className: "bg-blue-500/10 text-blue-300 border-blue-500/30",
          icon: <MessageSquare className="h-3 w-3 mr-1" />,
          text: task.channel_id.startsWith('#') ? task.channel_id : `Slack Channel ${task.channel_id}`
        });
      } else if (task.channel_id.startsWith('teams:')) {
        badges.push({
          variant: "outline" as const,
          className: "bg-purple-500/10 text-purple-300 border-purple-500/30",
          icon: <MessageSquare className="h-3 w-3 mr-1" />,
          text: task.channel_id.replace('teams:', 'Teams: ')
        });
      }
    }
    
    return badges;
  };

  // Helper function to handle unauthorized responses
  const handleUnauthorizedResponse = async (response: Response) => {
    if (!response) return false;
    
    try {
      const data = await response.json();
      if (response.status === 401 || data.shouldLogout) {
        toast({
          title: "Session Expired",
          description: "Please log in again to continue.",
          variant: "destructive",
        });
        // Redirect to login page
        router.push('/api/auth/login');
        return true;
      }
    } catch (error) {
      console.error('Error parsing response:', error);
    }
    return false;
  };

  const handleScheduleTask = async () => {
    try {
      const taskUuid = crypto.randomUUID();
      const taskId = taskUuid.replace(/-/g, '').substring(0, 32);
      const now = new Date().toISOString();
      
      // Default to first teammate if available
      const defaultTeammate = initialTeammates[0];
      const teammate = defaultTeammate ? {
        uuid: defaultTeammate.uuid,
        name: defaultTeammate.name,
        description: defaultTeammate.description,
        avatar: generateAvatarUrl(defaultTeammate)
      } : undefined;

      const response = await fetch('/api/scheduled_tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_id: taskId,
          task_uuid: taskUuid,
          task_type: 'message',
          status: 'pending',
          scheduled_time: now,
          channel_id: '#general',
          created_at: now,
          updated_at: now,
          parameters: {
            message_text: '',
            selected_agent: teammate?.uuid,
            selected_agent_name: teammate?.name,
            context: {}
          },
          teammate
        })
      });

      if (!response.ok) {
        // Check for unauthorized response
        if (await handleUnauthorizedResponse(response)) {
          return;
        }
        throw new Error('Failed to schedule task');
      }

      const data = await response.json();
      if (onScheduleTask) {
        await onScheduleTask(data);
      }
    } catch (error) {
      console.error('Error scheduling task:', error);
      toast({
        title: "Error",
        description: "Failed to schedule task. Please try again.",
        variant: "destructive",
      });
    }
  };

  // Group tasks by teammate for better organization
  const groupedTasks = sortedTasks.reduce((groups, task) => {
    // Get full teammate info
    const teammateInfo = task.teammate || 
      initialTeammates.find(t => 
        t.uuid.toLowerCase() === (task.parameters?.selected_agent || '').toLowerCase()
      );
    
    // Use teammate UUID as the key for consistent grouping
    const teammateKey = teammateInfo?.uuid?.toLowerCase() || 
      task.parameters?.selected_agent?.toLowerCase() || 
      'unassigned';
    
    if (!groups[teammateKey]) {
      // Find full teammate data with capabilities
      const fullTeammate = initialTeammates.find(t => 
        t.uuid.toLowerCase() === teammateKey
      ) as TeammateWithCapabilities | undefined;

      groups[teammateKey] = {
        name: fullTeammate?.name || teammateInfo?.name || task.parameters?.selected_agent_name || 'Unassigned',
        uuid: teammateKey,
        tasks: [],
        avatar: fullTeammate ? generateAvatarUrl({
          uuid: fullTeammate.uuid,
          name: fullTeammate.name
        }) : undefined,
        description: fullTeammate?.description,
        capabilities: fullTeammate?.capabilities,
        tools: fullTeammate?.tools || [],
        integrations: fullTeammate?.integrations || [],
        sources: fullTeammate?.sources || []
      };
    }
    groups[teammateKey].tasks.push(task);
    return groups;
  }, {} as Record<string, { 
    name: string; 
    uuid: string; 
    tasks: typeof sortedTasks; 
    avatar?: string;
    description?: string;
    capabilities?: TeammateWithCapabilities['capabilities'];
    tools: TeammateWithCapabilities['tools'];
    integrations: TeammateWithCapabilities['integrations'];
    sources: TeammateWithCapabilities['sources'];
  }>);

  // Update the task card styling
  const TaskItem = ({ task }: { task: Task }) => {
    const isDeleting = deletingTaskId === task.task_id;

    const handleDeleteClick = async () => {
      if (!isDeleting) {
        setDeletingTaskId(task.task_id);
        return;
      }

      try {
        if (!task.task_uuid) {
          throw new Error('Task UUID is missing');
        }

        await onDeleteTask?.(task.task_uuid);
        toast({
          title: "Success",
          description: "Task has been successfully deleted",
          duration: 3000,
        });
      } catch (error) {
        console.error('Error deleting task:', error);
        toast({
          variant: "destructive",
          title: "Error",
          description: error instanceof Error ? error.message : "Failed to delete task. Please try again.",
          duration: 5000,
        });
      } finally {
        setDeletingTaskId(null);
      }
    };

    const handleCancelDelete = () => {
      setDeletingTaskId(null);
    };

    return (
      <div 
        className={cn(
          "p-4 rounded-lg border transition-all duration-200",
          "hover:border-slate-600 group/task",
          task.status === 'pending' && "border-yellow-500/20 bg-yellow-500/5 hover:bg-yellow-500/10",
          task.status === 'completed' && "border-green-500/20 bg-green-500/5 hover:bg-green-500/10",
          task.status === 'failed' && "border-red-500/20 bg-red-500/5 hover:bg-red-500/10",
          isDeleting && "border-red-500/50 bg-red-500/10"
        )}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            {/* Status and Communication Method */}
            <div className="flex items-center gap-2 mb-3 flex-wrap">
              <Badge
                variant="outline"
                className={cn(
                  "px-2.5 py-0.5 text-xs font-medium",
                  task.status === 'pending' && "bg-yellow-500/10 text-yellow-300 border-yellow-500/30",
                  task.status === 'completed' && "bg-green-500/10 text-green-300 border-green-500/30",
                  task.status === 'failed' && "bg-red-500/10 text-red-300 border-red-500/30"
                )}
              >
                {task.status.charAt(0).toUpperCase() + task.status.slice(1)}
              </Badge>
              {getTaskBadges(task).map((badge, index) => (
                <Badge
                  key={index}
                  variant={badge.variant}
                  className={cn(
                    "px-2.5 py-0.5 text-xs font-medium",
                    badge.className
                  )}
                >
                  {badge.icon}
                  {badge.text}
                </Badge>
              ))}
            </div>

            {/* Message Preview */}
            <div className="text-sm text-slate-300 line-clamp-2 mb-3 group-hover/task:text-white transition-colors">
              {task.parameters.message_text || <span className="text-slate-500 italic">No message content</span>}
            </div>

            {/* Time Info */}
            <div className="flex items-center gap-4 text-xs text-slate-400">
              <div className="flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5" />
                <span>{format(new Date(task.scheduled_time), 'MMM d, yyyy')}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5" />
                <span>{format(new Date(task.scheduled_time), 'h:mm a')}</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 opacity-80 group-hover/task:opacity-100 transition-opacity">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsEditing(true)}
              className="text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
              disabled={isDeleting}
            >
              <PenSquare className="h-4 w-4" />
            </Button>
            {isDeleting ? (
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleDeleteClick}
                  className="text-red-400 hover:text-red-300 hover:bg-red-950 transition-colors"
                >
                  <Check className="h-4 w-4" />
                  <span className="ml-1">Confirm</span>
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCancelDelete}
                  className="text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
                >
                  <X className="h-4 w-4" />
                  <span className="ml-1">Cancel</span>
                </Button>
              </div>
            ) : (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDeleteClick}
                className="text-red-400 hover:text-red-300 hover:bg-red-950 transition-colors"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  };

  if (isLoading || isTeammateDataLoading) {
    return (
      <div className="h-full flex flex-col">
        <div className="flex items-center justify-between mb-6 animate-pulse">
          <div className="space-y-2">
            <div className="h-6 w-32 bg-slate-800 rounded"></div>
            <div className="h-4 w-48 bg-slate-800/50 rounded"></div>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-9 w-24 bg-slate-800 rounded"></div>
            <div className="h-9 w-32 bg-purple-500/20 rounded"></div>
          </div>
        </div>

        <div className="flex items-center gap-4 pb-4 border-b border-slate-800 animate-pulse">
          <div className="h-10 w-48 bg-slate-800 rounded"></div>
          <div className="h-10 w-48 bg-slate-800 rounded"></div>
        </div>

        <div className="mt-6 space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="p-4 rounded-lg border border-slate-800/50 animate-pulse">
              <div className="flex items-center gap-3 mb-3">
                <div className="h-8 w-8 rounded-full bg-slate-800"></div>
                <div className="space-y-2">
                  <div className="h-4 w-32 bg-slate-800 rounded"></div>
                  <div className="h-3 w-24 bg-slate-800/50 rounded"></div>
                </div>
              </div>
              <div className="space-y-2">
                <div className="h-4 w-3/4 bg-slate-800 rounded"></div>
                <div className="h-4 w-1/2 bg-slate-800/50 rounded"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with enhanced stats */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Scheduled Tasks</h2>
          <p className="text-sm text-slate-400">
            Manage your scheduled messages and recurring tasks
          </p>
          <div className="flex items-center gap-2 mt-2">
            {communicationStats.slack > 0 && (
              <Badge variant="outline" className="bg-blue-500/10 text-blue-300 border-blue-500/30">
                <MessageSquare className="h-3 w-3 mr-1" />
                {communicationStats.slack} Slack
              </Badge>
            )}
            {communicationStats.teams > 0 && (
              <Badge variant="outline" className="bg-purple-500/10 text-purple-300 border-purple-500/30">
                <MessageSquare className="h-3 w-3 mr-1" />
                {communicationStats.teams} Teams
              </Badge>
            )}
            {communicationStats.other > 0 && (
              <Badge variant="outline" className="bg-slate-500/10 text-slate-300 border-slate-500/30">
                <MessageSquare className="h-3 w-3 mr-1" />
                {communicationStats.other} Other
              </Badge>
            )}
            {stats.recurring > 0 && (
              <Badge variant="outline" className="bg-purple-500/10 text-purple-300 border-purple-500/30">
                <Clock className="h-3 w-3 mr-1" />
                {stats.recurring} Recurring
              </Badge>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="bg-purple-500/10 text-purple-300 border-purple-500/30">
            {sortedTasks.length} task{sortedTasks.length !== 1 ? 's' : ''}
          </Badge>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Users className="h-4 w-4 text-slate-400" />
          <Select
            value={selectedTeammate}
            onValueChange={setSelectedTeammate}
          >
            <SelectTrigger className="w-[200px] bg-slate-900/50 border-slate-800">
              <SelectValue placeholder="Filter by teammate" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Teammates</SelectItem>
              {initialTeammates.map((teammate) => (
                <SelectItem 
                  key={teammate.uuid.toLowerCase()} 
                  value={teammate.uuid.toLowerCase()}
                >
                  <div className="flex items-center gap-2">
                    <Avatar className="h-5 w-5">
                      <AvatarImage 
                        src={generateAvatarUrl({
                          uuid: teammate.uuid.toLowerCase(),
                          name: teammate.name
                        })} 
                        alt={teammate.name} 
                      />
                      <AvatarFallback>
                        {teammate.name.charAt(0)}
                      </AvatarFallback>
                    </Avatar>
                    <span>{teammate.name}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-slate-400" />
          <Select
            value={selectedStatus}
            onValueChange={setSelectedStatus}
          >
            <SelectTrigger className="w-[200px] bg-slate-900/50 border-slate-800">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="pending">
                <div className="flex items-center justify-between w-full">
                  <span>Pending</span>
                  <Badge variant="outline" className="bg-yellow-500/10 text-yellow-300 border-yellow-500/30">
                    {stats.byStatus.pending}
                  </Badge>
                </div>
              </SelectItem>
              <SelectItem value="completed">
                <div className="flex items-center justify-between w-full">
                  <span>Completed</span>
                  <Badge variant="outline" className="bg-green-500/10 text-green-300 border-green-500/30">
                    {stats.byStatus.completed}
                  </Badge>
                </div>
              </SelectItem>
              <SelectItem value="failed">
                <div className="flex items-center justify-between w-full">
                  <span>Failed</span>
                  <Badge variant="outline" className="bg-red-500/10 text-red-300 border-red-500/30">
                    {stats.byStatus.failed}
                  </Badge>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-slate-400" />
          <Select
            value={selectedTimeframe}
            onValueChange={setSelectedTimeframe}
          >
            <SelectTrigger className="w-[200px] bg-slate-900/50 border-slate-800">
              <SelectValue placeholder="Filter by timeframe" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Time</SelectItem>
              <SelectItem value="today">Today</SelectItem>
              <SelectItem value="week">Last 7 Days</SelectItem>
              <SelectItem value="month">Last 30 Days</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Enhanced task list with grouping */}
      <ScrollArea className="h-[calc(100vh-280px)]">
        <div className="space-y-8">
          {Object.entries(groupedTasks).map(([teammateKey, group]) => (
            <div key={teammateKey} className="group rounded-lg overflow-hidden">
              {/* Teammate Header */}
              <div className="flex items-start gap-4 px-4 mb-4 sticky top-0 bg-slate-900/95 backdrop-blur-sm py-3 z-10 border-b border-slate-700/50">
                <Avatar className="h-12 w-12 ring-2 ring-offset-2 ring-offset-slate-900 ring-purple-500/30 transition-all duration-300 group-hover:ring-purple-500/50">
                  {group.avatar ? (
                    <AvatarImage src={group.avatar} alt={group.name} />
                  ) : (
                    <AvatarFallback className="bg-purple-500/20 text-purple-200">
                      {group.name.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  )}
                </Avatar>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-lg font-medium text-white group-hover:text-purple-200 transition-colors">
                      {group.name}
                    </h3>
                    <Badge variant="outline" className="bg-purple-500/10 text-purple-300 border-purple-500/30 group-hover:bg-purple-500/20 transition-colors">
                      {group.tasks.length} task{group.tasks.length !== 1 ? 's' : ''}
                    </Badge>
                  </div>
                  
                  {/* Teammate Details */}
                  <div className="space-y-3">
                    {group.description && (
                      <p className="text-sm text-slate-300 group-hover:text-slate-200 transition-colors">
                        {group.description}
                      </p>
                    )}
                    
                    {/* Capabilities */}
                    {group.capabilities && (
                      <div className="flex items-center gap-3 text-xs">
                        {group.capabilities.llm_model && (
                          <Badge 
                            variant="outline" 
                            className="bg-blue-500/10 text-blue-300 border-blue-500/30 px-2.5 py-0.5 group-hover:bg-blue-500/20 transition-colors"
                          >
                            {group.capabilities.llm_model}
                          </Badge>
                        )}
                        {group.capabilities.instruction_type && (
                          <Badge 
                            variant="outline" 
                            className="bg-purple-500/10 text-purple-300 border-purple-500/30 px-2.5 py-0.5 group-hover:bg-purple-500/20 transition-colors"
                          >
                            {group.capabilities.instruction_type}
                          </Badge>
                        )}
                      </div>
                    )}
                    
                    {/* Tools & Integrations */}
                    <div className="flex items-center gap-4 text-xs">
                      {(group.tools?.length ?? 0) > 0 && (
                        <Badge 
                          variant="outline" 
                          className="bg-slate-700/50 text-slate-300 border-slate-600 px-2.5 py-0.5 group-hover:bg-slate-700 transition-colors"
                        >
                          <Wrench className="h-3.5 w-3.5 mr-1.5" />
                          {group.tools?.length || 0} tools
                        </Badge>
                      )}
                      {(group.integrations?.length ?? 0) > 0 && (
                        <div className="flex items-center gap-2">
                          {(group.integrations || []).map((integration, idx) => {
                            const integrationName = typeof integration === 'string' ? integration : integration.name;
                            return (
                              <Badge 
                                key={idx}
                                variant="outline" 
                                className="bg-slate-700/50 text-slate-300 border-slate-600 px-2.5 py-0.5 group-hover:bg-slate-700 transition-colors"
                              >
                                {getIcon(integrationName)}
                                <span className="ml-1.5">{integrationName}</span>
                              </Badge>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Tasks List - More Compact */}
              <div className="space-y-3 pl-16 pr-4 pb-6">
                {group.tasks.map(task => (
                  <TaskItem key={task.task_id} task={task} />
                ))}
              </div>
            </div>
          ))}
          {Object.keys(groupedTasks).length === 0 && (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <div className="text-slate-400 mb-2">No tasks found</div>
              <div className="text-sm text-slate-500">
                {selectedTeammate !== 'all' || selectedStatus !== 'all' || selectedTimeframe !== 'all'
                  ? 'Try adjusting your filters'
                  : 'Schedule a task to get started'}
              </div>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}; 