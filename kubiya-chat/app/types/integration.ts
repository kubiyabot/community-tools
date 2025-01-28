export interface Integration {
  name: string;
  type?: string;
  id?: string;
  provider?: string;
  config?: Record<string, any>;
  status?: 'active' | 'inactive' | 'pending';
  createdAt?: string;
  updatedAt?: string;
}

export interface IntegrationConfig {
  clientId?: string;
  clientSecret?: string;
  redirectUri?: string;
  scopes?: string[];
  apiKey?: string;
  webhookUrl?: string;
  customFields?: Record<string, any>;
}

export type IntegrationType = 
  | 'jira'
  | 'slack'
  | 'github'
  | 'gitlab'
  | 'webhook'
  | 'custom'; 