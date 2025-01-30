"use client";

import { useState, useEffect } from 'react';
import { Search, Terminal, AlertCircle } from 'lucide-react';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import { ScrollArea } from '../../../components/ui/scroll-area';
import { Skeleton } from '../../../components/ui/skeleton';
import { cn } from '@/lib/utils';
import type { TeammateTabProps, Runner } from './types';

interface RunnerCardProps {
  runner: Runner;
}

function RunnerCard({ runner }: RunnerCardProps) {
  return (
    <div className="group relative bg-card hover:bg-accent rounded-lg border border-border p-4 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 min-w-0">
          <div className="p-2 rounded-md bg-primary/10 border border-primary/20">
            <Terminal className="h-5 w-5 text-primary" />
          </div>
          <div className="min-w-0">
            <h4 className="text-sm font-medium text-foreground">{runner.name}</h4>
            <p className="text-xs text-muted-foreground mt-1">Type: {runner.type}</p>
          </div>
        </div>
        <Badge 
          variant="outline"
          className={cn(
            "text-xs whitespace-nowrap",
            runner.status === 'active'
              ? "bg-green-500/10 text-green-400 border-green-500/20"
              : "bg-red-500/10 text-red-400 border-red-500/20"
          )}
        >
          {runner.status}
        </Badge>
      </div>

      {runner.metadata && (
        <div className="mt-4 pt-4 border-t border-border">
          <div className="grid grid-cols-2 gap-2">
            {runner.metadata.version && (
              <div className="flex items-center gap-2 p-2 rounded-md bg-background/50 border border-border text-xs">
                <span className="text-muted-foreground">Version:</span>
                <code className="text-foreground font-mono">{runner.metadata.version}</code>
              </div>
            )}
            {runner.metadata.platform && (
              <div className="flex items-center gap-2 p-2 rounded-md bg-background/50 border border-border text-xs">
                <span className="text-muted-foreground">Platform:</span>
                <code className="text-foreground font-mono">{runner.metadata.platform}</code>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export function RunnersTab({ teammate }: TeammateTabProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [runners, setRunners] = useState<Runner[]>([]);

  useEffect(() => {
    const fetchRunners = async () => {
      if (!teammate?.uuid) return;
      
      try {
        setIsLoading(true);
        const res = await fetch('/api/runners');
        if (!res.ok) throw new Error('Failed to fetch runners');
        const data = await res.json();

        // Map teammate runners to full runner data
        const runnersData = teammate.runners?.map((runner: Runner | string) => {
          if (typeof runner === 'string') {
            return data.find((r: Runner) => r.id === runner || r.name === runner) || {
              id: runner,
              name: runner,
              type: 'Kubiya Kubernetes Operator',
              status: 'inactive' as const
            };
          }
          return runner;
        }) || [];

        setRunners(runnersData);
      } catch (error) {
        console.error('Error fetching runners:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchRunners();
  }, [teammate?.uuid, teammate?.runners]);

  const filteredRunners = runners.filter(runner => 
    runner.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    runner.type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="sticky top-0 z-10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 pb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Skeleton className="w-full h-10" />
          </div>
        </div>

        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-[120px] w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 pb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search runners..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-background border border-input rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>
      </div>

      {filteredRunners.length > 0 ? (
        <div className="grid gap-4">
          {filteredRunners.map((runner) => (
            <RunnerCard key={runner.id} runner={runner} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-12 bg-card/50 rounded-lg border border-dashed border-border">
          <div className="p-3 rounded-full bg-primary/10 border border-primary/20">
            {searchQuery ? (
              <AlertCircle className="h-6 w-6 text-primary" />
            ) : (
              <Terminal className="h-6 w-6 text-primary" />
            )}
          </div>
          <p className="text-sm text-muted-foreground mt-4">
            {searchQuery ? "No runners match your search" : "No runners available"}
          </p>
          {!searchQuery && (
            <p className="text-xs text-muted-foreground mt-1">
              Add runners to enable distributed task execution
            </p>
          )}
        </div>
      )}
    </div>
  );
} 