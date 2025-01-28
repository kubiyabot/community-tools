import { useState, useEffect, Dispatch, SetStateAction, useRef, useMemo } from 'react';
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
  Activity,
  Wrench,
  Database,
  Terminal
} from 'lucide-react';
import { toast } from './ui/use-toast';
import { cn } from '@/lib/utils';
import { DialogFooter } from './ui/dialog';
import { Badge } from '@/app/components/ui/badge';
import { Calendar } from "@/app/components/ui/calendar";
import { useUser } from '@auth0/nextjs-auth0/client';
import { WebhookFlowSection } from './webhook/WebhookFlowSection';
import { WebhookProvider as ImportedWebhookProvider } from './webhook/providers';
import { TeammateInfo } from '@/app/types/teammate';
import { Integration } from '@/app/types/integration';
import { Avatar, AvatarImage, AvatarFallback } from '@/app/components/ui/avatar';
import { Check } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuCheckboxItem, DropdownMenuTrigger } from '@/app/components/ui/dropdown-menu';

// Type definitions
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

interface InitialTaskData {
  description?: string;
  slackTarget?: string;
  scheduleType?: 'quick' | 'custom';
  repeatOption?: string;
  date?: Date;
  source?: WebhookProvider;
  assignmentMethod?: AssignmentMethod;
  webhookProvider?: WebhookProvider | null;
  webhookUrl?: string;
  promptTemplate?: string;
  eventType?: string;
}

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

interface Starter {
  command: string;
  display_name: string;
  icon?: string;
}

interface TeammateCapabilities {
  tools?: any[];
  integrations?: Array<string | Integration>;
  starters?: Array<Starter>;
  instruction_type?: string;
  llm_model?: string;
  description?: string;
  runner?: string;
}

interface TeammateWithCapabilities extends TeammateInfo {
  capabilities?: TeammateCapabilities;
}

interface TaskSchedulingModalProps {
  isOpen: boolean;
  onClose: () => void;
  teammate?: TeammateInfo;
  onSchedule: (data: TaskData) => Promise<void>;
  initialData?: InitialTaskData;
  capabilities?: TeammateCapabilities;
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
const TEAMMATES_PER_PAGE = 5;

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

// Add type for teammate selection step
type ModalStep = 'teammate' | 'method' | 'config' | 'schedule';

// Add avatar generation logic
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

interface AvatarInput {
  uuid: string;
  name: string;
}

function generateAvatarUrl(input: AvatarInput) {
  const seed = (input.uuid + input.name).split('').reduce((acc: number, char: string, i: number) => 
    acc + (char.charCodeAt(0) * (i + 1)), 0);
  const randomIndex = Math.abs(Math.sin(seed) * AVATAR_IMAGES.length) | 0;
  return `/images/avatars/${AVATAR_IMAGES[randomIndex]}`;
}

// Add new types for filtering
interface TeammateFilter {
  searchTerm: string;
  integrations: string[];
  tools: string[];
}

interface Tool {
  name: string;
  type?: string;
  description?: string;
}

// Helper function to get the appropriate icon for an integration
const getIcon = (type: string) => {
  const checkType = (keyword: string) => type.toLowerCase().includes(keyword);

  // Integration-specific icons with direct URLs
  if (checkType('slack')) return <img src="https://cdn4.iconfinder.com/data/icons/logos-and-brands/512/306_Slack_logo-512.png" alt="Slack" className="h-4 w-4 object-contain" />;
  if (checkType('aws')) return <img src="https://uxwing.com/wp-content/themes/uxwing/download/brands-and-social-media/aws-icon.png" alt="AWS" className="h-4 w-4 object-contain" />;
  if (checkType('github')) return <img src="https://cdn-icons-png.flaticon.com/512/25/25231.png" alt="GitHub" className="h-4 w-4 object-contain" />;
  if (checkType('jira')) return <img src="https://cdn-icons-png.flaticon.com/512/5968/5968875.png" alt="Jira" className="h-4 w-4 object-contain" />;
  if (checkType('kubernetes')) return <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Kubernetes_logo_without_workmark.svg/2109px-Kubernetes_logo_without_workmark.svg.png" alt="Kubernetes" className="h-4 w-4 object-contain" />;
  
  // Other icons
  if (checkType('terraform')) return <img src="/icons/terraform.svg" alt="Terraform" className="h-4 w-4" />;
  if (checkType('tool')) return <Wrench className="h-4 w-4 text-purple-400" />;
  if (checkType('workflow')) return <GitBranch className="h-4 w-4 text-blue-400" />;
  if (checkType('database')) return <Database className="h-4 w-4 text-green-400" />;
  if (checkType('code')) return <Code className="h-4 w-4 text-yellow-400" />;
  return <Terminal className="h-4 w-4 text-purple-400" />;
};

export function TaskSchedulingModal({ isOpen, onClose, teammate, onSchedule, initialData, capabilities }: TaskSchedulingModalProps) {
  const { user } = useUser();
  const { selectedTeammate, currentState, teammates } = useTeammateContext();
  const [hasJiraIntegration, setHasJiraIntegration] = useState(false);

  // Move state declarations from renderTeammateSelection to here
  const [teammateCurrentPage, setTeammateCurrentPage] = useState(1);
  const [selectedTeammateForList, setSelectedTeammateForList] = useState<TeammateWithCapabilities | null>(null);
  const [teammateFilters, setTeammateFilters] = useState<TeammateFilter>({
    searchTerm: '',
    integrations: [],
    tools: []
  });

  // Move useMemo hooks to top level
  const availableTools = useMemo(() => {
    const tools = new Set<string>();
    capabilities?.tools?.forEach(tool => {
      if (typeof tool === 'string') {
        tools.add(tool);
      } else if (tool.name) {
        tools.add(tool.name);
      }
    });
    return Array.from(tools);
  }, [capabilities?.tools]);

  const availableIntegrations = useMemo(() => {
    const integrations = new Set<string>();
    capabilities?.integrations?.forEach(integration => {
      if (typeof integration === 'string') {
        integrations.add(integration);
      } else if (integration.name) {
        integrations.add(integration.name);
      }
    });
    return Array.from(integrations);
  }, [capabilities?.integrations]);

  // Filter teammates computation
  const filteredTeammates = useMemo(() => {
    if (!teammates) return [];
    
    return teammates.filter((t: TeammateWithCapabilities) => {
      // Search filter
      if (teammateFilters.searchTerm && !t.name.toLowerCase().includes(teammateFilters.searchTerm.toLowerCase())) {
        return false;
      }

      // Tools filter
      if (teammateFilters.tools.length > 0) {
        const teammateTools = t.capabilities?.tools || [];
        const hasMatchingTool = teammateFilters.tools.some(tool => 
          teammateTools.some((t: string | Tool) => 
            (typeof t === 'string' ? t : t.name).toLowerCase() === tool.toLowerCase()
          )
        );
        if (!hasMatchingTool) return false;
      }

      // Integrations filter
      if (teammateFilters.integrations.length > 0) {
        const teammateIntegrations = t.capabilities?.integrations || [];
        const hasMatchingIntegration = teammateFilters.integrations.some(integration =>
          teammateIntegrations.some((i: string | Integration) =>
            (typeof i === 'string' ? i : i.name).toLowerCase() === integration.toLowerCase()
          )
        );
        if (!hasMatchingIntegration) return false;
      }

      return true;
    });
  }, [teammates, teammateFilters]);

  // Add filterOptions computation back
  const filterOptions = useMemo(() => {
    const integrations = new Set<string>();
    const tools = new Set<string>();

    teammates?.forEach(t => {
      t.capabilities?.integrations?.forEach((i: Integration | string) => {
        integrations.add(typeof i === 'string' ? i : i.name);
      });
    });

    capabilities?.tools?.forEach((tool: Tool | string) => {
      if (typeof tool === 'string') {
        tools.add(tool);
      } else {
        tools.add(tool.name);
      }
    });

    return {
      integrations: Array.from(integrations),
      tools: Array.from(tools)
    };
  }, [teammates, capabilities?.tools]);

  // Add filter states
  const [filters, setFilters] = useState<TeammateFilter>({
    integrations: [],
    tools: [],
    searchTerm: ''
  });

  // Update step state to include teammate selection
  const [step, setStep] = useState<ModalStep>(initialData?.source ? 'config' : 'teammate');
  const [selectedTeammateId, setSelectedTeammateId] = useState<string | undefined>(teammate?.uuid);
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

  // Create a wrapper function to handle the step type conversion
  const handleWebhookStepChange = (step: 'provider' | 'event' | 'event_example' | 'prompt' | 'webhook') => {
    setCurrentStep(step);
  };

  // Update the WebhookFlowSection props
  const renderStepContent = () => (
    <div className={cn(
      "transform transition-all duration-300",
      isLoadingProviders ? "opacity-50" : "opacity-100"
    )}>
      {step === 'teammate' ? (
        renderTeammateSelection()
      ) : step === 'method' ? (
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
            setCurrentStep={handleWebhookStepChange as any}
            session={{
              idToken: user?.sub || '',
              user: {
                email: user?.email || undefined,
                org_id: user?.org_id || undefined
              }
            }}
            teammate={teammates.find(t => t.uuid === selectedTeammateId)}
            standalone={false}
          />
        ) : null
      ) : (
        renderScheduleSection()
      )}
    </div>
  );

  const canProceed = () => {
    switch (step as ModalStep) {
      case 'teammate':
        return !!selectedTeammateId;
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
    if (step === 'teammate') {
      setStep('method');
    } else if (step === 'method') {
      setStep('config');
    } else if (step === 'config') {
      if (assignmentMethod === 'jira') {
        handleSchedule();
      } else {
        setStep('schedule');
      }
    } else if (step === 'schedule') {
      handleSchedule();
    }
  };

  const handleBack = () => {
    if (step === 'method') {
      setStep('teammate');
    } else if (step === 'config') {
      setStep('method');
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

  const handleSchedule = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!teammate) return;

    try {
      const channelId = slackTarget?.startsWith('#') ? slackTarget.substring(1) : slackTarget || '';
      const now = new Date();
      const taskId = crypto.randomUUID();
      
      const taskData: TaskData = {
        channel_id: channelId,
        channel_name: `#${channelId}`,
        created_at: now.toISOString(),
        next_schedule_time: date ? date.toISOString() : null,
        parameters: {
          action_context_data: {},
          body: {
            team: { id: teammate.team_id || '' },
            user: { id: teammate.user_id || '' }
          },
          channel_id: channelId,
          context: description || '',
          cron_string: getCronString(date, repeatOption),
          existing_session: false,
          message_text: description || '',
          organization_name: teammate.org_id || '',
          repeat: repeatOption !== 'never',
          task_uuid: taskId,
          team_id: teammate.team_id || '',
          user_email: teammate.email || ''
        },
        scheduled_time: date ? date.toISOString() : now.toISOString(),
        status: "scheduled",
        task_id: taskId,
        task_uuid: taskId,
        updated_at: null,
        user_email: teammate.email || ''
      };

      await onSchedule(taskData);
      onClose();
    } catch (error) {
      console.error('Failed to schedule task:', error);
      toast({
        title: 'Error',
        description: 'Failed to schedule task. Please try again.',
        variant: 'destructive'
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
    if (step === 'teammate') return 'Continue';
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
            if (step !== 'teammate') handleBack();
          }}
          className={cn(
            "flex items-center rounded-full px-3 py-1 transition-all",
            step === 'teammate'
              ? "bg-emerald-500 hover:bg-emerald-600 text-white"
              : "border border-emerald-500/30 hover:bg-emerald-500/10 text-emerald-400"
          )}
        >
          <Activity className="h-3 w-3 mr-1" />
          Teammate
        </button>
        {step !== 'teammate' && (
          <>
            <ChevronRight className="h-4 w-4 text-slate-600" />
            <button
              onClick={() => step !== 'method' && setStep('method')}
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

  // Update renderTeammateSelection to use the memoized values
  const renderTeammateSelection = (): JSX.Element => {
    // Pagination
    const totalPages = Math.ceil(filteredTeammates.length / TEAMMATES_PER_PAGE);
    const paginatedTeammates = filteredTeammates.slice(
      (teammateCurrentPage - 1) * TEAMMATES_PER_PAGE,
      teammateCurrentPage * TEAMMATES_PER_PAGE
    );

    // If teammate is pre-selected, show the nice confirmation UI
    if (teammate && !selectedTeammateForList) {
      setSelectedTeammateForList(teammate as TeammateWithCapabilities);
    }

    const renderTeammateCard = (t: TeammateWithCapabilities) => {
      const isSelected = selectedTeammateForList?.uuid === t.uuid;
      const tools = t.capabilities?.tools || [];
      const integrations = t.capabilities?.integrations || [];
      const runner = t.capabilities?.runner;

      return (
        <div
          key={t.uuid}
          className={cn(
            "flex flex-col p-6 rounded-lg transition-all cursor-pointer border",
            isSelected
              ? "bg-gradient-to-br from-emerald-500/20 to-emerald-500/5 border-emerald-500/30"
              : "bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700/30 hover:border-emerald-500/20 hover:from-emerald-500/10 hover:to-emerald-500/5"
          )}
          onClick={() => setSelectedTeammateForList(t)}
        >
          <div className="flex items-start gap-4">
            <Avatar className="h-12 w-12 rounded-lg border-2 border-slate-700/50">
              <AvatarImage src={generateAvatarUrl({ uuid: t.uuid, name: t.name })} />
              <AvatarFallback>{t.name[0]}</AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <h4 className="text-base font-medium text-slate-200">{t.name}</h4>
                {isSelected && (
                  <Badge variant="outline" className="border-emerald-500/30 text-emerald-400 bg-emerald-500/10">
                    <Check className="h-3 w-3 mr-1" />
                    Selected
                  </Badge>
                )}
              </div>
              {runner && (
                <div className="flex items-center gap-2 mt-1 text-sm text-slate-400">
                  <Terminal className="h-4 w-4 text-purple-400" />
                  <span>Runs with {runner}</span>
                </div>
              )}
            </div>
          </div>

          <div className="mt-4 space-y-3">
            {tools.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <Wrench className="h-4 w-4" />
                  <span>Tools</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {tools.slice(0, 4).map((tool: Tool | string, idx: number) => (
                    <Badge
                      key={idx}
                      variant="secondary"
                      className="bg-purple-500/10 text-purple-400 border-purple-500/20"
                    >
                      {typeof tool === 'string' ? tool : tool.name}
                    </Badge>
                  ))}
                  {tools.length > 4 && (
                    <Badge variant="secondary" className="bg-purple-500/10 text-purple-400 border-purple-500/20">
                      +{tools.length - 4} more
                    </Badge>
                  )}
                </div>
              </div>
            )}

            {integrations.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <Database className="h-4 w-4" />
                  <span>Integrations</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {integrations.slice(0, 4).map((integration: Integration | string, idx: number) => {
                    const type = typeof integration === 'string' ? integration.toLowerCase() : integration.type?.toLowerCase() || integration.name.toLowerCase();
                    return (
                      <Badge
                        key={idx}
                        variant="secondary"
                        className="bg-blue-500/10 text-blue-400 border-blue-500/20 flex items-center gap-1.5"
                      >
                        {getIcon(type)}
                        {typeof integration === 'string' ? integration : integration.name}
                      </Badge>
                    );
                  })}
                  {integrations.length > 4 && (
                    <Badge variant="secondary" className="bg-blue-500/10 text-blue-400 border-blue-500/20">
                      +{integrations.length - 4} more
                    </Badge>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      );
    };

    const renderFilterChips = () => {
      const chips = [
        ...teammateFilters.tools.map(tool => ({
          label: tool,
          type: 'tool' as const
        })),
        ...teammateFilters.integrations.map(integration => ({
          label: integration,
          type: 'integration' as const
        }))
      ];

      if (chips.length === 0) return null;

      return (
        <div className="flex flex-wrap gap-2 mb-4">
          {chips.map(chip => (
            <Badge
              key={`${chip.type}-${chip.label}`}
              variant="secondary"
              className={cn(
                "flex items-center gap-1.5 px-2 py-1",
                chip.type === 'tool' 
                  ? "bg-purple-500/10 text-purple-400 border-purple-500/20"
                  : "bg-blue-500/10 text-blue-400 border-blue-500/20"
              )}
            >
              {chip.type === 'tool' ? <Wrench className="h-3 w-3" /> : <Database className="h-3 w-3" />}
              {chip.label}
              <X
                className="h-3 w-3 ml-1 cursor-pointer hover:text-red-400 transition-colors"
                onClick={() => {
                  setTeammateFilters(prev => ({
                    ...prev,
                    [chip.type === 'tool' ? 'tools' : 'integrations']: prev[chip.type === 'tool' ? 'tools' : 'integrations'].filter(
                      item => item !== chip.label
                    )
                  }));
                }}
              />
            </Badge>
          ))}
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs text-slate-400 hover:text-purple-400"
            onClick={() => setTeammateFilters({ searchTerm: '', tools: [], integrations: [] })}
          >
            Clear all
          </Button>
        </div>
      );
    };

    return (
      <div className="space-y-6">
        {selectedTeammateForList && teammate?.uuid === selectedTeammateForList.uuid && (
          <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-3">
            <div className="p-2 rounded-full bg-emerald-500/20">
              <Check className="h-5 w-5 text-emerald-400" />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-medium text-emerald-400">Perfect Choice!</h4>
              <p className="text-sm text-slate-400">
                {selectedTeammateForList.name} is ready to handle this task with their expertise.
              </p>
            </div>
          </div>
        )}

        <div className="flex items-center gap-4">
          <div className="flex-1">
            <Input
              placeholder="Search teammates..."
              value={teammateFilters.searchTerm}
              onChange={e => setTeammateFilters(prev => ({ ...prev, searchTerm: e.target.value }))}
              className="w-full"
            />
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2">
                <Database className="h-4 w-4" />
                Integrations
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              {filterOptions.integrations.map(integration => (
                <DropdownMenuCheckboxItem
                  key={integration}
                  checked={teammateFilters.integrations.includes(integration)}
                  onCheckedChange={(checked) => {
                    setTeammateFilters(prev => ({
                      ...prev,
                      integrations: checked
                        ? [...prev.integrations, integration]
                        : prev.integrations.filter(i => i !== integration)
                    }));
                  }}
                >
                  {integration}
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2">
                <Wrench className="h-4 w-4" />
                Tools
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              {filterOptions.tools.map(tool => (
                <DropdownMenuCheckboxItem
                  key={tool}
                  checked={teammateFilters.tools.includes(tool)}
                  onCheckedChange={(checked) => {
                    setTeammateFilters(prev => ({
                      ...prev,
                      tools: checked
                        ? [...prev.tools, tool]
                        : prev.tools.filter(t => t !== tool)
                    }));
                  }}
                >
                  {tool}
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {renderFilterChips()}

        <div className="grid grid-cols-2 gap-4">
          {paginatedTeammates.map(renderTeammateCard)}
        </div>

        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setTeammateCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={teammateCurrentPage === 1}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm text-slate-400">
              Page {teammateCurrentPage} of {totalPages}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setTeammateCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={teammateCurrentPage === totalPages}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>
    );
  };

  return (
    <Dialog 
      open={isOpen} 
      onOpenChange={(open) => {
        if (!open) {
          // Reset all states when dialog closes
          setStep('teammate');
          setAssignmentMethod('chat');
          setSelectedTeammateId(teammate?.uuid);
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
            {step !== 'teammate' && (
              <Button
                variant="outline"
                size="lg"
                onClick={handleBack}
                className="bg-[#1E293B] border-[#2D3B4E] hover:bg-emerald-500/10 text-slate-200"
                disabled={isBackDisabled()}
              >
                <ArrowLeft className="h-5 w-5 mr-2" />
                Back to {step === 'config' ? 'Task Type' : 'Teammate'}
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