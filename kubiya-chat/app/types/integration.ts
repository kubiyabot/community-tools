export interface SimpleIntegration {
  name: string;
  integration_type: IntegrationType;
  auth_type: 'global' | 'per_user';
  description?: string;
}

export interface Integration extends SimpleIntegration {
  uuid?: string;
  task_id?: string;
  managed_by: string;
  configs: Array<IntegrationConfigItem>;
  kubiya_metadata: {
    created_at: string;
    last_updated: string;
    user_created?: string;
    user_last_updated?: string;
    icon_url?: string;
    capabilities?: string[];
    config_fields?: string[];
  };
}

export interface IntegrationConfigItem {
  name: string;
  is_default?: boolean;
  vendor_specific?: {
    arn?: string;
    region?: string;
    secret_name?: string;
    account_id?: string;
    role_name?: string;
    capabilities?: string[];
    supported_fields?: string[];
  };
  kubiya_metadata?: {
    created_at?: string;
    created_by?: string;
    last_updated?: string;
    updated_by?: string;
  };
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
  | 'aws'
  | 'aws-serviceaccount'
  | 'kubernetes'
  | 'webhook'
  | 'custom';

// Utility type for AWS-specific configuration
export interface AWSIntegrationConfig extends IntegrationConfig {
  region: string;
  arn: string;
  accountId: string;
  roleName: string;
}

// Utility type for GitHub-specific configuration
export interface GitHubIntegrationConfig extends IntegrationConfig {
  repositoryUrl?: string;
  accessToken?: string;
  webhookSecret?: string;
}

// Utility type for Slack-specific configuration
export interface SlackIntegrationConfig extends IntegrationConfig {
  botToken?: string;
  signingSecret?: string;
  appId?: string;
}

// Utility type for Jira-specific configuration
export interface JiraIntegrationConfig extends IntegrationConfig {
  baseUrl: string;
  projectKey?: string;
  username?: string;
}

// Utility type for Kubernetes-specific configuration
export interface KubernetesIntegrationConfig extends IntegrationConfig {
  clusterUrl?: string;
  namespace?: string;
  serviceAccount?: string;
} 