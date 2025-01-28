import * as React from 'react';
import { cn } from '@/lib/utils';
import { TabHeaderProps } from './types';
import { Calendar, Webhook, Bot, BarChart3 } from 'lucide-react';

const getTabStyles = (color: string, isActive: boolean) => {
  const styles = {
    purple: {
      active: "border-purple-500 text-purple-400 bg-purple-500/10",
      inactive: "text-slate-400 hover:text-purple-400 hover:bg-purple-500/10",
      badge: "bg-purple-500/10 text-purple-400",
    },
    blue: {
      active: "border-blue-500 text-blue-400 bg-blue-500/10",
      inactive: "text-slate-400 hover:text-blue-400 hover:bg-blue-500/10",
      badge: "bg-blue-500/10 text-blue-400",
    },
    green: {
      active: "border-green-500 text-green-400 bg-green-500/10",
      inactive: "text-slate-400 hover:text-green-400 hover:bg-green-500/10",
      badge: "bg-green-500/10 text-green-400",
    },
    amber: {
      active: "border-amber-500 text-amber-400 bg-amber-500/10",
      inactive: "text-slate-400 hover:text-amber-400 hover:bg-amber-500/10",
      badge: "bg-amber-500/10 text-amber-400",
    },
  };

  return styles[color as keyof typeof styles][isActive ? 'active' : 'inactive'];
};

const getBadgeStyles = (color: string) => {
  const styles = {
    purple: "bg-purple-500/10 text-purple-400",
    blue: "bg-blue-500/10 text-blue-400",
    green: "bg-green-500/10 text-green-400",
    amber: "bg-amber-500/10 text-amber-400",
  };

  return styles[color as keyof typeof styles];
};

export const TabHeader: React.FC<TabHeaderProps> = ({
  tasks,
  webhooks,
  teammates,
  activeTab,
  onTabChange,
}) => {
  const tabs = React.useMemo(() => [
    {
      id: 'tasks' as const,
      label: 'Tasks',
      icon: <Calendar className="h-4 w-4" />,
      count: tasks?.length || 0,
      color: 'purple',
    },
    {
      id: 'webhooks' as const,
      label: 'Webhooks',
      icon: <Webhook className="h-4 w-4" />,
      count: webhooks?.length || 0,
      color: 'blue',
    },
    {
      id: 'analytics' as const,
      label: 'Analytics',
      icon: <BarChart3 className="h-4 w-4" />,
      count: null,
      color: 'amber',
    },
    {
      id: 'teammates' as const,
      label: 'Teammate Analytics',
      icon: <Bot className="h-4 w-4" />,
      count: teammates?.length || 0,
      color: 'green',
    }
  ], [tasks?.length, webhooks?.length, teammates?.length]);

  return (
    <div className="border-b border-[#2A3347]">
      <nav className="-mb-px flex space-x-2" aria-label="Tabs">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={cn(
                "flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 border-transparent",
                isActive 
                  ? getTabStyles(tab.color, true)
                  : getTabStyles(tab.color, false),
                "transition-colors duration-200"
              )}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {tab.count !== null && (
                <span
                  className={cn(
                    "ml-2 rounded-full px-2 py-0.5 text-xs font-medium",
                    isActive ? getBadgeStyles(tab.color) : "bg-[#2A3347] text-slate-400"
                  )}
                >
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
}; 