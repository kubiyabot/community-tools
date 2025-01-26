import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/app/components/ui/dialog';
import { Button } from '@/app/components/ui/button';
import { Clock, Trash2, Slack, MessageSquare, X, Calendar, RotateCcw, Filter } from 'lucide-react';
import { format, isToday, isTomorrow, isThisWeek, isThisMonth } from 'date-fns';
import { toast } from '@/app/components/ui/use-toast';
import { cn } from '@/lib/utils';
import { useState, useMemo } from 'react';

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

type TimeFilter = 'all' | 'today' | 'tomorrow' | 'this-week' | 'this-month';
type StatusFilter = 'all' | 'pending' | 'completed' | 'recurring';

export function ScheduledTasksModal({ 
  isOpen, 
  onClose, 
  tasks, 
  onDelete, 
  isLoading, 
  teammate,
  onScheduleSimilar 
}: ScheduledTasksModalProps) {
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('all');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [isSchedulingModalOpen, setIsSchedulingModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<ScheduledTask | null>(null);

  const handleDelete = async (taskId: string) => {
    try {
      await onDelete(taskId);
    } catch (error) {
      console.error('Error deleting task:', error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to delete task. Please try again.",
      });
    }
  };

  const getDestinationIcon = (channelId: string) => {
    if (channelId.startsWith('#')) {
      return <Slack className="h-4 w-4 text-blue-400" />;
    }
    return <MessageSquare className="h-4 w-4 text-purple-400" />;
  };

  const formatTimeAgo = (date: Date) => {
    if (isToday(date)) return 'Today';
    if (isTomorrow(date)) return 'Tomorrow';
    if (isThisWeek(date)) return format(date, 'EEEE');
    if (isThisMonth(date)) return format(date, 'MMM d');
    return format(date, 'MMM d, yyyy');
  };

  const filteredTasks = useMemo(() => {
    // First filter by user's email
    let filtered = tasks.filter(task => 
      !teammate?.email || task.parameters.user_email === teammate.email
    );

    // Then apply time filter
    filtered = filtered.filter(task => {
      const date = new Date(task.scheduled_time);
      switch (timeFilter) {
        case 'today':
          return isToday(date);
        case 'tomorrow':
          return isTomorrow(date);
        case 'this-week':
          return isThisWeek(date);
        case 'this-month':
          return isThisMonth(date);
        default:
          return true;
      }
    });

    // Finally apply status filter
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
  }, [tasks, timeFilter, statusFilter, teammate?.email]);

  const timeFilters: { value: TimeFilter; label: string; icon: typeof Clock }[] = [
    { value: 'all', label: 'All Time', icon: Clock },
    { value: 'today', label: 'Today', icon: Clock },
    { value: 'tomorrow', label: 'Tomorrow', icon: Calendar },
    { value: 'this-week', label: 'This Week', icon: Calendar },
    { value: 'this-month', label: 'This Month', icon: Calendar },
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

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-[800px] max-h-[85vh] bg-[#0F172A] border-[#1E293B] p-0 overflow-hidden flex flex-col">
        <DialogHeader className="px-6 py-4 border-b border-[#1E293B] flex-shrink-0">
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center gap-2 text-slate-200">
              <Clock className="h-5 w-5 text-purple-400" />
              <span className="text-lg font-medium">Your Scheduled Tasks</span>
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

        <div className="p-5 space-y-4 overflow-y-auto flex-grow">
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
            <div className="space-y-3">
              {filteredTasks.map((task) => (
                <div 
                  key={task.task_id}
                  className="bg-[#1E293B] border border-[#2D3B4E] rounded-lg p-4 hover:border-purple-500/30 transition-colors group"
                >
                  <div className="flex items-start justify-between">
                    <div className="space-y-3 flex-1">
                      <div className="flex items-center gap-2">
                        <div className="flex items-center gap-2 text-sm text-slate-400">
                          <Clock className="h-4 w-4" />
                          <span>
                            {task.parameters.cron_string ? (
                              <span className="flex items-center gap-1.5">
                                <span className="text-purple-400">Recurring:</span>
                                {task.parameters.cron_string}
                              </span>
                            ) : (
                              <span className="flex items-center gap-1.5">
                                <span className="text-blue-400">{formatTimeAgo(new Date(task.scheduled_time))}</span>
                                at {format(new Date(task.scheduled_time), 'h:mm a')}
                              </span>
                            )}
                          </span>
                        </div>
                        {task.status === 'completed' && (
                          <span className="px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 text-xs font-medium">
                            Completed
                          </span>
                        )}
                      </div>
                      <div className="space-y-2">
                        <p className="text-slate-200 text-base">{task.parameters.message_text}</p>
                        <div className="flex items-center gap-4 text-sm">
                          <div className="flex items-center gap-2 text-slate-400">
                            {getDestinationIcon(task.channel_id)}
                            <span>{task.channel_id}</span>
                          </div>
                          <div className="text-slate-500">•</div>
                          <div className="text-slate-400">
                            Created {format(new Date(task.created_at), 'MMM d, h:mm a')}
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleScheduleSimilar(task)}
                        className="text-slate-400 hover:text-purple-400 hover:bg-purple-400/10"
                        title="Schedule Similar Task"
                      >
                        <Clock className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(task.task_id)}
                        className="text-slate-400 hover:text-red-400 hover:bg-red-400/10"
                        title="Delete Task"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
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
  );
} 