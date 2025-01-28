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

export interface InteractionConfig {
  destination: InteractionDestination;
  template?: string;
  variables?: Record<string, any>;
  metadata?: Record<string, any>;
}

export type InteractionMethod = 
  | 'chat'
  | 'webhook'
  | 'jira'
  | 'email'
  | 'custom'; 