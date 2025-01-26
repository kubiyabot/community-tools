import { useState } from 'react';
import { WebhookProvider } from '../providers';
import { InteractionDestination } from '../types';
import { toast } from '../../ui/use-toast';

export interface UseWebhookCreationProps {
  selectedProvider: WebhookProvider | null;
  selectedEvent: string;
  promptTemplate: string;
  teammate?: {
    uuid: string;
    name?: string;
    team_id?: string;
    user_id?: string;
    org_id?: string;
    email?: string;
    context?: string;
  };
  session: {
    idToken: string;
    user: {
      email?: string;
      org_id?: string;
    };
  };
  webhookUrl: string;
  setWebhookCreated: (created: boolean) => void;
  interaction?: InteractionDestination;
}

export function useWebhookCreation({
  selectedProvider,
  selectedEvent,
  promptTemplate,
  teammate,
  session,
  webhookUrl,
  setWebhookCreated,
  interaction
}: UseWebhookCreationProps) {
  const [isCreatingWebhook, setIsCreatingWebhook] = useState(false);
  const [isTestingWebhook, setIsTestingWebhook] = useState(false);

  const createWebhook = async () => {
    if (!selectedProvider || !selectedEvent || !promptTemplate) return;

    setIsCreatingWebhook(true);
    try {
      const response = await fetch('/api/webhooks/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.idToken}`
        },
        body: JSON.stringify({
          provider: selectedProvider.id,
          event: selectedEvent,
          prompt_template: promptTemplate,
          teammate_id: teammate?.uuid,
          interaction
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create webhook');
      }

      setWebhookCreated(true);
      toast({
        title: "Webhook created",
        description: "Your webhook endpoint has been created successfully."
      });
    } catch (error) {
      console.error('Error creating webhook:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : 'Failed to create webhook',
        variant: "destructive"
      });
    } finally {
      setIsCreatingWebhook(false);
    }
  };

  const handleTestWebhook = async () => {
    if (!selectedProvider || !selectedEvent) return;

    setIsTestingWebhook(true);
    try {
      const response = await fetch(webhookUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          test: true,
          provider: selectedProvider.id,
          event: selectedEvent
        })
      });

      if (!response.ok) {
        throw new Error('Failed to test webhook');
      }

      toast({
        title: "Test successful",
        description: "The webhook endpoint responded successfully."
      });
    } catch (error) {
      console.error('Error testing webhook:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : 'Failed to test webhook',
        variant: "destructive"
      });
    } finally {
      setIsTestingWebhook(false);
    }
  };

  return {
    isCreatingWebhook,
    isTestingWebhook,
    createWebhook,
    handleTestWebhook
  };
} 