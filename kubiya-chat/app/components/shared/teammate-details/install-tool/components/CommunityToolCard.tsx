import * as React from 'react';
import { Card, CardHeader } from '@/app/components/ui/card';
import { Badge } from '@/app/components/ui/badge';
import { Button } from '@/app/components/ui/button';
import { FolderGit, Star, Clock, ChevronRight, Code, Users, GitCommit } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { CommunityToolCardProps } from '../types';
import { formatDistanceToNow } from 'date-fns';

export function CommunityToolCard({
  tool,
  isSelected,
  onSelect,
  failedIcons,
  onIconError,
  expandedTools,
  setExpandedTools
}: CommunityToolCardProps) {
  const firstTool = tool.tools?.[0];
  const hasTools = tool.tools?.length > 0;
  const toolIcon = firstTool?.icon_url || tool.icon_url;

  const isLoading = tool.loadingState === 'loading' || tool.isDiscovering;
  const hasError = tool.loadingState === 'error';

  return (
    <Card
      className={cn(
        "bg-slate-900 border-slate-800",
        "transition-all duration-200",
        "cursor-pointer overflow-hidden",
        !hasTools && "opacity-50 cursor-not-allowed",
        isSelected && "ring-2 ring-purple-500 border-purple-500",
        hasTools && "hover:border-purple-500/30",
        tool.error && "border-red-500/30"
      )}
      onClick={() => hasTools && onSelect()}
    >
      <div className="p-4 space-y-4">
        {/* Header with Icon and Title */}
        <div className="flex items-start gap-3">
          <div className={cn(
            "p-2 rounded-md transition-colors",
            isSelected ? "bg-purple-500/20" : "bg-purple-500/10",
            "border border-purple-500/20"
          )}>
            {toolIcon && !failedIcons?.has(toolIcon) ? (
              <img 
                src={toolIcon} 
                alt={tool.name} 
                className="w-8 h-8"
                onError={() => onIconError?.(toolIcon)}
              />
            ) : (
              <Code className="w-8 h-8 text-purple-400" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-medium text-slate-200 truncate">{tool.name}</h3>
            <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">{tool.description}</p>
          </div>
        </div>

        {/* Metadata */}
        <div className="flex items-center gap-3 text-xs text-slate-400">
          {tool.stars !== undefined && (
            <div className="flex items-center gap-1">
              <Star className="w-3.5 h-3.5" />
              <span>{tool.stars}</span>
            </div>
          )}
          {tool.contributors_count !== undefined && (
            <div className="flex items-center gap-1">
              <Users className="w-3.5 h-3.5" />
              <span>{tool.contributors_count}</span>
            </div>
          )}
          {tool.lastCommit && (
            <div className="flex items-center gap-1" title={tool.lastCommit.message}>
              <GitCommit className="w-3.5 h-3.5" />
              <span>{formatDistanceToNow(new Date(tool.lastCommit.date), { addSuffix: true })}</span>
            </div>
          )}
        </div>

        {/* Tools Count */}
        {hasTools && (
          <div className="flex items-center justify-between">
            <Badge variant="secondary" className="bg-purple-500/10 text-purple-400 border-purple-500/20">
              {tool.tools.length} tool{tool.tools.length !== 1 ? 's' : ''}
            </Badge>
            <ChevronRight className="w-4 h-4 text-slate-400" />
          </div>
        )}

        {/* Error State */}
        {hasError && tool.error && (
          <div className="text-xs text-red-400 mt-2">
            {tool.error}
          </div>
        )}
      </div>
    </Card>
  );
} 