"use client";

import React, { useState, useMemo, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { 
  Lock, Variable, Database, Server, Cloud, Cpu, HardDrive, 
  GitBranch, Key, Shield, Clock, Settings, AlertCircle, User, Terminal, Users 
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useEntity } from '@/app/providers/EntityProvider';
import type { TeammateDetails, Runner } from './types';
import { Avatar, AvatarImage, AvatarFallback } from '../../../components/ui/avatar';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../../../components/ui/tooltip";

const EntityCard = ({ uuid, type }: { uuid: string; type: 'owner' | 'group' }) => {
  const { getEntityMetadata, isLoading } = useEntity();
  const entity = getEntityMetadata(uuid);

  if (isLoading || !entity) {
    return (
      <div className="p-6 rounded-lg bg-[#1E293B] border border-[#1E293B] animate-pulse">
        <div className="flex items-start gap-4">
          <div className="p-2.5 rounded-md bg-[#7C3AED]/10">
            {type === 'owner' ? (
              <User className="h-5 w-5 text-[#7C3AED]" />
            ) : (
              <Users className="h-5 w-5 text-[#7C3AED]" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="h-4 w-24 bg-[#2A3347] rounded" />
            <div className="h-6 w-48 bg-[#2A3347] rounded mt-2" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 rounded-lg bg-[#1E293B] border border-[#1E293B] hover:border-[#7C3AED]/20 transition-all duration-200">
      <div className="flex items-start gap-4">
        <div className="p-2.5 rounded-md bg-[#7C3AED]/10">
          {entity.type === 'user' ? (
            <div className="relative">
              {entity.image ? (
                <Avatar className="h-5 w-5">
                  <AvatarImage src={entity.image} alt={entity.name} />
                  <AvatarFallback>{entity.name.charAt(0)}</AvatarFallback>
                </Avatar>
              ) : (
                <User className="h-5 w-5 text-[#7C3AED]" />
              )}
              {entity.status === 'pending' && (
                <span className="absolute -top-1 -right-1 h-2 w-2 bg-yellow-500 rounded-full" />
              )}
            </div>
          ) : (
            <Users className="h-5 w-5 text-[#7C3AED]" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-[#94A3B8] uppercase tracking-wider">
            {type === 'owner' ? 'Owner' : 'Allowed Group'}
          </p>
          <p className="text-sm font-semibold text-white mt-1.5">{entity.name}</p>
          {entity.description && (
            <p className="text-xs text-[#94A3B8] mt-1">{entity.description}</p>
          )}
        </div>
      </div>
    </div>
  );
};

interface RunnerHealth {
  error: string;
  health: string;
  status: string;
  version: string;
}

const RunnerCard = ({ runner }: { runner: Runner | string }) => {
  const [health, setHealth] = useState<RunnerHealth | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isHosted = typeof runner === 'object' ? 
    runner.metadata?.is_hosted || 
    (runner.name?.toLowerCase().includes('kubiya') && runner.name?.toLowerCase().includes('hosted')) :
    runner.toLowerCase().includes('kubiya') && runner.toLowerCase().includes('hosted');
  
  useEffect(() => {
    const fetchHealth = async () => {
      try {
        setIsLoading(true);
        const runnerId = typeof runner === 'string' ? runner : runner.name;
        if (!runnerId) return;

        const response = await fetch(`/api/v3/runners/${runnerId}/health`);
        if (!response.ok) throw new Error('Failed to fetch runner health');
        
        const data = await response.json();
        setHealth(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch runner health');
      } finally {
        setIsLoading(false);
      }
    };

    fetchHealth();
  }, [runner]);
  
  return (
    <div className="p-6 rounded-lg bg-[#1E293B] border border-[#1E293B] hover:border-[#7C3AED]/20 transition-all duration-200">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <div className="p-2.5 rounded-md bg-[#7C3AED]/10">
                  {isHosted ? (
                    <Cloud className="h-5 w-5 text-[#7C3AED]" />
                  ) : (
                    <img 
                      src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Kubernetes_logo_without_workmark.svg/1055px-Kubernetes_logo_without_workmark.svg.png"
                      alt="Kubernetes"
                      className="h-5 w-5"
                    />
                  )}
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p className="text-sm">
                  {isHosted ? 
                    'Hosted runner, running on Kubiya isolated cloud infrastructure' : 
                    'Self-managed Kubernetes runner'
                  }
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-semibold text-white">
                {typeof runner === 'string' ? runner : runner.name || 'Unknown Runner'}
              </h4>
              <Badge 
                variant={health?.status === 'ok' ? 'default' : 'destructive'}
                className={cn(
                  "text-xs",
                  isLoading && "animate-pulse",
                  health?.status === 'ok' ? "bg-green-500/10 text-green-400 border-green-500/20" :
                  "bg-red-500/10 text-red-400 border-red-500/20"
                )}
              >
                {isLoading ? 'Checking...' : health?.status || 'Unknown'}
              </Badge>
              {health?.version && (
                <Badge variant="outline" className="text-xs border-[#1E293B] text-[#94A3B8]">
                  v{health.version}
                </Badge>
              )}
            </div>
            <p className="text-sm text-[#94A3B8] mt-1.5">
              {isHosted ? 
                'Hosted on Kubiya Cloud - Isolated Cloud Infrastructure' : 
                'Local (Self Managed)'} - {typeof runner === 'object' ? runner.metadata?.cluster_type || 'Unknown' : 'Unknown'}
            </p>
          </div>
        </div>
      </div>

      {typeof runner === 'object' && runner.metadata && (
        <div className="mt-6 grid grid-cols-3 gap-4">
          {runner.metadata.resources?.cpu && (
            <div className="flex items-center gap-3 p-3 rounded-md bg-[#2A3347]">
              <Cpu className="h-4 w-4 text-[#94A3B8]" />
              <span className="text-xs text-[#94A3B8]">
                CPU: {runner.metadata.resources.cpu}
              </span>
            </div>
          )}
          {runner.metadata.resources?.memory && (
            <div className="flex items-center gap-3 p-3 rounded-md bg-[#2A3347]">
              <HardDrive className="h-4 w-4 text-[#94A3B8]" />
              <span className="text-xs text-[#94A3B8]">
                Memory: {runner.metadata.resources.memory}
              </span>
            </div>
          )}
          {runner.metadata.resources?.storage && (
            <div className="flex items-center gap-3 p-3 rounded-md bg-[#2A3347]">
              <Database className="h-4 w-4 text-[#94A3B8]" />
              <span className="text-xs text-[#94A3B8]">
                Storage: {runner.metadata.resources.storage}
              </span>
            </div>
          )}
        </div>
      )}

      {(health?.error || error) && (
        <div className="mt-4 flex items-center gap-2 p-3 rounded-md bg-red-500/10 text-red-400 text-xs">
          <AlertCircle className="h-4 w-4" />
          {health?.error || error}
        </div>
      )}
    </div>
  );
};

const EnvVarCard = ({ name, value }: { name: string; value: string }) => (
  <div className="p-6 rounded-lg bg-[#1E293B] border border-[#1E293B] hover:border-[#7C3AED]/20 transition-all duration-200">
    <div className="flex items-start gap-4">
      <div className="p-2.5 rounded-md bg-[#7C3AED]/10">
        <Variable className="h-5 w-5 text-[#7C3AED]" />
      </div>
      <div className="flex-1 min-w-0 space-y-4">
        <div>
          <p className="text-xs font-medium text-[#94A3B8] uppercase tracking-wider">Variable Name</p>
          <p className="text-sm font-semibold text-white mt-1.5">{name}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-[#94A3B8] uppercase tracking-wider">Value</p>
          <div className="mt-1.5 p-2 rounded-md bg-[#2A3347]">
            <code className="text-sm font-medium text-white font-mono break-all">{value}</code>
          </div>
        </div>
      </div>
    </div>
  </div>
);

const SecretCard = ({ name, type }: { name: string; type: string }) => (
  <div className="p-6 rounded-lg bg-[#1E293B] border border-[#1E293B] hover:border-[#7C3AED]/20 transition-all duration-200">
    <div className="flex items-start gap-4">
      <div className="p-2.5 rounded-md bg-[#7C3AED]/10">
        <Key className="h-5 w-5 text-[#7C3AED]" />
      </div>
      <div className="flex-1 min-w-0 space-y-2">
        <p className="text-xs font-medium text-[#94A3B8] uppercase tracking-wider">Secret Name</p>
        <p className="text-sm font-semibold text-white">{name}</p>
        <div className="flex items-center gap-2 text-[#94A3B8]">
          <Shield className="h-4 w-4" />
          <p className="text-sm">{type}</p>
        </div>
      </div>
    </div>
  </div>
);

interface RuntimeTabProps {
  teammate: TeammateDetails;
}

export function RuntimeTab({ teammate }: RuntimeTabProps) {
  const envVars = teammate.environment_variables || {};
  const runners = teammate.runners || [];
  const starters = teammate.starters || [];

  if (!Object.keys(envVars).length && !runners.length && !starters.length) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-center p-6">
        <div className="p-3 rounded-full bg-[#1E293B] mb-4">
          <Settings className="h-6 w-6 text-[#94A3B8]" />
        </div>
        <h3 className="text-lg font-medium text-white mb-2">No Runtime Configuration</h3>
        <p className="text-sm text-[#94A3B8] max-w-sm">
          This teammate doesn't have any runtime configuration.
        </p>
      </div>
    );
  }

  return (
    <ScrollArea className="h-[calc(100vh-280px)] pr-6">
      <div className="space-y-8 pb-8">
        {/* Runners */}
        {runners.length > 0 && (
          <section className="space-y-4">
            <div className="flex items-center justify-between sticky top-0 bg-[#0F172A] py-2 z-10">
              <h3 className="text-lg font-semibold text-white">Runners</h3>
              <Badge variant="secondary" className="bg-[#1E293B] text-[#94A3B8] border-[#1E293B]">
                {runners.length} {runners.length === 1 ? 'Runner' : 'Runners'}
              </Badge>
            </div>
            <div className="grid gap-4">
              {runners.map((runner, idx) => (
                <RunnerCard key={`runner-${idx}`} runner={runner} />
              ))}
            </div>
          </section>
        )}

        {/* Environment Variables */}
        {Object.keys(envVars).length > 0 && (
          <section className="space-y-4">
            <div className="flex items-center justify-between sticky top-0 bg-[#0F172A] py-2 z-10">
              <h3 className="text-lg font-semibold text-white">Environment Variables</h3>
              <Badge variant="secondary" className="bg-[#1E293B] text-[#94A3B8] border-[#1E293B]">
                {Object.keys(envVars).length} Variables
              </Badge>
            </div>
            <div className="grid gap-4">
              {Object.entries(envVars).map(([name, value], idx) => (
                <EnvVarCard key={`env-${idx}`} name={name} value={value} />
              ))}
            </div>
          </section>
        )}

        {/* Starters */}
        {starters.length > 0 && (
          <section className="space-y-4">
            <div className="flex items-center justify-between sticky top-0 bg-[#0F172A] py-2 z-10">
              <h3 className="text-lg font-semibold text-white">Starters</h3>
              <Badge variant="secondary" className="bg-[#1E293B] text-[#94A3B8] border-[#1E293B]">
                {starters.length} {starters.length === 1 ? 'Starter' : 'Starters'}
              </Badge>
            </div>
            <div className="grid gap-4">
              {starters.map((starter, idx) => (
                <div key={`starter-${idx}`} className="p-6 rounded-lg bg-[#1E293B] border border-[#1E293B] hover:border-[#7C3AED]/20 transition-all duration-200">
                  <div className="flex items-start gap-4">
                    <div className="p-2.5 rounded-md bg-[#7C3AED]/10">
                      <Terminal className="h-5 w-5 text-[#7C3AED]" />
                    </div>
                    <div className="flex-1 min-w-0">
                      {starter.display_name && (
                        <p className="text-sm font-semibold text-white">{starter.display_name}</p>
                      )}
                      <code className="text-sm text-[#94A3B8] font-mono mt-2 block bg-[#2A3347] p-2 rounded">
                        {starter.command}
                      </code>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </ScrollArea>
  );
} 