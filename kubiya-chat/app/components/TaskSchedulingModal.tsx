import { useState, useEffect, Dispatch, SetStateAction, useRef } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import { format, addHours, addDays, addWeeks, addMonths } from 'date-fns';
import { useTeammateContext } from "@/app/MyRuntimeProvider";
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
  Activity
} from 'lucide-react';
import { toast } from './ui/use-toast';
import { cn } from '@/lib/utils';
import { DialogFooter } from './ui/dialog';
import { Badge } from '@/app/components/ui/badge';
import { Calendar } from "@/app/components/ui/calendar";
import { useUser } from '@auth0/nextjs-auth0/client';
import { WebhookFlowSection } from './webhook/WebhookFlowSection';
import { WebhookProvider as ImportedWebhookProvider } from './webhook/providers';

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
type WebhookStep = 'provider' | 'event' | 'event_example' | 'prompt' | 'webhook';

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

interface TaskSchedulingModalProps {
  isOpen: boolean;
  onClose: () => void;
  teammate?: {
    uuid: string;
    name?: string;
    team_id?: string;
    user_id?: string;
    org_id?: string;
    email?: string;
    context?: string;
  };
  onSchedule: (data: any) => void;
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

export function TaskSchedulingModal({ isOpen, onClose, teammate, onSchedule, initialData }: TaskSchedulingModalProps) {
  const { user } = useUser();
  const { selectedTeammate, currentState } = useTeammateContext();
  const [hasJiraIntegration, setHasJiraIntegration] = useState(false);

  // Check for JIRA integration on mount
  useEffect(() => {
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

  // State management
  const [step, setStep] = useState<'method' | 'config' | 'schedule'>(initialData?.source ? 'config' : 'method');
  const [assignmentMethod, setAssignmentMethod] = useState<'chat' | 'jira' | 'webhook'>(
    initialData?.assignmentMethod || 'chat'
  );
  const [selectedBoard, setSelectedBoard] = useState<string>('');
  const [selectedTicket, setSelectedTicket] = useState<string>('');
  const [description, setDescription] = useState(initialData?.description || '');
  const [additionalContext, setAdditionalContext] = useState('');
  const [shouldComment, setShouldComment] = useState(true);
  const [shouldTransition, setShouldTransition] = useState(true);
  const [selectedTransition, setSelectedTransition] = useState('');
  const [date, setDate] = useState<Date>(initialData?.date || new Date());
  const [scheduleType, setScheduleType] = useState<'quick' | 'custom'>(
    initialData?.scheduleType || 'quick'
  );
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

  // Reset states when assignment method changes
  useEffect(() => {
    setSelectedBoard('');
    setSelectedTicket('');
    setDescription('');
    setAdditionalContext('');
    setShouldComment(true);
    setShouldTransition(true);
    setSelectedTransition('');
  }, [assignmentMethod]);

  // Schedule options for chat/webhook
  const scheduleOptions = [
    { 
      label: "In 1 hour", 
      icon: Clock, 
      value: addHours(new Date(), 1),
      description: format(addHours(new Date(), 1), 'h:mm a')
    },
    { 
      label: "Tomorrow 9 AM", 
      icon: CalendarDays, 
      value: (() => {
        const tomorrow = addDays(new Date(), 1);
        tomorrow.setHours(9, 0, 0, 0);
        return tomorrow;
      })(),
      description: "Tomorrow at 9:00 AM"
    },
    { 
      label: "Next Monday 10 AM", 
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

  // Schedule section for chat/webhook
  const renderScheduleSection = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CalendarClock className="h-5 w-5 text-purple-400" />
          <h3 className="text-base font-medium text-slate-200">When should it run?</h3>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setScheduleType('quick')}
            className={cn(
              "bg-[#1E293B] border-[#2D3B4E] hover:bg-purple-500/10",
              scheduleType === 'quick' && "bg-purple-500/10 border-purple-500/30"
            )}
          >
            Quick Options
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setScheduleType('custom')}
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
                date.getTime() === option.value.getTime() && "bg-purple-500/10 border-purple-500/30"
              )}
              onClick={() => setDate(option.value)}
            >
              <div className="flex flex-col items-start gap-3">
                <div className="text-sm font-medium text-slate-200">{option.label}</div>
                <span className="text-xs text-slate-400">{option.description}</span>
              </div>
            </Button>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-[1fr,auto] gap-4">
          <Calendar
            mode="single"
            selected={date}
            onSelect={(newDate) => handleDateSelect(newDate)}
            className="rounded-lg border border-[#2D3B4E] bg-[#1E293B] p-3"
          />
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-[#1E293B] border border-[#2D3B4E]">
              <h4 className="text-sm font-medium text-slate-200 mb-3">Time</h4>
              <Input
                type="time"
                value={customTime}
                onChange={(e) => {
                  setCustomTime(e.target.value);
                  const [hours, minutes] = e.target.value.split(':');
                  const newDate = new Date(date);
                  newDate.setHours(parseInt(hours), parseInt(minutes));
                  setDate(newDate);
                }}
                className="bg-[#1E293B] border-[#2D3B4E] h-10"
              />
            </div>

            <div className="p-4 rounded-lg bg-[#1E293B] border border-[#2D3B4E]">
              <h4 className="text-sm font-medium text-slate-200 mb-3">Repeat</h4>
              <Select value={repeatOption} onValueChange={setRepeatOption}>
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
                {format(date, 'MMMM d')} at {format(date, 'h:mm a')}
              </p>
              {repeatOption !== 'never' && (
                <p className="text-sm text-purple-400 mt-1">Repeats {repeatOption}</p>
              )}
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

  // Add loading states
  const [isLoadingProviders, setIsLoadingProviders] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<WebhookProvider | null>(null);

  // Add provider loading effect
  useEffect(() => {
    if (webhookProvider) {
      setIsLoadingProviders(true);
      setTimeout(() => {
        setIsLoadingProviders(false);
        setSelectedProvider(webhookProvider);
      }, 800);
    }
  }, [webhookProvider]);

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
    switch (step) {
      case 'method':
        return true;
      case 'config':
        switch (assignmentMethod) {
          case 'chat':
            return slackTarget.trim().length > 0;
          case 'webhook':
            return webhookUrl.trim().length > 0;
          default:
            return false;
        }
      case 'schedule':
        return true;
    }
  };

  const handleNext = () => {
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
      setDescription('');
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

  if (!teammate) {
    return null;
  }

  const isValid = description.trim().length > 0 && !!date && slackTarget.trim().length > 0;

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

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    try {
      const channelId = slackTarget.startsWith('#') ? slackTarget.substring(1) : slackTarget;
      const taskUuid = crypto.randomUUID();
      const taskId = taskUuid.replace(/-/g, '').substring(0, 32);
      const scheduledTime = date.toISOString();
      
      const taskData = {
        channel_id: channelId,
        channel_name: `#${channelId}`,
        created_at: new Date().toISOString(),
        next_schedule_time: repeatOption !== 'never' ? scheduledTime : null,
        parameters: {
          action_context_data: {},
          body: {
            team: {
              id: teammate.team_id || ''
            },
            user: {
              id: teammate.user_id || ''
            }
          },
          channel_id: channelId,
          context: teammate.context || teammate.uuid,
          cron_string: getCronString(date, repeatOption),
          existing_session: false,
          message_text: description,
          organization_name: teammate.org_id || 'kubiya-ai',
          repeat: repeatOption !== 'never',
          task_uuid: taskUuid,
          team_id: teammate.team_id || '',
          user_email: teammate.email || ''
        },
        scheduled_time: scheduledTime,
        status: "scheduled",
        task_id: taskId,
        task_uuid: taskUuid,
        updated_at: null,
        user_email: teammate.email || ''
      };

      console.log('Submitting task:', JSON.stringify(taskData, null, 2));
      await onSchedule(taskData);
      
      toast({
        title: "Task Scheduled",
        description: "Your task has been scheduled successfully.",
      });
      onClose();
    } catch (error) {
      console.error('Failed to schedule task:', error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to schedule task. Please try again.",
      });
    }
  };

  const renderChatFlow = () => (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-6">
        <MessageSquare className="h-5 w-5 text-purple-400 flex-shrink-0" />
        <div>
          <h3 className="text-base font-medium text-slate-200">Where should the task run?</h3>
          <p className="text-sm text-slate-400 mt-1">Select a channel or user to receive the task updates</p>
        </div>
      </div>

      <div className="grid grid-cols-[2fr,3fr] gap-6">
        {/* Recent Selections */}
        <div className="space-y-4">
          <div className="p-4 rounded-lg bg-[#1E293B] border border-[#2D3B4E]">
            <h4 className="text-sm font-medium text-slate-200 mb-3">Recent Channels</h4>
            <div className="space-y-1">
              {['#devops', '#alerts', '#monitoring'].map((channel) => (
                <button
                  key={channel}
                  onClick={() => setSlackTarget(channel)}
                  className={cn(
                    "w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-sm",
                    "hover:bg-purple-500/10 transition-colors",
                    slackTarget === channel ? "bg-purple-500/10 text-purple-400" : "text-slate-400"
                  )}
                >
                  <span className="text-slate-500">#</span>
                  {channel.replace('#', '')}
                </button>
              ))}
            </div>
          </div>

          <div className="p-4 rounded-lg bg-[#1E293B] border border-[#2D3B4E]">
            <h4 className="text-sm font-medium text-slate-200 mb-3">Recent Users</h4>
            <div className="space-y-1">
              {['@john', '@sarah', '@devteam'].map((user) => (
                <button
                  key={user}
                  onClick={() => setSlackTarget(user)}
                  className={cn(
                    "w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm",
                    "hover:bg-purple-500/10 transition-colors",
                    slackTarget === user ? "bg-purple-500/10 text-purple-400" : "text-slate-400"
                  )}
                >
                  <span className="text-slate-500">@</span>
                  {user.replace('@', '')}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Main Configuration */}
        <div className="space-y-6">
          <div className="space-y-4">
            <label className="block text-sm font-medium text-slate-200">
              Channel or User
            </label>
            <div className="relative">
              <div className="absolute left-3 top-1/2 -translate-y-1/2">
                <img 
                  src="https://cdn-icons-png.flaticon.com/512/2111/2111615.png" 
                  alt="Slack" 
                  className="h-5 w-5 object-contain opacity-40" 
                />
              </div>
              <Input
                placeholder="Enter #channel or @user"
                value={slackTarget}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value && !value.startsWith('#') && !value.startsWith('@')) {
                    if (/^[A-Za-z]/.test(value)) {
                      setSlackTarget('#' + value);
                    }
                  } else {
                    setSlackTarget(value);
                  }
                }}
                className="bg-[#1E293B] border-[#2D3B4E] focus:border-purple-500 pl-10 pr-4 h-11 rounded-lg text-slate-200"
              />
            </div>
            <p className="text-xs text-slate-400">
              Use # for channels (e.g. #general) or @ for users (e.g. @john)
            </p>
          </div>

          <div className="p-4 rounded-lg bg-[#1E293B] border border-[#2D3B4E]">
            <h4 className="text-sm font-medium text-slate-200 mb-3">Task Description</h4>
            <textarea
              placeholder="What should the task do?"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full h-24 bg-[#1A2438] border-[#2D3B4E] rounded-lg p-3 text-slate-200 resize-none"
            />
          </div>
        </div>
      </div>
    </div>
  );

  const isBackDisabled = () => {
    return false; // Always allow going back
  };

  const getButtonText = () => {
    if (step === 'method') return 'Continue';
    if (step === 'config') {
      if (assignmentMethod === 'jira') return 'Create Task';
      return 'Next';
    }
    return 'Schedule Task';
  };

  const renderStepIndicator = () => (
    <div className="flex items-center gap-2 mb-6">
      <div className="flex items-center gap-2 p-2 rounded-lg bg-[#141B2B] border border-[#2D3B4E]">
        <button
          onClick={() => {
            if (step !== 'method') handleBack();
          }}
          className={cn(
            "flex items-center rounded-full px-3 py-1 transition-all",
            step === 'method'
              ? "bg-emerald-500 hover:bg-emerald-600 text-white"
              : "border border-emerald-500/30 hover:bg-emerald-500/10 text-emerald-400"
          )}
        >
          <ListTodo className="h-3 w-3 mr-1" />
          Task Type
        </button>
        {step !== 'method' && (
          <>
            <ChevronRight className="h-4 w-4 text-slate-600" />
            <div className={cn(
              "flex items-center rounded-full px-3 py-1",
              "bg-emerald-500 text-white"
            )}>
              {assignmentMethod === 'chat' && (
                <>
                  <MessageSquare className="h-3 w-3 mr-1" />
                  Chat
                </>
              )}
              {assignmentMethod === 'jira' && (
                <>
                  <Trello className="h-3 w-3 mr-1" />
                  JIRA
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
      </div>
    </div>
  );

  const handleDateSelect = (newDate: Date | undefined) => {
    if (newDate) {
      setDate(newDate);
    }
  };

  return (
    <Dialog 
      open={isOpen} 
      onOpenChange={(open) => {
        if (!open) {
          // Reset all states when dialog closes
          setStep('method');
          setAssignmentMethod('chat');
          setSelectedBoard('');
          setSelectedTicket('');
          setDescription('');
          setAdditionalContext('');
          setShouldComment(true);
          setShouldTransition(true);
          setSelectedTransition('');
          setDate(new Date());
          setScheduleType('quick');
          setRepeatOption('never');
          setSlackTarget('');
          setWebhookUrl('');
          setWebhookProvider(null);
          setPromptTemplate('');
          setTicketsPage(1);
          setTicketSearch('');
          setCustomTime('09:00');
          setEventType('');
          setCurrentStep('provider');
        }
        onClose();
      }}
    >
      <DialogContent className="max-w-[1200px] max-h-[95vh] bg-[#0F172A] border-[#1E293B] p-0 overflow-hidden flex flex-col">
        <DialogHeader className="p-8 border-b border-[#2D3B4E] flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                <Webhook className="h-6 w-6 text-emerald-400" />
              </div>
              <div>
                <DialogTitle className="text-2xl font-semibold text-slate-200">
                  Assign Task
                </DialogTitle>
                <DialogDescription className="text-base text-slate-400 mt-2">
                  Configure how you want to assign this task to {teammate?.name || 'the teammate'}.
                </DialogDescription>
              </div>
            </div>
            {renderStepIndicator()}
            <Button
              variant="ghost"
              size="lg"
              className="text-slate-400 hover:text-emerald-400"
              onClick={() => onClose()}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto p-8">
          {renderStepContent()}
        </div>

        <DialogFooter className="p-8 border-t border-[#2D3B4E] flex-shrink-0">
          <div className="flex justify-between w-full">
            {step !== 'method' && (
              <Button
                variant="outline"
                size="lg"
                onClick={handleBack}
                className="bg-[#1E293B] border-[#2D3B4E] hover:bg-emerald-500/10 text-slate-200"
                disabled={isBackDisabled()}
              >
                <ArrowLeft className="h-5 w-5 mr-2" />
                Back to {step === 'config' ? 'Task Type' : 'Configuration'}
              </Button>
            )}
            {(assignmentMethod !== 'webhook' || step !== 'config') && (
              <Button
                size="lg"
                onClick={handleNext}
                className={cn(
                  "ml-auto",
                  canProceed() 
                    ? "bg-emerald-500 hover:bg-emerald-600" 
                    : "bg-slate-700 text-slate-400 cursor-not-allowed"
                )}
                disabled={!canProceed()}
              >
                {getButtonText()}
                <ArrowRight className="h-5 w-5 ml-2" />
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
} 