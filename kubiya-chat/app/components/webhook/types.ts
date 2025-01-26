import { WebhookProvider } from './providers';

export type Step = 
  | 'provider'
  | 'event'
  | 'event_example'
  | 'prompt'
  | 'interaction'
  | 'webhook';

export interface InteractionDestination {
  type: string;
  channel: string;
  webhookUrl: string;
  webhookId: string;
  name: string;
  source: string;
  communication: {
    method: string;
    destination: string;
  };
  createdAt: string;
  createdBy: string;
  org: string;
}

export interface WebhookFlowState {
  provider: string | null;
  event: string | null;
  promptTemplate: string | null;
  interaction: InteractionDestination | null;
}

export interface ProviderSelectionProps {
  selectedProvider: WebhookProvider | null;
  onProviderSelect: (provider: WebhookProvider) => void;
}

export interface EventSelectionProps {
  selectedProvider: WebhookProvider | null;
  selectedEvent: string;
  onEventSelect: (type: string) => void;
}

export interface EventExampleProps {
  selectedProvider: WebhookProvider | null;
  selectedEvent: string;
  onContinue: () => void;
}

export interface PromptTemplateProps {
  selectedProvider: WebhookProvider | null;
  selectedEvent: string;
  promptTemplate: string;
  setPromptTemplate: (template: string) => void;
  onContinue: () => void;
}

export interface WebhookSetupProps {
  selectedProvider: WebhookProvider | null;
  selectedEvent: string;
  promptTemplate: string;
  webhookUrl: string;
  webhookCreated: boolean;
  isCreatingWebhook: boolean;
  isTestingWebhook: boolean;
  teammate?: {
    uuid: string;
    name?: string;
    team_id?: string;
    user_id?: string;
    org_id?: string;
    email?: string;
    context?: string;
  };
  onCreateWebhook: () => void;
  onTestWebhook: () => void;
}

export interface StepIndicatorProps {
  currentStep: Step;
  canNavigateToStep: (step: Step) => boolean;
  onStepClick: (step: Step) => void;
} 