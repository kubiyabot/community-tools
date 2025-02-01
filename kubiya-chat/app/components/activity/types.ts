export interface TeammateInfo {
  uuid: string;
  name: string;
  avatar?: string;
  description?: string;
  overview?: {
    description?: string;
    integrations?: string[];
    metrics?: {
      tasksCompleted: number;
      successRate: number;
      lastActive: string;
    };
  };
  capabilities?: {
    tools?: string[];
    integrations?: string[];
    starters?: string[];
    instruction_type?: string;
    llm_model?: string;
    description?: string;
  };
}

export interface TaskParameters {
  message_text: string;
  selected_agent?: string;
  selected_agent_name?: string;
  cron_string?: string;
  context?: string;
  user_email?: string;
  action_context_data?: Record<string, any>;
  body?: Record<string, any>;
  channel_id?: string;
  organization_name?: string;
  repeat?: boolean;
  task_uuid?: string;
  team_id?: string;
}

// Base task interface with common properties
interface BaseTask {
  task_id: string;
  task_uuid: string;
  task_type: string;
  status: 'scheduled' | 'pending' | 'completed' | 'failed';
  scheduled_time: string;
  channel_id: string;
  created_at: string;
  parameters: TaskParameters;
  teammate?: TeammateInfo;
}

// Task interface for API responses
export interface Task extends BaseTask {
  updated_at: string | null;
  channel_name?: string;
  user_email?: string;
  next_schedule_time?: string | null;
}

// Task interface for edit operations
export interface TaskEditData extends BaseTask {
  updated_at: string;
}

export interface Webhook {
  id: string;
  name: string;
  source: string;
  agent_id: string;
  event_type: string;
  prompt: string;
  communication: {
    destination: string;
    method: 'Slack' | 'Teams';
  };
  created_by: string;
  webhook_url: string;
  filter: string;
  teammate?: TeammateInfo;
  selected_agent?: TeammateInfo;
}

export interface TaskCardProps {
  task: Task;
  badges?: {
    variant: "outline";
    className: string;
    icon: React.ReactNode;
    text: string;
  }[];
  onDelete?: (taskId: string) => Promise<void>;
  onTeammateClick?: (teammate: any) => void;
  currentUserEmail?: string;
}

export interface WebhookCardProps {
  webhook: Webhook;
  onTest: (id: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

export interface TestWebhookData {
  webhook_id: string;
  data: string;
}

export interface TabHeaderProps {
  tasks: Task[];
  webhooks: Webhook[];
  teammates: TeammateMetrics[];
  activeTab: 'tasks' | 'webhooks' | 'analytics' | 'teammates';
  onTabChange: (tab: 'tasks' | 'webhooks' | 'analytics' | 'teammates') => void;
}

export interface TasksTabContentProps {
  tasks: Task[];
  isLoading: boolean;
  teammates?: TeammateMetrics[];
  onScheduleTask?: (task: TaskEditData) => void;
  onEditTask?: (task: TaskEditData) => void;
  onDeleteTask?: (taskId: string) => void;
  currentUserEmail?: string;
}

export interface WebhooksTabContentProps {
  webhooks: Webhook[];
  isLoading: boolean;
  teammates?: TeammateMetrics[];
  onTestWebhook: (webhookId: string) => Promise<void>;
  onDeleteWebhook: (webhookId: string) => Promise<void>;
}

export interface ActivityHubProps {
  isOpen: boolean;
  onClose: () => void;
  tasks: Task[];
  webhooks: Webhook[];
  isLoading: boolean;
  teammates?: TeammateMetrics[];
}

export type TimeFilter = 'all' | 'today' | 'week' | 'month';
export type StatusFilter = 'all' | 'pending' | 'completed' | 'recurring';
export type ActivityType = 'scheduled' | 'webhooks' | 'teammates';

export interface Teammate {
  uuid: string;
  name: string;
  avatar?: string;
  description?: string;
}

// Add this type for toast variants
export type ToastVariant = 'default' | 'destructive';

// Add these new types
export interface TeammateMetrics {
  uuid: string;
  name: string;
  avatar?: string;
  description?: string;
  metrics: {
    tasksCompleted: number;
    webhooksProcessed: number;
    jiraTicketsSolved: number;
    toolsExecuted: number;
    successRate: number;
    averageResponseTime: number;
    lastActive: string;
    team_id?: string;
    user_id?: string;
    org_id?: string;
    email?: string;
  };
  recentActivity: {
    date: string;
    type: 'task' | 'webhook' | 'jira' | 'tool';
    description: string;
  }[];
}

// Add the ActivityEvent type
export interface ActivityEvent {
  id: string;
  type: 'task' | 'webhook' | 'teammate' | 'user';
  action: string;
  status: 'success' | 'failed' | 'pending';
  timestamp: string;
  actor: {
    name: string;
    avatar?: string;
  };
  details: string;
}

export interface TeammatesTabContentProps {
  teammates: TeammateMetrics[];
  isLoading: boolean;
  onTeammateSelect?: (teammate: TeammateMetrics) => void;
}

export interface AnalyticsTabContentProps {
  isLoading: boolean;
} 