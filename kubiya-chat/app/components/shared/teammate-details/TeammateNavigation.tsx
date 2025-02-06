import { Info, Link as LinkIcon, Wrench, Settings, Lock, BookOpen } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TeammateNavigationProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export function TeammateNavigation({ activeTab, onTabChange }: TeammateNavigationProps) {
  const tabs = [
    { value: 'overview', icon: Info, text: 'Overview' },
    { value: 'integrations', icon: LinkIcon, text: 'Integrations' },
    { value: 'knowledge', icon: BookOpen, text: 'Knowledge' },
    { value: 'sources', icon: Wrench, text: 'Tools' },
    { value: 'runtime', icon: Settings, text: 'Runtime' },
    { value: 'access', icon: Lock, text: 'Access Control' }
  ];

  return (
    <nav className="flex-shrink-0 border-b border-[#1E293B] bg-[#0F172A]">
      <div className="max-w-[1200px] mx-auto px-8">
        <div className="flex">
          {tabs.map(({ value, icon: Icon, text }) => {
            const isActive = activeTab === value;
            return (
              <button
                key={value}
                onClick={() => onTabChange(value)}
                className={cn(
                  "flex items-center gap-2 py-4 px-6 border-b-2 text-sm font-medium transition-colors",
                  isActive
                    ? "border-purple-500 text-purple-400"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:border-purple-500/50"
                )}
              >
                <Icon className="h-4 w-4" />
                {text}
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
} 