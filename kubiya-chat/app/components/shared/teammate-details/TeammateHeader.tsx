"use client";

import { Calendar, User, Code, Cpu, Variable, Lock, Globe, Key, GitFork, GitMerge, GitPullRequest } from 'lucide-react';
import type { TeammateHeaderProps } from './types';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { generateAvatarUrl } from '@/app/components/TeammateSelector';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/app/components/ui/tooltip';

export function TeammateHeader({ teammate, integrations }: TeammateHeaderProps) {
  if (!teammate) return null;

  return (
    <div className="flex-shrink-0 border-b border-[#1E293B] bg-[#0F172A]">
      <div className="max-w-[1200px] mx-auto p-8">
        <div className="flex items-start gap-6">
          {/* Avatar Section */}
          <div className="relative flex-shrink-0">
            <div className="h-20 w-20 rounded-xl overflow-hidden bg-[#1E293B] border border-[#2A3347] flex items-center justify-center">
              <img 
                src={generateAvatarUrl({ uuid: teammate.uuid, name: teammate.name })}
                alt={teammate.name} 
                className="h-full w-full object-cover"
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
                  <p className="text-sm font-medium text-slate-200">
                    {teammate.metadata?.created_at ? 
                      new Date(teammate.metadata.created_at).toLocaleDateString() : 
                      'Unknown'
                    }
                  </p>
                </div>
              </div>
            </div>

            {/* Capabilities */}
            {teammate.metadata?.capabilities && teammate.metadata.capabilities.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-6">
                {teammate.metadata.capabilities.map((capability: string) => (
                  <Badge 
                    key={capability}
                    variant="secondary" 
                    className="bg-purple-500/10 text-purple-400 border-purple-500/20"
                  >
                    {capability}
                  </Badge>
                ))}
              </div>
            )}

            {integrations && integrations.length > 0 && (
              <div className="flex items-center gap-2 mt-3">
                <GitFork className="h-4 w-4 text-purple-400" />
                <div className="flex items-center gap-2">
                  {integrations.map((integration: any, index: number) => (
                    <Tooltip key={integration.id || index}>
                      <TooltipTrigger>
                        <Badge 
                          variant="outline" 
                          className="bg-blue-500/10 text-blue-400 border-blue-500/20 flex items-center gap-1"
                        >
                          <GitPullRequest className="h-3 w-3" />
                          {integration.name || integration.type}
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Connected to {integration.name || integration.type}</p>
                      </TooltipContent>
                    </Tooltip>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 