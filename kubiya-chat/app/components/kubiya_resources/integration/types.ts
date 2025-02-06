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

export interface VendorDetails {
  type: 'aws' | 'github' | 'jira' | 'generic';
  details: {
    [key: string]: any;
  };
} 