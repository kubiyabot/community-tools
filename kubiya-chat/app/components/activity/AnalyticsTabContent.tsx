import React, { useState, useEffect, useMemo } from 'react';
import { format } from 'date-fns';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import {
  Users,
  Clock,
  Activity,
  BarChart3,
  ChevronRight,
  Filter,
  Search,
  ArrowLeft,
  Loader2,
  AlertCircle,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Bot,
  MessageSquare,
  Webhook,
  Slack,
  Globe,
  MessagesSquare,
  ExternalLink,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { ScrollArea } from '../ui/scroll-area';
import { SessionDetails } from './SessionDetails';
import { Alert, AlertDescription } from '../ui/alert';
import { TooltipProvider, Tooltip, TooltipContent, TooltipTrigger } from '../ui/tooltip';
import { cn } from '../../lib/utils';
import { useActivityStream } from '../../hooks/useActivityStream';
import { useRouter, useSearchParams } from 'next/navigation';

interface AuditItem {
  id: string;
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

// Define ActivityEvent as the same type as AuditItem for now
type ActivityEvent = AuditItem;

interface AnalyticsTabContentProps {
  isLoading?: boolean;
}

interface SessionGroup {
  sessionId: string;
  user: string;
  category: string;
  startTime: string;
  endTime: string;
  events: ActivityEvent[];
  success: boolean;
}

const COLORS = {
  success: 'text-green-400 border-green-500/30 bg-green-500/10',
  failed: 'text-red-400 border-red-500/30 bg-red-500/10',
  category: 'text-blue-400 border-blue-500/30 bg-blue-500/10',
  count: 'text-purple-400 border-purple-500/30 bg-purple-500/10',
  warning: 'text-amber-400 border-amber-500/30 bg-amber-500/10',
  info: 'text-indigo-400 border-indigo-500/30 bg-indigo-500/10'
};

const CHART_COLORS = [
  '#10B981', // green
  '#3B82F6', // blue
  '#8B5CF6', // purple
  '#EC4899', // pink
  '#F59E0B', // amber
  '#6366F1', // indigo
  '#14B8A6', // teal
  '#F43F5E'  // rose
];

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

function generateTeammateAvatarUrl(input: { uuid: string; name: string }) {
  // Create a more random distribution using multiple properties
  const seed = (input.uuid + input.name).split('').reduce((acc, char, i) => 
    acc + (char.charCodeAt(0) * (i + 1)), 0);
  const randomIndex = Math.abs(Math.sin(seed) * AVATAR_IMAGES.length) | 0;
  return `/images/avatars/${AVATAR_IMAGES[randomIndex]}`;
}

const MetricCard: React.FC<{
  title: string;
  value: string | number;
  icon: React.ReactNode;
  isLoading?: boolean;
}> = ({ title, value, icon, isLoading }) => (
  <Card className="bg-slate-800 border-slate-700">
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <CardTitle className="text-sm font-medium text-slate-200">
        {title}
      </CardTitle>
      {icon}
    </CardHeader>
    <CardContent>
      {isLoading ? (
        <div className="h-8 bg-slate-700/50 rounded animate-pulse" />
      ) : (
        <div className="text-2xl font-bold text-slate-50">
          {value}
        </div>
      )}
    </CardContent>
  </Card>
);

const ChartSkeleton = () => (
  <div className="h-[400px] flex items-center justify-center bg-slate-800/50 rounded-lg border border-slate-700">
    <div className="flex flex-col items-center gap-4">
      <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      <p className="text-sm text-slate-400">Loading chart data...</p>
    </div>
  </div>
);

const SessionFilters: React.FC<{
  searchTerm: string;
  setSearchTerm: (value: string) => void;
  categoryFilter: string;
  setCategoryFilter: (value: string) => void;
  statusFilter: string;
  setStatusFilter: (value: string) => void;
  timeRange: string;
  setTimeRange: (value: string) => void;
  onRefresh: () => void;
  isLoading: boolean;
  isRealtime: boolean;
  setIsRealtime: (value: boolean) => void;
  isConnected: boolean;
}> = ({
  searchTerm,
  setSearchTerm,
  categoryFilter,
  setCategoryFilter,
  statusFilter,
  setStatusFilter,
  timeRange,
  setTimeRange,
  onRefresh,
  isLoading,
  isRealtime,
  setIsRealtime,
  isConnected
}) => (
  <div className="flex flex-col gap-4 p-4 bg-slate-800/50 rounded-lg border border-slate-700/50">
    <div className="flex items-center gap-4">
      <div className="flex-1">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search by user, session ID, or category..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-900 border-slate-700 text-slate-200 placeholder:text-slate-400 pl-10"
          />
        </div>
      </div>
      <Select value={timeRange} onValueChange={setTimeRange}>
        <SelectTrigger className="w-40 bg-slate-900 border-slate-700 text-slate-200">
          <Clock className="h-4 w-4 mr-2" />
          <SelectValue placeholder="Time Range" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="1h">Last Hour</SelectItem>
          <SelectItem value="24h">Last 24 Hours</SelectItem>
          <SelectItem value="7d">Last 7 Days</SelectItem>
          <SelectItem value="30d">Last 30 Days</SelectItem>
        </SelectContent>
      </Select>
      <div className="flex items-center gap-2">
        <Button 
          variant="outline" 
          onClick={onRefresh}
          className="bg-slate-900 border-slate-700 text-slate-200 hover:bg-slate-800"
          disabled={isLoading}
        >
          <RefreshCw className={cn("h-4 w-4 mr-2", isLoading && "animate-spin")} />
          Refresh
        </Button>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                className={cn(
                  "bg-slate-900 border-slate-700 hover:bg-slate-800",
                  isRealtime && "border-purple-500/50 bg-purple-500/10 text-purple-400 hover:bg-purple-500/20"
                )}
                onClick={() => setIsRealtime(!isRealtime)}
              >
                {isRealtime ? (
                  <div className="relative">
                    <Activity className="h-4 w-4" />
                    <div className="absolute -top-1 -right-1">
                      <div className="relative">
                        <div className={cn(
                          "w-2 h-2 rounded-full",
                          isConnected ? "bg-green-500" : "bg-yellow-500"
                        )} />
                        <div className={cn(
                          "absolute inset-0 rounded-full animate-ping opacity-75",
                          isConnected ? "bg-green-500" : "bg-yellow-500"
                        )} />
                      </div>
                    </div>
                  </div>
                ) : (
                  <Activity className="h-4 w-4 text-slate-400" />
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              <div className="text-sm">
                <p className="font-medium">{isRealtime ? 'Live Updates Active' : 'Live Updates Disabled'}</p>
                {isRealtime && (
                  <p className="text-xs text-slate-400">
                    {isConnected ? 'Connected' : 'Connecting...'}
                  </p>
                )}
              </div>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    </div>
    <div className="flex items-center gap-4">
      <Select value={categoryFilter} onValueChange={setCategoryFilter}>
        <SelectTrigger className="w-40 bg-slate-900 border-slate-700 text-slate-200">
          <Filter className="h-4 w-4 mr-2" />
          <SelectValue placeholder="Category" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Categories</SelectItem>
          <SelectItem value="agents">Agents</SelectItem>
          <SelectItem value="webhooks">Webhooks</SelectItem>
          <SelectItem value="tools">Tools</SelectItem>
        </SelectContent>
      </Select>
      <Select value={statusFilter} onValueChange={setStatusFilter}>
        <SelectTrigger className="w-40 bg-slate-900 border-slate-700 text-slate-200">
          <Filter className="h-4 w-4 mr-2" />
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Status</SelectItem>
          <SelectItem value="success">Success</SelectItem>
          <SelectItem value="failed">Failed</SelectItem>
        </SelectContent>
      </Select>
      {isLoading && (
        <div className="flex items-center gap-2 text-sm text-slate-400 ml-auto">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading...
        </div>
      )}
    </div>
  </div>
);

const getTriggerIcon = (session: SessionGroup) => {
  // Determine trigger type from events
  const firstEvent = session.events[0];
  if (firstEvent?.category_type?.toLowerCase().includes('webhook')) {
    return { icon: Webhook, color: 'text-cyan-400', label: 'Webhook Trigger' };
  }
  if (firstEvent?.category_type?.toLowerCase().includes('slack')) {
    return { icon: Slack, color: 'text-purple-400', label: 'Slack Integration' };
  }
  if (firstEvent?.category_type?.toLowerCase().includes('api')) {
    return { icon: Globe, color: 'text-green-400', label: 'API Call' };
  }
  // Default to conversation
  return { icon: MessagesSquare, color: 'text-blue-400', label: 'Conversation' };
};

const SessionCard: React.FC<{
  session: SessionGroup;
  onClick: () => void;
}> = ({ session, onClick }) => {
  // Get unique users and teammates from events
  const uniqueParticipants = useMemo(() => {
    const users = new Set<string>();
    const teammates = new Map<string, { id: string; name: string; events: number }>();
    
    session.events.forEach(event => {
      users.add(event.email);
      if (event.extra?.teammate_id && event.extra?.teammate_name) {
        if (!teammates.has(event.extra.teammate_id)) {
          teammates.set(event.extra.teammate_id, {
            id: event.extra.teammate_id,
            name: event.extra.teammate_name,
            events: 0
          });
        }
        teammates.get(event.extra.teammate_id)!.events++;
      }
    });

    return {
      users: Array.from(users),
      teammates: Array.from(teammates.values())
    };
  }, [session.events]);

  // Format display names
  const formatDisplayName = (email: string) => {
    const [firstName, lastName] = email.split('@')[0].split('.');
    return firstName && lastName 
      ? `${firstName.charAt(0).toUpperCase() + firstName.slice(1)} ${lastName.charAt(0).toUpperCase() + lastName.slice(1)}`
      : email;
  };

  const trigger = getTriggerIcon(session);

  return (
    <div
      className="flex items-center justify-between p-4 rounded-lg bg-slate-800/80 border border-slate-700/50 hover:bg-slate-800 transition-all cursor-pointer hover:shadow-lg hover:border-slate-600/50 hover:scale-[1.01] duration-200"
      onClick={onClick}
    >
      <div className="flex items-center gap-6">
        {/* Conversation Participants */}
        <div className="flex items-center">
          {/* User and First Teammate */}
          <div className="flex items-center">
            {/* User Avatar */}
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="relative">
                    <img
                      src={`https://ui-avatars.com/api/?name=${encodeURIComponent(formatDisplayName(session.user))}&background=random&color=fff&size=128&bold=true&format=svg`}
                      alt={formatDisplayName(session.user)}
                      className="w-14 h-14 rounded-xl ring-4 ring-slate-900 bg-slate-800 hover:scale-105 transition-all z-30"
                    />
                    <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center bg-slate-800 ring-2 ring-slate-900">
                      <Users className="h-3.5 w-3.5 text-blue-400" />
                    </div>
                  </div>
                </TooltipTrigger>
                <TooltipContent side="top" className="p-3">
                  <div className="text-sm space-y-1.5">
                    <p className="font-semibold text-slate-100">{formatDisplayName(session.user)}</p>
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                      <Users className="h-3.5 w-3.5" />
                      <span>Initiator</span>
                    </div>
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>

            {/* First Teammate Avatar (if exists) */}
            {uniqueParticipants.teammates.length > 0 && (
              <div className="flex items-center -ml-4">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="relative">
                        <div className="w-14 h-14 rounded-xl ring-4 ring-slate-900 bg-slate-800 hover:scale-105 transition-all overflow-hidden">
                          <img
                            src={generateTeammateAvatarUrl({ 
                              uuid: uniqueParticipants.teammates[0].id,
                              name: uniqueParticipants.teammates[0].name
                            })}
                            alt={uniqueParticipants.teammates[0].name}
                            className="w-full h-full object-contain"
                          />
                        </div>
                        <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center bg-slate-800 ring-2 ring-slate-900">
                          <Bot className="h-3.5 w-3.5 text-indigo-400" />
                        </div>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="p-3">
                      <div className="text-sm space-y-1.5">
                        <p className="font-semibold text-slate-100">{uniqueParticipants.teammates[0].name}</p>
                        <div className="flex items-center gap-1.5 text-xs text-slate-400">
                          <Bot className="h-3.5 w-3.5" />
                          <span>Assistant</span>
                          <span>•</span>
                          <span>{uniqueParticipants.teammates[0].events} interactions</span>
                        </div>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            )}
          </div>

          {/* Additional Participants (if any) */}
          {(uniqueParticipants.teammates.length > 1 || uniqueParticipants.users.length > 1) && (
            <div className="flex items-center -ml-4">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="relative">
                      <div className="w-14 h-14 rounded-xl ring-4 ring-slate-900 bg-slate-800 flex items-center justify-center text-slate-200 font-medium hover:scale-105 transition-all">
                        +{uniqueParticipants.teammates.length - 1 + uniqueParticipants.users.length - 1}
                      </div>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="p-3">
                    <div className="text-sm space-y-2">
                      {uniqueParticipants.teammates.slice(1).map(teammate => (
                        <div key={teammate.id} className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded-lg overflow-hidden">
                            <img
                              src={generateTeammateAvatarUrl({ uuid: teammate.id, name: teammate.name })}
                              alt={teammate.name}
                              className="w-full h-full object-contain"
                            />
                          </div>
                          <span className="text-slate-200">{teammate.name}</span>
                        </div>
                      ))}
                      {uniqueParticipants.users.filter(user => user !== session.user).map(user => (
                        <div key={user} className="flex items-center gap-2">
                          <img
                            src={`https://ui-avatars.com/api/?name=${encodeURIComponent(formatDisplayName(user))}&size=32`}
                            alt={formatDisplayName(user)}
                            className="w-6 h-6 rounded-lg"
                          />
                          <span className="text-slate-200">{formatDisplayName(user)}</span>
                        </div>
                      ))}
                    </div>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          )}

          {/* Trigger Icon */}
          <div className="relative ml-3">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="w-8 h-8 rounded-full bg-slate-800 ring-4 ring-slate-900 flex items-center justify-center">
                    {React.createElement(trigger.icon, { className: `h-4 w-4 ${trigger.color}` })}
                  </div>
                </TooltipTrigger>
                <TooltipContent side="top" className="p-2">
                  <p className="text-sm font-medium">{trigger.label}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>

        <div className="space-y-3">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <span className="font-medium text-slate-200">
                {formatDisplayName(session.user)}
              </span>
              <Badge variant="outline" className={COLORS.info}>
                {session.category}
              </Badge>
              <Badge variant="outline" className={session.success ? COLORS.success : COLORS.failed}>
                {session.success ? 'Success' : 'Failed'}
              </Badge>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-400">
              <div className="flex items-center gap-1.5">
                <Clock className="h-3 w-3" />
                {format(new Date(session.startTime), 'MMM d, HH:mm:ss')}
              </div>
              <span>•</span>
              <div className="flex items-center gap-1.5">
                <Activity className="h-3 w-3" />
                {session.events.length} events
              </div>
              {uniqueParticipants.teammates.length > 0 && (
                <>
                  <span>•</span>
                  <div className="flex items-center gap-1.5">
                    <Bot className="h-3 w-3" />
                    {uniqueParticipants.teammates.length} assistant{uniqueParticipants.teammates.length > 1 ? 's' : ''}
                  </div>
                </>
              )}
              {uniqueParticipants.users.length > 1 && (
                <>
                  <span>•</span>
                  <div className="flex items-center gap-1.5">
                    <Users className="h-3 w-3" />
                    {uniqueParticipants.users.length} users
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs">
            {uniqueParticipants.teammates.map((teammate) => (
              <Badge 
                key={teammate.id}
                variant="outline" 
                className="bg-indigo-500/10 text-indigo-400 border-indigo-500/30"
              >
                {teammate.name}
              </Badge>
            ))}
            {uniqueParticipants.users.length > 1 && uniqueParticipants.users.filter(user => user !== session.user).map((user) => (
              <Badge 
                key={user}
                variant="outline" 
                className="bg-blue-500/10 text-blue-400 border-blue-500/30"
              >
                {formatDisplayName(user)}
              </Badge>
            ))}
          </div>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <ChevronRight className="h-4 w-4 text-slate-400" />
      </div>
    </div>
  );
};

// Move interface before component usage
export interface SessionDetailsProps {
  sessionId: string;
  events: ActivityEvent[];
  onBack: () => void;
  isLoading?: boolean;
  initialEventId?: string | null;
}

export const AnalyticsTabContent: React.FC<AnalyticsTabContentProps> = ({
  isLoading = false,
}) => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [auditData, setAuditData] = useState<AuditItem[]>([]);
  const [timeRange, setTimeRange] = useState('24h');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(
    searchParams.get('session')
  );
  const [selectedEventId, setSelectedEventId] = useState<string | null>(
    searchParams.get('event')
  );
  const [isLoadingAuditData, setIsLoadingAuditData] = useState(false);
  const [isRealtime, setIsRealtime] = useState(true);

  // Use the enhanced activity stream hook
  const { lastUpdate, isConnected } = useActivityStream();

  // Handle URL updates when selection changes
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (selectedSessionId) {
      params.set('session', selectedSessionId);
      if (selectedEventId) {
        params.set('event', selectedEventId);
      } else {
        params.delete('event');
      }
    } else {
      params.delete('session');
      params.delete('event');
    }
    
    const newUrl = `${window.location.pathname}${params.toString() ? '?' + params.toString() : ''}`;
    window.history.replaceState({}, '', newUrl);
  }, [selectedSessionId, selectedEventId]);

  // Handle real-time updates
  useEffect(() => {
    if (isRealtime && lastUpdate?.type === 'activity_update' && lastUpdate.data) {
      setAuditData(prevData => {
        const newData = [lastUpdate.data, ...prevData];
        // Keep only the last 1000 items to prevent memory issues
        return newData.slice(0, 1000);
      });
    }
  }, [lastUpdate, isRealtime]);

  // Function to handle activity item click
  const handleActivityItemClick = (event: AuditItem) => {
    if (event.extra?.session_id) {
      setSelectedSessionId(event.extra.session_id);
      // Use id or timestamp as the identifier
      setSelectedEventId(event.id || event.timestamp);
    }
  };

  const fetchAuditData = async () => {
    setIsLoadingAuditData(true);
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
        page_size: '1000',
        sort: JSON.stringify({ timestamp: -1 })
      });

      const response = await fetch(`/api/auditing/items?${queryParams}`);
      if (!response.ok) {
        throw new Error('Failed to fetch audit data');
      }
      const data = await response.json();
      setAuditData(data || []);
    } catch (error) {
      console.error('Error fetching audit data:', error);
      setAuditData([]);
    } finally {
      setIsLoadingAuditData(false);
    }
  };

  useEffect(() => {
    fetchAuditData();
  }, [timeRange]);

  const sessionGroups = useMemo(() => {
    const groups = new Map<string, SessionGroup>();
    
    // Sort audit data by timestamp in descending order
    const sortedData = [...auditData].sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
    
    sortedData.forEach(item => {
      if (!item.extra?.session_id) return;
      
      if (!groups.has(item.extra.session_id)) {
        groups.set(item.extra.session_id, {
          sessionId: item.extra.session_id,
          user: item.email,
          category: item.category_type,
          startTime: item.timestamp,
          endTime: item.timestamp,
          events: [],
          success: false,
        });
      }
      
      const group = groups.get(item.extra.session_id)!;
      group.events.push(item);
      
      if (new Date(item.timestamp) < new Date(group.startTime)) {
        group.startTime = item.timestamp;
      }
      if (new Date(item.timestamp) > new Date(group.endTime)) {
        group.endTime = item.timestamp;
      }
      
      if (item.action_successful) {
        group.success = true;
      }
    });
    
    return Array.from(groups.values());
  }, [auditData]);

  const metrics = useMemo(() => {
    const totalEvents = auditData.length;
    const successfulEvents = auditData.filter(item => item.action_successful).length;
    const uniqueUsers = new Set(auditData.map(item => item.email)).size;
    const successRate = totalEvents > 0 ? (successfulEvents / totalEvents) * 100 : 0;
    
    const activityByCategory = auditData.reduce((acc, item) => {
      acc[item.category_type] = (acc[item.category_type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    const timelineData = auditData.reduce((acc, item) => {
      const hour = format(new Date(item.timestamp), 'HH:mm');
      acc[hour] = (acc[hour] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const categoryData = Object.entries(activityByCategory).map(([name, value]) => ({
      name,
      value,
    }));
    
    return {
      totalEvents,
      successRate,
      uniqueUsers,
      activityByCategory: categoryData,
      timelineData: Object.entries(timelineData)
        .map(([time, count]) => ({ time, count }))
        .sort((a, b) => a.time.localeCompare(b.time)),
    };
  }, [auditData]);

  const filteredSessions = useMemo(() => {
    return sessionGroups.filter(session => {
      const matchesSearch = searchTerm === '' || 
        session.user.toLowerCase().includes(searchTerm.toLowerCase()) ||
        session.sessionId.toLowerCase().includes(searchTerm.toLowerCase()) ||
        session.category.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesCategory = categoryFilter === 'all' || 
        session.category.toLowerCase() === categoryFilter.toLowerCase();
      
      const matchesStatus = statusFilter === 'all' || 
        (statusFilter === 'success' && session.success) ||
        (statusFilter === 'failed' && !session.success);
      
      return matchesSearch && matchesCategory && matchesStatus;
    });
  }, [sessionGroups, searchTerm, categoryFilter, statusFilter]);

  const selectedSession = useMemo(() => {
    if (!selectedSessionId) return null;
    const session = sessionGroups.find(s => s.sessionId === selectedSessionId) as SessionGroup | undefined;
    if (!session) return null;
    return session;
  }, [selectedSessionId, sessionGroups]);

  if (selectedSession) {
    return (
      <div className="fixed inset-0 bg-slate-900/95 backdrop-blur-sm z-[100] overflow-hidden">
        <div className="relative h-full w-full animate-in slide-in-from-right-1/4 duration-300">
          <SessionDetails
            sessionId={selectedSession.sessionId}
            events={selectedSession.events}
            onBack={() => {
              setSelectedSessionId(null);
              setSelectedEventId(null);
            }}
            isLoading={isLoadingAuditData}
            initialEventId={selectedEventId}
            onOpenInFullView={() => {
              router.push(`/activity/sessions/${selectedSession.sessionId}${selectedEventId ? `?event=${selectedEventId}` : ''}`);
            }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-shrink-0 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-white">Analytics</h2>
            <p className="text-sm text-slate-400">
              View detailed analytics and session history
            </p>
          </div>
        </div>

        {/* Filters */}
        <SessionFilters
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
          categoryFilter={categoryFilter}
          setCategoryFilter={setCategoryFilter}
          statusFilter={statusFilter}
          setStatusFilter={setStatusFilter}
          timeRange={timeRange}
          setTimeRange={setTimeRange}
          onRefresh={fetchAuditData}
          isLoading={isLoadingAuditData}
          isRealtime={isRealtime}
          setIsRealtime={setIsRealtime}
          isConnected={isConnected}
        />
      </div>

      {/* Content */}
      <div className="flex-1 min-h-0 overflow-auto space-y-6 mt-4">
        {/* Metrics Grid */}
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Total Events"
            value={metrics.totalEvents}
            icon={<Activity className="h-4 w-4 text-blue-400" />}
            isLoading={isLoadingAuditData}
          />
          <MetricCard
            title="Success Rate"
            value={`${metrics.successRate.toFixed(1)}%`}
            icon={<BarChart3 className="h-4 w-4 text-green-400" />}
            isLoading={isLoadingAuditData}
          />
          <MetricCard
            title="Unique Users"
            value={metrics.uniqueUsers}
            icon={<Users className="h-4 w-4 text-purple-400" />}
            isLoading={isLoadingAuditData}
          />
          <MetricCard
            title="Average Events/Session"
            value={(metrics.totalEvents / (filteredSessions.length || 1)).toFixed(1)}
            icon={<Activity className="h-4 w-4 text-amber-400" />}
            isLoading={isLoadingAuditData}
          />
        </div>

        {/* Charts Section */}
        <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-slate-200">Activity Timeline</CardTitle>
                <Badge variant="outline" className={COLORS.category}>Last {timeRange}</Badge>
              </div>
            </CardHeader>
            <CardContent className="h-[300px]">
              {isLoadingAuditData ? (
                <ChartSkeleton />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={metrics.timelineData}
                    margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="time" stroke="#94A3B8" />
                    <YAxis stroke="#94A3B8" />
                    <RechartsTooltip 
                      contentStyle={{ 
                        backgroundColor: '#1E293B',
                        border: '1px solid #334155',
                        borderRadius: '6px',
                        color: '#F8FAFC'
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="count"
                      stroke="#3B82F6"
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 8 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-slate-200">Activity by Category</CardTitle>
                <Badge variant="outline" className={COLORS.category}>Distribution</Badge>
              </div>
            </CardHeader>
            <CardContent className="h-[300px]">
              {isLoadingAuditData ? (
                <ChartSkeleton />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={metrics.activityByCategory}
                      cx="50%"
                      cy="50%"
                      innerRadius={80}
                      outerRadius={120}
                      fill="#8884d8"
                      paddingAngle={5}
                      dataKey="value"
                      label
                    >
                      {metrics.activityByCategory.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={CHART_COLORS[index % CHART_COLORS.length]}
                        />
                      ))}
                    </Pie>
                    <RechartsTooltip 
                      contentStyle={{ 
                        backgroundColor: '#1E293B',
                        border: '1px solid #334155',
                        borderRadius: '6px',
                        color: '#F8FAFC'
                      }}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sessions List with Animation */}
        <div className="space-y-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <h3 className="text-lg font-medium text-slate-200">Recent Sessions</h3>
              <Badge variant="outline" className={cn("border", COLORS.count)}>
                {filteredSessions.length} session{filteredSessions.length !== 1 ? 's' : ''}
              </Badge>
            </div>
          </div>

          <div className="relative min-h-[400px] rounded-lg border border-slate-700/50">
            {isLoadingAuditData ? (
              <div className="absolute inset-0 flex items-center justify-center bg-slate-800/50 rounded-lg">
                <div className="flex flex-col items-center gap-4 p-8">
                  <Loader2 className="h-8 w-8 text-slate-400 animate-spin" />
                  <p className="text-sm text-slate-400">Loading sessions...</p>
                </div>
              </div>
            ) : filteredSessions.length === 0 ? (
              <div className="absolute inset-0 flex items-center justify-center">
                <Alert className="max-w-md mx-auto">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    No sessions found for the selected filters.
                  </AlertDescription>
                </Alert>
              </div>
            ) : (
              <ScrollArea className="h-[400px]">
                <div className="space-y-4 p-4">
                  {filteredSessions.map((session) => (
                    <div
                      key={session.sessionId}
                      className="animate-in fade-in-0 slide-in-from-right-5 duration-500"
                    >
                      <SessionCard
                        session={session}
                        onClick={() => {
                          setSelectedSessionId(session.sessionId);
                          handleActivityItemClick(session.events[0]);
                        }}
                      />
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}; 