import * as React from 'react';
import { Card, CardHeader } from '@/app/components/ui/card';
import { Badge } from '@/app/components/ui/badge';
import { Button } from '@/app/components/ui/button';
import { FolderGit, Star, Clock, ChevronRight, Code, Users, GitCommit, Loader2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { CommunityToolCardProps } from '../types';
import { formatDistanceToNow } from 'date-fns';
import { Skeleton } from '@/app/components/ui/skeleton';

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
        hasError && "border-red-500/30"
      )}
      onClick={() => hasTools && onSelect()}
    >
      <div className="p-4 space-y-4">
        {/* Header with Icon and Title */}
        <div className="flex items-start gap-3">
          <div className={cn(
            "p-2 rounded-md transition-colors",
            isSelected ? "bg-purple-500/20" : "bg-purple-500/10",
            "border border-purple-500/20",
            "relative min-w-[48px] min-h-[48px] flex items-center justify-center"
          )}>
            {isLoading ? (
              <Loader2 className="h-6 w-6 text-purple-500 animate-spin" />
            ) : hasError ? (
              <AlertCircle className="h-6 w-6 text-red-500" />
            ) : toolIcon && !failedIcons?.has(toolIcon) ? (
              <img 
                src={toolIcon} 
                alt={tool.name} 
                className="h-6 w-6 object-contain"
                onError={() => onIconError(toolIcon)}
              />
            ) : (
              <FolderGit className="h-6 w-6 text-purple-500" />
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-medium text-slate-200 truncate">
                {tool.name}
              </h3>
              {tool.tools_count > 0 && (
                <Badge variant="secondary" className="shrink-0">
                  {tool.tools_count} {tool.tools_count === 1 ? 'tool' : 'tools'}
                </Badge>
              )}
            </div>
            <p className="text-xs text-slate-400 line-clamp-2 mt-1">
              {tool.description || 'No description available'}
            </p>
          </div>
        </div>

        {/* Metadata */}
        <div className="flex flex-wrap gap-3 text-xs text-slate-400">
          {tool.stars !== undefined && (
            <div className="flex items-center gap-1">
              <Star className="h-3.5 w-3.5" />
              <span>{tool.stars}</span>
            </div>
          )}
          {tool.lastUpdated && (
            <div className="flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              <span>Updated {formatDistanceToNow(new Date(tool.lastUpdated))} ago</span>
            </div>
          )}
          {tool.lastCommit && (
            <div className="flex items-center gap-1">
              <GitCommit className="h-3.5 w-3.5" />
              <span className="truncate max-w-[150px]">{tool.lastCommit.message}</span>
            </div>
          )}
        </div>

        {/* Tools Preview */}
        {hasTools && (
          <div className="space-y-2">
            <div className="text-xs font-medium text-slate-300">Available Tools:</div>
            <div className="space-y-1">
              {tool.tools.slice(0, expandedTools.has(tool.id) ? undefined : 3).map((subTool: any) => (
                <div key={subTool.name} className="flex items-center gap-2 text-xs text-slate-400 p-1.5 rounded-md bg-slate-800/50">
                  <Code className="h-3.5 w-3.5 shrink-0" />
                  <span className="truncate">{subTool.name}</span>
                  {subTool.description && (
                    <span className="hidden sm:inline text-slate-500 truncate">
                      - {subTool.description}
                    </span>
                  )}
                </div>
              ))}
            </div>
            {tool.tools.length > 3 && (
              <Button
                variant="ghost"
                size="sm"
                className="w-full text-xs"
                onClick={(e) => {
                  e.stopPropagation();
                  setExpandedTools(prev => {
                    const next = new Set(prev);
                    if (next.has(tool.id)) {
                      next.delete(tool.id);
                    } else {
                      next.add(tool.id);
                    }
                    return next;
                  });
                }}
              >
                {expandedTools.has(tool.id) ? 'Show Less' : `Show ${tool.tools.length - 3} More`}
              </Button>
            )}
          </div>
        )}

        {/* Error Message */}
        {hasError && (
          <div className="text-xs text-red-400 flex items-center gap-1.5">
            <AlertCircle className="h-3.5 w-3.5" />
            <span>{tool.error || 'Failed to load tools'}</span>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
          </div>
        )}
      </div>
    </Card>
  );
} 