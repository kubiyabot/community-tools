import * as React from 'react';
import { format } from 'date-fns';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { TeammateMetrics } from './types';
import { cn } from '@/lib/utils';
import { 
  Bot, 
  Clock, 
  CheckCircle2, 
  Wrench,
  Webhook, 
  TicketCheck, 
  Zap 
} from 'lucide-react';
import { TeammatesTabContentProps } from './types';
import { Badge } from '../ui/badge';

interface MetricCardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  trend?: number;
  suffix?: string;
}

interface ActivityItem {
  type: 'task' | 'webhook' | 'jira' | 'tool';
  description: string;
  date: string;
  status: 'success' | 'failed';
}

const ActivityIcon = ({ type }: { type: ActivityItem['type'] }) => {
  const icons = {
    task: <CheckCircle2 className="h-4 w-4 text-green-400" />,
    webhook: <Webhook className="h-4 w-4 text-blue-400" />,
    jira: <TicketCheck className="h-4 w-4 text-purple-400" />,
    tool: <Wrench className="h-4 w-4 text-orange-400" />,
  };
  return icons[type];
};

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon, trend, suffix }) => (
  <Card>
    <CardHeader className="pb-2">
      <div className="flex items-center justify-between">
        <CardTitle className="text-sm font-medium text-slate-400">{title}</CardTitle>
        {icon}
      </div>
    </CardHeader>
    <CardContent>
      <div className="flex items-baseline">
        <div className="text-2xl font-bold">
          {value}
          {suffix && <span className="text-sm font-normal text-slate-400 ml-1">{suffix}</span>}
        </div>
        {trend && (
          <span className={cn(
            "ml-2 text-sm",
            trend > 0 ? "text-green-400" : "text-red-400"
          )}>
            {trend > 0 ? "↑" : "↓"} {Math.abs(trend)}%
          </span>
        )}
      </div>
    </CardContent>
  </Card>
);

const formatDate = (dateStr: string | undefined): string => {
  if (!dateStr) return 'N/A';
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return 'N/A';
    return format(date, 'MMM d, HH:mm');
  } catch (error) {
    return 'N/A';
  }
};

export const TeammatesTabContent: React.FC<TeammatesTabContentProps> = ({
  teammates = [],
  isLoading,
  onTeammateSelect
}) => {
  console.log('TeammatesTabContent render:', {
    teammatesLength: teammates?.length,
    isLoading
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (!teammates.length) {
    return (
      <div className="flex flex-col items-center justify-center h-[400px] text-slate-400">
        <p className="text-lg">No teammate data available</p>
      </div>
    );
  }

  const metrics = [
    {
      title: "Total Tasks",
      value: teammates.reduce((acc, t) => acc + (t.metrics?.tasksCompleted || 0), 0),
      icon: <CheckCircle2 className="h-4 w-4 text-green-400" />,
      trend: 12,
    },
    {
      title: "Webhooks Processed",
      value: teammates.reduce((acc, t) => acc + (t.metrics?.webhooksProcessed || 0), 0),
      icon: <Webhook className="h-4 w-4 text-blue-400" />,
      trend: 8,
    },
    {
      title: "Tickets Solved",
      value: teammates.reduce((acc, t) => acc + (t.metrics?.jiraTicketsSolved || 0), 0),
      icon: <TicketCheck className="h-4 w-4 text-purple-400" />,
      trend: -3,
    },
    {
      title: "Tools Executed",
      value: teammates.reduce((acc, t) => acc + (t.metrics?.toolsExecuted || 0), 0),
      icon: <Wrench className="h-4 w-4 text-orange-400" />,
      trend: 15,
    },
    {
      title: "Success Rate",
      value: Math.round(
        teammates.reduce((acc, t) => acc + (t.metrics?.successRate || 0), 0) / teammates.length
      ),
      icon: <Zap className="h-4 w-4 text-yellow-400" />,
      suffix: "%",
    },
    {
      title: "Avg Response Time",
      value: (
        teammates.reduce((acc, t) => acc + (t.metrics?.averageResponseTime || 0), 0) / teammates.length
      ).toFixed(1),
      icon: <Clock className="h-4 w-4 text-pink-400" />,
      suffix: "s",
    },
  ];

  const chartData = teammates.map(teammate => ({
    name: teammate.name,
    tasks: teammate.metrics?.tasksCompleted || 0,
    webhooks: teammate.metrics?.webhooksProcessed || 0,
    tickets: teammate.metrics?.jiraTicketsSolved || 0,
    tools: teammate.metrics?.toolsExecuted || 0,
  }));

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex-shrink-0 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-white">Teammate Analytics</h2>
            <p className="text-sm text-slate-400">
              View performance metrics and activity for all teammates
            </p>
          </div>
          <Badge variant="outline" className="bg-blue-500/10 text-blue-300 border-blue-500/30">
            {teammates.length} teammate{teammates.length !== 1 ? 's' : ''}
          </Badge>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-h-0 overflow-auto space-y-6 mt-4">
        {/* Overview Cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {metrics.map((metric, index) => (
            <MetricCard key={index} {...metric} />
          ))}
        </div>

        {/* Performance Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle>Task Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="name" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1e293b',
                        border: '1px solid #334155',
                        borderRadius: '0.375rem',
                      }}
                    />
                    <Bar dataKey="tasks" name="Tasks" fill="#22c55e" />
                    <Bar dataKey="webhooks" name="Webhooks" fill="#3b82f6" />
                    <Bar dataKey="tickets" name="Tickets" fill="#a855f7" />
                    <Bar dataKey="tools" name="Tools" fill="#f97316" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle>Success Rate Trend</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="name" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1e293b',
                        border: '1px solid #334155',
                        borderRadius: '0.375rem',
                      }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="tasks" 
                      name="Success Rate" 
                      stroke="#22c55e"
                      strokeWidth={2}
                      dot={{ fill: '#22c55e' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Teammate Cards */}
        <div className="grid gap-4 pb-4">
          {teammates.map((teammate) => (
            <div 
              key={teammate.uuid}
              className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4 hover:border-purple-500/30 transition-colors cursor-pointer"
              onClick={() => onTeammateSelect?.(teammate)}
            >
              <div className="flex items-start gap-4">
                <Avatar className="h-12 w-12">
                  <AvatarImage src={teammate.avatar} alt={teammate.name} />
                  <AvatarFallback>{teammate.name.charAt(0)}</AvatarFallback>
                </Avatar>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-white">{teammate.name}</h3>
                      {teammate.description && (
                        <p className="text-sm text-slate-400">{teammate.description}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="bg-green-500/10 text-green-300 border-green-500/30">
                        {teammate.metrics?.successRate || 0}% Success Rate
                      </Badge>
                      <Badge variant="outline" className="bg-blue-500/10 text-blue-300 border-blue-500/30">
                        {teammate.metrics?.tasksCompleted || 0} Tasks
                      </Badge>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                    <div>
                      <p className="text-sm text-slate-500">Tasks Completed</p>
                      <p className="text-lg font-semibold">{teammate.metrics?.tasksCompleted || 0}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">Response Time</p>
                      <p className="text-lg font-semibold">
                        {teammate.metrics?.averageResponseTime || 0}s
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">Last Active</p>
                      <p className="text-lg font-semibold">
                        {formatDate(teammate.metrics?.lastActive)}
                      </p>
                    </div>
                  </div>

                  {teammate.recentActivity?.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-slate-800">
                      <h4 className="text-sm font-medium text-slate-400 mb-2">Recent Activity</h4>
                      <div className="space-y-2">
                        {teammate.recentActivity.slice(0, 3).map((activity, i) => (
                          <div key={i} className="flex items-center gap-2 text-sm">
                            <ActivityIcon type={activity.type} />
                            <span className="text-slate-300">{activity.description}</span>
                            <span className="text-slate-500 ml-auto">
                              {formatDate(activity.date)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}; 