import * as React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/app/components/ui/card';
import { Badge } from '@/app/components/ui/badge';
import { Button } from '@/app/components/ui/button';
import { 
  Code, 
  Ship, 
  Settings, 
  AlertCircle, 
  Box, 
  Terminal, 
  Database,
  Info,
  GitBranch,
  GitCommit,
  Hash,
  FolderGit,
  ExternalLink,
  MessageSquare,
  User2,
  Clock,
  Dock,
  Variable,
  Key,
  PackageOpen,
  Folder,
  FolderOpen,
  Loader2,
  PackageSearch
} from 'lucide-react';
import { Alert, AlertTitle, AlertDescription } from '@/app/components/ui/alert';
import { cn } from '@/lib/utils';
import type { ExtendedCommunityTool } from '../types';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/app/components/ui/tooltip";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/app/components/ui/hover-card";
import { format } from 'date-fns';
import { Separator } from '@/app/components/ui/separator';

interface PreviewStepProps {
  selectedTool: ExtendedCommunityTool | null;
  isLoading?: boolean;
}

function ToolCard({ tool }: { tool: any }) {
  const paramCount = tool.args?.length || 0;
  const secretCount = tool.secrets?.length || 0;
  const envCount = tool.env?.length || 0;

  return (
    <div className="group relative bg-slate-800/50 hover:bg-slate-800 rounded-lg border border-slate-700 hover:border-purple-500/30 transition-all duration-200">
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-md bg-slate-900/50 border border-slate-700">
              {tool.icon_url ? (
                <img 
                  src={tool.icon_url} 
                  alt={tool.name} 
                  className="h-5 w-5"
                  onError={(e) => {
                    e.currentTarget.src = '';
                    e.currentTarget.style.display = 'none';
                  }}
                />
              ) : (
                <Code className="h-5 w-5 text-purple-400" />
              )}
            </div>
            <div>
              <h4 className="text-sm font-medium text-slate-200 tracking-wide flex items-center gap-2">
                {tool.name}
                {tool.type && (
                  <Badge 
                    variant="outline" 
                    className={cn(
                      "text-xs font-medium tracking-wide",
                      tool.type === 'docker' 
                        ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                        : "bg-purple-500/10 text-purple-400 border-purple-500/20"
                    )}
                  >
                    {tool.type}
                  </Badge>
                )}
              </h4>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">{tool.description}</p>
              
              {/* Tool Metadata */}
              <div className="flex items-center gap-3 mt-3">
                <HoverCard>
                  <HoverCardTrigger asChild>
                    <div className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-purple-400 cursor-help">
                      <Settings className="h-3.5 w-3.5" />
                      <span>{paramCount} params</span>
                    </div>
                  </HoverCardTrigger>
                  <HoverCardContent className="w-80 p-3">
                    <div className="space-y-2">
                      <h5 className="text-sm font-medium text-slate-200">Parameters</h5>
                      <div className="space-y-1.5">
                        {tool.args?.map((param: any, idx: number) => (
                          <div key={idx} className="text-xs">
                            <div className="flex items-center gap-1.5">
                              <span className="font-medium text-purple-400">{param.name}</span>
                              <Badge variant="outline" className="text-[10px]">
                                {param.type}
                              </Badge>
                              {param.required && (
                                <Badge className="bg-red-500/10 text-red-400 border-red-500/20 text-[10px]">
                                  required
                                </Badge>
                              )}
                            </div>
                            <p className="text-slate-400 mt-0.5">{param.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </HoverCardContent>
                </HoverCard>

                {secretCount > 0 && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-purple-400 cursor-help">
                          <Key className="h-3.5 w-3.5" />
                          <span>{secretCount} secrets</span>
                        </div>
                      </TooltipTrigger>
                      <TooltipContent>
                        <div className="space-y-1">
                          {tool.secrets?.map((secret: string, idx: number) => (
                            <div key={idx} className="text-xs text-slate-400">{secret}</div>
                          ))}
                        </div>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}

                {envCount > 0 && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-purple-400 cursor-help">
                          <Variable className="h-3.5 w-3.5" />
                          <span>{envCount} env vars</span>
                        </div>
                      </TooltipTrigger>
                      <TooltipContent>
                        <div className="space-y-1">
                          {tool.env?.map((env: string, idx: number) => (
                            <div key={idx} className="text-xs text-slate-400">{env}</div>
                          ))}
                        </div>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}

                {tool.image && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-purple-400 cursor-help">
                          <Dock className="h-3.5 w-3.5" />
                          <span>Docker</span>
                        </div>
                      </TooltipTrigger>
                      <TooltipContent>
                        <div className="text-xs text-slate-400">{tool.image}</div>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function PreviewStep({ selectedTool, isLoading = false }: PreviewStepProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[400px] space-y-4">
        <div className="p-3 rounded-full bg-purple-500/10 border border-purple-500/20">
          <Loader2 className="h-6 w-6 text-purple-400 animate-spin" />
        </div>
        <p className="text-sm text-slate-400">Loading tool details...</p>
      </div>
    );
  }

  if (!selectedTool) {
    return (
      <div className="flex flex-col items-center justify-center h-[400px] space-y-4">
        <div className="p-3 rounded-full bg-amber-500/10 border border-amber-500/20">
          <PackageSearch className="h-6 w-6 text-amber-400" />
        </div>
        <div className="text-center space-y-2">
          <h3 className="text-lg font-medium text-slate-200">No Tool Selected</h3>
          <p className="text-sm text-slate-400 max-w-md">
            Please go back and select a tool to continue.
          </p>
          <Button 
            variant="outline" 
            onClick={() => window.history.back()}
            className="mt-4 bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-slate-200"
          >
            <AlertCircle className="mr-2 h-4 w-4" />
            Go Back to Selection
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Source Info */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-md bg-purple-500/10 border border-purple-500/20">
              <FolderGit className="h-5 w-5 text-purple-400" />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <CardTitle className="text-lg font-medium text-slate-200">
                  {selectedTool.name}
                </CardTitle>
                {selectedTool.type && (
                  <Badge 
                    variant="outline" 
                    className="bg-purple-500/10 text-purple-400 border-purple-500/20"
                  >
                    {selectedTool.type}
                  </Badge>
                )}
              </div>

              <p className="text-sm text-slate-400 mt-2">{selectedTool.description}</p>

              {/* Source Metadata */}
              {selectedTool.source && typeof selectedTool.source === 'object' && (
                <div className="flex flex-col gap-1 mt-3">
                  {selectedTool.source.metadata?.git_branch && (
                    <div className="flex items-center gap-2 text-xs text-slate-400">
                      <GitBranch className="h-3.5 w-3.5 text-emerald-400" />
                      <span>Branch: {selectedTool.source.metadata.git_branch}</span>
                    </div>
                  )}
                  {selectedTool.source.metadata?.git_commit && (
                    <div className="flex items-center gap-2 text-xs text-slate-400">
                      <Hash className="h-3.5 w-3.5 text-emerald-400" />
                      <span>Commit: {selectedTool.source.metadata.git_commit.slice(0, 7)}</span>
                    </div>
                  )}
                  {selectedTool.source.metadata?.last_updated && (
                    <div className="flex items-center gap-2 text-xs text-slate-400">
                      <Clock className="h-3.5 w-3.5 text-emerald-400" />
                      <span>Last Updated: {format(new Date(selectedTool.source.metadata.last_updated), 'MMM d, yyyy')}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Tools Grid */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-medium">Available Tools</CardTitle>
            <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/20">
              {selectedTool.tools?.length || 0} tools
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {selectedTool.tools && selectedTool.tools.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {selectedTool.tools.map((tool: any, index: number) => (
                <ToolCard key={`${tool.name}-${index}`} tool={tool} />
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <div className="p-3 rounded-full bg-slate-800 border border-slate-700">
                <PackageOpen className="h-6 w-6 text-slate-400" />
              </div>
              <h3 className="text-lg font-medium text-slate-200 mt-4">No Tools Found</h3>
              <p className="text-sm text-slate-400 max-w-md mt-2">
                No tools were discovered in this source. This could be because the source is still being scanned or there are no compatible tools.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
} 