import { Terminal, GitBranch, Database, Code, Settings, Search, Bot, Workflow, Globe, Cloud } from 'lucide-react';
import React from 'react';

export interface CustomToolUI {
  name: string;
  description: string;
  icon: React.ComponentType<any> | string;
  metadata?: {
    category?: string;
    version?: string;
  };
  component?: React.ComponentType<any>;
}

// Helper function to get the appropriate icon for a tool type
const getIcon = (type: string) => {
  const checkType = (keyword: string) => type.toLowerCase().includes(keyword);

  // Integration-specific icons with direct URLs
  if (checkType('slack')) return "https://cdn4.iconfinder.com/data/icons/logos-and-brands/512/306_Slack_logo-512.png";
  if (checkType('aws')) return "https://uxwing.com/wp-content/themes/uxwing/download/brands-and-social-media/aws-icon.png";
  if (checkType('github')) return "https://cdn-icons-png.flaticon.com/512/25/25231.png";
  if (checkType('jira')) return "https://cdn-icons-png.flaticon.com/512/5968/5968875.png";
  if (checkType('kubernetes')) return "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Kubernetes_logo_without_workmark.svg/2109px-Kubernetes_logo_without_workmark.svg.png";
  
  // Default icons based on type
  if (checkType('terraform')) return '/icons/terraform.svg';
  if (checkType('git')) return GitBranch;
  if (checkType('database')) return Database;
  if (checkType('code')) return Code;
  if (checkType('search')) return Search;
  if (checkType('workflow')) return Workflow;
  if (checkType('http')) return Globe;
  if (checkType('cloud')) return Cloud;
  
  return Terminal;
};

export const toolRegistry: Record<string, CustomToolUI> = {
  'tool': {
    name: 'Tool Execution',
    description: 'Executes a tool or command',
    icon: Terminal
  },
  'tool_init': {
    name: 'Tool Initialization',
    description: 'Initializing tool execution',
    icon: Settings
  },
  'tool_output': {
    name: 'Tool Output',
    description: 'Output from tool execution',
    icon: Terminal
  },
  'tool_error': {
    name: 'Tool Error',
    description: 'Error from tool execution',
    icon: Terminal
  }
};

export const getToolMetadata = (toolName: string): CustomToolUI => {
  // Try to match exact tool name first
  if (toolRegistry[toolName]) {
    return toolRegistry[toolName];
  }

  // Get icon based on tool type
  const icon = getIcon(toolName);
  
  // Format the display name
  const displayName = toolName
    .split(/[_-]/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');

  // Try to determine category based on name
  let category = 'Other';
  if (toolName.toLowerCase().includes('git')) category = 'Version Control';
  else if (toolName.toLowerCase().includes('kube')) category = 'Kubernetes';
  else if (toolName.toLowerCase().includes('aws')) category = 'Cloud';
  else if (toolName.toLowerCase().includes('db') || toolName.toLowerCase().includes('sql')) category = 'Database';

  return {
    name: displayName,
    description: `Execute ${displayName} operations`,
    icon,
    metadata: {
      category,
      version: '1.0'
    }
  };
};

export const ToolProvider: React.FC = () => {
  return null; // This is just a registry, no UI needed
}; 