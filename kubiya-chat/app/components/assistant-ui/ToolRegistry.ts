import { Terminal } from 'lucide-react';
import type { ComponentType } from 'react';

export interface CustomToolUI {
  name: string;
  description: string;
  icon: ComponentType<any>;
  component?: ComponentType<any>;
  category?: string;
  version?: string;
  metadata?: {
    category?: string;
    version?: string;
    [key: string]: any;
  };
}

export const toolRegistry: Record<string, CustomToolUI> = {};

// Default tool UI
export const defaultToolUI: CustomToolUI = {
  name: 'Tool Execution',
  description: 'Running tool command',
  icon: Terminal,
  metadata: {}
}; 