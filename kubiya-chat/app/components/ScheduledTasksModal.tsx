import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/app/components/ui/dialog';
import { Button } from '@/app/components/ui/button';
import { Clock, Trash2, Slack, MessageSquare, X, Calendar, RotateCcw, Filter, User, Check, AlertCircle, ChevronRight, Webhook, GitBranch, Trello, Cloud, Hash, RefreshCcw, Search } from 'lucide-react';
import { format, isToday, isTomorrow, isThisWeek, isThisMonth, isAfter, isBefore } from 'date-fns';
import { toast } from '@/app/components/ui/use-toast';
import { cn } from '@/lib/utils';
import { useState, useMemo, useEffect, useRef } from 'react';
import { useEntity } from '@/app/providers/EntityProvider';
import { useTeammateContext } from '@/app/MyRuntimeProvider';
import { Badge } from '@/app/components/ui/badge';
import type { EntityMetadata } from '@/app/types/user';
import { TeammateDetailsModal } from '@/app/components/shared/TeammateDetailsModal';
import type { TeammateDetails as TeammateDetailsType } from '@/app/components/shared/teammate-details/types';
import { generateAvatarUrl } from '@/app/components/TeammateSelector';
import type { TeammateInfo } from '@/app/types/teammate';
import { type BaseIntegration } from '@/app/components/shared/teammate-details/types';
import { Input } from '@/app/components/ui/input';
import { useOnClickOutside } from '@/app/hooks/use-on-click-outside';

interface ScheduledTask {
  id: string;
  task_id: string;
  task_uuid: string;
  task_type: string;
  scheduled_time: string;
  channel_id: string;
  status?: 'pending' | 'completed' | 'failed' | 'scheduled';
  teammate?: TeammateDetailsType;
  parameters: {
    message_text: string;
    team_id: string;
    user_email: string;
    cron_string?: string;
    selected_agent?: string;
    selected_agent_name?: string;
    slack_info?: {
      channel_id: string;
      channel_name: string;
      channel_link: string;
      tooltips: {
        channel_context: string;
        bi_directional: string;
        direct_commands: string;
      };
    };
  };
  created_at?: string;
  updated_at?: string | null;
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

type TimeFilter = 'all' | 'today' | 'tomorrow' | 'this-week' | 'this-month' | 'upcoming' | 'past';
type StatusFilter = 'all' | 'pending' | 'completed' | 'recurring';

interface QuickTeammateSwitchProps {
  teammates: TeammateInfo[];
  currentTeammate: TeammateInfo | null;
  onSelect: (teammate: TeammateInfo) => void;
  onClose: () => void;
}

function QuickTeammateSwitch({ teammates, currentTeammate, onSelect, onClose }: QuickTeammateSwitchProps) {
  const [search, setSearch] = useState('');
  const switchRef = useRef<HTMLDivElement>(null);
  
  useOnClickOutside(switchRef, onClose);
  
  const filteredTeammates = useMemo(() => {
    return teammates.filter(teammate => 
      teammate.name?.toLowerCase().includes(search.toLowerCase()) ||
      teammate.email?.toLowerCase().includes(search.toLowerCase())
    );
  }, [teammates, search]);

  return (
    <div ref={switchRef} className="absolute top-full right-0 mt-2 w-[300px] bg-[#1A1F2E] border border-[#2D3B4E] rounded-lg shadow-xl z-50">
      <div className="p-3 border-b border-[#2D3B4E]">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search teammates..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 bg-[#0F172A] border-[#2D3B4E] text-slate-200 placeholder:text-slate-400"
          />
        </div>
      </div>
      
      <div className="max-h-[300px] overflow-y-auto">
        {filteredTeammates.map((teammate) => (
          <button
            key={teammate.uuid}
            onClick={() => {
              onSelect(teammate);
              onClose();
            }}
            className="w-full px-3 py-2 flex items-center gap-3 hover:bg-purple-500/10 transition-colors group"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500/10 to-purple-500/5 border border-purple-500/20 flex items-center justify-center">
              <img
                src={generateAvatarUrl({ 
                  uuid: teammate.uuid, 
                  name: teammate.name || 'Unknown'
                })}
                alt={teammate.name || 'Unknown'}
                className="w-6 h-6 rounded object-cover"
              />
            </div>
            <div className="flex-1 text-left">
              <div className="text-sm font-medium text-slate-200 group-hover:text-purple-400">
                {teammate.name || 'Unknown'}
              </div>
              {teammate.email && (
                <div className="text-xs text-slate-400">{teammate.email}</div>
              )}
            </div>
            {currentTeammate?.uuid === teammate.uuid && (
              <Check className="h-4 w-4 text-purple-400" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

// Helper function to convert TeammateInfo to TeammateDetails
function convertToTeammateDetails(teammate: TeammateInfo): TeammateDetailsType {
  let status: 'active' | 'inactive' | 'error' | undefined = undefined;
  if (teammate.status) {
    if (teammate.status === 'busy' || teammate.status === 'active') {
      status = 'active';
    } else if (teammate.status === 'inactive') {
      status = 'inactive';
    }
  }

  return {
    id: teammate.uuid,
    uuid: teammate.uuid,
    name: teammate.name || '',
    description: teammate.context || '',
    avatar_url: teammate.avatar || '',
    status,
    metadata: {
      created_at: new Date().toISOString(),
      last_updated: new Date().toISOString(),
      tools_count: 0,
      integrations_count: teammate.integrations?.length || 0,
      sources_count: 0
    },
    integrations: teammate.integrations?.map(i => {
      const integrationType = typeof i === 'string' ? 'custom' : (i.integration_type || 'custom');
      return {
        id: typeof i === 'string' ? i : i.name,
        name: typeof i === 'string' ? i : i.name,
        type: integrationType,
        integration_type: integrationType,
        auth_type: 'global',
        managed_by: teammate.uuid,
        configs: [],
        kubiya_metadata: {
          created_at: new Date().toISOString(),
          last_updated: new Date().toISOString()
        }
      } as BaseIntegration;
    }) || []
  };
}

// Helper function to convert TeammateDetails to TeammateInfo
function convertToTeammateInfo(teammate: TeammateDetailsType): TeammateInfo {
  let status: 'active' | 'inactive' | 'busy' | undefined = undefined;
  if (teammate.status) {
    if (teammate.status === 'error') {
      status = 'inactive';
    } else {
      status = teammate.status;
    }
  }

  return {
    uuid: teammate.id,
    name: teammate.name,
    context: teammate.description,
    avatar: teammate.avatar_url,
    status
  };
}

// Add the normalizeName helper function from TasksTabContent
function normalizeName(name: string): string {
  return name.toLowerCase()
    .replace(/[^a-z0-9]/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '');
}

// Update the findTeammate function with proper typing
function findTeammate(teammates: TeammateInfo[], nameOrId: string | undefined | null): TeammateInfo | undefined {
  if (!nameOrId) {
    console.log('No nameOrId provided to findTeammate');
    return undefined;
  }
  
  console.log('Searching for teammate:', {
    nameOrId,
    availableTeammates: teammates.map(t => ({ uuid: t.uuid, name: t.name }))
  });

  // First try direct UUID match
  const byUuid = teammates.find(t => t.uuid === nameOrId);
  if (byUuid) {
    console.log('Found teammate by UUID match:', {
      uuid: byUuid.uuid,
      name: byUuid.name
    });
    return byUuid;
  }

  // Then try normalized name match
  const normalizedSearch = normalizeName(nameOrId);
  console.log('Trying normalized name match:', {
    normalizedSearch,
    originalNameOrId: nameOrId
  });

  const byName = teammates.find(t => 
    normalizeName(t.name || '') === normalizedSearch ||
    normalizeName(t.uuid) === normalizedSearch
  );

  if (byName) {
    console.log('Found teammate by normalized name:', {
      uuid: byName.uuid,
      name: byName.name,
      normalizedName: normalizeName(byName.name || '')
    });
    return byName;
  }

  console.log('No teammate found for:', {
    nameOrId,
    normalizedSearch
  });
  return undefined;
}

// Update the TeammateDetails type to include uuid
interface TeammateDetailsWithUUID extends Omit<TeammateDetailsType, 'uuid'> {
  uuid: string;
}

// Update the group type in the groupedTasks
type TeammateGroup = {
  teammate: TeammateDetailsWithUUID | null;
  tasks: ScheduledTask[];
};

// Add type guard for TeammateDetailsType
function isTeammateDetails(teammate: any): teammate is TeammateDetailsType {
  return teammate && 'id' in teammate;
}

// Add type guard for TeammateInfo
function isTeammateInfo(teammate: any): teammate is TeammateInfo {
  return teammate && 'uuid' in teammate;
}

export function ScheduledTasksModal({ 
  isOpen, 
  onClose, 
  tasks, 
  onDelete, 
  isLoading,
  teammate,
  onScheduleSimilar 
}: ScheduledTasksModalProps) {
  const { getEntityMetadata } = useEntity();
  const { teammates, selectedTeammate: contextSelectedTeammate, setSelectedTeammate } = useTeammateContext();
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('all');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [isSchedulingModalOpen, setIsSchedulingModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<ScheduledTask | null>(null);
  const [isTeammateSelectionOpen, setIsTeammateSelectionOpen] = useState(false);
  const [taskToDelete, setTaskToDelete] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isTeammateDetailsOpen, setIsTeammateDetailsOpen] = useState(false);
  const [selectedTeammateForDetails, setSelectedTeammateForDetails] = useState<TeammateDetailsType | null>(null);
  const [isLoadingTeammateDetails, setIsLoadingTeammateDetails] = useState(false);
  const [isQuickSwitchOpen, setIsQuickSwitchOpen] = useState(false);

  const currentTeammate = useMemo(() => {
    if (!contextSelectedTeammate && !teammate?.uuid) return null;
    
    const base = teammates.find((t: TeammateInfo) => t.uuid === (contextSelectedTeammate || teammate?.uuid));
    if (!base && teammate?.uuid) {
      return {
        uuid: teammate.uuid,
        name: teammate.name || 'Unknown',
        status: 'active' as const
      } as TeammateInfo;
    }
    if (!base) return null;

    return {
      uuid: base.uuid,
      name: base.name,
      status: base.status,
      context: base.context,
      avatar: base.avatar,
      integrations: base.integrations
    } as TeammateInfo;
  }, [teammates, contextSelectedTeammate, teammate]);

  const getTeammateName = (teammate: TeammateInfo | null) => {
    if (!teammate) return 'Unknown';
    return teammate.name || 'Unknown';
  };

  const handleSwitchTeammate = () => {
    setIsTeammateSelectionOpen(true);
  };

  const handleDeleteConfirmation = async (taskId: string) => {
    setTaskToDelete(taskId);
  };

  const handleConfirmedDelete = async () => {
    if (!taskToDelete) return;
    
    setIsDeleting(true);
    try {
      const taskToDeleteObj = tasks.find(t => t.task_id === taskToDelete);
      if (!taskToDeleteObj?.task_uuid) {
        throw new Error('Task UUID is missing');
      }

      await onDelete(taskToDeleteObj.task_uuid);
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
      setIsDeleting(false);
      setTaskToDelete(null);
    }
  };

  const getDestinationIcon = (channelId: string) => {
    if (channelId.startsWith('#')) {
      return <Slack className="h-4 w-4 text-blue-400" />;
    }
    return <MessageSquare className="h-4 w-4 text-purple-400" />;
  };

  const safeParseDate = (dateStr: string | number | Date | null | undefined): Date | null => {
    if (!dateStr) return null;
    const parsed = new Date(dateStr);
    return isNaN(parsed.getTime()) ? null : parsed;
  };

  const formatTimeAgo = (dateStr: string | number | Date | null | undefined): string => {
    const date = safeParseDate(dateStr);
    if (!date) return 'Invalid date';
    
    try {
      if (isToday(date)) return format(date, 'h:mm a');
      if (isTomorrow(date)) return 'Tomorrow';
      if (isThisWeek(date)) return format(date, 'EEEE');
      if (isThisMonth(date)) return format(date, 'MMM d');
      return format(date, 'MMM d, yyyy');
    } catch (error) {
      console.error('Error formatting date:', error);
      return 'Invalid date';
    }
  };

  const filteredTasks = useMemo(() => {
    let filtered = tasks.filter(task => 
      !currentTeammate?.uuid || task.parameters.selected_agent === currentTeammate.uuid
    );

    filtered = filtered.filter(task => {
      const taskDate = safeParseDate(task.scheduled_time);
      if (!taskDate) return false;
      
      switch (timeFilter) {
        case 'today':
          return isToday(taskDate);
        case 'tomorrow':
          return isTomorrow(taskDate);
        case 'this-week':
          return isThisWeek(taskDate);
        case 'this-month':
          return isThisMonth(taskDate);
        case 'upcoming':
          return isAfter(taskDate, new Date());
        case 'past':
          return isBefore(taskDate, new Date());
        default:
          return true;
      }
    });

    filtered = filtered.filter(task => {
      switch (statusFilter) {
        case 'pending':
          return task.status === 'scheduled' && !task.parameters.cron_string;
        case 'completed':
          return task.status === 'completed';
        case 'recurring':
          return !!task.parameters.cron_string;
        default:
          return true;
      }
    });

    return filtered;
  }, [tasks, timeFilter, statusFilter, currentTeammate?.uuid]);

  const convertTeammateDetailsToInfo = (teammate: TeammateDetailsType): TeammateInfo => {
    let status: TeammateInfo['status'];
    if (teammate.status === 'error' || teammate.status === 'inactive') {
      status = 'inactive';
    } else {
      status = 'active';
    }

    return {
      uuid: teammate.id,
      name: teammate.name,
      avatar: teammate.avatar_url,
      context: teammate.description,
      status
    };
  };

  const groupedTasks = useMemo(() => {
    const groups = new Map<string, TeammateGroup>();

    const tasksWithTeammates = filteredTasks.map(task => {
      const findAndConvertTeammate = (teammateId: string | undefined) => {
        if (!teammateId) return null;
        const teammate = findTeammate(teammates, teammateId);
        if (!teammate) return null;
        
        return {
          ...convertToTeammateDetails(teammate),
          uuid: teammate.uuid
        };
      };

      // Try to find teammate from task.teammate first
      const teammateFromTask = task.teammate && isTeammateDetails(task.teammate) ? 
        findAndConvertTeammate(task.teammate.id) : null;

      // If no teammate found, try selected_agent
      const teammateFromAgent = !teammateFromTask && task.parameters?.selected_agent ? 
        findAndConvertTeammate(task.parameters.selected_agent) : null;

      return {
        ...task,
        teammate: teammateFromTask || teammateFromAgent || null
      } as ScheduledTask;
    });

    tasksWithTeammates.forEach(task => {
      const teammateName = task.parameters.selected_agent_name || task.parameters.selected_agent || 'unassigned';
      const existingGroup = groups.get(teammateName);

      if (existingGroup) {
        existingGroup.tasks.push(task);
      } else {
        groups.set(teammateName, {
          teammate: task.teammate || null,
          tasks: [task]
        });
      }
    });

    return Array.from(groups.entries()).sort((a, b) => 
      a[0].localeCompare(b[0])
    );
  }, [filteredTasks, teammates]);

  const handleTeammateClick = async (teammate: TeammateDetailsWithUUID | TeammateInfo | null) => {
    if (!teammate) return;
    
    try {
      setIsLoadingTeammateDetails(true);
      const teammateId = isTeammateInfo(teammate) ? teammate.uuid : teammate.id;
      const response = await fetch(`/api/teammates/${teammateId?.toLowerCase()}`);
      if (!response.ok) throw new Error('Failed to fetch teammate details');
      
      const data = await response.json();
      const teammateDetails: TeammateDetailsType = {
        id: data.id || teammateId || '',
        uuid: data.uuid || teammateId || '',
        name: teammate.name || data.name || '',
        description: data.description || '',
        avatar_url: data.avatar_url || '',
        status: data.status || 'active',
        metadata: {
          created_at: data.metadata?.created_at || new Date().toISOString(),
          last_updated: data.metadata?.last_updated || new Date().toISOString(),
          tools_count: data.metadata?.tools_count || 0,
          integrations_count: data.metadata?.integrations_count || 0,
          sources_count: data.metadata?.sources_count || 0
        },
        integrations: data.integrations || []
      };

      setSelectedTeammateForDetails(teammateDetails);
      setIsTeammateDetailsOpen(true);
    } catch (error) {
      console.error('Error fetching teammate details:', error);
      toast({
        title: "Error",
        description: "Failed to load teammate details",
        variant: "destructive"
      });
    } finally {
      setIsLoadingTeammateDetails(false);
    }
  };

  const timeFilters: { value: TimeFilter; label: string; icon: typeof Clock }[] = [
    { value: 'all', label: 'All Time', icon: Clock },
    { value: 'today', label: 'Today', icon: Clock },
    { value: 'tomorrow', label: 'Tomorrow', icon: Calendar },
    { value: 'this-week', label: 'This Week', icon: Calendar },
    { value: 'this-month', label: 'This Month', icon: Calendar },
    { value: 'upcoming', label: 'Upcoming', icon: Clock },
    { value: 'past', label: 'Past', icon: Clock },
  ];

  const statusFilters: { value: StatusFilter; label: string }[] = [
    { value: 'all', label: 'All Status' },
    { value: 'pending', label: 'Pending' },
    { value: 'completed', label: 'Completed' },
    { value: 'recurring', label: 'Recurring' },
  ];

  const handleScheduleSimilar = (task: ScheduledTask) => {
    if (onScheduleSimilar) {
      onScheduleSimilar({
        description: task.parameters.message_text,
        slackTarget: task.channel_id,
        scheduleType: task.parameters.cron_string ? 'custom' : 'quick',
        repeatOption: task.parameters.cron_string ? 'custom' : 'never'
      });
    }
  };

  const getIntegrationIcon = (integration: BaseIntegration) => {
    const type = (integration.integration_type || integration.name || '').toLowerCase();
    
    if (type.includes('slack')) return <Slack className="h-4 w-4 text-blue-400" />;
    if (type.includes('github')) return <GitBranch className="h-4 w-4 text-purple-400" />;
    if (type.includes('jira')) return <Trello className="h-4 w-4 text-blue-400" />;
    if (type.includes('aws')) return <Cloud className="h-4 w-4 text-orange-400" />;
    
    return <Webhook className="h-4 w-4 text-emerald-400" />;
  };

  const handleTeammateSwitch = async (newTeammate: TeammateInfo) => {
    try {
      setSelectedTeammate?.(newTeammate.uuid);
      
      const response = await fetch(`/api/tasks/reassign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tasks: tasks.map(task => task.task_uuid),
          newTeammateId: newTeammate.uuid,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to reassign tasks');
      }

      toast({
        title: "Success",
        description: `Tasks reassigned to ${newTeammate.name}`,
        duration: 3000,
      });

      setIsQuickSwitchOpen(false);

    } catch (error) {
      console.error('Error switching teammate:', error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to reassign tasks. Please try again.",
        duration: 5000,
      });
    }
  };

  const getAvatarUrl = (teammate: TeammateDetailsWithUUID | TeammateInfo | null) => {
    if (!teammate) {
      return generateAvatarUrl({ 
        uuid: 'default', 
        name: 'Unknown'
      });
    }
    const id = 'id' in teammate ? teammate.id : teammate.uuid;
    return generateAvatarUrl({ 
      uuid: id || 'default', 
      name: teammate.name || 'Unknown'
    });
  };

  return (
    <>
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-[800px] max-h-[85vh] bg-[#0F172A] border-[#1E293B] p-0 overflow-hidden flex flex-col">
          <DialogHeader className="px-6 py-4 border-b border-[#1E293B] flex-shrink-0">
            <div className="flex items-center justify-between">
              <DialogTitle className="flex items-center gap-2 text-slate-200">
                <Clock className="h-5 w-5 text-purple-400" />
                <div>
                  <span className="text-lg font-medium">My Scheduled Tasks</span>
                  <p className="text-sm text-slate-400 font-normal mt-1">
                    Delegate tasks to your teammates - they'll handle everything, even when you're away
                  </p>
                </div>
              </DialogTitle>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setTimeFilter('all');
                    setStatusFilter('all');
                  }}
                  className="text-slate-400 hover:text-purple-400 hover:bg-purple-500/10"
                >
                  <RotateCcw className="h-4 w-4 mr-1" />
                  Reset Filters
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onScheduleSimilar?.({
                    description: '',
                    slackTarget: '',
                    scheduleType: 'quick',
                    repeatOption: 'never'
                  })}
                  className="bg-purple-500/10 text-purple-400 border-purple-500/30 hover:bg-purple-500/20"
                >
                  <Clock className="h-4 w-4 mr-1.5" />
                  New Task
                </Button>
              </div>
            </div>
          </DialogHeader>

          {currentTeammate && (
            <div className="px-6 py-4 border-b border-[#1E293B] bg-[#1A1F2E]">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-4">
                  <div className="relative">
                    <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-500/10 to-purple-500/5 border border-purple-500/20 flex items-center justify-center">
                      <img
                        src={getAvatarUrl(currentTeammate)}
                        alt={currentTeammate.name || 'Teammate'}
                        className="w-8 h-8 rounded object-cover"
                      />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-medium text-slate-200 truncate">
                        {getTeammateName(currentTeammate)}
                      </h4>
                      {currentTeammate.status === 'active' && (
                        <Badge variant="secondary" className={cn(
                          "bg-opacity-10 border-opacity-20",
                          "bg-purple-500 text-purple-400 border-purple-500"
                        )}>
                          Active
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
                <div className="relative">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsQuickSwitchOpen(!isQuickSwitchOpen)}
                    className="text-slate-400 hover:text-purple-400 group shrink-0"
                  >
                    Choose Different Teammate
                    <ChevronRight className="h-4 w-4 ml-1 group-hover:translate-x-0.5 transition-transform" />
                  </Button>
                  
                  {isQuickSwitchOpen && (
                    <QuickTeammateSwitch
                      teammates={teammates}
                      currentTeammate={currentTeammate}
                      onSelect={handleTeammateSwitch}
                      onClose={() => setIsQuickSwitchOpen(false)}
                    />
                  )}
                </div>
              </div>
            </div>
          )}

          <div className="px-6 py-3 border-b border-[#1E293B] bg-[#1A1F2E] flex-shrink-0">
            <div className="flex flex-wrap gap-2">
              {timeFilters.map((filter) => (
                <Button
                  key={filter.value}
                  variant="ghost"
                  size="sm"
                  onClick={() => setTimeFilter(filter.value)}
                  className={cn(
                    "rounded-lg px-3 py-1.5",
                    timeFilter === filter.value
                      ? "bg-purple-500/10 text-purple-400 border-purple-500/30"
                      : "text-slate-400 hover:bg-purple-500/10 hover:text-purple-400"
                  )}
                >
                  <filter.icon className="h-3.5 w-3.5 mr-1.5" />
                  {filter.label}
                </Button>
              ))}
              <div className="h-6 w-px bg-[#2D3B4E] mx-1" />
              {statusFilters.map((filter) => (
                <Button
                  key={filter.value}
                  variant="ghost"
                  size="sm"
                  onClick={() => setStatusFilter(filter.value)}
                  className={cn(
                    "rounded-lg px-3 py-1.5",
                    statusFilter === filter.value
                      ? "bg-purple-500/10 text-purple-400 border-purple-500/30"
                      : "text-slate-400 hover:bg-purple-500/10 hover:text-purple-400"
                  )}
                >
                  {filter.label}
                </Button>
              ))}
            </div>
          </div>

          <div className="p-5 space-y-6 overflow-y-auto flex-grow">
            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="bg-[#1E293B] border border-[#2D3B4E] rounded-lg p-4 animate-pulse">
                    <div className="flex items-start justify-between">
                      <div className="space-y-3 flex-1">
                        <div className="h-4 w-32 bg-[#2D3B4E] rounded"></div>
                        <div className="h-6 w-3/4 bg-[#2D3B4E] rounded"></div>
                        <div className="h-4 w-24 bg-[#2D3B4E] rounded"></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : !currentTeammate ? (
              <div className="text-center py-8">
                <User className="h-12 w-12 text-purple-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-200 mb-2">Select a Teammate</h3>
                <p className="text-sm text-slate-400 mb-4">
                  Please select a teammate to view their scheduled tasks
                </p>
                <Button
                  variant="default"
                  onClick={handleSwitchTeammate}
                  className="bg-purple-500 text-white hover:bg-purple-600"
                >
                  <User className="h-4 w-4 mr-1.5" />
                  Select Teammate
                </Button>
              </div>
            ) : filteredTasks.length === 0 ? (
              <div className="text-center py-8">
                <Clock className="h-12 w-12 text-slate-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-200 mb-2">No Tasks Found</h3>
                <p className="text-sm text-slate-400 mb-4">
                  {timeFilter !== 'all' || statusFilter !== 'all'
                    ? 'Try adjusting your filters'
                    : 'You haven\'t scheduled any tasks yet'}
                </p>
                <Button
                  variant="outline"
                  onClick={() => onScheduleSimilar?.({
                    description: '',
                    slackTarget: '',
                    scheduleType: 'quick',
                    repeatOption: 'never'
                  })}
                  className="bg-purple-500/10 text-purple-400 border-purple-500/30 hover:bg-purple-500/20"
                >
                  <Clock className="h-4 w-4 mr-1.5" />
                  Schedule Your First Task
                </Button>
              </div>
            ) : (
              <div className="space-y-8">
                {groupedTasks.map(([teammateName, group]) => (
                  <div key={teammateName} className="space-y-4">
                    <div 
                      className="flex items-center gap-2 cursor-pointer group"
                      onClick={() => group.teammate && handleTeammateClick(group.teammate)}
                    >
                      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500/10 to-purple-500/5 border border-purple-500/20 flex items-center justify-center">
                        <img
                          src={getAvatarUrl(group.teammate)}
                          alt={group.teammate?.name || 'Unknown'}
                          className="w-6 h-6 rounded object-cover"
                        />
                      </div>
                      <div className="flex-1">
                        <h3 className="text-sm font-medium text-slate-200 group-hover:text-purple-400 transition-colors">
                          {group.teammate?.name || 'Unassigned'}
                        </h3>
                        <p className="text-xs text-slate-400">
                          {group.tasks.length} task{group.tasks.length !== 1 ? 's' : ''}
                        </p>
                      </div>
                    </div>

                    <div className="space-y-4 pl-10">
                      {group.tasks.map((task) => (
                        <div key={task.task_id} className="bg-[#1E293B] rounded-lg shadow-sm p-4 border border-[#2D3B4E] hover:border-purple-500/30 transition-colors">
                          <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center mb-2 gap-2">
                                <div className="flex items-center">
                                  {task.parameters.slack_info?.channel_id && (
                                    <div className="group relative">
                                      <a
                                        href={task.parameters.slack_info.channel_link}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center text-blue-400 hover:text-blue-300"
                                      >
                                        <Slack className="h-4 w-4 mr-1" />
                                        <span className="font-medium">{task.parameters.slack_info.channel_name}</span>
                                      </a>
                                      <div className="invisible group-hover:visible absolute z-10 w-72 p-2 mt-2 text-sm bg-[#0F172A] text-slate-200 rounded-md shadow-lg border border-[#2D3B4E]">
                                        <p className="mb-1">{task.parameters.slack_info.tooltips.channel_context}</p>
                                        <p className="mb-1">{task.parameters.slack_info.tooltips.bi_directional}</p>
                                        <p>{task.parameters.slack_info.tooltips.direct_commands}</p>
                                      </div>
                                    </div>
                                  )}
                                </div>
                                <div className="flex items-center gap-2">
                                  {task.parameters.cron_string && (
                                    <Badge variant="secondary" className="flex items-center gap-1 bg-purple-500/10 text-purple-400">
                                      <RefreshCcw className="h-3 w-3" />
                                      <span>Recurring</span>
                                    </Badge>
                                  )}
                                  <Badge 
                                    variant="secondary"
                                    className={cn(
                                      "capitalize",
                                      task.status === 'completed' 
                                        ? 'bg-green-500/10 text-green-400' 
                                        : 'bg-blue-500/10 text-blue-400'
                                    )}
                                  >
                                    {task.status}
                                  </Badge>
                                </div>
                              </div>

                              <div className="space-y-2">
                                <p className="text-sm text-slate-300 whitespace-pre-wrap">
                                  {task.parameters.message_text}
                                </p>

                                <div className="flex items-center gap-4 text-sm text-slate-400">
                                  <div className="flex items-center">
                                    <Clock className="h-4 w-4 mr-1" />
                                    <span>{formatTimeAgo(task.scheduled_time)}</span>
                                  </div>
                                  {task.parameters.cron_string && (
                                    <div className="flex items-center">
                                      <Calendar className="h-4 w-4 mr-1" />
                                      <span>{task.parameters.cron_string}</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>

                            <div className="flex items-start space-x-2 ml-4">
                              {onScheduleSimilar && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleScheduleSimilar(task)}
                                  className="text-slate-400 hover:text-purple-400"
                                  title="Schedule Similar Task"
                                >
                                  <RotateCcw className="h-4 w-4" />
                                </Button>
                              )}
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDeleteConfirmation(task.task_id)}
                                className="text-slate-400 hover:text-red-400"
                                title="Delete Task"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="px-6 py-3 border-t border-[#1E293B] flex-shrink-0">
            <div className="flex items-center justify-between">
              <div className="text-sm text-slate-400">
                {filteredTasks.length} task{filteredTasks.length !== 1 ? 's' : ''} found
              </div>
              <Button 
                variant="ghost" 
                onClick={onClose}
                className="hover:bg-purple-500/10 hover:text-purple-400 rounded-lg px-4 py-2"
              >
                Close
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <TeammateDetailsModal
        isOpen={isTeammateDetailsOpen}
        onCloseAction={() => {
          setIsTeammateDetailsOpen(false);
          setSelectedTeammateForDetails(null);
        }}
        teammate={selectedTeammateForDetails}
        integrations={selectedTeammateForDetails?.integrations || []}
      />
    </>
  );
} 