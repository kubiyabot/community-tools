import * as React from 'react';
import { cn } from '@/lib/utils';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../ui/tooltip';
import { Variable, User, Users, Webhook, Wrench, Link, Calendar } from 'lucide-react';

interface ContextVariableProps {
  variable: string;
  className?: string;
}

export const ContextVariable: React.FC<ContextVariableProps> = ({ variable, className }) => {
  // Remove any {{ }} from the variable name if present
  const cleanVariable = variable.replace(/[{}]/g, '').trim();

  const getVariableInfo = (v: string) => {
    if (v.startsWith('.event.')) {
      return {
        icon: Webhook,
        color: 'text-blue-300',
        bgColor: 'bg-blue-500/10',
        borderColor: 'border-blue-500/20',
        hoverBg: 'hover:bg-blue-500/20',
        hoverBorder: 'hover:border-blue-500/30',
        label: 'Event Data',
        description: 'Data from the webhook payload'
      };
    }
    if (v.startsWith('.user.')) {
      return {
        icon: User,
        color: 'text-green-300',
        bgColor: 'bg-green-500/10',
        borderColor: 'border-green-500/20',
        hoverBg: 'hover:bg-green-500/20',
        hoverBorder: 'hover:border-green-500/30',
        label: 'User Context',
        description: 'Information about the current user'
      };
    }
    if (v.startsWith('.tool.')) {
      return {
        icon: Wrench,
        color: 'text-orange-300',
        bgColor: 'bg-orange-500/10',
        borderColor: 'border-orange-500/20',
        hoverBg: 'hover:bg-orange-500/20',
        hoverBorder: 'hover:border-orange-500/30',
        label: 'Tool Context',
        description: 'Tool configuration and parameters'
      };
    }
    if (v.startsWith('.source.')) {
      return {
        icon: Link,
        color: 'text-cyan-300',
        bgColor: 'bg-cyan-500/10',
        borderColor: 'border-cyan-500/20',
        hoverBg: 'hover:bg-cyan-500/20',
        hoverBorder: 'hover:border-cyan-500/30',
        label: 'Source Context',
        description: 'Source of the request or action'
      };
    }
    if (v.startsWith('.time.') || v.includes('_at')) {
      return {
        icon: Calendar,
        color: 'text-purple-300',
        bgColor: 'bg-purple-500/10',
        borderColor: 'border-purple-500/20',
        hoverBg: 'hover:bg-purple-500/20',
        hoverBorder: 'hover:border-purple-500/30',
        label: 'Time Context',
        description: 'Temporal information and timestamps'
      };
    }
    return {
      icon: Variable,
      color: 'text-slate-300',
      bgColor: 'bg-slate-500/10',
      borderColor: 'border-slate-500/20',
      hoverBg: 'hover:bg-slate-500/20',
      hoverBorder: 'hover:border-slate-500/30',
      label: 'Context Variable',
      description: 'Dynamic context variable'
    };
  };

  const info = getVariableInfo(cleanVariable);
  const Icon = info.icon;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            className={cn(
              "inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md",
              info.bgColor,
              info.color,
              info.borderColor,
              info.hoverBg,
              info.hoverBorder,
              "border transition-all duration-200 cursor-help font-mono text-sm",
              "whitespace-nowrap",
              className
            )}
          >
            <Icon className="h-3 w-3" />
            {cleanVariable}
          </span>
        </TooltipTrigger>
        <TooltipContent 
          side="top" 
          className="bg-slate-800 border-slate-700"
        >
          <div className="space-y-1">
            <p className="text-xs font-medium text-slate-300">{info.label}</p>
            <p className="text-xs text-slate-400">{info.description}</p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}; 