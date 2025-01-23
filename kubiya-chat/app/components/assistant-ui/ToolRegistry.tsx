import { Terminal, GitBranch, Database, Globe, Box } from 'lucide-react';
import { GenericToolUI } from './ToolUI';

export interface CustomToolUI {
  name: string;
  icon?: React.ComponentType<any>;
  description?: string;
  component?: React.ComponentType<any>;
  metadata?: {
    category: string;
    version: string;
  };
}

// Registry of custom tool UIs
export const toolRegistry: Record<string, CustomToolUI> = {
  kubectl: {
    name: 'Kubernetes',
    icon: Terminal,
    description: 'Execute Kubernetes commands',
  },
  git: {
    name: 'Git',
    icon: GitBranch,
    description: 'Execute Git commands',
  },
  sql: {
    name: 'SQL',
    icon: Database,
    description: 'Execute SQL queries',
  },
  http: {
    name: 'HTTP',
    icon: Globe,
    description: 'Make HTTP requests',
  },
  docker: {
    name: 'Docker',
    icon: Box,
    description: 'Execute Docker commands',
  },
};

export const getToolMetadata = (toolName: string) => {
  const tool = toolRegistry[toolName];
  if (!tool) return null;

  return {
    icon: tool.icon,
    description: tool.description,
    customComponent: tool.component,
  };
};

export const ToolProvider = () => {
  return <GenericToolUI />;
}; 