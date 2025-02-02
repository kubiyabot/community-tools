import * as React from 'react';
import { Settings, Code, Box } from 'lucide-react';
import type { Step } from './types';

export const STEPS: Step[] = [
  {
    id: 'source',
    title: 'Select Source',
    description: 'Choose tools to install',
    icon: React.createElement(Code, { className: "h-5 w-5" })
  },
  {
    id: 'preview',
    title: 'Preview',
    description: 'Review selected tools',
    icon: React.createElement(Box, { className: "h-5 w-5" })
  },
  {
    id: 'configure',
    title: 'Configure',
    description: 'Set up installation',
    icon: React.createElement(Settings, { className: "h-5 w-5" })
  }
]; 