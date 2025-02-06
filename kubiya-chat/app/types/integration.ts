export type IntegrationType = 'aws' | 'github' | 'jira' | 'slack' | 'generic';

export interface AWSVendorSpecific {
  region?: string;
  account_id?: string;
  role_name?: string;
  arn?: string;
  external_id?: string;
  session_name?: string;
  capabilities?: string[];
  supported_fields?: string[];
}

export interface GitHubVendorSpecific {
  repository?: string;
  owner?: string;
  branch?: string;
  installation_id?: string;
  capabilities?: string[];
  supported_fields?: string[];
}

export interface JiraVendorSpecific {
  site?: string;
  cloud_id?: string;
  project_key?: string;
  capabilities?: string[];
  supported_fields?: string[];
}

export type VendorSpecific = AWSVendorSpecific | GitHubVendorSpecific | JiraVendorSpecific;

export interface KubiyaMetadata {
  created_at: string;
  last_updated: string;
  user_created?: string;
  user_last_updated?: string;
  created_by?: string;
  icon_url?: string;
  capabilities?: string[];
  config_fields?: string[];
}

export interface IntegrationConfigItem {
  name: string;
  is_default?: boolean;
  vendor_specific?: VendorSpecific;
  kubiya_metadata?: KubiyaMetadata;
}

export interface SimpleIntegration {
  name: string;
  description?: string;
  integration_type: IntegrationType;
  auth_type?: string;
  configs: IntegrationConfigItem[];
  kubiya_metadata: KubiyaMetadata;
}

export interface Integration extends SimpleIntegration {
  uuid?: string;
} 