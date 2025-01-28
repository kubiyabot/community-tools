export interface Task {
  id: string;
  name: string;
  description?: string;
  schedule?: string;
  status: 'active' | 'inactive';
  created_at: string;
  updated_at: string;
  owner: string;
}

export interface Webhook {
  id: string;
  name: string;
  url: string;
  description?: string;
  status: 'active' | 'inactive';
  created_at: string;
  updated_at: string;
  owner: string;
}

export interface ActivityEvent {
  org: string;
  email: string;
  version: number;
  category_type: string;
  category_name: string;
  resource_type: string;
  resource_text: string;
  action_type: string;
  action_successful: boolean;
  timestamp: string;
  extra: {
    is_user_message?: boolean;
    session_id?: string;
    tool_name?: string;
    tool_args?: any;
    tool_execution_status?: string;
  };
  scope: string;
}

export interface TabHeaderProps {
  tasks: Task[];
  webhooks: Webhook[];
  teammates: any[];
  activeTab: string;
  onTabChange: (tab: string) => void;
} 