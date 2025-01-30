import { Info, GitBranch, GitPullRequest, User, Github, Trello, Cloud, Lock, MessageSquare } from 'lucide-react';
import { generateAvatarUrl } from '../TeammateSelector';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { cn } from '@/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider
} from '../ui/tooltip';

interface Integration {
  name: string;
  type?: string;
  details?: {
    accountId?: string;
    authType?: string;
    region?: string;
    status?: string;
    [key: string]: any;
  };
}

interface TeammateContextCardProps {
  teammate: {
    uuid: string;
    name?: string;
    description?: string;
    email?: string;
    integrations?: (Integration | string)[];
  };
  onSwitchTeammate?: () => void;
  className?: string;
}

const normalizeIntegration = (integration: Integration | string): Integration => {
  if (typeof integration === 'string') {
    return { name: integration };
  }
  return integration;
};

const getIntegrationIcon = (integration: Integration | string) => {
  const normalized = normalizeIntegration(integration);
  const name = normalized.name.toLowerCase();
  
  // Check for substring matches
  if (name.includes('github')) return <Github className="h-2.5 w-2.5" />;
  if (name.includes('jira')) return <Trello className="h-2.5 w-2.5" />;
  if (name.includes('aws') || name.includes('amazon')) return <Cloud className="h-2.5 w-2.5" />;
  if (name.includes('oauth')) return <Lock className="h-2.5 w-2.5" />;
  if (name.includes('slack')) return <MessageSquare className="h-2.5 w-2.5" />;
  
  return <GitPullRequest className="h-2.5 w-2.5" />;
};

const getIntegrationTooltipContent = (integration: Integration | string) => {
  const normalized = normalizeIntegration(integration);
  const name = normalized.name.toLowerCase();
  const details = normalized.details || {};

  // Check for substring matches for specific integrations
  if (name.includes('aws') || name.includes('amazon')) {
    return (
      <div className="space-y-1.5">
        <p className="font-medium">AWS Integration</p>
        {details.accountId && <p className="text-xs">Account ID: {details.accountId}</p>}
        {details.region && <p className="text-xs">Region: {details.region}</p>}
        <p className="text-xs text-emerald-400">✓ Connected</p>
      </div>
    );
  }

  if (name.includes('github')) {
    return (
      <div className="space-y-1.5">
        <p className="font-medium">GitHub Integration</p>
        <p className="text-xs">Auth: {details.authType || 'OAuth2'}</p>
        {details.org && <p className="text-xs">Organization: {details.org}</p>}
        <p className="text-xs text-emerald-400">✓ Active</p>
      </div>
    );
  }

  if (name.includes('jira')) {
    return (
      <div className="space-y-1.5">
        <p className="font-medium">Jira Integration</p>
        {details.instance && <p className="text-xs">Instance: {details.instance}</p>}
        <p className="text-xs">Auth: {details.authType || 'OAuth2'}</p>
        <p className="text-xs text-emerald-400">✓ Connected</p>
      </div>
    );
  }

  if (name.includes('slack')) {
    return (
      <div className="space-y-1.5">
        <p className="font-medium">Slack Integration</p>
        {details.workspace && <p className="text-xs">Workspace: {details.workspace}</p>}
        <p className="text-xs text-emerald-400">✓ Connected</p>
      </div>
    );
  }

  // Default tooltip for other integrations
  return (
    <div className="space-y-1.5">
      <p className="font-medium">{normalized.name} Integration</p>
      {Object.entries(details).map(([key, value]) => (
        <p key={key} className="text-xs capitalize">
          {key.replace(/_/g, ' ')}: {value}
        </p>
      ))}
      <p className="text-xs text-emerald-400">✓ Connected</p>
    </div>
  );
};

export function TeammateContextCard({ teammate, onSwitchTeammate, className }: TeammateContextCardProps) {
  if (!teammate) return null;

  const handleSwitchTeammate = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (onSwitchTeammate) {
      // Store current state in localStorage if needed
      onSwitchTeammate();
    }
  };

  return (
    <TooltipProvider>
      <div className={cn(
        "flex items-start gap-4 p-4 rounded-lg bg-[#1E293B] border border-[#2D3B4E]",
        className
      )}>
        {/* Avatar Section */}
        <div className="relative flex-shrink-0">
          <div className="h-12 w-12 rounded-xl overflow-hidden bg-[#141B2B] border border-[#2A3347] flex items-center justify-center">
            <img 
              src={generateAvatarUrl({ uuid: teammate.uuid, name: teammate.name || '' })}
              alt={teammate.name} 
              className="h-full w-full object-cover"
            />
          </div>
          <div className="absolute -bottom-1 -right-1 h-3 w-3 rounded-full border-2 border-[#1E293B] bg-green-500" />
        </div>

        {/* Info Section */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-slate-200">{teammate.name}</h3>
              {teammate.description && (
                <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">{teammate.description}</p>
              )}
            </div>
            {onSwitchTeammate && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleSwitchTeammate}
                className="h-8 text-xs text-slate-400 hover:text-purple-400 hover:bg-purple-500/10"
              >
                <User className="h-3 w-3 mr-1.5" />
                Switch
              </Button>
            )}
          </div>

          {teammate.integrations && teammate.integrations.length > 0 && (
            <div className="flex items-center gap-2 mt-2">
              <GitBranch className="h-3 w-3 text-purple-400" />
              <div className="flex items-center gap-1.5 flex-wrap">
                {teammate.integrations.map((integration, index) => {
                  const normalized = normalizeIntegration(integration);
                  return (
                    <Tooltip key={normalized.name || index}>
                      <TooltipTrigger asChild>
                        <Badge 
                          variant="outline" 
                          className="bg-blue-500/10 text-blue-400 border-blue-500/20 flex items-center gap-1 text-xs py-0.5 cursor-help"
                        >
                          {getIntegrationIcon(integration)}
                          {normalized.name}
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent side="bottom" className="p-3">
                        {getIntegrationTooltipContent(integration)}
                      </TooltipContent>
                    </Tooltip>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Info Button with Tooltip */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 text-slate-400 hover:text-purple-400 hover:bg-purple-500/10 flex-shrink-0"
            >
              <Info className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="left" className="p-3">
            <div className="space-y-2">
              <p className="font-medium">Teammate Details</p>
              {teammate.email && (
                <p className="text-xs text-slate-300">{teammate.email}</p>
              )}
              <p className="text-xs text-slate-400">
                UUID: {teammate.uuid}
              </p>
            </div>
          </TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
} 