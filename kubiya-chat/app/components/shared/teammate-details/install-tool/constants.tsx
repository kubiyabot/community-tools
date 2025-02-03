import * as React from 'react';
import { GitBranch, Search, Settings } from 'lucide-react';
import type { Step } from './types';

export const STEPS: Step[] = [
  {
    id: 'source',
    title: 'Choose Source',
    description: 'Select a tool source from our community or add your own',
    icon: <GitBranch className="h-5 w-5" />
  },
  {
    id: 'select',
    title: 'Select Tool',
    description: 'Review and select tools to install',
    icon: <Search className="h-5 w-5" />
  },
  {
    id: 'configure',
    title: 'Configure',
    description: 'Configure installation settings',
    icon: <Settings className="h-5 w-5" />
  }
]; 