import { useState, useEffect, Dispatch, SetStateAction, useRef } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import { format, addHours, addDays, addWeeks, addMonths } from 'date-fns';
import { useTeammateContext } from "@/app/MyRuntimeProvider";
import { useForm, ControllerRenderProps, FieldValues, FormProvider } from "react-hook-form";
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from "./ui/form";
import { 
  Clock, 
  Calendar as CalendarIcon, 
  CalendarDays,
  CalendarClock,
  CalendarRange,
  AlertCircle,
  X,
  MessageSquare,
  Webhook,
  Trello,
  ArrowRight,
  ListTodo,
  Search,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  Code,
  Copy,
  Loader2,
  Slack,
  GitPullRequest,
  GitBranch,
  Rocket,
  Smile,
  Bell,
  Activity,
  Info
} from 'lucide-react';
import { toast } from './ui/use-toast';
import { cn } from '@/lib/utils';
import { Badge } from '@/app/components/ui/badge';
import { Calendar } from "@/app/components/ui/calendar";
import { useUser } from '@auth0/nextjs-auth0/client';
import { WebhookFlowSection } from './webhook/WebhookFlowSection';
import { WebhookProvider as ImportedWebhookProvider } from './webhook/providers';
import { TeammateContextCard } from './shared/TeammateContextCard';
import { TeammateSwitch } from './shared/TeammateSwitch';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "./ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";
import * as z from 'zod';
import type { Teammate } from './shared/TeammateSwitch';

// Type definitions
interface Integration {
  name: string;
  type?: string;
}

interface ContextVariable {
  path: string;
  description: string;
  example: any;
}

interface WebhookEvent {
  type: string;
  name: string;
  description: string;
  variables: ContextVariable[];
  example: Record<string, any>;
  category?: string;
}

interface WebhookContextMap {
  [key: string]: {
    description: string;
    events: WebhookEvent[];
  };
}

export type WebhookProvider = ImportedWebhookProvider;

// Update the type definition
type WebhookStep = 'provider' | 'event' | 'event_example' | 'prompt' | 'interaction' | 'webhook';

interface WebhookFlowProps {
  webhookProvider: WebhookProvider | null;
  eventType: string;
  promptTemplate: string;
  currentStep: WebhookStep;
  setWebhookProvider: (provider: WebhookProvider | null) => void;
  setEventType: (type: string) => void;
  setPromptTemplate: (template: string) => void;
  setCurrentStep: (step: WebhookStep) => void;
  session: any;
  teammate: any;
  standalone: boolean;
}

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

interface TaskSchedulingModalProps {
  isOpen: boolean;
  onClose: () => void;
  teammate?: Teammate;
  onSchedule: (data: ScheduleTaskPayload) => Promise<ScheduleTaskResult>;
  initialData?: {
    description?: string;
    slackTarget?: string;
    scheduleType?: 'quick' | 'custom';
    repeatOption?: string;
    date?: Date;
    source?: WebhookProvider;
    assignmentMethod?: 'chat' | 'jira' | 'webhook';
    webhookProvider?: WebhookProvider | null;
    webhookUrl?: string;
    promptTemplate?: string;
    eventType?: string;
  };
}

interface QuickTemplate {
  label: string;
  description: string;
  prompt: string;
  icon: JSX.Element;
}

const quickTemplates: QuickTemplate[] = [
  {
    label: "Check K8s Pods",
    description: "List and monitor Kubernetes pods",
    prompt: "List running K8s pods in prod",
    icon: <svg className="h-4 w-4 text-purple-400" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.375 0 0 5.375 0 12s5.375 12 12 12 12-5.375 12-12S18.625 0 12 0zm0 22c-5.523 0-10-4.477-10-10S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10z"/>
    </svg>
  },
  {
    label: "Monitor EC2",
    description: "Check EC2 resource usage",
    prompt: "Show EC2 CPU & memory usage",
    icon: <svg className="h-4 w-4 text-purple-400" viewBox="0 0 24 24" fill="currentColor">
      <path d="M3 3h18v18H3V3zm16 16V5H5v14h14z"/>
    </svg>
  },
  {
    label: "Check Logs",
    description: "View application logs",
    prompt: "Show me the last 50 error logs",
    icon: <svg className="h-4 w-4 text-purple-400" viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z"/>
      <path d="M7 12h10v2H7zm0-4h10v2H7zm0 8h7v2H7z"/>
    </svg>
  },
  {
    label: "Security Scan",
    description: "Run security checks",
    prompt: "Run security vulnerability scan",
    icon: <svg className="h-4 w-4 text-purple-400" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
    </svg>
  }
];

type AssignmentMethod = 'chat' | 'jira' | 'webhook'

// Add new types for JIRA integration
interface JiraTicket {
  id: string;
  title: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  status: string;
  assignee: string;
  description: string;
  transitions?: Array<{
    id: string;
    name: string;
    to: string;
  }>;
}

interface JiraBoard {
  id: string;
  name: string;
  description: string;
  type: 'scrum' | 'kanban';
}

// Constants
const TICKETS_PER_PAGE = 5;

// Add more mock tickets for pagination demo
const JIRA_MOCK_DATA = {
  boards: [
    { 
      id: 'DEV', 
      name: 'Development Board', 
      description: 'Main development workflow',
      type: 'scrum'
    },
    { 
      id: 'OPS', 
      name: 'Operations Board', 
      description: 'DevOps and infrastructure tasks',
      type: 'kanban'
    }
  ] as JiraBoard[],
  tickets: [
    { 
      id: 'DEV-123', 
      title: 'Implement new feature', 
      priority: 'high',
      status: 'open',
      assignee: 'John Doe',
      description: 'Implement the new authentication feature with OAuth2 integration',
      transitions: [
        { id: 't1', name: 'Start Progress', to: 'in_progress' },
        { id: 't2', name: 'Review', to: 'review' }
      ]
    },
    { 
      id: 'DEV-124', 
      title: 'Fix security vulnerability', 
      priority: 'critical',
      status: 'open',
      assignee: 'Sarah Smith',
      description: 'Address the critical security vulnerability in the login system',
      transitions: [
        { id: 't1', name: 'Start Progress', to: 'in_progress' },
        { id: 't2', name: 'Review', to: 'review' }
      ]
    },
    { 
      id: 'DEV-125', 
      title: 'Optimize database queries', 
      priority: 'high',
      status: 'in_progress',
      assignee: 'Mike Brown',
      description: 'Improve database performance by optimizing slow queries and adding proper indexes',
      transitions: [
        { id: 't1', name: 'Review', to: 'review' },
        { id: 't2', name: 'Done', to: 'done' }
      ]
    },
    { 
      id: 'DEV-126', 
      title: 'Update dependencies', 
      priority: 'medium',
      status: 'open',
      assignee: 'Emma Wilson',
      description: 'Update all project dependencies to their latest stable versions',
      transitions: [
        { id: 't1', name: 'Start Progress', to: 'in_progress' },
        { id: 't2', name: 'Review', to: 'review' }
      ]
    }
  ] as JiraTicket[]
};

// Add type for webhook provider options
interface WebhookExample {
  event: string;
  format: Record<string, any>;
}

type WebhookExamples = Record<string, WebhookExample>;

// Update webhook examples to match providers
const webhookExamples: Partial<WebhookExamples> = {
  github: {
    event: 'pull_request.opened',
    format: {
      action: "opened",
      pull_request: {
        number: 123,
        title: "Add new feature",
        user: { login: "johndoe" },
        html_url: "https://github.com/org/repo/pull/123",
        changed_files: 5,
        additions: 150,
        deletions: 30
      },
      repository: { full_name: "org/repo" }
    }
  },
  gitlab: {
    event: 'merge_request',
    format: {
      object_kind: "merge_request",
      object_attributes: {
        iid: 42,
        title: "Feature: Add new API endpoint",
        source_branch: "feature/new-api",
        target_branch: "main",
        url: "https://gitlab.com/org/repo/-/merge_requests/42"
      }
    }
  },
  datadog: {
    event: 'alert',
    format: {
      alert: {
        title: "High CPU Usage",
        status: "Triggered",
        severity: "ERROR",
        metric: "system.cpu.user",
        threshold: 90
      }
    }
  },
  prometheus: {
    event: 'alert',
    format: {
      alerts: [{
        status: "firing",
        labels: { alertname: "HighLatency" },
        annotations: {
          summary: "High latency detected",
          description: "Latency above threshold"
        }
      }]
    }
  },
  pagerduty: {
    event: 'incident.triggered',
    format: {
      incident: {
        id: "PT4KHLK",
        title: "Production database is down",
        urgency: "high",
        html_url: "https://org.pagerduty.com/incidents/PT4KHLK"
      }
    }
  },
  jenkins: {
    event: 'build',
    format: {
      build: {
        number: "123",
        phase: "COMPLETED",
        status: "SUCCESS",
        full_url: "https://jenkins.org/job/main/123"
      }
    }
  },
  servicenow: {
    event: 'incident.created',
    format: {
      incident: {
        number: "INC0010001",
        short_description: "Email service is down",
        priority: "1 - Critical",
        assigned_to: "John Doe"
      }
    }
  },
  aws_eventbridge: {
    event: 'aws.ec2',
    format: {
      "detail-type": "EC2 Instance State-change Notification",
      region: "us-east-1",
      detail: {
        "instance-id": "i-1234567890abcdef0",
        state: "running"
      }
    }
  },
  custom: {
    event: 'custom',
    format: {
      event: {
        type: "custom",
        data: "Your custom event data here"
      }
    }
  }
};

// Helper function to safely get nested object value
const getNestedValue = (obj: any, path: string[]): any => {
  return path.reduce((current, key) => 
    (current && current[key] !== undefined ? current[key] : undefined), 
    obj
  );
};

// Update the PromptTemplateEditor component
function PromptTemplateEditor({
  value,
  onChange,
  provider,
  eventType,
  variables
}: {
  value: string;
  onChange: (value: string) => void;
  provider: WebhookProvider;
  eventType: string;
  variables: ContextVariable[];
}) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [cursorPosition, setCursorPosition] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Format the display value to show user-friendly placeholders
  const getDisplayValue = (rawValue: string) => {
    let displayValue = rawValue;
    variables.forEach(variable => {
      const pattern = new RegExp(`{{.${variable.path}}}`, 'g');
      displayValue = displayValue.replace(pattern, `⟪${variable.description}⟫`);
    });
    return displayValue;
  };

  // Convert display value back to template format
  const getRawValue = (displayValue: string) => {
    let rawValue = displayValue;
    variables.forEach(variable => {
      const pattern = new RegExp(`⟪${variable.description}⟫`, 'g');
      rawValue = rawValue.replace(pattern, `{{.${variable.path}}}`);
    });
    return rawValue;
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === '{' && e.shiftKey) {
      e.preventDefault();
      setShowSuggestions(true);
    }
  };

  const insertVariable = (variable: ContextVariable) => {
    const before = value.slice(0, cursorPosition);
    const after = value.slice(cursorPosition);
    const newValue = `${before}⟪${variable.description}⟫${after}`;
    onChange(getRawValue(newValue));
    setShowSuggestions(false);
    
    if (textareaRef.current) {
      const newPosition = cursorPosition + variable.description.length + 2; // +2 for ⟪⟫
      textareaRef.current.focus();
      textareaRef.current.setSelectionRange(newPosition, newPosition);
    }
  };

  // Example prompts based on event type
  const getExamplePrompt = () => {
    switch (`${provider}.${eventType}`) {
      case 'github.pull_request.opened':
        return 'Please review PR #⟪PR number⟫ titled "⟪PR title⟫" by ⟪PR author⟫. Focus on code quality and security.';
      case 'github.push':
        return 'New commits pushed to ⟪Git ref⟫ by ⟪Pusher name⟫. Latest commit: "⟪Latest commit message⟫"';
      case 'jira.issue.created':
        return 'New JIRA issue ⟪Issue key⟫: "⟪Issue title⟫" with priority ⟪Issue priority⟫';
      case 'slack.message.created':
        return 'New message in #⟪Channel name⟫ from ⟪Sender name⟫: "⟪Message text⟫"';
      default:
        return 'Enter your prompt here... Use variables to make it dynamic';
    }
  };

  return (
    <div className="relative">
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Code className="h-4 w-4 text-purple-400" />
          <span className="text-sm font-medium text-slate-200">Prompt Template</span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs text-slate-400 hover:text-purple-400"
            onClick={() => onChange(getRawValue(getExamplePrompt()))}
          >
            <MessageSquare className="h-3 w-3 mr-1" />
            Use Example
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs text-slate-400 hover:text-purple-400"
            onClick={() => setShowSuggestions(true)}
          >
            <Code className="h-3 w-3 mr-1" />
            Insert Variable
          </Button>
        </div>
      </div>
      
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={getDisplayValue(value)}
          onChange={(e) => {
            onChange(getRawValue(e.target.value));
            setCursorPosition(e.target.selectionStart);
          }}
          onKeyDown={handleKeyDown}
          onClick={(e) => {
            const target = e.target as HTMLTextAreaElement;
            setCursorPosition(target.selectionStart);
          }}
          placeholder={getExamplePrompt()}
          className="w-full h-32 bg-[#1E293B] border border-[#2D3B4E] rounded-lg p-3 text-sm text-slate-200 resize-none focus:border-purple-500"
        />

        {showSuggestions && (
          <div 
            className="fixed z-50 w-[600px] py-1 bg-[#1E293B] rounded-lg border border-[#2D3B4E] shadow-lg max-h-[300px] overflow-y-auto"
            style={{
              top: textareaRef.current ? 
                textareaRef.current.getBoundingClientRect().bottom + window.scrollY + 4 : 0,
              left: textareaRef.current ? 
                textareaRef.current.getBoundingClientRect().left + window.scrollX : 0
            }}
          >
            <div className="sticky top-0 px-3 py-2 border-b border-[#2D3B4E] bg-[#1E293B]">
              <h4 className="text-sm font-medium text-purple-400">Available Variables</h4>
              <p className="text-xs text-slate-400 mt-1">
                Click to insert or press Shift + {'{'} while typing
              </p>
            </div>
            <div className="p-1">
              {variables.map((variable) => (
                <button
                  key={variable.path}
                  onClick={() => insertVariable(variable)}
                  className="w-full px-3 py-2 text-left hover:bg-purple-500/10 rounded-md flex items-start gap-3 group"
                >
                  <Code className="h-4 w-4 text-purple-400 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-slate-200 flex items-center gap-2">
                      <span className="truncate">{variable.description}</span>
                      <span className="text-xs text-slate-500 group-hover:text-purple-400">
                        {variable.path}
                      </span>
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5">
                      Example: <span className="text-green-400">{JSON.stringify(variable.example)}</span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {value && (
        <div className="mt-2 p-3 rounded-lg bg-purple-500/5 border border-purple-500/20">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-purple-400">Raw Template</span>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 text-xs text-slate-400 hover:text-purple-400"
              onClick={() => {
                navigator.clipboard.writeText(value);
                toast({
                  title: "Copied to clipboard",
                  description: "The prompt template has been copied to your clipboard.",
                });
              }}
            >
              <Copy className="h-3 w-3 mr-1" />
              Copy
            </Button>
          </div>
          <div className="text-sm text-slate-500 font-mono whitespace-pre-wrap">
            {value}
          </div>
        </div>
      )}
    </div>
  );
}

// Update the EventTypeSelect component
function EventTypeSelect({
  value,
  onChange,
  events,
}: {
  value: string;
  onChange: (value: string) => void;
  events: WebhookEvent[];
}) {
  // Group events by category
  const eventsByCategory = events.reduce((acc, event) => {
    const category = event.category || 'Other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(event);
    return acc;
  }, {} as Record<string, WebhookEvent[]>);

  return (
    <div className="space-y-4">
      {Object.entries(eventsByCategory).map(([category, categoryEvents]) => (
        <div key={category} className="space-y-2">
          <h3 className="text-sm font-medium text-slate-400 px-1">{category}</h3>
          <div className="grid grid-cols-2 gap-3">
            {categoryEvents.map((event) => (
              <div
                key={event.type}
                onClick={() => onChange(event.type)}
                className={cn(
                  "w-full p-3 rounded-lg text-left transition-all cursor-pointer",
                  "border hover:border-opacity-30",
                  value === event.type
                    ? "bg-green-500/10 border-green-500/30"
                    : "bg-[#1E293B] border-[#2D3B4E] hover:bg-green-500/5"
                )}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onChange(event.type);
                  }
                }}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 flex-shrink-0">
                    {category === 'Pull Requests' && <GitPullRequest className="h-4 w-4 text-green-400" />}
                    {category === 'Issues' && <AlertCircle className="h-4 w-4 text-green-400" />}
                    {category === 'Repository' && <GitBranch className="h-4 w-4 text-green-400" />}
                    {category === 'Deployments' && <Rocket className="h-4 w-4 text-green-400" />}
                    {category === 'Messages' && <MessageSquare className="h-4 w-4 text-green-400" />}
                    {category === 'Reactions' && <Smile className="h-4 w-4 text-green-400" />}
                    {category === 'Sprints' && <Calendar className="h-4 w-4 text-green-400" />}
                    {category === 'Other' && <Code className="h-4 w-4 text-green-400" />}
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-slate-200 truncate">
                      {event.name}
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5 line-clamp-2">
                      {event.description}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// Utility function to extract field paths from JSON object
function extractFieldPaths(obj: any, prefix = ''): string[] {
  let paths: string[] = [];
  for (const key in obj) {
    const value = obj[key];
    const newPath = prefix ? `${prefix}.${key}` : key;
    paths.push(newPath);
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      paths = paths.concat(extractFieldPaths(value, newPath));
    }
  }
  return paths;
}

// Update the styles object
const styles = {
  dialog: {
    content: "bg-[#0F172A] border border-[#2A3347] p-0 max-w-5xl w-full h-[95vh] overflow-hidden flex flex-col",
    header: "p-6 border-b border-[#2A3347] flex-shrink-0",
    body: "flex-1 flex flex-col min-h-0 overflow-hidden"
  },
  // ... rest of styles object ...
};

// Add this helper function before the component
const areDatesEqual = (date1: Date, date2: Date): boolean => {
  return (
    date1.getFullYear() === date2.getFullYear() &&
    date1.getMonth() === date2.getMonth() &&
    date1.getDate() === date2.getDate() &&
    date1.getHours() === date2.getHours() &&
    date1.getMinutes() === date2.getMinutes()
  );
};

interface FormValues {
  description: string;
  slackTarget: string;
  scheduleType: 'quick' | 'custom';
  repeatOption: string;
  date: Date;
  webhookUrl: string;
  promptTemplate: string;
  eventType: string;
}

const formSchema = z.object({
  description: z.string()
    .min(1, 'Task description is required')
    .min(5, 'Description must be at least 5 characters long')
    .max(1000, 'Description should not exceed 1000 characters'),
  slackTarget: z.string()
    .min(1, 'Channel or user is required')
    .refine((val: string) => val.startsWith('#') || val.startsWith('@'), {
      message: 'Channel must start with # or user with @'
    }),
  scheduleType: z.enum(['quick', 'custom']),
  repeatOption: z.string(),
  date: z.date().refine((value) => value.getTime() > Date.now(), {
    message: 'Date must be in the future',
  }),
  webhookUrl: z.union([
    z.literal(''),
    z.string().url()
  ]),
  promptTemplate: z.string().optional(),
  eventType: z.string().optional()
});

export function TaskSchedulingModal({ isOpen, onClose, teammate, onSchedule, initialData }: TaskSchedulingModalProps) {
  const { user } = useUser();
  const { selectedTeammate, currentState } = useTeammateContext();
  
  // Form setup
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      description: initialData?.description || '',
      slackTarget: initialData?.slackTarget || '#general',
      scheduleType: initialData?.scheduleType || 'quick',
      repeatOption: initialData?.repeatOption || 'never',
      date: initialData?.date || addHours(new Date(), 1),
      webhookUrl: initialData?.webhookUrl || '',
      promptTemplate: initialData?.promptTemplate || '',
      eventType: initialData?.eventType || ''
    },
    mode: 'onChange'
  });

  // All state hooks grouped together
  const [hasJiraIntegration, setHasJiraIntegration] = useState(false);
  const [showTeammateSwitch, setShowTeammateSwitch] = useState(false);
  const [step, setStep] = useState<'method' | 'config' | 'schedule'>(initialData?.source ? 'config' : 'method');
  const [assignmentMethod, setAssignmentMethod] = useState<'chat' | 'jira' | 'webhook'>(
    initialData?.assignmentMethod || 'chat'
  );
  const [selectedBoard, setSelectedBoard] = useState<string>('');
  const [selectedTicket, setSelectedTicket] = useState<string>('');
  const [additionalContext, setAdditionalContext] = useState('');
  const [shouldComment, setShouldComment] = useState(true);
  const [shouldTransition, setShouldTransition] = useState(true);
  const [selectedTransition, setSelectedTransition] = useState('');
  const [repeatOption, setRepeatOption] = useState(initialData?.repeatOption || 'never');
  const [slackTarget, setSlackTarget] = useState(initialData?.slackTarget || '');
  const [webhookUrl, setWebhookUrl] = useState(initialData?.webhookUrl || '');
  const [webhookProvider, setWebhookProvider] = useState<WebhookProvider | null>(initialData?.webhookProvider || null);
  const [promptTemplate, setPromptTemplate] = useState(initialData?.promptTemplate || '');
  const [ticketsPage, setTicketsPage] = useState(1);
  const [ticketSearch, setTicketSearch] = useState('');
  const [customTime, setCustomTime] = useState('09:00');
  const [eventType, setEventType] = useState(initialData?.eventType || '');
  const [currentStep, setCurrentStep] = useState<WebhookStep>('provider');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoadingProviders, setIsLoadingProviders] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<WebhookProvider | null>(null);
  const [currentTeammate, setCurrentTeammate] = useState<Teammate | null>(teammate || null);

  // All useEffect hooks grouped together
  useEffect(() => {
    // Check for JIRA integration on mount
    const checkJiraIntegration = async () => {
      if (!teammate?.uuid) return;
      try {
        const response = await fetch(`/api/teammates/${teammate.uuid}/integrations`);
        const data = await response.json();
        setHasJiraIntegration(data?.integrations?.some((i: string | Integration) => 
          typeof i === 'string' ? i.toLowerCase() === 'jira' : i.name.toLowerCase() === 'jira'
        ));
      } catch (error) {
        console.error('Failed to check JIRA integration:', error);
        setHasJiraIntegration(false);
      }
    };
    checkJiraIntegration();
  }, [teammate?.uuid]);

  useEffect(() => {
    if (webhookProvider) {
      setIsLoadingProviders(true);
      setTimeout(() => {
        setIsLoadingProviders(false);
        setSelectedProvider(webhookProvider);
      }, 800);
    }
  }, [webhookProvider]);

  useEffect(() => {
    if (isOpen) {
      const savedState = localStorage.getItem('taskSchedulingState');
      if (savedState) {
        try {
          const state = JSON.parse(savedState);
          setStep(state.step || 'method');
          setAssignmentMethod(state.assignmentMethod || 'chat');
          form.reset(state);
          localStorage.removeItem('taskSchedulingState');
        } catch (error) {
          console.error('Error restoring task scheduling state:', error);
          localStorage.removeItem('taskSchedulingState');
        }
      }
    }
  }, [isOpen, form]);

  // Cleanup effect
  useEffect(() => {
    return () => {
      localStorage.removeItem('taskSchedulingState');
    };
  }, []);

  // Schedule options for chat/webhook
  const scheduleOptions = [
    { 
      label: "In 1 hour", 
      icon: Clock, 
      value: addHours(new Date(), 1),
      description: format(addHours(new Date(), 1), 'h:mm a')
    },
    { 
      label: "Tomorrow morning", 
      icon: CalendarDays, 
      value: (() => {
        const tomorrow = addDays(new Date(), 1);
        tomorrow.setHours(9, 0, 0, 0);
        return tomorrow;
      })(),
      description: "Tomorrow at 9:00 AM"
    },
    { 
      label: "Next Monday", 
      icon: CalendarRange, 
      value: (() => {
        const today = new Date();
        const nextMonday = addDays(today, (8 - today.getDay()) % 7 || 7);
        nextMonday.setHours(10, 0, 0, 0);
        return nextMonday;
      })(),
      description: format((() => {
        const today = new Date();
        const nextMonday = addDays(today, (8 - today.getDay()) % 7 || 7);
        nextMonday.setHours(10, 0, 0, 0);
        return nextMonday;
      })(), 'MMM d, h:mm a')
    }
  ];

  // "scheduleType" now comes from form:
  const scheduleType = form.watch('scheduleType');

  // Quick helper: update form scheduleType on button click 
  const handleScheduleTypeChange = (type: 'quick' | 'custom') => {
    form.setValue('scheduleType', type, { shouldValidate: true });
  };

  // Update the schedule section
  const renderScheduleSection = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CalendarClock className="h-5 w-5 text-purple-400" />
          <h3 className="text-base font-medium text-slate-200">When should it run?</h3>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => handleScheduleTypeChange('quick')}
            variant="outline"
            size="sm"
            className={cn(
              "bg-[#1E293B] border-[#2D3B4E] hover:bg-purple-500/10",
              scheduleType === 'quick' && "bg-purple-500/10 border-purple-500/30"
            )}
          >
            Quick Options
          </Button>
          <Button
            onClick={() => handleScheduleTypeChange('custom')}
            variant="outline"
            size="sm"
            className={cn(
              "bg-[#1E293B] border-[#2D3B4E] hover:bg-purple-500/10",
              scheduleType === 'custom' && "bg-purple-500/10 border-purple-500/30"
            )}
          >
            Custom Schedule
          </Button>
        </div>
      </div>

      {scheduleType === 'quick' ? (
        <div className="grid grid-cols-3 gap-3">
          {scheduleOptions.map((option) => (
            <Button
              key={option.label}
              variant="outline"
              className={cn(
                "flex items-center gap-3 px-4 py-3 h-auto",
                "bg-[#1E293B] hover:bg-purple-500/10",
                "border-[#2D3B4E] hover:border-purple-500/30",
                areDatesEqual(form.getValues('date'), option.value) && "bg-purple-500/10 border-purple-500/30"
              )}
              onClick={() => {
                form.setValue('date', option.value, { shouldValidate: true });
              }}
            >
              <option.icon className="h-4 w-4 text-purple-400" />
              <div className="flex flex-col items-start gap-1">
                <div className="text-sm font-medium text-slate-200">{option.label}</div>
                <span className="text-xs text-slate-400">{option.description}</span>
              </div>
            </Button>
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          <div className="p-4 rounded-lg bg-[#1E293B] border border-[#2D3B4E]">
            <h3 className="text-sm font-medium text-slate-200 mb-1">Custom Schedule Setup</h3>
            <p className="text-xs text-slate-400">
              Pick a date on the calendar, select your time, then choose how often it should repeat.
            </p>
          </div>

          <div className="grid grid-cols-[1fr,auto] gap-4">
            <Calendar
              mode="single"
              selected={form.getValues('date')}
              onSelect={(newDate) => {
                if (newDate) {
                  const currentDate = form.getValues('date');
                  newDate.setHours(currentDate.getHours());
                  newDate.setMinutes(currentDate.getMinutes());
                  form.setValue('date', newDate, { shouldValidate: true });
                }
              }}
              className="rounded-lg border border-[#2D3B4E] bg-[#1E293B] p-3"
            />

            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-[#1E293B] border border-[#2D3B4E]">
                <h4 className="text-sm font-medium text-slate-200 mb-3">Select Time</h4>
                <Input
                  type="time"
                  value={format(form.getValues('date'), 'HH:mm')}
                  onChange={(e) => {
                    const [hours, minutes] = e.target.value.split(':');
                    const newDate = new Date(form.getValues('date'));
                    newDate.setHours(parseInt(hours), parseInt(minutes));
                    form.setValue('date', newDate, { shouldValidate: true });
                  }}
                  className="bg-[#1E293B] border-[#2D3B4E] h-10"
                />
              </div>

              <div className="p-4 rounded-lg bg-[#1E293B] border border-[#2D3B4E]">
                <h4 className="text-sm font-medium text-slate-200 mb-3">Repeat Options</h4>
                <Select
                  value={form.getValues('repeatOption')}
                  onValueChange={(value) => form.setValue('repeatOption', value, { shouldValidate: true })}
                >
                  <SelectTrigger className="bg-[#1E293B] border-[#2D3B4E] h-10">
                    <SelectValue placeholder="Choose frequency" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="never">Never</SelectItem>
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="weekly">Weekly</SelectItem>
                    <SelectItem value="monthly">Monthly</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="p-4 rounded-lg bg-[#1E293B] border border-[#2D3B4E]">
                <h4 className="text-sm font-medium text-slate-200 mb-2">Selected Schedule:</h4>
                <p className="text-sm text-slate-400">
                  {format(form.getValues('date'), 'MMMM d')} at {format(form.getValues('date'), 'h:mm a')}
                </p>
                {form.getValues('repeatOption') !== 'never' && (
                  <p className="text-sm text-purple-400 mt-1">
                    Repeats {form.getValues('repeatOption')}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const handleMethodSelect = (method: AssignmentMethod) => {
    setAssignmentMethod(method);
    setStep('config');
    // Reset webhook states when selecting webhook method
    if (method === 'webhook') {
      setWebhookProvider(null);
      setEventType('');
      setPromptTemplate('');
      setCurrentStep('provider');
    }
  };

  const renderMethodSelection = () => (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <ListTodo className="h-5 w-5 text-purple-400 flex-shrink-0" />
        <div>
          <h3 className="text-base font-medium text-slate-200">
            How would you like to assign this task?
          </h3>
          <p className="text-sm text-slate-400 mt-1">
            Choose how you want to create and manage this task
          </p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <button
          onClick={() => handleMethodSelect('chat')}
          className={cn(
            "relative p-4 rounded-lg text-left transition-all group",
            "border hover:border-opacity-30",
            assignmentMethod === 'chat'
              ? "bg-gradient-to-br from-purple-500/20 to-purple-500/5 border-purple-500/30"
              : "bg-gradient-to-br from-slate-800 to-slate-900 border-[#2D3B4E] hover:from-purple-500/10 hover:to-purple-500/5"
          )}
        >
          <div className="flex flex-col items-start gap-3">
            <img 
              src="https://cdn-icons-png.flaticon.com/512/2111/2111615.png" 
              alt="Slack" 
              className="h-6 w-6 object-contain" 
            />
            <div>
              <div className="text-sm font-medium text-slate-200">Chat Destination</div>
              <div className="text-xs text-slate-400 mt-1 line-clamp-2">Schedule tasks to run in Slack or Teams channels</div>
            </div>
            <Badge 
              variant="outline" 
              className="mt-auto border-purple-500/30 text-purple-400 text-xs bg-purple-500/5"
            >
              <Clock className="w-3 h-3 mr-1" />
              Scheduled
            </Badge>
          </div>
        </button>

        <button
          onClick={() => {
            if (!hasJiraIntegration) {
              toast({
                title: "JIRA Integration Required",
                description: "Please enable JIRA integration in your management console at app.kubiya.ai",
                variant: "destructive"
              });
              return;
            }
            handleMethodSelect('jira');
          }}
          className={cn(
            "relative p-4 rounded-lg text-left transition-all group",
            "border hover:border-opacity-30",
            !hasJiraIntegration && "opacity-50 cursor-not-allowed",
            assignmentMethod === 'jira'
              ? "bg-gradient-to-br from-blue-500/20 to-blue-500/5 border-blue-500/30"
              : "bg-gradient-to-br from-slate-800 to-slate-900 border-[#2D3B4E] hover:from-blue-500/10 hover:to-blue-500/5"
          )}
        >
          <div className="flex flex-col items-start gap-3">
            <img 
              src="https://cdn.worldvectorlogo.com/logos/jira-1.svg" 
              alt="JIRA" 
              className="h-6 w-6 object-contain" 
            />
            <div>
              <div className="text-sm font-medium text-slate-200">JIRA Ticket</div>
              <div className="text-xs text-slate-400 mt-1 line-clamp-2">Create and manage JIRA tickets with automated workflows</div>
            </div>
            <Badge 
              variant="outline" 
              className="mt-auto border-blue-500/30 text-blue-400 text-xs bg-blue-500/5"
            >
              <Trello className="w-3 h-3 mr-1" />
              Immediate
            </Badge>
            {!hasJiraIntegration && (
              <div className="absolute inset-0 bg-black/50 rounded-lg flex items-center justify-center">
                <Badge variant="outline" className="border-red-500/30 text-red-400 text-xs bg-red-500/5">
                  Integration Required
                </Badge>
              </div>
            )}
          </div>
        </button>

        <button
          onClick={() => handleMethodSelect('webhook')}
          className={cn(
            "relative p-4 rounded-lg text-left transition-all group",
            "border hover:border-opacity-30",
            assignmentMethod === 'webhook'
              ? "bg-gradient-to-br from-green-500/20 to-green-500/5 border-green-500/30"
              : "bg-gradient-to-br from-slate-800 to-slate-900 border-[#2D3B4E] hover:from-green-500/10 hover:to-green-500/5"
          )}
        >
          <div className="flex flex-col items-start gap-3">
            <Webhook className="h-6 w-6 text-green-400" />
            <div>
              <div className="text-sm font-medium text-slate-200">Webhook</div>
              <div className="text-xs text-slate-400 mt-1 line-clamp-2">Respond to events from external systems</div>
            </div>
            <Badge 
              variant="outline" 
              className="mt-auto border-green-500/30 text-green-400 text-xs bg-green-500/5"
            >
              <Webhook className="w-3 h-3 mr-1" />
              Event-Driven
            </Badge>
          </div>
        </button>
      </div>
    </div>
  );

  // Update the step content wrapper
  const renderStepContent = () => (
    <div className={cn(
      "transform transition-all duration-300",
      isLoadingProviders ? "opacity-50" : "opacity-100"
    )}>
      {step === 'method' ? (
        renderMethodSelection()
      ) : step === 'config' ? (
        assignmentMethod === 'chat' ? (
          renderChatFlow()
        ) : assignmentMethod === 'webhook' ? (
          <WebhookFlowSection
            webhookProvider={webhookProvider}
            eventType={eventType}
            promptTemplate={promptTemplate}
            currentStep={currentStep}
            setWebhookProvider={setWebhookProvider}
            setEventType={setEventType}
            setPromptTemplate={setPromptTemplate}
            setCurrentStep={setCurrentStep}
            session={{
              idToken: user?.sub || '',
              user: {
                email: user?.email || undefined,
                org_id: user?.org_id || undefined
              }
            }}
            teammate={teammate}
            standalone={false}
          />
        ) : null
      ) : (
        renderScheduleSection()
      )}
    </div>
  );

  const canProceed = () => {
    const errors = form.formState.errors;

    // DEBUG: Log the form data and errors on every render
    console.log("### DEBUG: canProceed() called ###");
    console.log("Form values:", form.getValues());
    console.log("Form errors:", errors);
    console.log("scheduleType from form.watch:", scheduleType);
    console.log("description length:", form.getValues('description')?.trim().length);
    console.log("slackTarget length:", form.getValues('slackTarget')?.trim().length);
    console.log("date (ISO):", form.getValues('date')?.toISOString());
    console.log("===========================================");

    return (
      !errors.description &&
      !errors.slackTarget &&
      !errors.date &&
      form.getValues('description').trim().length >= 5 &&
      form.getValues('slackTarget').trim().length >= 1 &&
      (scheduleType === 'quick' || scheduleType === 'custom')
    );
  };

  const handleNext = () => {
    // DEBUG: Log the step + valid state
    console.log("### DEBUG: handleNext() invoked ###");
    console.log("Current step:", step);
    console.log("canProceed() =>", canProceed());
    console.log("Form values at handleNext:", form.getValues());
    console.log("Form errors at handleNext:", form.formState.errors);
    console.log("=================================");

    if (step === 'method') {
      setStep('config');
    } else if (step === 'config') {
      if (assignmentMethod === 'jira') {
        handleSubmit();
      } else {
        setStep('schedule');
      }
    } else if (step === 'schedule') {
      handleSubmit();
    }
  };

  const handleBack = () => {
    if (step === 'config') {
      // Reset all states when going back to method selection
      setStep('method');
      setAssignmentMethod('chat');
      setSelectedBoard('');
      setSelectedTicket('');
      setAdditionalContext('');
      setShouldComment(true);
      setShouldTransition(true);
      setSelectedTransition('');
      setWebhookUrl('');
      setWebhookProvider(null);
      setPromptTemplate('');
      setTicketsPage(1);
      setTicketSearch('');
      setCustomTime('09:00');
      setEventType('');
      setCurrentStep('provider');
    } else if (step === 'schedule') {
      setStep('config');
    }
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!isValid()) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const formData = form.getValues();
      const cronString = formData.scheduleType === 'custom' ? getCronString(formData.date, formData.repeatOption) : '';
      
      // Ensure date is properly formatted and in UTC
      const scheduleDate = new Date(formData.date);
      const scheduleTime = scheduleDate.toISOString();
      
      // Format teammate name as requested (demo_teammate format)
      const formattedTeammateName = teammate?.name ? 
        teammate.name.toLowerCase().replace(/\s+/g, '_') : 
        'demo_teammate';
      
      const payload: ScheduleTaskPayload = {
        schedule_time: scheduleTime,
        channel_id: formData.slackTarget,
        task_description: formData.description,
        selected_agent: formattedTeammateName,
        cron_string: cronString || ''
      };

      console.log('Scheduling task with payload:', payload);
      const result = await onSchedule(payload);

      // Show success toast immediately
      toast({
        title: "Task Scheduled Successfully",
        description: `Task will run ${cronString ? 'on schedule' : 'at'} ${format(scheduleDate, 'PPpp')}`,
        variant: "default",
        duration: 4000,
      });

      // Create an assistant message that will appear in the chat flow
      const assistantMessage = {
        id: `scheduled-task-${Date.now()}-assistant`,
        role: 'assistant',
        content: [],
        metadata: {
          custom: {
            isScheduledTask: true,
            task: {
              id: `scheduled-task-${Date.now()}`,
              task_id: result.task_id,
              task_uuid: result.task_uuid,
              scheduled_time: scheduleDate.toISOString(),
              parameters: {
                message_text: formData.description,
                cron_string: cronString || undefined,
                team_id: teammate?.team_id || '',
                user_email: teammate?.email || '',
                channel_id: formData.slackTarget
              },
              status: 'scheduled',
              created_at: new Date().toISOString()
            }
          }
        },
        createdAt: new Date()
      };

      // Create a system message for tracking
      const systemMessage = {
        id: `scheduled-task-${Date.now()}-system`,
        role: 'system',
        content: [
          {
            type: 'text',
            text: `✅ Task scheduled successfully\n${formData.description}\n${
              cronString 
                ? `Recurring: ${cronString}` 
                : `Scheduled for: ${format(scheduleDate, 'PPpp')}`
            }`
          }
        ],
        metadata: {
          custom: {
            isSystemMessage: true,
            scheduledTask: result
          }
        },
        createdAt: new Date()
      };

      // Add both messages to the chat
      if (window.postMessage) {
        // First add the system message for tracking
        window.postMessage({
          type: 'ADD_SYSTEM_MESSAGE',
          message: systemMessage
        }, '*');

        // Then add the assistant message that will be visible in the chat flow
        window.postMessage({
          type: 'ADD_ASSISTANT_MESSAGE',
          message: assistantMessage
        }, '*');
      }

      // Close modal and reset state
      handleClose();

    } catch (err) {
      console.error('Failed to schedule task:', err);
      setError(err instanceof Error ? err.message : 'Failed to schedule task. Please try again.');
      
      toast({
        title: "Failed to Schedule Task",
        description: err instanceof Error ? err.message : 'Please try again',
        variant: "destructive",
        duration: 5000,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderChatFlow = () => (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <MessageSquare className="h-5 w-5 text-purple-400 flex-shrink-0" />
        <div>
          <h3 className="text-base font-medium text-slate-200">Task Configuration</h3>
          <p className="text-sm text-slate-400">Configure your task and its destination</p>
        </div>
      </div>

      <div className="space-y-4">
        {/* Task Description */}
        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <div className="flex items-center justify-between">
                <FormLabel className="text-sm font-medium text-slate-200">
                  Task Description
                </FormLabel>
              </div>
              <FormControl>
                <textarea
                  {...field}
                  placeholder="Describe what you want the AI to do..."
                  className={cn(
                    "w-full h-[120px] bg-[#1A2438] border-[#2D3B4E] rounded-lg p-3 text-slate-200 resize-none focus:border-purple-500 text-sm",
                    form.formState.errors.description && "border-red-500 focus:border-red-500"
                  )}
                />
              </FormControl>
              {form.formState.errors.description && (
                <p className="mt-1 text-xs text-red-400">
                  {form.formState.errors.description.message?.toString()}
                </p>
              )}
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Channel / Slack Target */}
        <FormField
          control={form.control}
          name="slackTarget"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-sm font-medium text-slate-200">
                Destination (Channel/User)
              </FormLabel>
              <FormControl>
                <div className="relative">
                  <Input
                    {...field}
                    placeholder="#general or @mate"
                    className={cn(
                      "bg-[#1A2438] border-[#2D3B4E] text-slate-200",
                      form.formState.errors.slackTarget && "border-red-500 focus:border-red-500"
                    )}
                  />
                </div>
              </FormControl>
              {form.formState.errors.slackTarget && (
                <p className="mt-1 text-xs text-red-400">
                  {form.formState.errors.slackTarget.message?.toString()}
                </p>
              )}
              <FormMessage />
            </FormItem>
          )}
        />

        {/* You can add a short note reminding the user to pick a date/time too */}
        <p className="text-xs text-slate-400">@someone or #channel must be in the future date/time below</p>

      </div>
    </div>
  );

  const isBackDisabled = () => {
    return false; // Always allow going back
  };

  const getButtonText = () => {
    if (step === 'method') return 'Continue to Details';
    if (step === 'config') {
      if (assignmentMethod === 'jira') return 'Create Task';
      return 'Set Schedule';
    }
    return 'Schedule Task';
  };

  const renderStepIndicator = () => (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-2 p-1.5 rounded-lg bg-[#141B2B] border border-[#2D3B4E]">
        {/* Method Selection Step */}
        <button
          onClick={() => {
            if (step !== 'method') handleBack();
          }}
          className={cn(
            "flex items-center rounded-full px-2.5 py-1 transition-all text-xs",
            step === 'method'
              ? "bg-purple-500 text-white"
              : "border border-purple-500/30 hover:bg-purple-500/10 text-purple-400"
          )}
        >
          <ListTodo className="h-3 w-3 mr-1" />
          Method
        </button>

        {/* Configuration Step */}
        {step !== 'method' && (
          <>
            <ChevronRight className="h-3.5 w-3.5 text-slate-600" />
            <div className={cn(
              "flex items-center rounded-full px-2.5 py-1 text-xs",
              step === 'config'
                ? "bg-purple-500 text-white"
                : "border border-purple-500/30 text-purple-400"
            )}>
              {assignmentMethod === 'chat' && (
                <>
                  <MessageSquare className="h-3 w-3 mr-1" />
                  Details
                </>
              )}
              {assignmentMethod === 'jira' && (
                <>
                  <Trello className="h-3 w-3 mr-1" />
                  Ticket
                </>
              )}
              {assignmentMethod === 'webhook' && (
                <>
                  <Webhook className="h-3 w-3 mr-1" />
                  Webhook
                </>
              )}
            </div>
          </>
        )}

        {/* Schedule Step */}
        {step === 'schedule' && (
          <>
            <ChevronRight className="h-3.5 w-3.5 text-slate-600" />
            <div className="flex items-center rounded-full px-2.5 py-1 text-xs bg-purple-500 text-white">
              <Clock className="h-3 w-3 mr-1" />
              Schedule
            </div>
          </>
        )}
      </div>
    </div>
  );

  const handleTeammateSelect = (newTeammate: Teammate) => {
    setCurrentTeammate(newTeammate);
    setShowTeammateSwitch(false);
  };

  const handleClose = () => {
    // Reset form
    form.reset({
      description: '',
      slackTarget: '#general',
      scheduleType: 'quick',
      repeatOption: 'never',
      date: addHours(new Date(), 1),
      webhookUrl: '',
      promptTemplate: '',
      eventType: ''
    });

    // Reset all state variables
    setStep('method');
    setAssignmentMethod('chat');
    setSelectedBoard('');
    setSelectedTicket('');
    setAdditionalContext('');
    setShouldComment(true);
    setShouldTransition(true);
    setSelectedTransition('');
    setWebhookUrl('');
    setWebhookProvider(null);
    setPromptTemplate('');
    setTicketsPage(1);
    setTicketSearch('');
    setCustomTime('09:00');
    setEventType('');
    setCurrentStep('provider');
    setShowTeammateSwitch(false);
    setError(null);
    setIsSubmitting(false);

    // Remove any saved state from localStorage
    localStorage.removeItem('taskSchedulingState');

    // Close the modal
    onClose();
  };

  if (!teammate) {
    return null;
  }

  const isValid = () => {
    const formState = form.getValues();
    const formErrors = form.formState.errors;
    
    // Basic validation for required fields
    if (!formState.description?.trim() || formErrors.description) {
      return false;
    }
    
    if (!formState.slackTarget?.trim() || formErrors.slackTarget) {
      return false;
    }
    
    if (!formState.date || formErrors.date) {
      return false;
    }
    
    // All validations passed
    return true;
  };

  const getCronString = (date: Date, repeatOption: string): string => {
    const minutes = date.getMinutes();
    const hours = date.getHours();
    const dayOfMonth = date.getDate();
    const dayOfWeek = date.getDay();

    switch (repeatOption) {
      case 'never':
        return '';
      case 'daily':
        return `${minutes} ${hours} * * *`;
      case 'weekly':
        return `${minutes} ${hours} * * ${dayOfWeek}`;
      case 'monthly':
        return `${minutes} ${hours} ${dayOfMonth} * *`;
      default:
        return '';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <FormProvider {...form}>
        <DialogContent 
          className={cn(
            "max-w-5xl h-[90vh] bg-[#0F172A] border-[#1E293B] p-0 overflow-hidden flex flex-col"
          )}
          aria-describedby="dialog-description"
        >
          <DialogHeader className="px-6 py-4 border-b border-[#1E293B] flex-shrink-0">
            <div className="flex items-center justify-between">
              <DialogTitle className="text-lg font-medium text-slate-200">
                Assign a Task
              </DialogTitle>
              <DialogDescription id="dialog-description">
                Assign a task to {teammate?.name || 'your teammate'}
              </DialogDescription>
            </div>
          </DialogHeader>

          {error && (
            <div className="px-6 py-3 bg-red-500/10 border-y border-red-500/20">
              <div className="flex items-center gap-2 text-sm text-red-400">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            </div>
          )}

          <div className="flex-1 min-h-0 flex flex-col">
            {/* Teammate Context Card - Fixed at top */}
            <div className="px-6 py-3 border-b border-[#1E293B] flex-shrink-0">
              <TeammateContextCard 
                teammate={teammate}
                onSwitchTeammate={() => setShowTeammateSwitch(true)}
                className="w-full"
              />
            </div>

            {/* Step Indicator - Fixed below teammate card */}
            <div className="px-6 py-3 border-b border-[#1E293B] flex-shrink-0">
              {renderStepIndicator()}
            </div>

            {/* Scrollable Content Area */}
            <div className="flex-1 overflow-y-auto">
              <div className="px-6 py-4">
                {renderStepContent()}
              </div>
            </div>

            {/* Footer - Fixed at bottom */}
            <div className="px-6 py-4 border-t border-[#1E293B] flex-shrink-0">
              <div className="flex justify-between w-full">
                {step !== 'method' && (
                  <Button
                    variant="outline"
                    size="lg"
                    onClick={handleBack}
                    className="bg-[#1E293B] border-[#2D3B4E] hover:bg-emerald-500/10 text-slate-200"
                    disabled={isBackDisabled() || isSubmitting}
                  >
                    <ArrowLeft className="h-5 w-5 mr-2" />
                    Back to {step === 'config' ? 'Task Type' : 'Configuration'}
                  </Button>
                )}
                {(assignmentMethod !== 'webhook' || step !== 'config') && (
                  <Button
                    size="lg"
                    onClick={step === 'schedule' ? handleSubmit : handleNext}
                    className={cn(
                      "ml-auto",
                      canProceed() 
                        ? "bg-emerald-500 hover:bg-emerald-600" 
                        : "bg-slate-700 text-slate-400 cursor-not-allowed"
                    )}
                    disabled={!canProceed() || isSubmitting}
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Scheduling...
                      </>
                    ) : (
                      getButtonText()
                    )}
                  </Button>
                )}
              </div>
            </div>
          </div>
        </DialogContent>
      </FormProvider>

      {showTeammateSwitch && teammate && (
        <TeammateSwitch
          currentTeammate={teammate}
          onSelect={handleTeammateSelect}
          onClose={() => setShowTeammateSwitch(false)}
        />
      )}
    </Dialog>
  );
} 