import { PackageOpen, Info, RefreshCw } from 'lucide-react';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/app/components/ui/hover-card';
import { Button } from '@/app/components/ui/button';
import { useState } from 'react';

interface CommunityToolsHeaderProps {
  onRefresh: () => void;
}

export function CommunityToolsHeader({ onRefresh }: CommunityToolsHeaderProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className="flex items-start gap-4 mb-6">
      <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
        <PackageOpen className="h-6 w-6 text-purple-400" />
      </div>
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-semibold text-slate-200">Community Tools</h2>
            <HoverCard>
              <HoverCardTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 p-1 text-slate-400 hover:text-slate-300 hover:bg-slate-800 rounded-full"
                >
                  <Info className="h-4 w-4" />
                </Button>
              </HoverCardTrigger>
              <HoverCardContent className="w-80">
                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-slate-200">
                    Kubiya Community Tools
                  </h4>
                  <p className="text-xs text-slate-400">
                    A curated collection of tools maintained by the Kubiya team and community. 
                    These tools provide ready-to-use integrations with popular platforms and services, 
                    allowing you to extend your teammate's capabilities with just a click.
                  </p>
                  <div className="pt-2 flex flex-wrap gap-2">
                    <span className="px-2 py-1 bg-purple-500/10 text-purple-400 rounded-md text-xs">
                      Maintained by Kubiya
                    </span>
                    <span className="px-2 py-1 bg-blue-500/10 text-blue-400 rounded-md text-xs">
                      Community Supported
                    </span>
                  </div>
                </div>
              </HoverCardContent>
            </HoverCard>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="h-8 bg-slate-900 text-slate-400 border-slate-700 hover:bg-slate-800 hover:text-slate-300"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </div>
        <p className="text-slate-400 mt-1">
          Extend your teammate with pre-built tools for common platforms and services
        </p>
      </div>
    </div>
  );
} 