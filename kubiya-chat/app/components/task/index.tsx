import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../ui/dialog';
import { Button } from '../ui/button';
import { Webhook, X, ArrowLeft, ArrowRight, AlertCircle } from 'lucide-react';
import { toast } from '../ui/use-toast';
import { cn } from '@/lib/utils';
import { TeammateSelector } from './TeammateSelector';
import { MethodSelection, type AssignmentMethod } from './MethodSelection';
import { ChatFlow } from './ChatFlow';
import { WebhookFlowSection } from '../webhook/WebhookFlowSection';
import { JiraFlow } from './JiraFlow';
import { ScheduleSection } from './ScheduleSection';
import { type Step } from '../webhook/types';
import { type WebhookProvider, type WebhookProviderType, WEBHOOK_PROVIDERS } from '../webhook/providers';
import { GitHubIcon, GitLabIcon } from '../webhook/VendorIcons';

interface TeammateInfo {
  uuid: string;
  name: string;
  team_id?: string;
  user_id?: string;
  org_id?: string;
  email?: string;
  context?: string;
  integrations?: (Integration | string)[];
}

interface Integration {
  name: string;
  type?: string;
}

interface JiraBoard {
  id: string;
  name: string;
  key: string;
}

interface JiraTicket {
  id: string;
  key: string;
  summary: string;
  status: string;
  priority: string;
}

interface JiraTransition {
  id: string;
  name: string;
  to: {
    name: string;
    statusCategory: {
      colorName: string;
    };
  };
}

type ModalStep = 'method' | 'config' | 'schedule' | 'details';

interface TaskSchedulingModalProps {
  isOpen: boolean;
  onClose: () => void;
  teammate?: TeammateInfo;
  onSchedule: (data: any) => Promise<void>;
  initialData?: {
    source?: string;
    assignmentMethod?: AssignmentMethod;
    description?: string;
    date?: Date;
    scheduleType?: 'quick' | 'custom';
    repeatOption?: string;
    slackTarget?: string;
    webhookProvider?: WebhookProvider;
    webhookUrl?: string;
    promptTemplate?: string;
    eventType?: string;
  };
}

interface TeammateContextType {
  teammates: TeammateInfo[];
  selectedTeammate?: TeammateInfo;
  setSelectedTeammate: (teammate: TeammateInfo | string) => void;
}

// Update mock data to match WebhookProvider type
const mockProviders: WebhookProvider[] = [
  {
    id: 'github',
    name: 'GitHub',
    description: 'GitHub webhook integration',
    icon: GitHubIcon,
    events: WEBHOOK_PROVIDERS.github.events
  },
  {
    id: 'gitlab',
    name: 'GitLab',
    description: 'GitLab webhook integration',
    icon: GitLabIcon,
    events: WEBHOOK_PROVIDERS.gitlab.events
  }
];

const mockBoards: JiraBoard[] = [
  { id: '1', name: 'Development Board', key: 'DEV' },
  { id: '2', name: 'Operations Board', key: 'OPS' }
];

const mockTickets: JiraTicket[] = [
  { id: '1', key: 'DEV-123', summary: 'Fix login bug', status: 'In Progress', priority: 'High' },
  { id: '2', key: 'DEV-124', summary: 'Update documentation', status: 'Open', priority: 'Medium' }
];

const mockTransitions: JiraTransition[] = [
  {
    id: '1',
    name: 'Start Progress',
    to: { name: 'In Progress', statusCategory: { colorName: 'blue-gray' } }
  },
  {
    id: '2',
    name: 'Complete',
    to: { name: 'Done', statusCategory: { colorName: 'green' } }
  }
];

export function TaskSchedulingModal({
  isOpen,
  onClose,
  teammate: initialTeammate,
  onSchedule,
  initialData
}: TaskSchedulingModalProps) {
  // Temporarily mock the teammates context until we find the proper hook
  const teammates: TeammateInfo[] = [];
  const hasJira = false;

  // Mock data for development
  const providers = mockProviders;
  const boards = mockBoards;
  const tickets = mockTickets;
  const transitions = mockTransitions;
  const totalPages = 1;

  // State management
  const [open, setOpen] = useState(isOpen);
  const [currentTeammate, setCurrentTeammate] = useState<TeammateInfo | undefined>(initialTeammate);
  const [step, setStep] = useState<ModalStep>(initialData?.source ? 'config' : 'method');
  const [assignmentMethod, setAssignmentMethod] = useState<AssignmentMethod>(initialData?.assignmentMethod || 'chat');
  const [description, setDescription] = useState(initialData?.description || '');
  const [date, setDate] = useState<Date>(initialData?.date || new Date());
  const [scheduleType, setScheduleType] = useState<'quick' | 'custom'>(initialData?.scheduleType || 'quick');
  const [repeatOption, setRepeatOption] = useState(initialData?.repeatOption || 'never');
  const [slackTarget, setSlackTarget] = useState(initialData?.slackTarget || '');
  const [webhookProvider, setWebhookProvider] = useState<WebhookProvider | null>(initialData?.webhookProvider || null);
  const [webhookUrl, setWebhookUrl] = useState(initialData?.webhookUrl || '');
  const [promptTemplate, setPromptTemplate] = useState(initialData?.promptTemplate || '');
  const [eventType, setEventType] = useState<string>(initialData?.eventType || '');
  const [customTime, setCustomTime] = useState('09:00');

  // JIRA specific states
  const [selectedBoard, setSelectedBoard] = useState('');
  const [selectedTicket, setSelectedTicket] = useState('');
  const [additionalContext, setAdditionalContext] = useState('');
  const [shouldComment, setShouldComment] = useState(true);
  const [shouldTransition, setShouldTransition] = useState(false);
  const [selectedTransition, setSelectedTransition] = useState('');
  const [ticketsPage, setTicketsPage] = useState(1);
  const [ticketSearch, setTicketSearch] = useState('');

  // Loading states
  const [isLoadingTeammate, setIsLoadingTeammate] = useState(false);
  const [isLoadingProviders, setIsLoadingProviders] = useState(false);
  const [isLoadingBoards, setIsLoadingBoards] = useState(false);
  const [isLoadingTickets, setIsLoadingTickets] = useState(false);
  const [isLoadingTransitions, setIsLoadingTransitions] = useState(false);

  // Handle dialog state changes
  const handleOpenChange = (newOpen: boolean) => {
    setOpen(newOpen);
    if (!newOpen) {
      // Reset all states to initial values
      setStep('method');
      setAssignmentMethod('chat');
      setDescription('');
      setDate(new Date());
      setScheduleType('quick');
      setRepeatOption('never');
      setSlackTarget('');
      setWebhookProvider(null);
      setPromptTemplate('');
      setEventType('');
      setCustomTime('09:00');
      
      // Reset JIRA states
      setSelectedBoard('');
      setSelectedTicket('');
      setAdditionalContext('');
      setShouldComment(true);
      setShouldTransition(false);
      setSelectedTransition('');
      setTicketsPage(1);
      setTicketSearch('');
      
      // Only reset teammate if not provided initially
      if (!initialTeammate) {
        setCurrentTeammate(undefined);
      }
      
      onClose();
    }
  };

  // Handle method selection
  const handleMethodSelect = (method: AssignmentMethod) => {
    setAssignmentMethod(method);
    setStep('config');
  };

  // Handle next step
  const handleNext = () => {
    if (!currentTeammate) {
      toast({
        title: "Error",
        description: "Please select a teammate first",
        variant: "destructive"
      });
      return;
    }

    switch (step) {
      case 'method':
        setStep('config');
        break;
      case 'config':
        if (assignmentMethod === 'webhook' && (!webhookProvider || !eventType)) {
          toast({
            title: "Error",
            description: "Please select a webhook provider and event type",
            variant: "destructive"
          });
          return;
        }
        setStep('schedule');
        break;
      case 'schedule':
        handleSubmit();
        break;
    }
  };

  // Handle back
  const handleBack = () => {
    if (step === 'config') {
      setStep('method');
    } else if (step === 'schedule') {
      setStep('config');
    }
  };

  // Handle submit
  const handleSubmit = async () => {
    if (!currentTeammate) return;
    
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
              id: currentTeammate.team_id || ''
            },
            user: {
              id: currentTeammate.user_id || ''
            }
          },
          channel_id: channelId,
          context: currentTeammate.context || currentTeammate.uuid,
          cron_string: getCronString(date, repeatOption),
          existing_session: false,
          message_text: description,
          organization_name: currentTeammate.org_id || 'kubiya-ai',
          repeat: repeatOption !== 'never',
          task_uuid: taskUuid,
          team_id: currentTeammate.team_id || '',
          user_email: currentTeammate.email || ''
        },
        scheduled_time: scheduledTime,
        status: "scheduled",
        task_id: taskId,
        task_uuid: taskUuid,
        updated_at: null,
        user_email: currentTeammate.email || ''
      };

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

  // Helper functions
  const isBackDisabled = () => {
    return step === 'method';
  };

  const getButtonText = () => {
    if (step === 'schedule') return 'Schedule';
    return 'Continue';
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

  // Render step indicator
  const renderStepIndicator = () => (
    <div className="flex items-center justify-center gap-2 mb-6">
      {['method', 'config', 'schedule'].map((s, index) => (
        <React.Fragment key={s}>
          <div
            className={`w-3 h-3 rounded-full ${
              step === s ? 'bg-purple-500' : index < ['method', 'config', 'schedule'].indexOf(step) ? 'bg-purple-800' : 'bg-slate-700'
            }`}
          />
          {index < 2 && (
            <div
              className={`w-16 h-0.5 ${
                index < ['method', 'config', 'schedule'].indexOf(step) ? 'bg-purple-800' : 'bg-slate-700'
              }`}
            />
          )}
        </React.Fragment>
      ))}
    </div>
  );

  // Render step content
  const renderStepContent = () => {
    if (!currentTeammate) {
      return (
        <div className="flex flex-col items-center justify-center py-12">
          <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mb-4">
            <AlertCircle className="h-8 w-8 text-slate-400" />
          </div>
          <h3 className="text-lg font-medium text-slate-200 mb-2">No Teammate Selected</h3>
          <p className="text-sm text-slate-400">Please select a teammate to continue</p>
        </div>
      );
    }

    switch (step) {
      case 'method':
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <TeammateSelector
                currentTeammate={currentTeammate}
                onTeammateSelect={setCurrentTeammate}
                teammates={teammates}
                isLoading={isLoadingTeammate}
              />
            </div>
            <MethodSelection
              currentTeammate={currentTeammate}
              hasJira={hasJira}
              onMethodSelect={handleMethodSelect}
            />
          </div>
        );
      case 'config':
        switch (assignmentMethod) {
          case 'chat':
            return (
              <ChatFlow
                slackTarget={slackTarget}
                onSlackTargetChange={setSlackTarget}
                description={description}
                onDescriptionChange={setDescription}
              />
            );
          case 'webhook':
            return (
              <WebhookFlowSection
                webhookProvider={webhookProvider}
                eventType={eventType}
                promptTemplate={promptTemplate}
                currentStep={'provider' as Step}
                setWebhookProvider={(provider: WebhookProvider | null) => setWebhookProvider(provider)}
                setEventType={setEventType}
                setPromptTemplate={setPromptTemplate}
                setCurrentStep={(step: Step) => {
                  // Map webhook steps to modal steps if needed
                  if (step === 'webhook' as Step) {
                    handleNext();
                  }
                }}
                session={{
                  idToken: '', // TODO: Get from auth context
                  user: {
                    email: currentTeammate?.email,
                    org_id: currentTeammate?.org_id
                  }
                }}
                teammate={currentTeammate}
                standalone={false}
              />
            );
          case 'jira':
            return (
              <JiraFlow
                selectedBoard={selectedBoard}
                onBoardSelect={setSelectedBoard}
                selectedTicket={selectedTicket}
                onTicketSelect={setSelectedTicket}
                additionalContext={additionalContext}
                onContextChange={setAdditionalContext}
                shouldComment={shouldComment}
                onCommentChange={setShouldComment}
                shouldTransition={shouldTransition}
                onTransitionChange={setShouldTransition}
                selectedTransition={selectedTransition}
                onTransitionSelect={setSelectedTransition}
                ticketsPage={ticketsPage}
                onPageChange={setTicketsPage}
                ticketSearch={ticketSearch}
                onSearchChange={setTicketSearch}
                boards={boards}
                tickets={tickets}
                transitions={transitions}
                isLoadingBoards={isLoadingBoards}
                isLoadingTickets={isLoadingTickets}
                isLoadingTransitions={isLoadingTransitions}
                totalPages={totalPages}
              />
            );
          default:
            return null;
        }
      case 'schedule':
        return (
          <ScheduleSection
            date={date}
            onDateChange={setDate}
            scheduleType={scheduleType}
            onScheduleTypeChange={setScheduleType}
            repeatOption={repeatOption}
            onRepeatOptionChange={setRepeatOption}
            customTime={customTime}
            onCustomTimeChange={setCustomTime}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Dialog 
      open={open} 
      onOpenChange={handleOpenChange}
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
                  Configure and schedule a task for {currentTeammate?.name || 'the teammate'}.
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
            {!isBackDisabled() && (
              <Button
                variant="outline"
                size="lg"
                onClick={handleBack}
                className="bg-[#1E293B] border-[#2D3B4E] hover:bg-emerald-500/10 text-slate-200"
              >
                <ArrowLeft className="h-5 w-5 mr-2" />
                Back to {step === 'config' ? 'Task Type' : 'Configuration'}
              </Button>
            )}
            <Button
              size="lg"
              onClick={handleNext}
              className={cn(
                "ml-auto",
                "bg-emerald-500 hover:bg-emerald-600"
              )}
            >
              {getButtonText()}
              <ArrowRight className="h-5 w-5 ml-2" />
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
} 