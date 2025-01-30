"use client";

import { useMemo, useEffect, useState, useCallback } from 'react';
import { FolderGit, Link as LinkIcon, GitBranch, ExternalLink, Loader2, Bot, Package, Database, Code, Terminal, Settings, Info, Hash, Box, Dock, AlertCircle } from 'lucide-react';
import type { TeammateTabProps } from './types';
import type { Tool as SourceTool } from '@/app/types/tool';
import type { Tool as TeammateToolType, TeammateDetails } from '@/app/types/teammate';
import type { SourceInfo } from '@/app/types/source';
import { Badge } from '@/app/components/ui/badge';
import { Button } from '@/app/components/ui/button';
import { Separator } from '@/app/components/ui/separator';
import { ToolDetailsModal } from '../tool-details/ToolDetailsModal';
import { cn } from '@/lib/utils';
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
import type { Tool } from '@/app/types/tool';
import { EntityProvider } from '@/app/providers/EntityProvider';

interface KubiyaMetadata {
  created_at: string;
  last_updated: string;
  user_created: string;
  user_last_updated: string;
}

interface SourceMeta {
  id: string;
  url: string;
  commit: string;
  committer: string;
  branch: string;
}

interface DynamicConfig {
  [key: string]: any;
}

interface ToolParameter {
  name: string;
  type: string;
  description: string;
  required?: boolean;
}

interface Source {
  sourceId: string;
  uuid?: string;
  name: string;
  type?: string;
  tools?: any[];
  isLoading?: boolean;
  error?: string;
}

const LoadingSpinner = () => (
  <div className="flex flex-col items-center justify-center h-[400px] p-6">
    <div className="p-3 rounded-full bg-[#1E293B] border border-[#1E293B]">
      <Loader2 className="h-6 w-6 text-[#7C3AED] animate-spin" />
    </div>
    <p className="text-sm font-medium text-[#94A3B8] mt-4">Loading sources...</p>
  </div>
);

const EmptyState = () => (
  <div className="flex flex-col items-center justify-center h-[400px] p-6">
    <div className="p-3 rounded-full bg-[#1E293B] border border-[#1E293B]">
      <FolderGit className="h-6 w-6 text-[#7C3AED]" />
    </div>
    <p className="text-sm font-medium text-[#94A3B8] mt-4">No tools available</p>
  </div>
);

const ErrorState = ({ message }: { message: string }) => (
  <div className="flex flex-col items-center justify-center h-[400px] p-6">
    <div className="p-3 rounded-full bg-red-500/10 border border-red-500/20">
      <FolderGit className="h-6 w-6 text-red-400" />
    </div>
    <p className="text-sm font-medium text-red-400 mt-4">{message}</p>
  </div>
);

const ToolCard = ({ tool, source }: { tool: SourceTool; source: SourceInfo }) => {
  const [showDetails, setShowDetails] = useState(false);
  const paramCount = tool.args?.length || 0;
  const secretCount = tool.secrets?.length || 0;
  const envCount = Number(tool.env?.length) || 0;

  const handleClose = useCallback(() => {
    setShowDetails(false);
  }, []);

  // Convert SourceTool to TeammateToolType for ToolDetailsModal
  const teammateToolData = {
    id: tool.name, // Using name as id since it should be unique within a source
    name: tool.name,
    description: tool.description || '', // Ensure description is never undefined
    type: tool.type || 'unknown',
    icon_url: tool.icon_url,
    image: tool.image,
    content: tool.content, // Map code to content for entrypoint.sh
    workdir: tool.workdir,
    args: tool.args,
    env: tool.env,
    secrets: tool.secrets,
    with_files: tool.with_files?.map(file => ({
      source: file.source || '',
      target: file.source || '', // Use source as target if destination is not available
      content: file.content
    })),
    mounts: tool.mounts?.map(mount => {
      if (typeof mount === 'string') {
        return { source: mount, target: mount };
      }
      return mount;
    }),
    mermaid: tool.mermaid,
    source: tool.source ? {
      name: tool.source.name,
      url: tool.source.url,
      metadata: {
        git_branch: tool.source.metadata?.git_branch,
        git_commit: tool.source.metadata?.git_commit,
        git_path: '',
        docker_image: '',
        last_updated: tool.source.metadata?.last_updated,
        created_at: tool.source.metadata?.last_updated
      }
    } : undefined,
    uuid: tool.name, // Add uuid field
    alias: tool.name // Add alias field
  } as Tool;

  return (
    <>
      <div 
        className="group relative bg-[#1E293B]/50 hover:bg-[#1E293B] rounded-lg border border-[#1E293B] hover:border-[#7C3AED]/50 transition-all duration-200 cursor-pointer"
        onClick={() => setShowDetails(true)}
      >
        <div className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-md bg-[#2A3347] border border-[#2A3347]">
                {teammateToolData.icon_url ? (
                  <img src={teammateToolData.icon_url} alt={teammateToolData.name} className="h-5 w-5" />
                ) : (
                  <Code className="h-5 w-5 text-[#7C3AED]" />
                )}
              </div>
              <div>
                <h4 className="text-sm font-medium text-white tracking-wide flex items-center gap-2">
                  {teammateToolData.name}
                  {teammateToolData.type && (
                    <Badge 
                      variant="outline" 
                      className={cn(
                        "text-xs font-medium tracking-wide",
                        teammateToolData.type === 'docker' 
                          ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                          : "bg-purple-500/10 text-purple-400 border-purple-500/20"
                      )}
                    >
                      {teammateToolData.type}
                    </Badge>
                  )}
                </h4>
                <p className="text-xs text-[#94A3B8] mt-1 leading-relaxed">{teammateToolData.description}</p>
                
                {/* Tool Metadata */}
                <div className="flex items-center gap-3 mt-3">
                  <HoverCard>
                    <HoverCardTrigger asChild>
                      <div className="flex items-center gap-1.5 text-xs text-[#94A3B8] hover:text-[#7C3AED] cursor-help">
                        <Settings className="h-3.5 w-3.5" />
                        <span>{paramCount} params</span>
                      </div>
                    </HoverCardTrigger>
                    <HoverCardContent className="w-80 p-3">
                      <div className="space-y-2">
                        <h5 className="text-sm font-medium text-white">Parameters</h5>
                        <div className="space-y-1.5">
                          {teammateToolData.args?.map((param: ToolParameter, idx: number) => (
                            <div key={idx} className="text-xs">
                              <div className="flex items-center gap-1.5">
                                <span className="font-medium text-[#7C3AED]">{param.name}</span>
                                <Badge variant="outline" className="text-[10px]">
                                  {param.type}
                                </Badge>
                                {param.required && (
                                  <Badge className="bg-red-500/10 text-red-400 border-red-500/20 text-[10px]">
                                    required
                                  </Badge>
                                )}
                              </div>
                              <p className="text-[#94A3B8] mt-0.5">{param.description}</p>
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
                          <div className="flex items-center gap-1.5 text-xs text-[#94A3B8] hover:text-[#7C3AED] cursor-help">
                            <Database className="h-3.5 w-3.5" />
                            <span>{secretCount} secrets</span>
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>
                          <div className="space-y-1">
                            {teammateToolData.secrets?.map((secret: string, idx: number) => (
                              <div key={idx} className="text-xs text-[#94A3B8]">{secret}</div>
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
                          <div className="flex items-center gap-1.5 text-xs text-[#94A3B8] hover:text-[#7C3AED] cursor-help">
                            <Box className="h-3.5 w-3.5" />
                            <span>{envCount} env vars</span>
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>
                          <div className="space-y-1">
                            {Array.isArray(teammateToolData.env) && teammateToolData.env.map((env: string, idx: number) => (
                              <div key={idx} className="text-xs text-[#94A3B8]">{env}</div>
                            ))}
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  )}

                  {teammateToolData.image && (
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div className="flex items-center gap-1.5 text-xs text-[#94A3B8] hover:text-[#7C3AED] cursor-help">
                            <Dock className="h-3.5 w-3.5" />
                            <span>Docker</span>
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>
                          <div className="text-xs text-[#94A3B8]">{teammateToolData.image}</div>
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

      <EntityProvider>
        <ToolDetailsModal
          tool={teammateToolData}
          source={source}
          isOpen={showDetails}
          onCloseAction={handleClose}
        />
      </EntityProvider>
    </>
  );
};

const getSourceDisplayName = (url: string, name: string): string => {
  try {
    const urlObj = new URL(url);
    if (urlObj.hostname === 'github.com') {
      const parts = urlObj.pathname.split('/');
      const lastPart = parts[parts.length - 1];
      return lastPart || name;
    }
    return name;
  } catch {
    return name;
  }
};

const getGitHubInfo = (url: string) => {
  try {
    const urlObj = new URL(url);
    if (urlObj.hostname === 'github.com') {
      const parts = urlObj.pathname.split('/');
      const owner = parts[1];
      const repo = parts[2];
      const isTree = parts.includes('tree');
      const isBlobOrRaw = parts.includes('blob') || parts.includes('raw');
      const branch = isTree ? parts[parts.indexOf('tree') + 1] : 
                    isBlobOrRaw ? parts[parts.indexOf('blob') + 1] || parts[parts.indexOf('raw') + 1] : 'main';
      const path = isTree ? parts.slice(parts.indexOf(branch) + 1).join('/') :
                  isBlobOrRaw ? parts.slice(parts.indexOf(branch) + 1).join('/') : '';
      
      return {
        owner,
        repo,
        branch,
        path,
        viewOnGitHub: url,
        repoUrl: `https://github.com/${owner}/${repo}`,
        branchUrl: `https://github.com/${owner}/${repo}/tree/${branch}`,
        commitUrl: `https://github.com/${owner}/${repo}/commit/`
      };
    }
    return null;
  } catch {
    return null;
  }
};

const SourceGroup = ({ source }: { source: SourceInfo }) => {
  const gitHubInfo = useMemo(() => getGitHubInfo(source.url), [source.url]);

  return (
    <div className="bg-[#1E293B] rounded-xl p-6 space-y-4">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-md bg-[#2A3347] border border-[#2A3347]">
            {source.type === 'github' ? (
              <img src="https://cdn-icons-png.flaticon.com/512/25/25231.png" alt="GitHub" className="h-5 w-5" />
            ) : (
              <FolderGit className="h-5 w-5 text-[#7C3AED]" />
            )}
          </div>
          <div className="space-y-2">
            <div>
              <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
                {source.name}
                {source.errors_count > 0 && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Badge variant="destructive" className="bg-red-500/10 text-red-400 border-red-500/20 cursor-help">
                          {source.errors_count} {source.errors_count === 1 ? 'error' : 'errors'}
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent className="w-80 bg-[#1E293B] border border-red-500/20 p-3">
                        <div className="space-y-2">
                          <h5 className="text-sm font-medium text-white flex items-center gap-2">
                            <AlertCircle className="h-4 w-4 text-red-400" />
                            Source Errors
                          </h5>
                          {source.error && (
                            <div className="text-xs text-red-400 bg-red-500/10 p-2 rounded border border-red-500/20">
                              {source.error}
                            </div>
                          )}
                        </div>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </h3>
              
              {/* Source Control Links */}
              {gitHubInfo && (
                <div className="flex flex-col gap-1 mt-1">
                  <div className="flex items-center gap-2 text-xs">
                    <a
                      href={gitHubInfo.repoUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[#94A3B8] hover:text-[#7C3AED] flex items-center gap-1 transition-colors"
                    >
                      <FolderGit className="h-3 w-3" />
                      {gitHubInfo.owner}/{gitHubInfo.repo}
                    </a>
                    {source.source_meta.branch && (
                      <>
                        <span className="text-[#4B5563]">/</span>
                        <a
                          href={gitHubInfo.branchUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[#94A3B8] hover:text-[#7C3AED] flex items-center gap-1 transition-colors"
                        >
                          <GitBranch className="h-3 w-3" />
                          {source.source_meta.branch}
                        </a>
                      </>
                    )}
                  </div>
                  {source.source_meta.commit && (
                    <div className="flex items-center gap-2 text-xs">
                      <a
                        href={`${gitHubInfo.commitUrl}${source.source_meta.commit}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#94A3B8] hover:text-[#7C3AED] flex items-center gap-1 transition-colors group"
                      >
                        <Hash className="h-3 w-3" />
                        <span className="font-mono">{source.source_meta.commit.slice(0, 7)}</span>
                        <span className="text-[#4B5563]">by</span>
                        <span>{source.source_meta.committer}</span>
                        <ExternalLink className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </a>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Source Metadata */}
            <div className="grid grid-cols-2 gap-4 mt-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
                  <Package className="h-3.5 w-3.5" />
                  <span>{source.connected_tools_count} tools</span>
                </div>
                {source.connected_workflows_count > 0 && (
                  <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
                    <Terminal className="h-3.5 w-3.5" />
                    <span>{source.connected_workflows_count} workflows</span>
                  </div>
                )}
              </div>
            </div>

            {/* Dynamic Configuration */}
            {source.dynamic_config && Object.keys(source.dynamic_config).length > 0 && (
              <HoverCard>
                <HoverCardTrigger asChild>
                  <div className="flex items-center gap-2 text-xs text-[#94A3B8] hover:text-[#7C3AED] cursor-help mt-2">
                    <Settings className="h-3.5 w-3.5" />
                    <span>Dynamic Configuration Available</span>
                  </div>
                </HoverCardTrigger>
                <HoverCardContent className="w-80">
                  <div className="space-y-2">
                    <h5 className="text-sm font-medium text-white">Dynamic Configuration</h5>
                    <pre className="text-xs text-[#94A3B8] bg-[#1E293B] p-2 rounded-md overflow-auto max-h-60">
                      {JSON.stringify(source.dynamic_config, null, 2)}
                    </pre>
                  </div>
                </HoverCardContent>
              </HoverCard>
            )}

            {/* Creation Info */}
            <div className="text-xs text-[#94A3B8] mt-2">
              <div className="flex items-center gap-1">
                <span>Created by</span>
                <span className="font-medium">{source.kubiya_metadata.user_created}</span>
                <span>on</span>
                <span>{new Date(source.kubiya_metadata.created_at).toLocaleDateString()}</span>
              </div>
              <div className="flex items-center gap-1">
                <span>Updated by</span>
                <span className="font-medium">{source.kubiya_metadata.user_last_updated}</span>
                <span>on</span>
                <span>{new Date(source.kubiya_metadata.last_updated).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        </div>
        {source.isLoading && (
          <div className="flex items-center gap-2 text-[#94A3B8]">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-xs">Loading tools...</span>
          </div>
        )}
      </div>

      <Separator className="bg-[#2D3B4E]" />

      {source.error ? (
        <div className="bg-red-500/10 text-red-400 rounded-lg p-3 text-sm">
          {source.error}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {source.tools.map((tool, toolIndex) => (
            <ToolCard key={`${tool.name}-${toolIndex}`} tool={tool} source={source} />
          ))}
        </div>
      )}
    </div>
  );
};

function getSourceNameFromUrl(url: string): string {
  if (!url) return '';
  try {
    const urlObj = new URL(url);
    if (urlObj.hostname === 'github.com') {
      const parts = urlObj.pathname.split('/');
      if (parts.length >= 3) {
        return `${parts[1]}/${parts[2]}`;
      }
    }
    return urlObj.hostname;
  } catch {
    return '';
  }
}

function getSourceType(url: string): string {
  if (!url) return 'local';
  try {
    const urlObj = new URL(url);
    if (urlObj.hostname === 'github.com') return 'github';
    return 'git';
  } catch {
    return 'local';
  }
}

export function SourcesTab({ teammate, sources = [], isLoading = false }: TeammateTabProps) {
  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!sources.length) {
    return <EmptyState />;
  }

  return (
    <div className="p-6 space-y-6">
      {/* Teammate Header */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex-shrink-0 w-12 h-12 rounded-full bg-[#2D3B4E] flex items-center justify-center">
          {teammate?.avatar_url ? (
            <img 
              src={teammate.avatar_url} 
              alt={teammate.name || 'Assistant'} 
              className="w-full h-full rounded-full object-cover"
            />
          ) : (
            <Bot className="h-6 w-6 text-[#7C3AED]" />
          )}
        </div>
        <div>
          <h2 className="text-xl font-semibold text-white">
            {teammate?.name || 'Unknown Teammate'}
          </h2>
          <p className="text-sm text-[#94A3B8]">
            {teammate?.description || 'No description available'}
          </p>
        </div>
      </div>

      <Separator className="bg-[#2D3B4E]" />

      {/* Sources Grid */}
      <div className="space-y-8">
        {sources.map((source: SourceInfo) => (
          <SourceGroup key={source.uuid} source={source} />
        ))}
      </div>
    </div>
  );
} 