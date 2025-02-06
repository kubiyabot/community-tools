"use client";

import { useMemo, useEffect, useState, useCallback } from 'react';
import { FolderGit, Link as LinkIcon, GitBranch, ExternalLink, Loader2, Bot, Package, Database, Code, Terminal, Settings, Hash, Box, Dock, AlertCircle, Plus, Search, Info, Trash2, FileCode, FileJson, FileText, File, User, Calendar } from 'lucide-react';
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
import { InstallToolForm } from './install-tool/InstallToolForm';
import { InstallToolProvider } from './install-tool/context';
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
import { useToast } from "@/app/components/ui/use-toast";
import type { FormValues } from './install-tool/schema';
import type { UseInstallToolReturn } from './install-tool/types';
import { useInstallTool } from './install-tool/hooks/useInstallTool';

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

interface ExtendedSourceInfo extends Omit<SourceInfo, 'tools'> {
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
    type?: string;
  }>;
  source_meta: {
    id: string;
    url: string;
    branch: string;
    commit: string;
    committer: string;
  };
}

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

// Add error type info helper
function getErrorTypeInfo(type: string = 'Error') {
  switch (type.toLowerCase()) {
    case 'importerror':
      return {
        color: 'text-amber-400',
        bgColor: 'bg-amber-500/10',
        borderColor: 'border-amber-500/20',
        icon: <Package className="h-4 w-4" />,
        label: 'Import Error'
      };
    case 'syntaxerror':
      return {
        color: 'text-red-400',
        bgColor: 'bg-red-500/10',
        borderColor: 'border-red-500/20',
        icon: <Code className="h-4 w-4" />,
        label: 'Syntax Error'
      };
    case 'typeerror':
      return {
        color: 'text-purple-400',
        bgColor: 'bg-purple-500/10',
        borderColor: 'border-purple-500/20',
        icon: <AlertCircle className="h-4 w-4" />,
        label: 'Type Error'
      };
    case 'loading':
      return {
        color: 'text-blue-400',
        bgColor: 'bg-blue-500/10',
        borderColor: 'border-blue-500/20',
        icon: <Loader2 className="h-4 w-4 animate-spin" />,
        label: 'Loading'
      };
    case 'attributeerror':
      return {
        color: 'text-orange-400',
        bgColor: 'bg-orange-500/10',
        borderColor: 'border-orange-500/20',
        icon: <Settings className="h-4 w-4" />,
        label: 'Attribute Error'
      };
    case 'valueerror':
      return {
        color: 'text-pink-400',
        bgColor: 'bg-pink-500/10',
        borderColor: 'border-pink-500/20',
        icon: <AlertCircle className="h-4 w-4" />,
        label: 'Value Error'
      };
    case 'nameerror':
      return {
        color: 'text-yellow-400',
        bgColor: 'bg-yellow-500/10',
        borderColor: 'border-yellow-500/20',
        icon: <Hash className="h-4 w-4" />,
        label: 'Name Error'
      };
    default:
      return {
        color: 'text-red-400',
        bgColor: 'bg-red-500/10',
        borderColor: 'border-red-500/20',
        icon: <AlertCircle className="h-4 w-4" />,
        label: type || 'Error'
      };
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
    type?: string;
  };
  source: ExtendedSourceInfo;
  allErrors: Array<{
    file: string;
    error: string;
    details?: string;
    code?: string;
    lineNumber?: number;
    type?: string;
  }>;
}

function ErrorPreviewModal({ isOpen, onClose, error: focusedError, source, allErrors }: ErrorPreviewModalProps) {
  // Group errors by file
  const errorsByFile = useMemo(() => {
    return allErrors.reduce((acc, error) => {
      if (!acc[error.file]) {
        acc[error.file] = [];
      }
      acc[error.file].push(error);
      return acc;
    }, {} as Record<string, typeof allErrors>);
  }, [allErrors]);

  // Get current file's errors
  const currentFileErrors = errorsByFile[focusedError.file] || [];
  
  // State for selected file
  const [selectedFile, setSelectedFile] = useState(focusedError.file);
  
  // Get file info for the selected file
  const fileExtension = selectedFile.split('.').pop()?.toLowerCase() || '';
  const fileName = selectedFile.split('/').pop() || '';
  const filePath = selectedFile.split('/').slice(0, -1).join('/');
  
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[900px] max-h-[80vh] overflow-y-auto bg-[#0A0F1E] border-[#1E293B]">
        <div className="flex h-full">
          {/* Left Sidebar - File List */}
          <div className="w-72 border-r border-[#1E293B] pr-4 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-white flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-[#EF4444]" />
                Source Files
              </h3>
              <Badge variant="outline" className="bg-[#1E293B] border-[#2D3B4E] text-[#94A3B8]">
                {allErrors.length} {allErrors.length === 1 ? 'error' : 'errors'}
              </Badge>
            </div>
            <div className="space-y-2">
              {Object.entries(errorsByFile).map(([file, errors]) => {
                const isSelected = file === selectedFile;
                const fileErrorTypeInfo = getErrorTypeInfo(errors[0].type);
                return (
                  <button
                    key={file}
                    onClick={() => setSelectedFile(file)}
                    className={cn(
                      "w-full text-left rounded-lg p-2 border transition-colors",
                      isSelected ? "bg-[#2D3B4E] border-[#7C3AED]" : "border-[#2D3B4E] hover:bg-[#2D3B4E]/50"
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 min-w-0">
                        {getFileIcon(file)}
                        <span className="font-mono text-xs text-white truncate">
                          {file.split('/').pop()}
                        </span>
                      </div>
                      <Badge 
                        variant="outline" 
                        className={cn(
                          "text-[10px]",
                          fileErrorTypeInfo.bgColor,
                          fileErrorTypeInfo.color,
                          fileErrorTypeInfo.borderColor
                        )}
                      >
                        {errors.length}
                      </Badge>
                    </div>
                    {isSelected && (
                      <div className="mt-2 text-[10px] text-[#94A3B8] truncate">
                        {filePath}
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 pl-4 space-y-4 min-h-0 overflow-y-auto">
            {/* Source Info */}
            <div className="bg-[#1E293B] rounded-lg p-3 border border-[#2D3B4E] space-y-2">
              <h4 className="text-xs font-medium text-white flex items-center gap-2">
                <GitBranch className="h-3.5 w-3.5 text-[#7C3AED]" />
                Source Information
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <div className="flex items-center gap-1.5 text-xs">
                    <Hash className="h-3.5 w-3.5 text-[#94A3B8]" />
                    <span className="text-[#94A3B8]">Commit:</span>
                    <span className="font-mono text-white">{source.source_meta.commit.slice(0, 7)}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs">
                    <GitBranch className="h-3.5 w-3.5 text-[#94A3B8]" />
                    <span className="text-[#94A3B8]">Branch:</span>
                    <span className="font-mono text-white">{source.source_meta.branch}</span>
                  </div>
                </div>
                <div className="space-y-1.5">
                  <div className="flex items-center gap-1.5 text-xs">
                    <User className="h-3.5 w-3.5 text-[#94A3B8]" />
                    <span className="text-[#94A3B8]">Author:</span>
                    <span className="font-mono text-white">{source.source_meta.committer}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs">
                    <Calendar className="h-3.5 w-3.5 text-[#94A3B8]" />
                    <span className="text-[#94A3B8]">Last Updated:</span>
                    <span className="font-mono text-white">
                      {new Date(source.kubiya_metadata.last_updated).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* File Errors */}
            <div className="space-y-4">
              {errorsByFile[selectedFile]?.map((error, index) => {
                const errorTypeInfo = getErrorTypeInfo(error.type);
                const isFocused = error === focusedError;
                return (
                  <div 
                    key={index}
                    className={cn(
                      "rounded-lg p-4 border transition-colors",
                      isFocused ? "border-[#7C3AED] bg-[#2D3B4E]" : "border-[#2D3B4E] bg-[#1E293B]"
                    )}
                  >
                    <div className="flex items-start gap-3">
                      {errorTypeInfo.icon}
                      <div className="space-y-2 flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <h4 className={cn("font-medium", errorTypeInfo.color)}>
                            {error.error}
                          </h4>
                          <Badge 
                            variant="outline" 
                            className={cn(
                              "font-mono text-xs",
                              errorTypeInfo.bgColor,
                              errorTypeInfo.color,
                              errorTypeInfo.borderColor
                            )}
                          >
                            {errorTypeInfo.label}
                          </Badge>
                        </div>
                        {error.details && (
                          <p className={cn("text-sm", errorTypeInfo.color, "opacity-90")}>
                            {error.details}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Troubleshooting Tips */}
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-white flex items-center gap-2">
                <Info className="h-4 w-4 text-[#7C3AED]" />
                Troubleshooting Tips
              </h4>
              <div className="bg-[#1E293B] rounded-lg p-4 border border-[#2D3B4E] space-y-3">
                {focusedError.type?.toLowerCase() === 'importerror' && (
                  <>
                    <p className="text-sm text-[#94A3B8]">This error occurs when Python cannot find or import a module. Common causes:</p>
                    <ul className="text-sm text-[#94A3B8] list-disc list-inside space-y-1.5 ml-2">
                      <li>The module is not installed in the environment</li>
                      <li>The module name is misspelled</li>
                      <li>The module is not in the Python path</li>
                      <li>The module has dependencies that are not installed</li>
                    </ul>
                  </>
                )}
                {focusedError.type?.toLowerCase() === 'syntaxerror' && (
                  <>
                    <p className="text-sm text-[#94A3B8]">This error indicates invalid Python syntax. Common causes:</p>
                    <ul className="text-sm text-[#94A3B8] list-disc list-inside space-y-1.5 ml-2">
                      <li>Missing or extra parentheses, brackets, or braces</li>
                      <li>Invalid indentation</li>
                      <li>Missing colons after control statements</li>
                      <li>Invalid string formatting</li>
                    </ul>
                  </>
                )}
                {(!focusedError.type || !['importerror', 'syntaxerror'].includes(focusedError.type.toLowerCase())) && (
                  <p className="text-sm text-[#94A3B8]">
                    Review the error message and code context carefully. Check the documentation for the correct usage and ensure all dependencies are properly installed and configured.
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        <DialogFooter className="gap-2 pt-6 border-t border-[#1E293B]">
          <Button
            variant="outline"
            onClick={onClose}
            className="gap-2 border-[#2D3B4E] text-[#94A3B8] hover:text-white hover:bg-[#2D3B4E]"
          >
            Close
          </Button>
          {selectedFile.includes('github.com') && (
            <Button
              onClick={() => window.open(`https://github.com/${selectedFile}`, '_blank')}
              className="gap-2 bg-[#7C3AED] hover:bg-[#6D28D9] text-white"
            >
              <ExternalLink className="h-4 w-4" />
              View on GitHub
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

const SourceGroup = ({ source, onSourcesChange, allSources, teammate }: { 
  source: ExtendedSourceInfo; 
  onSourcesChange?: () => void;
  allSources: ExtendedSourceInfo[];
  teammate: TeammateDetails;
}) => {
  const { toast } = useToast();
  const [showSyncDialog, setShowSyncDialog] = useState(false);
  const [showRemoveDialog, setShowRemoveDialog] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isRemoving, setIsRemoving] = useState(false);
  const [sourceMetadata, setSourceMetadata] = useState<any>(null);
  const [isLoadingMetadata, setIsLoadingMetadata] = useState(false);
  const gitHubInfo = useMemo(() => getGitHubInfo(source.url), [source.url]);
  const firstToolWithIcon = useMemo(() => source.tools.find(tool => tool.icon_url), [source.tools]);
  
  // Add state for error preview modal
  const [selectedError, setSelectedError] = useState<{
    file: string;
    error: string;
    details?: string;
    code?: string;
    lineNumber?: number;
    type?: string;
  } | null>(null);

  // Get source errors from metadata
  const sourceErrors = useMemo(() => {
    // Debug log to see what we're getting
    console.log('Source metadata for', source.name, ':', sourceMetadata);

    // The errors are directly in the metadata response
    if (!sourceMetadata?.errors || !Array.isArray(sourceMetadata.errors)) {
      // If no metadata yet but we know there are errors, show loading state
      if (source.errors_count > 0 && isLoadingMetadata) {
        return [{
          file: 'Loading...',
          error: 'Loading error details...',
          details: '',
          type: 'loading'
        }];
      }
      return [];
    }
    
    // Map the errors to our expected format
    return sourceMetadata.errors.map((error: { 
      file: string;
      error: string;
      details?: string;
      type?: string;
    }) => ({
      file: error.file,
      error: error.error,
      details: error.details || '',
      type: error.type
    }));
  }, [sourceMetadata, source.errors_count, isLoadingMetadata, source.name]);

  // Fetch source metadata when component mounts or source changes
  useEffect(() => {
    const fetchSourceMetadata = async () => {
      // Only fetch if we know there are errors or haven't fetched yet
      if (!source.uuid || (!source.errors_count && sourceMetadata !== null)) return;
      
      try {
        setIsLoadingMetadata(true);
        console.log('Fetching metadata for source:', source.name, source.uuid);
        const response = await fetch(`/api/v1/sources/${source.uuid}/metadata`);
        if (!response.ok) {
          throw new Error('Failed to fetch source metadata');
        }
        const data = await response.json();
        console.log('Received metadata for', source.name, ':', data);
        setSourceMetadata(data);
      } catch (error) {
        console.error('Error fetching metadata for', source.name, ':', error);
        toast({
          title: "Failed to load error details",
          description: error instanceof Error ? error.message : 'An unexpected error occurred',
          variant: "destructive",
        });
      } finally {
        setIsLoadingMetadata(false);
      }
    };

    fetchSourceMetadata();
  }, [source.uuid, source.errors_count, source.name, toast]);

  const handleSync = async () => {
    try {
      setIsSyncing(true);
      
      // Show syncing toast
      const syncingToast = toast({
        title: "Syncing source...",
        description: `Syncing ${source.name} with the latest changes`,
        duration: Infinity,
      });
      
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

      // Fetch updated metadata after sync
      const metadataResponse = await fetch(`/api/v1/sources/${source.uuid}/metadata`);
      if (metadataResponse.ok) {
        const metadataData = await metadataResponse.json();
        setSourceMetadata(metadataData);
      }

      // Call onSourcesChange to trigger a re-render with the latest data
      if (onSourcesChange) {
        await onSourcesChange();
      }

      // Dismiss syncing toast and show success
      syncingToast.dismiss();
      toast({
        title: "Source synced successfully",
        description: `${source.name} has been synced with the latest changes`,
        variant: "default",
      });
    } catch (error) {
      console.error('Error syncing source:', error);
      
      // Show error toast
      toast({
        title: "Failed to sync source",
        description: error instanceof Error ? error.message : 'An unexpected error occurred',
        variant: "destructive",
      });
    } finally {
      setIsSyncing(false);
      setShowSyncDialog(false);
    }
  };

  const handleRemove = async () => {
    try {
      setIsRemoving(true);
      
      // Show removing toast
      const removingToast = toast({
        title: "Removing source...",
        description: `Removing ${source.name} from teammate`,
        duration: Infinity,
      });
      
      // Get the raw source UUIDs from the teammate
      // The API expects an array of source UUIDs, not SourceInfo objects
      const sourceUuids = teammate.sources?.map(s => typeof s === 'string' ? s : s.uuid) || [];
      const updatedSourceUuids = sourceUuids.filter(uuid => uuid !== source.uuid);
      
      console.log('Removing source:', {
        sourceToRemove: source.uuid,
        beforeRemoval: sourceUuids,
        afterRemoval: updatedSourceUuids,
        teammate: teammate
      });
      
      // Use teammate's UUID instead of ID
      const response = await fetch(`/api/teammates/${teammate.uuid}/sources`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          sources: updatedSourceUuids
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || errorData.details || 'Failed to remove source');
      }

      // Parse the response to verify the update
      const responseData = await response.json();
      
      // Verify the source was actually removed
      if (!responseData.success || !responseData.updatedSources) {
        throw new Error('Failed to verify source removal');
      }

      // Verify our source is not in the updated sources
      if (responseData.updatedSources.includes(source.uuid)) {
        throw new Error('Source was not properly removed');
      }

      // Dismiss removing toast and show success
      removingToast.dismiss();
      toast({
        title: "Source removed successfully",
        description: `${source.name} has been removed from teammate`,
        variant: "default",
      });

      // Force a re-fetch of sources to update the UI
      if (onSourcesChange) {
        await onSourcesChange();
      }

      // Close the dialog
      setShowRemoveDialog(false);
    } catch (error) {
      console.error('Error removing source:', error);
      
      // Show error toast
      toast({
        title: "Failed to remove source",
        description: error instanceof Error ? error.message : 'An unexpected error occurred',
        variant: "destructive",
      });
    } finally {
      setIsRemoving(false);
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
                  {sourceErrors.length > 0 && (
                    <HoverCard>
                      <HoverCardTrigger asChild>
                        <Badge 
                          variant="destructive" 
                          className="bg-red-500/10 text-red-400 border-red-500/20 cursor-help hover:bg-red-500/20 transition-colors"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (sourceErrors[0]) {
                              setSelectedError(sourceErrors[0]);
                            }
                          }}
                        >
                          <AlertCircle className="h-3.5 w-3.5 mr-1" />
                          {sourceErrors.length} {sourceErrors.length === 1 ? 'error' : 'errors'}
                        </Badge>
                      </HoverCardTrigger>
                      <HoverCardContent className="w-96 p-0">
                        <div className="p-3 space-y-3">
                          <div className="flex items-start justify-between">
                            <h5 className="text-sm font-medium text-white flex items-center gap-2">
                              <AlertCircle className="h-4 w-4 text-[#EF4444]" />
                              Source Errors
                            </h5>
                            <Badge variant="outline" className="bg-[#1E293B] border-[#2D3B4E] text-[#94A3B8]">
                              Click error to view details
                            </Badge>
                          </div>
                          <div className="space-y-2 max-h-60 overflow-y-auto">
                            {sourceErrors.map((error: {
                              file: string;
                              error: string;
                              details?: string;
                              type?: string;
                            }, index: number) => {
                              const errorTypeInfo = getErrorTypeInfo(error.type);
                              return (
                                <button
                                  key={index}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedError(error);
                                  }}
                                  className={cn(
                                    "w-full text-left rounded-md p-2 border space-y-1.5 transition-colors",
                                    errorTypeInfo.bgColor,
                                    errorTypeInfo.borderColor,
                                    "hover:bg-opacity-20"
                                  )}
                                >
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                      {getFileIcon(error.file)}
                                      <span className="font-mono text-xs text-[#94A3B8]">{error.file}</span>
                                    </div>
                                    <Badge 
                                      variant="outline" 
                                      className={cn(
                                        "text-[10px]",
                                        errorTypeInfo.bgColor,
                                        errorTypeInfo.color,
                                        errorTypeInfo.borderColor
                                      )}
                                    >
                                      {errorTypeInfo.label}
                                    </Badge>
                                  </div>
                                  <div className={cn("text-xs pl-6", errorTypeInfo.color)}>
                                    {error.error}
                                  </div>
                                </button>
                              );
                            })}
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
          source={source}
          allErrors={sourceMetadata?.errors || []}
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

  const handleInstall = async (
    values: FormValues,
    updateProgress: (stepId: string, status: 'pending' | 'loading' | 'success' | 'error', error?: string) => void
  ): Promise<void> => {
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
    } catch (error) {
      console.error('Installation error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Installation failed';
      updateProgress('validate', 'error', errorMessage);
      throw error;
    }
  };

  // Add useInstallTool hook after handleInstall is defined
  const installToolState = useInstallTool({
    onInstall: handleInstall,
    teammate: teammate!,
    onClose: () => setShowInstallModal(false)
  });

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

  // Early return if loading
  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!teammate) {
    return <ErrorState message="No teammate data available" />;
  }

  return (
    <InstallToolProvider teammate={teammate!} value={installToolState}>
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
                  teammate={teammate!}
                />
              ))}
            </div>
          )}
        </div>

        {/* Install Tool Form */}
        <InstallToolForm
          isOpen={showInstallModal}
          onClose={() => setShowInstallModal(false)}
          onInstall={handleInstall}
          teammate={teammate}
        />
      </div>
    </InstallToolProvider>
  );
} 