"use client";

import { useMemo } from 'react';
import { Calendar, User, Code, Cpu, Variable, Lock, Globe, Key, GitFork, GitMerge, GitPullRequest } from 'lucide-react';
import type { TeammateHeaderProps, BaseIntegration } from './types';
import { Badge } from '@/app/components/ui/badge';
import { cn } from '@/lib/utils';
import { generateAvatarUrl } from '@/app/components/TeammateSelector';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/app/components/ui/tooltip';
import { useVirtualizer } from '@tanstack/react-virtual';

const MAX_VISIBLE_CAPABILITIES = 10;
const MAX_VISIBLE_INTEGRATIONS = 5;

export function TeammateHeader({ teammate, integrations }: TeammateHeaderProps) {
  if (!teammate) return null;

  // Memoize avatar URL to prevent regeneration on every render
  const avatarUrl = useMemo(() => 
    generateAvatarUrl({ uuid: teammate.uuid, name: teammate.name }), 
    [teammate.uuid, teammate.name]
  );

  // Memoize formatted date
  const formattedDate = useMemo(() => 
    teammate.metadata?.created_at ? 
      new Date(teammate.metadata.created_at).toLocaleDateString() : 
      'Unknown',
    [teammate.metadata?.created_at]
  );

  // Memoize capabilities list with limit
  const capabilities = useMemo(() => 
    teammate.metadata?.capabilities?.slice(0, MAX_VISIBLE_CAPABILITIES) || [],
    [teammate.metadata?.capabilities]
  );

  // Memoize integrations list with limit
  const visibleIntegrations = useMemo(() => 
    integrations?.slice(0, MAX_VISIBLE_INTEGRATIONS) || [],
    [integrations]
  );

  // Get total capabilities count safely
  const totalCapabilities = teammate.metadata?.capabilities?.length || 0;
  const hasMoreCapabilities = totalCapabilities > MAX_VISIBLE_CAPABILITIES;

  // Get total integrations count safely
  const totalIntegrations = integrations?.length || 0;
  const hasMoreIntegrations = totalIntegrations > MAX_VISIBLE_INTEGRATIONS;

  return (
    <div className="flex-shrink-0 border-b border-[#1E293B] bg-[#0F172A]">
      <div className="max-w-[1200px] mx-auto p-8">
        <div className="flex items-start gap-6">
          {/* Avatar Section */}
          <div className="relative flex-shrink-0">
            <div className="h-20 w-20 rounded-xl overflow-hidden bg-[#1E293B] border border-[#2A3347] flex items-center justify-center">
              <img 
                src={avatarUrl}
                alt={teammate.name} 
                className="h-full w-full object-cover"
                loading="lazy"
                decoding="async"
              />
            </div>
            <div className={cn(
              "absolute -bottom-1 -right-1 h-4 w-4 rounded-full border-2 border-[#0F172A]",
              teammate.status === 'active' ? "bg-green-500" :
              teammate.status === 'error' ? "bg-red-500" :
              "bg-yellow-500"
            )} />
          </div>

          {/* Info Section */}
          <div className="flex-1 min-w-0">
            <h2 className="text-2xl font-semibold text-slate-200">{teammate.name}</h2>
            {teammate.description && (
              <p className="text-sm text-slate-400 mt-2 max-w-2xl">{teammate.description}</p>
            )}
            
            {/* Stats Cards */}
            <div className="grid grid-cols-2 gap-4 mt-6 max-w-md">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-[#1E293B] border border-[#2A3347]">
                <div className="p-2 rounded-md bg-purple-500/10">
                  <Code className="h-4 w-4 text-purple-400" />
                </div>
                <div>
                  <p className="text-xs text-slate-400">Type</p>
                  <p className="text-sm font-medium text-slate-200">tools</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 rounded-lg bg-[#1E293B] border border-[#2A3347]">
                <div className="p-2 rounded-md bg-purple-500/10">
                  <Calendar className="h-4 w-4 text-purple-400" />
                </div>
                <div>
                  <p className="text-xs text-slate-400">Created</p>
                  <p className="text-sm font-medium text-slate-200">{formattedDate}</p>
                </div>
              </div>
            </div>

            {/* Capabilities with "Show More" */}
            {capabilities.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-6">
                {capabilities.map((capability: string) => (
                  <Badge 
                    key={capability}
                    variant="secondary" 
                    className="bg-purple-500/10 text-purple-400 border-purple-500/20"
                  >
                    {capability}
                  </Badge>
                ))}
                {hasMoreCapabilities && (
                  <Tooltip>
                    <TooltipTrigger>
                      <Badge variant="secondary" className="bg-slate-500/10 text-slate-400 border-slate-500/20">
                        +{totalCapabilities - MAX_VISIBLE_CAPABILITIES} more
                      </Badge>
                    </TooltipTrigger>
                    <TooltipContent>
                      <div className="max-w-xs">
                        {teammate.metadata?.capabilities?.slice(MAX_VISIBLE_CAPABILITIES).join(', ')}
                      </div>
                    </TooltipContent>
                  </Tooltip>
                )}
              </div>
            )}

            {/* Integrations with "Show More" */}
            {visibleIntegrations.length > 0 && (
              <div className="flex items-center gap-2 mt-3">
                <GitFork className="h-4 w-4 text-purple-400" />
                <div className="flex items-center gap-2">
                  {visibleIntegrations.map((integration: BaseIntegration, index: number) => {
                    const displayName = integration.name;
                    return (
                      <Tooltip key={integration.uuid || index}>
                        <TooltipTrigger>
                          <Badge 
                            variant="outline" 
                            className="bg-blue-500/10 text-blue-400 border-blue-500/20 flex items-center gap-1"
                          >
                            <GitPullRequest className="h-3 w-3" />
                            {displayName}
                          </Badge>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Connected to {displayName}</p>
                        </TooltipContent>
                      </Tooltip>
                    );
                  })}
                  {hasMoreIntegrations && (
                    <Tooltip>
                      <TooltipTrigger>
                        <Badge variant="outline" className="bg-slate-500/10 text-slate-400 border-slate-500/20">
                          +{totalIntegrations - MAX_VISIBLE_INTEGRATIONS} more
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent>
                        <div className="max-w-xs">
                          {integrations?.slice(MAX_VISIBLE_INTEGRATIONS)
                            .map((i: BaseIntegration) => i.name)
                            .join(', ')}
                        </div>
                      </TooltipContent>
                    </Tooltip>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 