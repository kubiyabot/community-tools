"use client";

import { useMemo, useEffect, useState, useCallback } from 'react';
import { FolderGit, Link as LinkIcon, GitBranch, ExternalLink, Loader2, Bot, Package, Database, Code, Terminal, Settings, Hash, Box, Dock, AlertCircle, Plus, Search, Info, Trash2, FileCode, FileJson, FileText, File } from 'lucide-react';
import type { Tool as SourceTool } from '@/app/types/tool';
import type { TeammateDetails } from '@/app/types/teammate';
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/app/components/ui/dialog";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "../../ui/form";
import { Input } from "../../ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../ui/select";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { Textarea } from "@/app/components/ui/textarea";
import { InstallToolForm } from './InstallToolForm';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/app/components/ui/alert-dialog";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

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

interface Runner {
  name: string;
  description: string;
  runner_type: string;
}

interface SourceData {
  name: string;
  url: string;
  runner: string;
  type: string;
  dynamic_config?: any;
  teammate_id: string;
  status: string;
  source_meta: {
    branch: string;
    url: string;
  };
  workspace_id?: string;
  managed_by?: string;
}

type ExtendedSourceInfo = Omit<SourceInfo, 'tools'> & {
  teammate_id: string;
  tools: SourceTool[];
  sourceId: string;
  type: string;
  runner: string;
  connected_agents_count: number;
  connected_tools_count: number;
  connected_workflows_count: number;
  kubiya_metadata: {
    created_at: string;
    last_updated: string;
    user_created: string;
    user_last_updated: string;
  };
  errors_count: number;
  errors?: Array<{
    file: string;
    error: string;
    details?: string;
    code?: string;
    lineNumber?: number;
  }>;
  source_meta: {
    id: string;
    url: string;
    branch: string;
    commit: string;
    committer: string;
  };
};

interface SyncPayload {
  name: string;
  url: string;
  dynamic_config?: any;
  runner?: string;
}

const sourceFormSchema = z.object({
  name: z.string().min(1, "Name is required"),
  url: z.string().url("Must be a valid URL"),
  runner: z.string().optional(),
  dynamic_config: z.string().optional().transform(val => {
    if (!val) return {};
    try {
      return JSON.parse(val);
    } catch {
      return {};
    }
  }),
});

type SourceFormValues = z.infer<typeof sourceFormSchema>;

// Add helper functions before components
function getFileIcon(filename: string) {
  const ext = filename.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'py':
    case 'js':
    case 'ts':
    case 'jsx':
    case 'tsx':
      return <FileCode className="h-4 w-4 text-blue-400" />;
    case 'json':
      return <FileJson className="h-4 w-4 text-yellow-400" />;
    case 'md':
    case 'txt':
      return <FileText className="h-4 w-4 text-gray-400" />;
    default:
      return <File className="h-4 w-4 text-gray-400" />;
  }
}

const LoadingSpinner = () => (
  <div className="flex flex-col items-center justify-center h-[400px] p-6">
    <div className="p-3 rounded-full bg-[#1E293B] border border-[#1E293B]">
      <Loader2 className="h-6 w-6 text-[#7C3AED] animate-spin" />
    </div>
    <p className="text-sm font-medium text-[#94A3B8] mt-4">Loading tool sources attached to this teammate...</p>
  </div>
);

const EmptyState = () => (
  <div className="flex flex-col items-center justify-center h-[400px] p-6">
    <div className="p-3 rounded-full bg-[#1E293B] border border-[#1E293B]">
      <FolderGit className="h-6 w-6 text-[#7C3AED]" />
    </div>
    <p className="text-sm font-medium text-[#94A3B8] mt-4">No tools available for this teammate, please add a tool source to get started.</p>
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

const ToolCard = ({ tool, source }: { tool: SourceTool; source: ExtendedSourceInfo }) => {
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
    with_files: tool.with_files?.map(file => {
      if (typeof file === 'string') {
        return { source: file, target: file };
      }
      return {
        source: file.source || '',
        target: file.target || file.source || '',
        content: file.content
      };
    }),
    mounts: tool.mounts?.map(mount => {
      if (typeof mount === 'string') {
        return { source: mount, target: mount };
      }
      return mount;
    }),
    mermaid: tool.mermaid,
    source: tool.source ? {
      name: typeof tool.source === 'string' ? tool.source : tool.source.name,
      url: typeof tool.source === 'string' ? '' : tool.source.url,
      metadata: typeof tool.source === 'string' ? undefined : {
        git_branch: tool.source.metadata?.git_branch,
        git_commit: tool.source.metadata?.git_commit,
        git_path: '',
        docker_image: '',
        last_updated: tool.source.metadata?.last_updated,
        created_at: tool.source.metadata?.created_at
      }
    } : undefined,
    uuid: tool.name,
    alias: tool.name
  } as Tool;

  return (
    <>
      <div 
        className="group relative bg-[#1E293B]/50 hover:bg-[#1E293B] rounded-lg border border-[#1E293B] hover:border-[#7C3AED]/50 transition-all duration-200 cursor-pointer overflow-hidden"
        onClick={() => setShowDetails(true)}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-[#1E293B]/0 to-[#1E293B] opacity-0 group-hover:opacity-100 transition-opacity" />
        <div className="p-4 relative">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-md bg-[#2A3347] border border-[#2A3347] group-hover:border-[#7C3AED]/20 transition-colors">
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
                      {teammateToolData.type === 'docker' ? (
                        <div className="flex items-center gap-1">
                          <img 
                            src="https://cdn4.iconfinder.com/data/icons/logos-and-brands/512/97_Docker_logo_logos-512.png"
                            alt="Docker"
                            className="h-3 w-3 mr-1"
                          />
                          docker
                        </div>
                      ) : teammateToolData.type}
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

interface ErrorPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  error: {
    file: string;
    error: string;
    details?: string;
    code?: string;
    lineNumber?: number;
  };
}

function ErrorPreviewModal({ isOpen, onClose, error }: ErrorPreviewModalProps) {
  const fileExtension = error.file.split('.').pop() || '';
  
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[900px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {getFileIcon(error.file)}
            <span>{error.file}</span>
          </DialogTitle>
          <DialogDescription className="text-red-400">
            {error.error}
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {error.code && (
            <div className="relative rounded-md overflow-hidden">
              <div className="absolute top-2 right-2 z-10">
                <Badge variant="outline" className="bg-red-500/10 text-red-400 border-red-500/20">
                  Line {error.lineNumber}
                </Badge>
              </div>
              <SyntaxHighlighter
                language={fileExtension}
                style={vscDarkPlus}
                showLineNumbers
                wrapLines
                lineProps={(lineNumber: number) => ({
                  style: {
                    backgroundColor: lineNumber === error.lineNumber ? 'rgba(239, 68, 68, 0.1)' : undefined,
                    display: 'block',
                    width: '100%',
                  },
                })}
              >
                {error.code}
              </SyntaxHighlighter>
            </div>
          )}
          
          {error.details && (
            <div className="bg-[#1E293B] rounded-md p-4 border border-[#2D3B4E]">
              <h4 className="text-sm font-medium text-white mb-2">Additional Details</h4>
              <p className="text-sm text-[#94A3B8] whitespace-pre-wrap">{error.details}</p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

const SourceGroup = ({ source, onSourcesChange, allSources }: { 
  source: ExtendedSourceInfo; 
  onSourcesChange?: () => void;
  allSources: ExtendedSourceInfo[];
}) => {
  const [showSyncDialog, setShowSyncDialog] = useState(false);
  const [showRemoveDialog, setShowRemoveDialog] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isRemoving, setIsRemoving] = useState(false);
  const gitHubInfo = useMemo(() => getGitHubInfo(source.url), [source.url]);
  const firstToolWithIcon = useMemo(() => source.tools.find(tool => tool.icon_url), [source.tools]);
  
  // Add state for error preview modal
  const [selectedError, setSelectedError] = useState<{
    file: string;
    error: string;
    details?: string;
    code?: string;
    lineNumber?: number;
  } | null>(null);

  const handleSync = async () => {
    try {
      setIsSyncing(true);
      
      // Construct the payload with dynamic_config if it exists
      const payload = {
        name: source.name,
        url: source.url,
        dynamic_config: source.dynamic_config || null
      };

      const response = await fetch(`/api/sources/${source.uuid}/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to sync source');
      }

      // Get the updated data
      const data = await response.json();

      // Call onSourcesChange to trigger a re-render with the latest data
      if (onSourcesChange) {
        await onSourcesChange();
      }
    } catch (error) {
      console.error('Error syncing source:', error);
      // TODO: Show error toast or notification
    } finally {
      setIsSyncing(false);
      setShowSyncDialog(false);
    }
  };

  const handleRemove = async () => {
    try {
      setIsRemoving(true);
      
      // Get current teammate's sources
      const currentSources = allSources.map((s: ExtendedSourceInfo) => s.uuid);
      // Remove the current source from the list
      const updatedSources = currentSources.filter((id: string) => id !== source.uuid);
      
      const response = await fetch(`/api/teammates/${source.teammate_id}/sources`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          sources: updatedSources
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to remove source');
      }

      if (onSourcesChange) {
        await onSourcesChange();
      }
    } catch (error) {
      console.error('Error removing source:', error);
    } finally {
      setIsRemoving(false);
      setShowRemoveDialog(false);
    }
  };

  return (
    <>
      <div className="bg-[#1E293B] rounded-xl p-6 space-y-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            {/* Main Icon - Use first tool's icon or fallback */}
            <div className="p-2 rounded-md bg-[#2A3347] border border-[#2A3347]">
              {firstToolWithIcon?.icon_url ? (
                <img src={firstToolWithIcon.icon_url} alt={source.name} className="h-5 w-5" />
              ) : (
                <Code className="h-5 w-5 text-[#7C3AED]" />
              )}
            </div>
            <div className="space-y-2">
              <div>
                <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
                  {source.name}
                  {source.errors_count > 0 && (
                    <HoverCard>
                      <HoverCardTrigger asChild>
                        <Badge 
                          variant="destructive" 
                          className="bg-red-500/10 text-red-400 border-red-500/20 cursor-help hover:bg-red-500/20 transition-colors"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (source.errors && source.errors[0]) {
                              setSelectedError(source.errors[0]);
                            }
                          }}
                        >
                          <AlertCircle className="h-3.5 w-3.5 mr-1" />
                          {source.errors_count} {source.errors_count === 1 ? 'error' : 'errors'}
                        </Badge>
                      </HoverCardTrigger>
                      <HoverCardContent className="w-96 p-0">
                        <div className="p-3 space-y-3">
                          <div className="flex items-start justify-between">
                            <h5 className="text-sm font-medium text-white flex items-center gap-2">
                              <AlertCircle className="h-4 w-4 text-red-400" />
                              Source Errors
                            </h5>
                            <Badge variant="outline" className="bg-[#2A3347] border-[#2D3B4E] text-[#94A3B8]">
                              Click error to view details
                            </Badge>
                          </div>
                          <div className="space-y-2 max-h-60 overflow-y-auto">
                            {source.errors?.map((error, index) => (
                              <button
                                key={index}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setSelectedError(error);
                                }}
                                className="w-full text-left bg-red-500/10 rounded-md p-2 border border-red-500/20 space-y-1.5 hover:bg-red-500/20 transition-colors"
                              >
                                <div className="flex items-center gap-2">
                                  {getFileIcon(error.file)}
                                  <span className="font-mono text-red-400 text-xs">{error.file}</span>
                                </div>
                                <div className="text-red-300 text-xs pl-6">
                                  {error.error}
                                </div>
                                {error.details && (
                                  <div className="text-red-300/70 text-[10px] pl-6 pt-1 border-t border-red-500/20">
                                    {error.details}
                                  </div>
                                )}
                              </button>
                            ))}
                          </div>
                        </div>
                      </HoverCardContent>
                    </HoverCard>
                  )}
                </h3>
                
                {/* Source Control Links */}
                {gitHubInfo && (
                  <div className="flex flex-col gap-1 mt-1">
                    <div className="flex items-center gap-2 text-xs">
                      <div className="flex items-center gap-1.5">
                        <img 
                          src="https://cdn-icons-png.flaticon.com/512/25/25231.png" 
                          alt="GitHub" 
                          className="h-3.5 w-3.5 opacity-60"
                        />
                        <a
                          href={gitHubInfo.repoUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[#94A3B8] hover:text-[#7C3AED] flex items-center gap-1 transition-colors"
                        >
                          {gitHubInfo.owner}/{gitHubInfo.repo}
                        </a>
                      </div>
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
          <div className="flex items-center gap-2">
            {isSyncing ? (
              <div className="flex items-center gap-2 text-[#94A3B8]">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-xs">Syncing...</span>
              </div>
            ) : (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowSyncDialog(true)}
                  className="text-[#94A3B8] hover:text-[#7C3AED] border-[#2D3B4E] hover:border-[#7C3AED]/50"
                >
                  <GitBranch className="h-3.5 w-3.5 mr-1.5" />
                  Sync
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowRemoveDialog(true)}
                  className="text-red-400 hover:text-red-300 border-[#2D3B4E] hover:border-red-500/50"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </>
            )}
          </div>
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

      {/* Sync Confirmation Dialog */}
      <AlertDialog open={showSyncDialog} onOpenChange={setShowSyncDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Sync Source</AlertDialogTitle>
            <AlertDialogDescription>
              This will pull the latest changes from the repository and update the tools. Are you sure you want to continue?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isSyncing}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleSync}
              disabled={isSyncing}
              className="bg-[#7C3AED] hover:bg-[#6D28D9]"
            >
              {isSyncing && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              Sync Source
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Remove Confirmation Dialog */}
      <AlertDialog open={showRemoveDialog} onOpenChange={setShowRemoveDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove Source</AlertDialogTitle>
            <AlertDialogDescription className="space-y-3">
              <p>
                Are you sure you want to remove <span className="font-medium text-white">{source.name}</span> from this teammate?
              </p>
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-md p-3">
                <div className="flex items-start gap-2">
                  <AlertCircle className="h-5 w-5 text-amber-400 mt-0.5" />
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-amber-400">This will:</p>
                    <ul className="text-sm text-amber-300/90 list-disc list-inside space-y-1">
                      <li>Remove {source.tools.length} tools from this teammate</li>
                      {source.connected_workflows_count > 0 && (
                        <li>Affect {source.connected_workflows_count} connected workflows</li>
                      )}
                      <li>This action cannot be undone</li>
                    </ul>
                  </div>
                </div>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isRemoving}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleRemove}
              disabled={isRemoving}
              className="bg-red-500 hover:bg-red-600"
            >
              {isRemoving ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Removing...
                </>
              ) : (
                <>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Remove Source
                </>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Add ErrorPreviewModal */}
      {selectedError && (
        <ErrorPreviewModal
          isOpen={!!selectedError}
          onClose={() => setSelectedError(null)}
          error={selectedError}
        />
      )}
    </>
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

interface FormFieldProps {
  field: {
    value: any;
    onChange: (value: any) => void;
    name: string;
  };
}

interface TeammateModalProps {
  isOpen: boolean;
  onClose: () => void;
  teammate: TeammateDetails;
  onInstall: (values: SourceFormValues) => Promise<void>;
}

function InstallToolModal({ 
  isOpen, 
  onClose,
  teammate,
  onInstall
}: TeammateModalProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [runners, setRunners] = useState<Runner[]>([]);
  const [previewData, setPreviewData] = useState<any>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);

  const form = useForm<SourceFormValues>({
    resolver: zodResolver(sourceFormSchema),
    defaultValues: {
      name: "",
      url: "",
      runner: "automatic",
      dynamic_config: "",
    },
  });

  useEffect(() => {
    // Fetch runners
    fetch('/api/v3/runners')
      .then(res => res.json())
      .then(data => setRunners(data))
      .catch(err => console.error('Failed to fetch runners:', err));
  }, []);

  const handleSubmit = async (values: SourceFormValues) => {
    try {
      setIsLoading(true);
      await onInstall(values);
      onClose();
    } catch (error) {
      console.error('Failed to install tool:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePreview = async (url: string, runner: string) => {
    try {
      setIsLoading(true);
      setPreviewData(null);
      setPreviewError(null);

      const response = await fetch(`/api/v1/sources/load?url=${encodeURIComponent(url)}&runner=${encodeURIComponent(runner)}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to load source');
      }

      setPreviewData(data);
    } catch (error) {
      setPreviewError(error instanceof Error ? error.message : 'Failed to load source');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const subscription = form.watch((value, { name }) => {
      if ((name === 'url' || name === 'runner') && value.url && value.runner) {
        handlePreview(value.url, value.runner);
      }
    });
    return () => subscription.unsubscribe();
  }, [form.watch]);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Install Tool</DialogTitle>
          <DialogDescription>
            Add a new tool source to your teammate. The source will be scanned for available tools.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="name"
              render={({ field }: FormFieldProps) => (
                <FormItem>
                  <FormLabel>Source Name</FormLabel>
                  <FormControl>
                    <Input placeholder="my-awesome-tools" {...field} />
                  </FormControl>
                  <FormDescription>
                    A unique name for this tool source
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="url"
              render={({ field }: FormFieldProps) => (
                <FormItem>
                  <FormLabel>Source URL</FormLabel>
                  <FormControl>
                    <Input placeholder="https://github.com/org/repo" {...field} />
                  </FormControl>
                  <FormDescription>
                    URL to the Git repository containing the tools
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="runner"
              render={({ field }: FormFieldProps) => (
                <FormItem>
                  <FormLabel>Runner</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a runner" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="automatic">Automatic</SelectItem>
                      {runners.map((runner) => (
                        <SelectItem key={runner.name} value={runner.name}>
                          {runner.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger className="flex items-center gap-1 text-xs text-[#94A3B8] hover:text-[#7C3AED]">
                          <Info className="h-3.5 w-3.5" />
                          What is a runner?
                        </TooltipTrigger>
                        <TooltipContent className="max-w-sm">
                          <p>A runner is an executor which will clone the repository to extract tools from the code using the Kubiya operator.</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="dynamic_config"
              render={({ field }: FormFieldProps) => (
                <FormItem>
                  <FormLabel>Dynamic Configuration (Optional)</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="{}"
                      className="font-mono"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    JSON configuration for the source
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {isLoading && (
              <div className="flex items-center justify-center p-4">
                <Loader2 className="h-6 w-6 animate-spin text-[#7C3AED]" />
                <span className="ml-2 text-sm text-[#94A3B8]">
                  {previewData ? 'Loading preview...' : 'Discovering tools...'}
                </span>
              </div>
            )}

            {previewError && (
              <div className="bg-red-500/10 text-red-400 rounded-lg p-4 text-sm">
                {previewError}
              </div>
            )}

            {previewData && (
              <div className="space-y-4">
                <h4 className="text-sm font-medium text-white">Preview</h4>
                
                {previewData.errors && previewData.errors.length > 0 && (
                  <div className="space-y-2">
                    <h5 className="text-sm font-medium text-red-400">Errors</h5>
                    {previewData.errors.map((error: any, index: number) => (
                      <div key={index} className="bg-red-500/10 text-red-400 rounded-lg p-3 text-xs">
                        <div className="font-medium">{error.file}</div>
                        <div>{error.error}</div>
                        {error.details && <div className="mt-1 text-red-300">{error.details}</div>}
                      </div>
                    ))}
                  </div>
                )}

                {previewData.tools && (
                  <div className="space-y-2">
                    <h5 className="text-sm font-medium text-white">Tools</h5>
                    <div className="grid grid-cols-1 gap-2">
                      {previewData.tools.map((tool: any, index: number) => (
                        <div key={index} className="bg-[#1E293B] rounded-lg p-3">
                          <div className="flex items-start gap-3">
                            <div className="p-2 rounded-md bg-[#2A3347] border border-[#2A3347]">
                              {tool.icon_url ? (
                                <img src={tool.icon_url} alt={tool.name} className="h-5 w-5" />
                              ) : (
                                <Code className="h-5 w-5 text-[#7C3AED]" />
                              )}
                            </div>
                            <div>
                              <h4 className="text-sm font-medium text-white">
                                {tool.name}
                              </h4>
                              <p className="text-xs text-[#94A3B8] mt-1">
                                {tool.description}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={isLoading}
              >
                Cancel
              </Button>
              <Button 
                type="submit"
                disabled={isLoading || !previewData}
              >
                Install Source
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

interface SourcesTabProps {
  teammate: TeammateDetails | null;
  sources?: ExtendedSourceInfo[];
  isLoading?: boolean;
  onSourcesChange?: () => void;
}

export function SourcesTab({ 
  teammate, 
  sources = [], 
  isLoading = false,
  onSourcesChange
}: SourcesTabProps) {
  const [showInstallModal, setShowInstallModal] = useState(false);
  const [syncingSourceIds, setSyncingSourceIds] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');

  const filteredSources = useMemo(() => {
    if (!searchQuery.trim()) return sources;
    
    const query = searchQuery.toLowerCase();
    return sources.map(source => ({
      ...source,
      tools: source.tools.filter(tool => 
        tool.name.toLowerCase().includes(query) ||
        tool.description?.toLowerCase().includes(query) ||
        tool.type?.toLowerCase().includes(query)
      )
    })).filter(source => source.tools.length > 0);
  }, [sources, searchQuery]);

  const handleSync = async (sourceId: string) => {
    try {
      setSyncingSourceIds(prev => new Set([...prev, sourceId]));
      
      // Find the source to get its dynamic_config
      const source = sources.find(s => s.uuid === sourceId);
      if (!source) {
        throw new Error('Source not found');
      }

      const response = await fetch(`/api/sources/${source.uuid}/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          dynamic_config: source.dynamic_config || null 
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to sync source');
      }

      if (onSourcesChange) {
        await onSourcesChange();
      }
    } catch (error) {
      console.error('Error syncing source:', error);
    } finally {
      setSyncingSourceIds(prev => {
        const next = new Set(prev);
        next.delete(sourceId);
        return next;
      });
    }
  };

  const handleInstall = async (
    values: SourceFormValues,
    updateProgress: (stepId: string, status: 'pending' | 'loading' | 'success' | 'error', error?: string) => void
  ) => {
    try {
      updateProgress('validate', 'loading');

      // Use the correct endpoint for installing sources
      const response = await fetch(`/api/v1/sources`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...values,
          teammate_id: teammate?.id
        })
      });

      let errorMessage = 'Failed to install tool';

      if (!response.ok) {
        if (response.status === 405) {
          errorMessage = 'Installation method not allowed. Please check your permissions and try again.';
        } else {
          try {
            const errorData = await response.json();
            errorMessage = errorData.message || errorMessage;
          } catch (e) {
            console.error('Failed to parse error response:', e);
            // Use status text if available
            errorMessage = response.statusText ? `Installation failed: ${response.statusText}` : errorMessage;
          }
        }
        
        throw new Error(errorMessage);
      }

      // Try to parse the response as JSON if it exists
      const contentType = response.headers.get('content-type');
      let data = null;
      
      if (contentType && contentType.includes('application/json')) {
        try {
          data = await response.json();
        } catch (e) {
          console.error('Failed to parse response:', e);
          // If JSON parsing fails but response was ok, we can still continue
          if (response.ok) {
            console.log('Response was successful but not JSON. Continuing...');
          } else {
            throw new Error('Failed to parse installation response');
          }
        }
      }

      updateProgress('validate', 'success');
      
      if (onSourcesChange) {
        await onSourcesChange();
      }

      return data;
    } catch (error) {
      console.error('Installation error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Installation failed';
      updateProgress('validate', 'error', errorMessage);
      throw error;
    }
  };

  // Early return if loading
  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!teammate) {
    return <ErrorState message="No teammate data available" />;
  }

  return (
    <div className="p-6 space-y-6">
      {/* Tools Information Header */}
      <div className="bg-gradient-to-br from-[#1E293B] to-[#0F172A] rounded-xl overflow-hidden border border-[#2D3B4E]">
        <div className="relative p-5">
          {/* Background Pattern */}
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAxOGMzLjMxIDAgNiAyLjY5IDYgNnMtMi42OSA2LTYgNi02LTIuNjktNi02IDIuNjktNiA2LTZ6IiBzdHJva2U9IiMyRDNCNEUiIG9wYWNpdHk9Ii4yIi8+PC9nPjwvc3ZnPg==')] opacity-5" />
          
          <div className="relative flex items-start gap-6">
            {/* Icon Stack */}
            <div className="flex flex-col items-center space-y-2">
              <div className="relative w-12 h-12">
                <div className="absolute inset-0 bg-gradient-to-br from-[#7C3AED] to-[#4F46E5] opacity-20 rounded-xl blur-lg" />
                <div className="relative w-full h-full rounded-xl bg-[#2A3347] border border-[#2D3B4E] flex items-center justify-center">
                  <img 
                    src="https://cdn4.iconfinder.com/data/icons/logos-and-brands/512/97_Docker_logo_logos-512.png"
                    alt="Docker" 
                    className="h-6 w-6"
                  />
                </div>
              </div>
              <div className="h-12 w-px bg-gradient-to-b from-[#2D3B4E] to-transparent" />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <h2 className="text-lg font-semibold text-white tracking-tight">Extend Your Teammate with Tools</h2>
                  <p className="text-sm text-[#94A3B8] leading-relaxed max-w-3xl">
                    Tools leverage LLM function calling with container orchestration to extend teammates to execute nearly any operation.
                  </p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-3 ml-4">
                  <Button
                    onClick={() => setShowInstallModal(true)}
                    size="sm"
                    className="bg-[#7C3AED] hover:bg-[#6D28D9] text-white"
                  >
                    <Plus className="h-4 w-4 mr-1.5" />
                    Install Tool
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    asChild
                    className="border-[#2D3B4E] text-[#94A3B8] hover:text-[#7C3AED] hover:border-[#7C3AED]/50"
                  >
                    <a 
                      href="https://docs.kubiya.ai/docs/kubiya-resources/tools" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex items-center gap-1.5"
                    >
                      <ExternalLink className="h-4 w-4" />
                      Learn More
                    </a>
                  </Button>
                </div>
              </div>

              {/* Feature Pills */}
              <div className="flex items-center gap-4 mt-3">
                <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-[#2A3347] border border-[#2D3B4E]">
                  <Bot className="h-3.5 w-3.5 text-[#7C3AED]" />
                  <span className="text-xs text-[#94A3B8]">LLM Integration</span>
                </div>
                <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-[#2A3347] border border-[#2D3B4E]">
                  <Package className="h-3.5 w-3.5 text-[#7C3AED]" />
                  <span className="text-xs text-[#94A3B8]">Container Orchestration</span>
                </div>
                <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-[#2A3347] border border-[#2D3B4E]">
                  <GitBranch className="h-3.5 w-3.5 text-[#7C3AED]" />
                  <span className="text-xs text-[#94A3B8]">Version Control</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Search and Tools Section */}
      <div className="space-y-4">
        {/* Search Bar */}
        <div className="flex items-center justify-between">
          <div className="relative flex-1 max-w-md">
            <Input
              type="text"
              placeholder="Search tools by name, description, or type..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#1E293B] border-[#2D3B4E] focus:border-[#7C3AED] text-white placeholder-[#94A3B8] pl-10"
            />
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-[#94A3B8]" />
          </div>
          <div className="text-sm text-[#94A3B8]">
            {filteredSources.reduce((acc, source) => acc + source.tools.length, 0)} tools available
          </div>
        </div>

        {/* Tools Grid */}
        {!filteredSources.length ? (
          searchQuery ? (
            <div className="flex flex-col items-center justify-center h-[300px] p-6">
              <div className="p-3 rounded-full bg-[#1E293B] border border-[#1E293B]">
                <Search className="h-6 w-6 text-[#7C3AED]" />
              </div>
              <p className="text-sm font-medium text-[#94A3B8] mt-4">No tools found matching "{searchQuery}"</p>
            </div>
          ) : (
            <EmptyState />
          )
        ) : (
          <div className="space-y-8">
            {filteredSources.map((source: ExtendedSourceInfo) => (
              <SourceGroup 
                key={source.uuid} 
                source={source}
                onSourcesChange={onSourcesChange}
                allSources={filteredSources}
              />
            ))}
          </div>
        )}
      </div>

      <InstallToolForm
        isOpen={showInstallModal}
        onClose={() => setShowInstallModal(false)}
        onInstall={handleInstall}
        teammate={teammate!}
      />
    </div>
  );
} 