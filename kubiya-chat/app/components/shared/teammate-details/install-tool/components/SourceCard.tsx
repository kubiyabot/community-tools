import * as React from 'react';
import { 
  FolderGit, 
  GitBranch, 
  Hash, 
  ExternalLink, 
  Package, 
  Terminal, 
  Bot, 
  Globe, 
  User,
  Settings,
  AlertCircle,
  RotateCw,
  Trash2,
  Info,
  Loader2,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { Badge } from '@/app/components/ui/badge';
import { Button } from '@/app/components/ui/button';
import { Separator } from '@/app/components/ui/separator';
import { cn } from '@/lib/utils';
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/app/components/ui/hover-card";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/app/components/ui/tooltip";
import type { SourceInfo } from '@/app/types/source';
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/app/components/ui/pagination"
import { ToolDetailsModal } from '../../../tool-details/ToolDetailsModal';
import { EntityProvider } from '@/app/providers/EntityProvider';
import type { Tool } from '@/app/types/tool';

interface SourceCardProps {
  source: SourceInfo;
  onSync: (sourceId: string) => Promise<any>;
  onDelete: (sourceId: string) => Promise<void>;
  onExpand: () => void;
  isExpanded: boolean;
}

const getSourceIcon = (url: string) => {
  try {
    const urlObj = new URL(url);
    switch(urlObj.hostname) {
      case 'github.com':
        return 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png';
      case 'gitlab.com':
        return 'https://about.gitlab.com/images/press/logo/png/gitlab-icon-rgb.png';
      case 'bitbucket.org':
        return 'https://wac-cdn.atlassian.com/assets/img/favicons/bitbucket/favicon-32x32.png';
      default:
        return null;
    }
  } catch {
    return null;
  }
};

const getRepoInfo = (url: string) => {
  try {
    const urlObj = new URL(url);
    const parts = urlObj.pathname.split('/');
    
    if (urlObj.hostname === 'github.com') {
      return {
        type: 'github',
        owner: parts[1],
        repo: parts[2],
        branch: parts.includes('tree') ? parts[parts.indexOf('tree') + 1] : 'main',
        repoUrl: `https://github.com/${parts[1]}/${parts[2]}`,
        branchUrl: `https://github.com/${parts[1]}/${parts[2]}/tree/${parts.includes('tree') ? parts[parts.indexOf('tree') + 1] : 'main'}`,
        commitUrl: `https://github.com/${parts[1]}/${parts[2]}/commit/`
      };
    }
    
    if (urlObj.hostname === 'gitlab.com') {
      return {
        type: 'gitlab',
        owner: parts[1],
        repo: parts[2],
        branch: parts.includes('tree') ? parts[parts.indexOf('tree') + 1] : 'main',
        repoUrl: `https://gitlab.com/${parts[1]}/${parts[2]}`,
        branchUrl: `https://gitlab.com/${parts[1]}/${parts[2]}/-/tree/${parts.includes('tree') ? parts[parts.indexOf('tree') + 1] : 'main'}`,
        commitUrl: `https://gitlab.com/${parts[1]}/${parts[2]}/-/commit/`
      };
    }
    
    if (urlObj.hostname === 'bitbucket.org') {
      return {
        type: 'bitbucket',
        owner: parts[1],
        repo: parts[2],
        branch: parts.includes('branch') ? parts[parts.indexOf('branch') + 1] : 'main',
        repoUrl: `https://bitbucket.org/${parts[1]}/${parts[2]}`,
        branchUrl: `https://bitbucket.org/${parts[1]}/${parts[2]}/branch/${parts.includes('branch') ? parts[parts.indexOf('branch') + 1] : 'main'}`,
        commitUrl: `https://bitbucket.org/${parts[1]}/${parts[2]}/commits/`
      };
    }
    
    return null;
  } catch {
    return null;
  }
};

const getMetadataValue = (source: SourceInfo, field: 'user_created' | 'user_last_updated' | 'created_at' | 'last_updated') => {
  return source?.kubiya_metadata?.[field] || 'Unknown';
};

const getFormattedDate = (dateString?: string) => {
  if (!dateString) return 'Unknown date';
  try {
    return new Date(dateString).toLocaleDateString();
  } catch {
    return 'Invalid date';
  }
};

const getSourceDisplayName = (source: SourceInfo): string => {
  if (!source.url) return source.name;
  try {
    const urlObj = new URL(source.url);
    if (urlObj.hostname === 'github.com') {
      const parts = urlObj.pathname.split('/');
      return `${parts[1]}/${parts[2]}`;
    }
    if (urlObj.hostname === 'gitlab.com') {
      const parts = urlObj.pathname.split('/');
      return `${parts[1]}/${parts[2]}`;
    }
    return source.name;
  } catch {
    return source.name;
  }
};

export function SourceCard({ source, onSync, onDelete, onExpand, isExpanded }: SourceCardProps) {
  const [isSyncing, setIsSyncing] = React.useState(false);
  const [isDeleting, setIsDeleting] = React.useState(false);
  const [metadata, setMetadata] = React.useState<any>(null);
  const [isLoadingMetadata, setIsLoadingMetadata] = React.useState(false);
  const [isLoadingTools, setIsLoadingTools] = React.useState(false);
  const [currentPage, setCurrentPage] = React.useState(1);
  const [selectedTool, setSelectedTool] = React.useState<Tool | null>(null);
  const [tools, setTools] = React.useState<any[]>([]);
  const itemsPerPage = 6;
  
  const sourceIcon = getSourceIcon(source.url);
  const repoInfo = getRepoInfo(source.url);
  const displayName = getSourceDisplayName(source);

  // Fetch metadata when component mounts
  React.useEffect(() => {
    const fetchMetadata = async () => {
      if (!source.uuid || isLoadingMetadata) return;
      
      setIsLoadingMetadata(true);
      try {
        // Get metadata from the global sources endpoint
        const response = await fetch('/api/v1/sources');
        if (!response.ok) {
          throw new Error('Failed to fetch sources metadata');
        }
        const data = await response.json();
        
        // Find our source's metadata from the items array
        const sourceMetadata = data.items?.find((s: any) => s.uuid === source.uuid);
        if (!sourceMetadata) {
          throw new Error('Source metadata not found');
        }

        console.log('Source Metadata:', sourceMetadata);
        setMetadata(sourceMetadata);
      } catch (error) {
        console.error('Failed to fetch metadata:', error);
      } finally {
        setIsLoadingMetadata(false);
      }
    };

    fetchMetadata();
  }, [source.uuid]);

  // Fetch tools when expanded
  React.useEffect(() => {
    const fetchTools = async () => {
      if (!source.uuid || !isExpanded) return;
      
      setIsLoadingTools(true);
      try {
        const response = await fetch(`/api/v1/sources/${source.uuid}/metadata`);
        if (!response.ok) {
          throw new Error('Failed to fetch tools');
        }
        const data = await response.json();
        setTools(data.tools || []);
      } catch (error) {
        console.error('Failed to fetch tools:', error);
      } finally {
        setIsLoadingTools(false);
      }
    };

    if (isExpanded) {
      fetchTools();
    }
  }, [source.uuid, isExpanded]);

  const firstTool = tools[0] || source.tools?.[0];
  const totalPages = Math.ceil(tools.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentTools = tools.slice(startIndex, endIndex);

  // Convert source to match the expected type for ToolDetailsModal
  const sourceForModal = {
    ...source,
    type: source.type || 'unknown',
    sourceId: source.sourceId || source.uuid,
    tools: tools,
    source_meta: source.source_meta || {
      branch: 'main',
      commit: '',
      committer: '',
      url: source.url || '',
    }
  };

  // Debug metadata
  React.useEffect(() => {
    console.log('Source:', source);
    console.log('Source Meta:', source.source_meta);
  }, [source]);

  const handleSync = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!source.uuid || isSyncing) return;
    
    setIsSyncing(true);
    try {
      await onSync(source.uuid);
    } catch (error) {
      console.error('Failed to sync:', error);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!source.uuid || isDeleting) return;
    
    if (!window.confirm('Are you sure you want to delete this source?')) return;
    
    setIsDeleting(true);
    try {
      await onDelete(source.uuid);
    } catch (error) {
      console.error('Failed to delete:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <div className="bg-[#1E293B] rounded-xl p-6 space-y-4 group hover:border hover:border-[#7C3AED]/30 transition-all duration-200">
        <div className="flex items-start justify-between">
          <div 
            className="flex items-start gap-3 flex-1 cursor-pointer" 
            onClick={onExpand}
          >
            {/* Source Icon */}
            <div className="p-2 rounded-md bg-[#2A3347] border border-[#2A3347]">
              {sourceIcon ? (
                <img src={sourceIcon} alt={repoInfo?.type || 'Source'} className="h-5 w-5" />
              ) : (
                <FolderGit className="h-5 w-5 text-[#7C3AED]" />
              )}
            </div>

            <div className="space-y-2 flex-1">
              {/* Source Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
                    {displayName}
                    <div className="text-slate-400 group-hover:text-purple-400 transition-colors">
                      {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </div>
                  </h3>
                  <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/20">
                    {repoInfo?.type || source.type || 'local'}
                  </Badge>
                  {source.errors_count > 0 && (
                    <Badge variant="destructive" className="bg-red-500/10 text-red-400 border-red-500/20">
                      {source.errors_count} {source.errors_count === 1 ? 'error' : 'errors'}
                    </Badge>
                  )}
                </div>
              </div>

              {/* Repository Info */}
              {repoInfo && source.source_meta && (
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2 text-xs">
                    <a
                      href={repoInfo.repoUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[#94A3B8] hover:text-[#7C3AED] flex items-center gap-1 transition-colors"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <FolderGit className="h-3 w-3" />
                      {repoInfo.owner}/{repoInfo.repo}
                    </a>
                    {source.source_meta.branch && (
                      <>
                        <span className="text-[#4B5563]">/</span>
                        <a
                          href={repoInfo.branchUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[#94A3B8] hover:text-[#7C3AED] flex items-center gap-1 transition-colors"
                          onClick={(e) => e.stopPropagation()}
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
                        href={`${repoInfo.commitUrl}${source.source_meta.commit}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#94A3B8] hover:text-[#7C3AED] flex items-center gap-1 transition-colors group"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Hash className="h-3 w-3" />
                        <span className="font-mono">{source.source_meta.commit.slice(0, 7)}</span>
                        {source.source_meta.committer && (
                          <>
                            <span className="text-[#4B5563]">by</span>
                            <span>{source.source_meta.committer}</span>
                          </>
                        )}
                        <ExternalLink className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </a>
                    </div>
                  )}
                </div>
              )}

              {/* Source Stats */}
              <div className="grid grid-cols-2 gap-4 mt-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
                    <Package className="h-3.5 w-3.5" />
                    <span>{source.connected_tools_count || 0} tools</span>
                  </div>
                  {source.connected_workflows_count > 0 && (
                    <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
                      <Terminal className="h-3.5 w-3.5" />
                      <span>{source.connected_workflows_count} workflows</span>
                    </div>
                  )}
                  {source.connected_agents_count > 0 && (
                    <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
                      <Bot className="h-3.5 w-3.5" />
                      <span>{source.connected_agents_count} agents</span>
                    </div>
                  )}
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
                    <Globe className="h-3.5 w-3.5" />
                    <span>Runner: {source.runner || 'Inherited'}</span>
                  </div>
                  {source.managed_by && (
                    <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
                      <User className="h-3.5 w-3.5" />
                      <span>Managed by: {source.managed_by}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
                    <RotateCw className="h-3.5 w-3.5" />
                    <span>Last synced: {getFormattedDate(source.kubiya_metadata?.last_updated)}</span>
                  </div>
                </div>
              </div>

              {/* First Tool Preview - Only show when not expanded */}
              {!isExpanded && firstTool && (
                <div className="mt-3 p-2 rounded-lg bg-[#2A3347]/50 border border-[#2A3347]">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 rounded bg-[#2A3347]">
                        {firstTool.icon_url ? (
                          <img 
                            src={firstTool.icon_url} 
                            alt={firstTool.name} 
                            className="h-4 w-4" 
                          />
                        ) : (
                          <Package className="h-4 w-4 text-[#7C3AED]" />
                        )}
                      </div>
                      <div>
                        <div className="text-xs font-medium text-white">
                          {firstTool.name}
                        </div>
                        <div className="text-[11px] text-[#94A3B8]">
                          {firstTool.description}
                        </div>
                      </div>
                    </div>
                    <div className="text-xs text-[#94A3B8] group-hover:text-purple-400 transition-colors">
                      Click to view all tools
                    </div>
                  </div>
                </div>
              )}

              {/* Loading State */}
              {isLoadingMetadata && (
                <div className="flex items-center gap-2 text-xs text-[#94A3B8] mt-2">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Loading metadata...</span>
                </div>
              )}

              {/* Dynamic Config Indicator */}
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
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSync}
              disabled={isSyncing || !source.uuid}
              className={cn(
                "text-slate-400 hover:text-purple-400",
                "hover:bg-purple-500/10",
                isSyncing && "opacity-50 cursor-not-allowed"
              )}
            >
              <RotateCw className={cn(
                "h-4 w-4",
                isSyncing && "animate-spin"
              )} />
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDelete}
              disabled={isDeleting || !source.uuid}
              className={cn(
                "text-slate-400 hover:text-red-400",
                "hover:bg-red-500/10",
                isDeleting && "opacity-50 cursor-not-allowed"
              )}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {isExpanded && (
          <>
            <Separator className="bg-[#2D3B4E]" />
            
            {/* Tools Grid */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-white">Available Tools</h4>
                {tools.length > 0 && (
                  <div className="text-xs text-[#94A3B8]">
                    Showing {startIndex + 1}-{Math.min(endIndex, tools.length)} of {tools.length} tools
                  </div>
                )}
              </div>

              {isLoadingTools ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-[#7C3AED]" />
                  <span className="ml-2 text-sm text-[#94A3B8]">Loading tools...</span>
                </div>
              ) : tools.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <Package className="h-8 w-8 text-[#94A3B8]" />
                  <p className="mt-2 text-sm text-[#94A3B8]">No tools available</p>
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {currentTools.map((tool: any, index: number) => (
                      <div 
                        key={`${tool.name}-${index}`}
                        className="p-4 rounded-lg bg-[#2A3347]/50 border border-[#2A3347] hover:border-[#7C3AED]/30 transition-all duration-200 cursor-pointer"
                        onClick={() => setSelectedTool(tool)}
                      >
                        <div className="flex items-start gap-3">
                          <div className="p-2 rounded bg-[#2A3347]">
                            {tool.icon_url ? (
                              <img src={tool.icon_url} alt={tool.name} className="h-5 w-5" />
                            ) : (
                              <Package className="h-5 w-5 text-[#7C3AED]" />
                            )}
                          </div>
                          <div>
                            <h5 className="text-sm font-medium text-white">{tool.name}</h5>
                            <p className="text-xs text-[#94A3B8] mt-1">{tool.description}</p>
                            {tool.type && (
                              <Badge 
                                variant="outline" 
                                className="mt-2 bg-purple-500/10 text-purple-400 border-purple-500/20"
                              >
                                {tool.type}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {totalPages > 1 && (
                    <Pagination className="mt-4">
                      <PaginationContent>
                        <PaginationItem>
                          <PaginationPrevious 
                            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                            disabled={currentPage === 1}
                          />
                        </PaginationItem>
                        
                        {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                          <PaginationItem key={page}>
                            <PaginationLink
                              onClick={() => setCurrentPage(page)}
                              isActive={currentPage === page}
                            >
                              {page}
                            </PaginationLink>
                          </PaginationItem>
                        ))}
                        
                        <PaginationItem>
                          <PaginationNext 
                            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                            disabled={currentPage === totalPages}
                          />
                        </PaginationItem>
                      </PaginationContent>
                    </Pagination>
                  )}
                </>
              )}
            </div>
          </>
        )}
      </div>

      {selectedTool && (
        <EntityProvider>
          <ToolDetailsModal
            tool={selectedTool}
            source={sourceForModal}
            isOpen={!!selectedTool}
            onCloseAction={() => setSelectedTool(null)}
          />
        </EntityProvider>
      )}
    </>
  );
} 