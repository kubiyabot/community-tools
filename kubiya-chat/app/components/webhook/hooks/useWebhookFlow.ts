import { useState, useEffect } from 'react';
import { WebhookProvider } from '../providers';
import { Step, InteractionDestination } from '../types';

const createDefaultInteraction = (): InteractionDestination => ({
  type: 'slack',
  channel: '',
  webhookUrl: '',
  webhookId: '',
  name: '',
  source: '',
  communication: {
    method: 'Slack',
    destination: ''
  },
  createdAt: '',
  createdBy: '',
  org: ''
});

interface UseWebhookFlowProps {
  webhookProvider: WebhookProvider | null;
  eventType: string;
  promptTemplate: string;
  currentStep: Step;
  setWebhookProvider: (provider: WebhookProvider | null) => void;
  setEventType: (type: string) => void;
  setPromptTemplate: (template: string) => void;
  setCurrentStep: (step: Step) => void;
  interaction?: InteractionDestination;
  setInteraction?: (interaction: InteractionDestination) => void;
  teammate?: {
    uuid: string;
    name?: string;
    team_id?: string;
    user_id?: string;
    org_id?: string;
    email?: string;
    context?: string;
  };
}

export function useWebhookFlow({
  webhookProvider,
  eventType,
  promptTemplate,
  currentStep,
  setWebhookProvider,
  setEventType,
  setPromptTemplate,
  setCurrentStep,
  interaction,
  setInteraction,
  teammate
}: UseWebhookFlowProps) {
  const [webhookUrl, setWebhookUrl] = useState('');
  const [isTestingWebhook, setIsTestingWebhook] = useState(false);

  useEffect(() => {
    if (teammate?.uuid) {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || window.location.origin;
      setWebhookUrl(`${baseUrl}/api/webhooks/${teammate.uuid}`);
    }
  }, [teammate]);

  const handleProviderSelect = (provider: WebhookProvider) => {
    if (provider.id !== webhookProvider?.id) {
      setWebhookProvider(provider);
      setEventType('');
      setPromptTemplate('');
      if (setInteraction) setInteraction(createDefaultInteraction());
      setCurrentStep('event');
    }
  };

  const handleEventSelect = (type: string) => {
    setEventType(type);
    setCurrentStep('event_example');
  };

  const handleBack = () => {
    switch (currentStep) {
      case 'event':
        setWebhookProvider(null);
        setEventType('');
        setCurrentStep('provider');
        break;
      case 'event_example':
        setEventType('');
        setCurrentStep('event');
        break;
      case 'prompt':
        setCurrentStep('event_example');
        break;
      case 'interaction':
        setCurrentStep('prompt');
        break;
      case 'webhook':
        setCurrentStep('interaction');
        break;
    }
  };

  const handleContinue = () => {
    switch (currentStep) {
      case 'provider':
        if (webhookProvider) {
          setCurrentStep('event');
        }
        break;
      case 'event':
        if (eventType) {
          setCurrentStep('event_example');
        }
        break;
      case 'event_example':
        setCurrentStep('prompt');
        break;
      case 'prompt':
        if (promptTemplate.trim()) {
          setCurrentStep('interaction');
        }
        break;
      case 'interaction':
        if (interaction?.type && (interaction.type === 'teams' || interaction.channel)) {
          setCurrentStep('webhook');
        }
        break;
    }
  };

  const canContinue = () => {
    switch (currentStep) {
      case 'provider':
        return !!webhookProvider;
      case 'event':
        return !!eventType;
      case 'event_example':
        return true;
      case 'prompt':
        return !!promptTemplate.trim();
      case 'interaction':
        return !!interaction?.type && (interaction.type === 'teams' || !!interaction.channel);
      default:
        return false;
    }
  };

  const canNavigateToStep = (step: Step) => {
    switch (step) {
      case 'provider':
        return true;
      case 'event':
        return !!webhookProvider;
      case 'event_example':
        return !!webhookProvider && !!eventType;
      case 'prompt':
        return !!webhookProvider && !!eventType;
      case 'interaction':
        return !!webhookProvider && !!eventType && !!promptTemplate.trim();
      case 'webhook':
        return !!webhookProvider && !!eventType && !!promptTemplate.trim() && 
               !!interaction?.type && (interaction.type === 'teams' || !!interaction.channel);
      default:
        return false;
    }
  };

  const resetState = () => {
    setWebhookProvider(null);
    setEventType('');
    setPromptTemplate('');
    if (setInteraction) setInteraction(createDefaultInteraction());
    setCurrentStep('provider');
    setWebhookUrl('');
    setIsTestingWebhook(false);
  };

  return {
    webhookUrl,
    isTestingWebhook,
    handleProviderSelect,
    handleEventSelect,
    handleBack,
    handleContinue,
    canContinue,
    canNavigateToStep,
    resetState,
    setIsTestingWebhook
  };
} 