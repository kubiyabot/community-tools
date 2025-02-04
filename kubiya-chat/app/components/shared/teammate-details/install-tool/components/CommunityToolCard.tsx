import * as React from 'react';
import { Card, CardHeader } from '@/app/components/ui/card';
import { Badge } from '@/app/components/ui/badge';
import { Button } from '@/app/components/ui/button';
import { FolderGit, Star, Clock, ChevronRight, Code } from 'lucide-react';
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
                className="h-8 w-8 object-contain"
                onError={() => onIconError?.(toolIcon!)} 
              />
            ) : (
              <FolderGit className={cn(
                "h-8 w-8",
                isSelected ? "text-purple-400" : "text-purple-400/70"
              )} />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-medium text-slate-200">{tool.name}</h3>
                {tool.tools_count > 0 && (
                  <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/20">
                    {tool.tools_count} tools
                  </Badge>
                )}
              </div>
            </div>
            <p className="text-sm text-slate-400 mt-1">{tool.description}</p>
          </div>
        </div>

        {/* Metadata Row */}
        <div className="flex items-center gap-4 text-xs text-slate-400">
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
        </div>

        {/* README Preview */}
        {tool.readme && (
          <div className="mt-3">
            <div className="text-xs font-medium text-slate-300 mb-2">README</div>
            <div className="text-xs text-slate-400 line-clamp-3">
              {tool.readme}
            </div>
          </div>
        )}

        {/* Tool Preview */}
        {hasTools && (
          <div className="border-t border-slate-800 pt-3 mt-3">
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs font-medium text-slate-300">Available Tools</div>
              <Button 
                variant="ghost" 
                size="sm" 
                className="h-6 px-2 text-xs"
                onClick={(e) => {
                  e.stopPropagation();
                  setExpandedTools?.(prev => {
                    const next = new Set(prev);
                    if (next.has(tool.name)) {
                      next.delete(tool.name);
                    } else {
                      next.add(tool.name);
                    }
                    return next;
                  });
                }}
              >
                View All <ChevronRight className={cn(
                  "h-3 w-3 ml-1 transition-transform",
                  expandedTools?.has(tool.name) && "rotate-90"
                )} />
              </Button>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex -space-x-2">
                {tool.tools.slice(0, 3).map((subTool, idx) => (
                  <div
                    key={idx}
                    className={cn(
                      "w-6 h-6 rounded-md border-2 border-slate-800 bg-slate-900",
                      "flex items-center justify-center overflow-hidden"
                    )}
                  >
                    {subTool.icon_url && !failedIcons?.has(subTool.icon_url) ? (
                      <img
                        src={subTool.icon_url}
                        alt={subTool.name}
                        className="h-4 w-4 object-contain"
                        onError={() => onIconError?.(subTool.icon_url!)}
                      />
                    ) : (
                      <Code className="h-3 w-3 text-slate-400" />
                    )}
                  </div>
                ))}
              </div>
              {tool.tools.length > 3 && (
                <span className="text-xs text-slate-400">
                  +{tool.tools.length - 3} more
                </span>
              )}
            </div>

            {/* Expanded Tools List */}
            {expandedTools?.has(tool.name) && (
              <div className="mt-3 space-y-2">
                {tool.tools.map((subTool, idx) => (
                  <div 
                    key={idx}
                    className="flex items-center gap-2 p-2 rounded-md bg-slate-800/50"
                  >
                    <div className="w-6 h-6 rounded-md bg-slate-900 flex items-center justify-center">
                      {subTool.icon_url && !failedIcons?.has(subTool.icon_url) ? (
                        <img
                          src={subTool.icon_url}
                          alt={subTool.name}
                          className="h-4 w-4 object-contain"
                          onError={() => onIconError?.(subTool.icon_url!)}
                        />
                      ) : (
                        <Code className="h-3 w-3 text-slate-400" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-slate-200">{subTool.name}</div>
                      <p className="text-xs text-slate-400 truncate">{subTool.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center">
            <div className="animate-spin">
              <FolderGit className="h-6 w-6 text-purple-400" />
            </div>
          </div>
        )}

        {/* Error State */}
        {hasError && (
          <div className="mt-2 text-xs text-red-400">
            {tool.error || 'Failed to load tool details'}
          </div>
        )}
      </div>
    </Card>
  );
} 