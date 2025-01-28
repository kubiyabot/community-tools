import React, { useState, useEffect, useMemo } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/app/components/ui/dialog';
import { Button } from '@/app/components/ui/button';
import { Input } from '@/app/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/app/components/ui/select';
import { TeammateSelector, TeammateInfo as TeammateDisplayInfo } from './TeammateSelector';
import { toast } from '@/app/components/ui/use-toast';
import { Filter, X, Clock, Calendar, CalendarDays, CalendarClock, CalendarRange, Webhook, ArrowLeft, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { format, addHours, addDays } from 'date-fns';
import { TeammateInfo } from '@/app/types/teammate';
import { Integration } from '@/app/types/integration';

interface TeammateFilter {
  hasTools: boolean;
  hasSources: boolean;
  hasIntegrations: boolean;
  searchTerm: string;
}

type ModalStep = 'method' | 'config' | 'schedule';
type AssignmentMethod = 'chat' | 'jira' | 'webhook';
type WebhookProvider = string;

interface TaskData {
  // Required fields
  channel_id: string;
  channel_name: string;
  created_at: string;
  parameters: {
    action_context_data: Record<string, any>;
    body: {
      team: { id: string };
      user: { id: string };
    };
    channel_id: string;
    channel_name: string;
    team_id: string;
    user_id: string;
    user_email: string;
  };
  status: string;
  teammate_id: string;
  title: string;
  description: string;

  // Optional fields
  source?: WebhookProvider | null;
  assignmentMethod?: AssignmentMethod;
  date?: Date;
  scheduleType?: 'quick' | 'custom';
  repeatOption?: string;
  slackTarget?: string;
  webhookUrl?: string;
  webhookProvider?: WebhookProvider | null;
  promptTemplate?: string;
  eventType?: string;
  user_email?: string;
}

interface TaskSchedulingModalProps {
  isOpen: boolean;
  onClose: () => void;
  teammate?: TeammateInfo;
  onSchedule: (data: TaskData) => Promise<void>;
  initialData?: TaskData;
}

// Transform teammate to match TeammateSelector format
const transformTeammate = (teammate: TeammateInfo): TeammateDisplayInfo => {
  return {
    ...teammate,
    integrations: teammate.integrations?.map(integration => 
      typeof integration === 'string' 
        ? { name: integration } 
        : { name: integration.name, type: integration.type }
    )
  };
};

export function TaskSchedulingModal({
  isOpen,
  onClose,
  teammate: initialTeammate,
  onSchedule,
  initialData
}: TaskSchedulingModalProps) {
  // State for loading and data
  const [isLoadingTools, setIsLoadingTools] = useState(true);
  const [isLoadingTeammates, setIsLoadingTeammates] = useState(true);
  const [tools, setTools] = useState<any[]>([]);
  const [teammates, setTeammates] = useState<TeammateInfo[]>([]);
  const [filters, setFilters] = useState<TeammateFilter>({
    hasTools: false,
    hasSources: false,
    hasIntegrations: false,
    searchTerm: ''
  });

  // Existing state management
  const [open, setOpen] = useState(isOpen);
  const [currentTeammate, setCurrentTeammate] = useState<TeammateDisplayInfo | undefined>(
    initialTeammate ? transformTeammate(initialTeammate) : undefined
  );
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

  // Load tools and teammates in parallel
  useEffect(() => {
    const loadData = async () => {
      try {
        const [toolsRes, teammatesRes] = await Promise.all([
          fetch('/api/tools'),
          fetch('/api/teammates')
        ]);

        const toolsData = await toolsRes.json();
        const teammatesData = await teammatesRes.json();

        setTools(toolsData);
        setTeammates(teammatesData);
      } catch (error) {
        console.error('Error loading data:', error);
        toast({
          variant: "destructive",
          title: "Error",
          description: "Failed to load data. Please try again.",
        });
      } finally {
        setIsLoadingTools(false);
        setIsLoadingTeammates(false);
      }
    };

    loadData();
  }, []);

  // Filter teammates based on criteria
  const filteredTeammates = useMemo(() => {
    return teammates.filter(teammate => {
      const matchesSearch = !filters.searchTerm || 
        teammate.name.toLowerCase().includes(filters.searchTerm.toLowerCase());

      const hasIntegrations = teammate.integrations && teammate.integrations.length > 0;

      const matchesTools = !filters.hasTools || hasIntegrations;
      const matchesSources = !filters.hasSources || hasIntegrations;
      const matchesIntegrations = !filters.hasIntegrations || hasIntegrations;

      return matchesSearch && matchesTools && matchesSources && matchesIntegrations;
    }).map(transformTeammate);
  }, [teammates, filters]);

  // Render teammate filter chips
  const renderFilterChips = () => (
    <div className="flex flex-wrap gap-2 mb-3">
      {Object.entries(filters).map(([key, value]) => {
        if (key === 'searchTerm' || !value) return null;
        return (
          <div 
            key={key}
            className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-purple-500/10 text-purple-400 text-xs"
          >
            <span>{key.replace(/^has/, 'Has ')}</span>
            <button
              onClick={() => setFilters(prev => ({ ...prev, [key]: false }))}
              className="p-0.5 hover:bg-purple-500/20 rounded-full"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        );
      })}
      {Object.values(filters).some(Boolean) && (
        <button
          onClick={() => setFilters({
            hasTools: false,
            hasSources: false,
            hasIntegrations: false,
            searchTerm: ''
          })}
          className="text-xs text-slate-400 hover:text-purple-400"
        >
          Clear all
        </button>
      )}
    </div>
  );

  // Enhanced teammate selection with filters
  const renderTeammateSelection = () => (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Input
          placeholder="Search teammates..."
          value={filters.searchTerm}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => 
            setFilters(prev => ({ ...prev, searchTerm: e.target.value }))}
          className="flex-1"
        />
        <Select
          value={filters.hasTools ? "tools" : ""}
          onValueChange={(value) => setFilters(prev => ({ ...prev, hasTools: value === "tools" }))}
        >
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Filter by..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="tools">Has Tools</SelectItem>
            <SelectItem value="sources">Has Sources</SelectItem>
            <SelectItem value="integrations">Has Integrations</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {renderFilterChips()}

      <TeammateSelector
        currentTeammate={currentTeammate}
        onTeammateSelect={setCurrentTeammate}
        teammates={filteredTeammates}
        isLoading={isLoadingTeammates}
      />
    </div>
  );

  const handleSchedule = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!currentTeammate) return;

    try {
      const channelId = slackTarget?.startsWith('#') ? slackTarget.substring(1) : slackTarget || '';
      const taskData: TaskData = {
        channel_id: channelId,
        channel_name: `#${channelId}`,
        created_at: new Date().toISOString(),
        parameters: {
          action_context_data: {},
          body: {
            team: { id: currentTeammate.team_id || '' },
            user: { id: currentTeammate.user_id || '' }
          },
          channel_id: channelId,
          channel_name: `#${channelId}`,
          team_id: currentTeammate.team_id || '',
          user_id: currentTeammate.user_id || '',
          user_email: currentTeammate.email || ''
        },
        status: "scheduled",
        teammate_id: currentTeammate.uuid,
        title: description || '',
        description: description || '',
        source: webhookProvider || undefined,
        assignmentMethod: assignmentMethod,
        date: date,
        scheduleType: scheduleType,
        repeatOption: repeatOption,
        slackTarget: slackTarget,
        webhookUrl: webhookUrl,
        webhookProvider: webhookProvider || undefined,
        promptTemplate: promptTemplate,
        eventType: eventType,
        user_email: currentTeammate.email || ''
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

  return (
    <div>
      {/* Component JSX */}
    </div>
  );
} 