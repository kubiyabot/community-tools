import React from 'react';
import { 
  Database,
  Shield,
  Code2,
  Workflow,
  Box
} from 'lucide-react';
import type { CategoryInfo } from '../components/shared/teammate-details/install-tool/types';

export const CACHE_KEY = 'kubiya_community_tools_cache';
export const CACHE_EXPIRY = 1000 * 60 * 60; // 1 hour

export const TOOL_CATEGORIES: Record<string, CategoryInfo> = {
  infrastructure: {
    name: 'Infrastructure',
    description: 'Tools for managing infrastructure',
    Icon: Database,
    matcher: (tool) => tool.path.includes('infrastructure')
  },
  security: {
    name: 'Security',
    description: 'Security and compliance tools',
    Icon: Shield,
    matcher: (tool) => tool.path.includes('security')
  },
  development: {
    name: 'Development',
    description: 'Development, CI/CD, and code management tools',
    Icon: Code2,
    matcher: (tool: { name: string; description: string }) => 
      /git|ci|cd|build|deploy|dev/i.test(tool.name + tool.description)
  },
  automation: {
    name: 'Automation',
    description: 'Workflow automation and integration tools',
    Icon: Workflow,
    matcher: (tool: { name: string; description: string }) => 
      /automation|workflow|integration|bot/i.test(tool.name + tool.description)
  },
  other: {
    name: 'Other',
    description: 'Miscellaneous tools',
    Icon: Box,
    matcher: (tool) => !tool.path.includes('infrastructure') && !tool.path.includes('security')
  }
};

// Remove old interfaces since we're using CategoryInfo from types
export type ToolCategories = typeof TOOL_CATEGORIES; 