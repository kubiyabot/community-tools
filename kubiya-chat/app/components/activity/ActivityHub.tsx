import React, { useState, useEffect } from 'react';
import { Task, Webhook, ActivityEvent, TeammateMetrics } from './types';
import { AnalyticsTabContent } from './AnalyticsTabContent';
import { TeammatesTabContent } from './TeammatesTabContent';
import { TasksTabContent } from './TasksTabContent';
import { WebhooksTabContent } from './WebhooksTabContent';
import { GlobalActivityFeed } from './GlobalActivityFeed';
import { cn } from '@/lib/utils';
import { X, ChevronRight, ChevronLeft, Clock, ListTodo } from 'lucide-react';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { useRouter } from 'next/navigation';
import { TaskSchedulingModal } from '../TaskSchedulingModal';
import { toast } from '../ui/use-toast';
import { useTeammateContext } from '@/app/MyRuntimeProvider';

type TabValue = 'activity' | 'analytics' | 'teammates' | 'tasks' | 'webhooks';
type TimeRange = '1h' | '24h' | '7d' | '30d' | 'all';

interface TaskData {
  channel_id: string;
  channel_name: string;
  created_at: string;
  next_schedule_time: string | null;
  parameters: {
    action_context_data: Record<string, any>;
    body: {
      team: {
        id: string;
      };
      user: {
        id: string;
      };
    };
    channel_id: string;
    context: string;
    cron_string: string;
    existing_session: boolean;
    message_text: string;
    organization_name: string;
    repeat: boolean;
    task_uuid: string;
    team_id: string;
    user_email: string;
  };
  scheduled_time: string;
  status: string;
  task_id: string;
  task_uuid: string;
  updated_at: string | null;
  user_email: string;
}

interface AuditEvent {
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
  };
  scope: string;
}

interface ActivityHubProps {
  isOpen: boolean;
  onClose: () => void;
  tasks: Task[];
  webhooks: Webhook[];
  isLoading: boolean;
  teammates: any[];
}

interface TeammateContextType {
  teammates: TeammateMetrics[];
  selectedTeammate: string;
  setSelectedTeammate: (uuid: string) => void;
}

export const ActivityHub: React.FC<ActivityHubProps> = ({
  isOpen,
  onClose,
  tasks: initialTasks,
  webhooks: initialWebhooks,
  isLoading: initialLoading,
  teammates
}) => {
  const router = useRouter();
  const { teammates: contextTeammates, selectedTeammate: contextSelectedTeammate } = useTeammateContext();
  const [activeTab, setActiveTab] = useState<TabValue>('analytics');
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [isLoading, setIsLoading] = useState(initialLoading);
  const [tasks, setTasks] = useState<Task[]>(initialTasks);
  const [webhooks, setWebhooks] = useState<Webhook[]>(initialWebhooks);
  const [timeRange, setTimeRange] = useState<TimeRange>('24h');
  const [isActivityPanelOpen, setIsActivityPanelOpen] = useState(true);
  const [isLoadingEvents, setIsLoadingEvents] = useState(false);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [selectedTeammate, setSelectedTeammate] = useState<TeammateMetrics | null>(null);
  const [isLoadingWebhooks, setIsLoadingWebhooks] = useState(false);

  // Add webhook fetching
  useEffect(() => {
    const fetchWebhooks = async () => {
      if (!isOpen) return;
      
      setIsLoadingWebhooks(true);
      try {
        const response = await fetch('/api/v1/webhook');
        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.error || 'Failed to fetch webhooks');
        }
        
        setWebhooks(data);
      } catch (error) {
        console.error('Failed to fetch webhooks:', error);
        toast({
          variant: "destructive",
          title: "Error",
          description: "Failed to load webhooks. Please try again.",
        });
        setWebhooks([]); // Set empty array on error
      } finally {
        setIsLoadingWebhooks(false);
      }
    };

    fetchWebhooks();
  }, [isOpen]);

  // Update state when props change
  useEffect(() => {
    setTasks(initialTasks);
    setIsLoading(initialLoading);
  }, [initialTasks, initialLoading]);

  const handleAssignTask = () => {
    if (!contextSelectedTeammate) {
      toast({
        title: "No Teammate Selected",
        description: "Please select a teammate first or choose one from the Teammates tab.",
        variant: "destructive"
      });
      setActiveTab('teammates');
      return;
    }

    const teammate = contextTeammates.find(t => t.uuid === contextSelectedTeammate);
    if (teammate) {
      setShowTaskModal(true);
    } else {
      toast({
        title: "Teammate Not Found",
        description: "The selected teammate could not be found. Please try selecting another teammate.",
        variant: "destructive"
      });
      setActiveTab('teammates');
    }
  };

  // Fetch audit events when component mounts or time range changes
  useEffect(() => {
    const fetchEvents = async () => {
      setIsLoadingEvents(true);
      try {
        const now = new Date();
        let startDate;
        switch (timeRange) {
          case '1h':
            startDate = new Date(now.getTime() - (60 * 60 * 1000));
            break;
          case '24h':
            startDate = new Date(now.getTime() - (24 * 60 * 60 * 1000));
            break;
          case '7d':
            startDate = new Date(now.getTime() - (7 * 24 * 60 * 60 * 1000));
            break;
          case '30d':
            startDate = new Date(now.getTime() - (30 * 24 * 60 * 60 * 1000));
            break;
          default:
            startDate = new Date(0);
        }

        const filter = {
          timestamp: {
            gte: startDate.toISOString(),
            lte: now.toISOString()
          }
        };

        const queryParams = new URLSearchParams({
          filter: JSON.stringify(filter),
          page: '1',
          page_size: '100',
          sort: JSON.stringify({ timestamp: -1 })
        });

        const response = await fetch(`/api/auditing/items?${queryParams}`);
        if (!response.ok) {
          throw new Error('Failed to fetch audit events');
        }
        const data = await response.json();
        setAuditEvents(data || []);
      } catch (error) {
        console.error('Failed to fetch audit events:', error);
        setAuditEvents([]);
      } finally {
        setIsLoadingEvents(false);
      }
    };

    if (isOpen) {
      fetchEvents();
      
      // Set up polling for new events every 30 seconds
      const pollInterval = setInterval(fetchEvents, 30000);
      
      return () => {
        clearInterval(pollInterval);
      };
    }
  }, [isOpen, timeRange]);

  // Add handlers for webhook operations
  const handleTestWebhook = async (webhookId: string): Promise<void> => {
    try {
      await fetch(`/api/webhooks/${webhookId}/test`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('Error testing webhook:', error);
    }
  };

  const handleDeleteWebhook = async (webhookId: string): Promise<void> => {
    try {
      await fetch(`/api/webhooks/${webhookId}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error('Error deleting webhook:', error);
    }
  };

  const handleViewSession = (sessionId: string) => {
    router.push(`/activity/sessions/${sessionId}`);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/90 backdrop-blur-sm overflow-hidden">
      <div className="fixed inset-0 flex">
        <div className="w-full h-full flex flex-col bg-slate-900 shadow-2xl">
          {/* Header */}
          <div className="flex-shrink-0 flex items-center justify-between px-6 h-16 border-b border-slate-800">
            <h2 className="text-xl font-semibold text-slate-200">Activity Hub</h2>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={handleAssignTask}
                className="bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20"
              >
                <ListTodo className="h-4 w-4 mr-1.5" />
                Assign Task
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="text-slate-400 hover:text-slate-300 hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 flex min-h-0">
            {/* Left Panel */}
            <div className="flex-1 flex flex-col min-w-0">
              {/* Stats Bar */}
              <div className="flex-shrink-0 flex items-center justify-between px-6 h-14 border-b border-slate-800">
                <div className="flex items-center space-x-4">
                  <button
                    onClick={() => setActiveTab('tasks')}
                    className={cn(
                      "flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors",
                      activeTab === 'tasks' ? "bg-purple-500/10 text-purple-400" : "text-slate-400 hover:text-slate-300"
                    )}
                  >
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    Tasks
                    <span className="px-1.5 py-0.5 text-xs rounded-md bg-slate-800">{tasks.length}</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('webhooks')}
                    className={cn(
                      "flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors",
                      activeTab === 'webhooks' ? "bg-blue-500/10 text-blue-400" : "text-slate-400 hover:text-slate-300"
                    )}
                  >
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    Webhooks
                    <span className="px-1.5 py-0.5 text-xs rounded-md bg-slate-800">{webhooks.length}</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('analytics')}
                    className={cn(
                      "flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors",
                      activeTab === 'analytics' ? "bg-green-500/10 text-green-400" : "text-slate-400 hover:text-slate-300"
                    )}
                  >
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    Analytics
                  </button>

                  <button
                    onClick={() => setActiveTab('teammates')}
                    className={cn(
                      "flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors",
                      activeTab === 'teammates' ? "bg-yellow-500/10 text-yellow-400" : "text-slate-400 hover:text-slate-300"
                    )}
                  >
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                    Teammate Analytics
                    <span className="px-1.5 py-0.5 text-xs rounded-md bg-slate-800">{contextTeammates.length}</span>
                  </button>
                </div>

                <div className="flex items-center gap-3">
                  {(activeTab === 'analytics' || activeTab === 'teammates') && (
                    <Select value={timeRange} onValueChange={(value: TimeRange) => setTimeRange(value)}>
                      <SelectTrigger className="min-w-[160px] h-8 bg-slate-800 border-slate-700 text-slate-200 text-sm">
                        <div className="flex items-center truncate">
                          <Clock className="w-4 h-4 mr-2 text-slate-400 flex-shrink-0" />
                          <SelectValue placeholder="Select time" className="truncate" />
                        </div>
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1h">Last hour</SelectItem>
                        <SelectItem value="24h">Last 24 hours</SelectItem>
                        <SelectItem value="7d">Last 7 days</SelectItem>
                        <SelectItem value="30d">Last 30 days</SelectItem>
                        <SelectItem value="all">All time</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 px-3 flex items-center gap-1.5 text-slate-400 hover:text-slate-300 hover:bg-slate-800 border border-slate-700/50 rounded-md"
                    onClick={() => setIsActivityPanelOpen(!isActivityPanelOpen)}
                  >
                    {isActivityPanelOpen ? (
                      <>
                        <ChevronRight className="h-4 w-4" />
                        <span className="text-xs">Hide Activity</span>
                      </>
                    ) : (
                      <>
                        <ChevronLeft className="h-4 w-4" />
                        <span className="text-xs">Show Activity</span>
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {/* Content Area */}
              <div className="flex-1 min-h-0 overflow-hidden">
                {activeTab === 'activity' && (
                  <div className="h-full overflow-auto px-6 py-4">
                    <GlobalActivityFeed events={auditEvents} timeRange={timeRange} isLoading={isLoadingEvents} />
                  </div>
                )}
                {activeTab === 'analytics' && (
                  <div className="h-full overflow-auto px-6 py-4">
                    <AnalyticsTabContent isLoading={isLoading} />
                  </div>
                )}
                {activeTab === 'teammates' && (
                  <div className="h-full overflow-auto px-6 py-4">
                    <TeammatesTabContent 
                      teammates={contextTeammates as TeammateMetrics[]} 
                      isLoading={isLoading}
                      onTeammateSelect={(teammate) => {
                        setSelectedTeammate(teammate);
                        setShowTaskModal(true);
                      }}
                    />
                  </div>
                )}
                {activeTab === 'tasks' && (
                  <div className="h-full overflow-auto px-6 py-4">
                    <TasksTabContent
                      tasks={tasks}
                      isLoading={isLoading}
                      teammates={contextTeammates as TeammateMetrics[]}
                    />
                  </div>
                )}
                {activeTab === 'webhooks' && (
                  <div className="h-full overflow-auto px-6 py-4">
                    <WebhooksTabContent
                      webhooks={webhooks}
                      isLoading={isLoadingWebhooks}
                      teammates={contextTeammates as TeammateMetrics[]}
                      onTestWebhook={handleTestWebhook}
                      onDeleteWebhook={handleDeleteWebhook}
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Right Panel - Activity Feed */}
            {isActivityPanelOpen && (
              <div className="relative w-[400px] border-l border-slate-800 flex-shrink-0 bg-slate-900/50 flex flex-col">
                {/* Resize Handle */}
                <div className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-indigo-500/50 group"
                     onMouseDown={(e) => {
                       e.preventDefault();
                       const startX = e.pageX;
                       const handle = e.currentTarget as HTMLDivElement;
                       const panel = handle.parentElement as HTMLDivElement;
                       const startWidth = panel?.offsetWidth || 400;
                       
                       const handleMouseMove = (e: MouseEvent) => {
                         const delta = startX - e.pageX;
                         const newWidth = Math.max(300, Math.min(800, startWidth + delta));
                         if (panel) {
                           panel.style.width = `${newWidth}px`;
                         }
                       };
                       
                       const handleMouseUp = () => {
                         document.removeEventListener('mousemove', handleMouseMove);
                         document.removeEventListener('mouseup', handleMouseUp);
                       };
                       
                       document.addEventListener('mousemove', handleMouseMove);
                       document.addEventListener('mouseup', handleMouseUp);
                     }}
                >
                  <div className="absolute inset-y-0 -left-0.5 w-1 bg-slate-700/50 group-hover:bg-indigo-500/50" />
                </div>
                <div className="flex-shrink-0 px-6 h-14 flex items-center border-b border-slate-800">
                  <h3 className="text-sm font-medium text-slate-400">Recent Activity</h3>
                </div>
                <div className="flex-1 overflow-auto">
                  <GlobalActivityFeed 
                    events={auditEvents} 
                    timeRange={timeRange} 
                    isLoading={isLoadingEvents}
                    onViewSession={handleViewSession}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Task Scheduling Modal */}
      {showTaskModal && (
        <TaskSchedulingModal
          isOpen={showTaskModal}
          onClose={() => setShowTaskModal(false)}
          teammate={contextTeammates.find(t => t.uuid === contextSelectedTeammate)}
          onSchedule={async (data: TaskData) => {
            try {
              await fetch('/api/tasks', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
              });
              toast({
                title: "Task Scheduled",
                description: "The task has been scheduled successfully.",
              });
              setShowTaskModal(false);
            } catch (error) {
              console.error('Failed to schedule task:', error);
              toast({
                variant: "destructive",
                title: "Error",
                description: "Failed to schedule task. Please try again.",
              });
            }
          }}
        />
      )}
    </div>
  );
}; 