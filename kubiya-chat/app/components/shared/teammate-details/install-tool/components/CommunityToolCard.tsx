import * as React from 'react';
import { FolderGit, Code, AlertCircle, Loader2 } from 'lucide-react';
import { Badge } from '@/app/components/ui/badge';
import { Card, CardHeader, CardTitle, CardDescription } from '@/app/components/ui/card';
import { HoverCard, HoverCardTrigger, HoverCardContent } from '@/app/components/ui/hover-card';
import { cn } from '@/lib/utils';
import { styles } from '../styles';
import type { CommunityToolCardProps } from '../types';
import { Button } from '@/app/components/ui/button';

const PYTHON_ICON_URL = 'https://www.svgrepo.com/show/376344/python.svg';

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
  const toolIcon = firstTool?.icon_url || tool.icon;

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
      <CardHeader className="flex flex-row items-start gap-4 p-4">
        <div className={cn(
          "p-2 rounded-md transition-colors",
          isSelected ? "bg-purple-500/20" : "bg-purple-500/10",
          "border border-purple-500/20"
        )}>
          {toolIcon && !failedIcons?.has(toolIcon) ? (
            <img 
              src={toolIcon} 
              alt={tool.name} 
              className="h-8 w-8"
              onError={() => onIconError?.(toolIcon)} 
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
              <CardTitle className={cn(
                "text-lg",
                isSelected ? "text-purple-400" : "text-slate-200"
              )}>
                {tool.name}
              </CardTitle>
              {isLoading ? (
                <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20">
                  <Loader2 className="h-3 w-3 animate-spin mr-1" />
                  Loading tools...
                </Badge>
              ) : hasError ? (
                <Badge variant="outline" className="bg-red-500/10 text-red-400 border-red-500/20">
                  Failed to load tools
                </Badge>
              ) : !hasTools ? (
                <Badge variant="outline" className="bg-slate-500/10 text-slate-400 border-slate-500/20">
                  No Tools
                </Badge>
              ) : (
                <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/20">
                  {tool.tools.length} tool{tool.tools.length !== 1 && 's'}
                </Badge>
              )}
            </div>
          </div>
          <CardDescription className="text-slate-400 mt-1">
            {tool.description}
          </CardDescription>
        </div>
      </CardHeader>

      {isSelected && hasTools && (
        <div className="border-t border-slate-800 p-4 bg-slate-900/50">
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-purple-400">Available Tools</h4>
            <div className="grid grid-cols-1 gap-2">
              {tool.tools.map((t: any) => (
                <HoverCard key={t.name} openDelay={200}>
                  <HoverCardTrigger>
                    <div className="flex items-start gap-3 p-2 rounded-md bg-slate-900/50 border border-slate-800 hover:border-purple-500/30 transition-colors">
                      <div className="p-1.5 rounded-md bg-purple-500/10 border border-purple-500/20">
                        <Code className="h-4 w-4 text-purple-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-200">{t.name}</p>
                        <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{t.description}</p>
                      </div>
                    </div>
                  </HoverCardTrigger>
                  <HoverCardContent className="w-80">
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium text-slate-200">{t.name}</h4>
                      <p className="text-xs text-slate-400">{t.description}</p>
                      {t.args && (
                        <div className="pt-2">
                          <span className="text-xs font-medium text-slate-300">Arguments:</span>
                          <div className="mt-1 space-y-1">
                            {Object.entries(t.args).map(([name, arg]: [string, any]) => (
                              <div key={name} className="flex items-center gap-2">
                                <code className="px-1.5 py-0.5 bg-slate-800 rounded text-xs font-mono text-slate-300">
                                  {name}
                                </code>
                                {arg.required && (
                                  <Badge variant="outline" className="text-[10px] bg-red-500/10 text-red-400 border-red-500/20">
                                    Required
                                  </Badge>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </HoverCardContent>
                </HoverCard>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="p-4 border-t border-slate-800 bg-slate-900">
        <Button
          variant="outline"
          size="sm"
          onClick={onSelect}
          className="h-8 bg-slate-900 text-slate-400 border-slate-700 hover:bg-slate-800 hover:text-slate-300"
        >
          <Code className="h-4 w-4 mr-2" />
          View Details
        </Button>
      </div>
    </Card>
  );
} 