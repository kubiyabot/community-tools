"use client";

import React from 'react';
import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/app/components/ui/dialog";
import { Button } from "@/app/components/ui/button";
import { ScrollArea } from "@/app/components/ui/scroll-area";
import { Badge } from "@/app/components/ui/badge";
import Editor from '@monaco-editor/react';
import { cn } from "@/lib/utils";
import {
  X,
  Code,
  Ship,
  ExternalLink,
  Loader2,
  AlertCircle,
  Globe,
  Tag,
  Folder,
  File,
  GitBranch,
  GitCommit,
  Clock,
  Settings,
  FolderTree,
  GitFork,
  Terminal,
  Database,
  Box,
  Key,
  Variable,
  FileJson,
  PackageOpen,
  GitPullRequest,
  Hash,
  FileText,
  FolderOpen,
  Lock,
  FileCode,
  FileQuestion,
  Info,
  MessageSquare,
  RefreshCw,
  User2,
  Wrench
} from 'lucide-react';
import { toast } from '@/app/components/use-toast';
import { Tool } from '@/app/types/tool';
import { TeammateAPI } from '@/app/api/teammates/client';
import { Separator } from "@/app/components/ui/separator";
import type { SourceInfo } from "@/app/types/source";
import Mermaid from '@/app/components/ui/mermaid';
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/app/components/ui/hover-card";
import { format } from 'date-fns';

const modalStyles = {
  dialog: {
    content: "bg-[#0F172A] border border-[#2A3347] p-0 max-w-4xl w-full h-[90vh] overflow-hidden flex flex-col",
    header: "p-6 border-b border-[#2A3347] flex-shrink-0",
    body: "flex-1 flex flex-col min-h-0 overflow-hidden"
  },
  text: {
    primary: "text-slate-200",
    secondary: "text-slate-400",
    accent: "text-purple-400",
    subtitle: "text-sm font-medium text-slate-200 mb-3"
  },
  cards: {
    base: "bg-[#1E293B] border border-[#2D3B4E] rounded-lg",
    container: "bg-[#1E293B] border border-[#2D3B4E] rounded-lg p-4"
  },
  buttons: {
    ghost: "text-slate-400 hover:text-slate-300 hover:bg-[#1E293B]",
    primary: "bg-purple-500 text-white hover:bg-purple-600"
  }
} as const;

interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  content?: string;
  extension?: string;
  isInjected?: boolean;
  children?: FileNode[];
  source?: string;
  isReserved?: boolean;
}

// Add type for volume mounts
interface VolumeMount {
  path: string;
  name: string;
}

interface WithFile {
  source?: string;
  target?: string;
  destination?: string;
  content?: string;
}

interface FileSpec {
  source?: string;
  target?: string;
  destination?: string;
  content?: string;
  isInjected?: boolean;
  isReserved?: boolean;
}

interface FileDebugInfo {
  path: string;
  source?: string;
  hasContent: boolean;
  isInjected?: boolean;
}

function getFileIcon(fileName: string | undefined, isInjected: boolean = false, isReserved: boolean = false) {
  if (!fileName) return <FileQuestion className="h-4 w-4 text-slate-400" />;
  if (isInjected) return <Lock className="h-4 w-4 text-orange-400" />;
  if (isReserved) return <Terminal className="h-4 w-4 text-blue-400" />;
  
  const ext = fileName.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'py':
      return <FileCode className="h-4 w-4 text-blue-400" />;
    case 'js':
    case 'ts':
      return <FileCode className="h-4 w-4 text-yellow-400" />;
    case 'sh':
      return <Terminal className="h-4 w-4 text-green-400" />;
    case 'json':
      return <FileJson className="h-4 w-4 text-purple-400" />;
    case 'md':
      return <FileText className="h-4 w-4 text-slate-400" />;
    default:
      return <FileQuestion className="h-4 w-4 text-slate-400" />;
  }
}

function buildFileTree(files: Array<{ source?: string; target?: string; destination?: string; content?: string; isReserved?: boolean }>) {
  const root: FileNode = { name: '/', path: '/', type: 'directory', children: [] };
  
  files.forEach(file => {
    // Handle different file path specifications
    const filePath = file.target || file.destination || file.source || '';
    if (!filePath) return; // Skip if no valid path found

    const pathParts = filePath.split('/').filter(Boolean);
    let currentNode = root;
    
    pathParts.forEach((part, index) => {
      if (index === pathParts.length - 1) {
        // This is a file
        const extension = part.includes('.') ? part.split('.').pop() : undefined;
        currentNode.children = currentNode.children || [];
        currentNode.children.push({
          name: part,
          path: filePath,
          type: 'file',
          content: file.content,
          extension,
          isInjected: !file.content,
          isReserved: file.isReserved,
          source: file.source
        });
      } else {
        // This is a directory
        currentNode.children = currentNode.children || [];
        let dirNode = currentNode.children.find(
          node => node.type === 'directory' && node.name === part
        );
        if (!dirNode) {
          dirNode = {
            name: part,
            path: pathParts.slice(0, index + 1).join('/'),
            type: 'directory',
            children: []
          };
          currentNode.children.push(dirNode);
        }
        currentNode = dirNode;
      }
    });
  });

  // Sort the tree - directories first, then files alphabetically
  const sortNode = (node: FileNode) => {
    if (node.children) {
      node.children.sort((a, b) => {
        // Directories first
        if (a.type !== b.type) return a.type === 'directory' ? -1 : 1;
        // Then alphabetically by name
        return a.name.localeCompare(b.name);
      });
      // Recursively sort children
      node.children.forEach(sortNode);
    }
  };
  sortNode(root);
  
  return root;
}

function FileTreeNode({ node, onSelect }: { node: FileNode; onSelect: (node: FileNode) => void }) {
  const [isExpanded, setIsExpanded] = useState(true);
  
  if (node.type === 'file') {
    return (
      <div
        className="flex items-center gap-2 py-1 px-2 hover:bg-[#1E293B] rounded cursor-pointer group"
        onClick={() => onSelect(node)}
      >
        {getFileIcon(node.name, node.isInjected, node.isReserved)}
        <span className="text-sm text-slate-300">{node.name}</span>
        {node.isInjected && (
          <Badge variant="outline" className="ml-2 text-[10px] bg-orange-500/10 text-orange-400 border-orange-500/20">
            injected
          </Badge>
        )}
        {node.isReserved && (
          <HoverCard>
            <HoverCardTrigger>
              <Badge variant="outline" className="ml-2 text-[10px] bg-blue-500/10 text-blue-400 border-blue-500/20">
                container system
              </Badge>
            </HoverCardTrigger>
            <HoverCardContent className="w-80">
              <div className="space-y-2">
                <h5 className="text-sm font-medium text-slate-200">Container Entrypoint</h5>
                <p className="text-xs text-slate-400">
                  This is the first script that will run every time this tool is called.
                  It sets up the container environment and executes the main functionality.
                </p>
              </div>
            </HoverCardContent>
          </HoverCard>
        )}
      </div>
    );
  }
  
  return (
    <div>
      <div
        className="flex items-center gap-2 py-1 px-2 hover:bg-[#1E293B] rounded cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? (
          <FolderOpen className="h-4 w-4 text-blue-400" />
        ) : (
          <Folder className="h-4 w-4 text-blue-400" />
        )}
        <span className="text-sm font-medium text-slate-300">{node.name}</span>
      </div>
      {isExpanded && node.children && (
        <div className="ml-4">
          {node.children.sort((a, b) => {
            // Directories first, then files
            if (a.type !== b.type) return a.type === 'directory' ? -1 : 1;
            return a.name.localeCompare(b.name);
          }).map((child, index) => (
            <FileTreeNode key={child.path + index} node={child} onSelect={onSelect} />
          ))}
        </div>
      )}
    </div>
  );
}

interface ToolDetailsModalProps {
  teammateId?: string;
  toolId?: string;
  isOpen: boolean;
  onCloseAction: () => void;
  tool: Tool;
  source?: SourceInfo;
}

// Add error boundary component
const MermaidErrorBoundary = ({ children }: { children: React.ReactNode }) => {
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    const handleError = () => setHasError(true);
    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, []);

  if (hasError) {
    return null;
  }

  return <>{children}</>;
};

export function ToolDetailsModal({ teammateId, toolId, isOpen, onCloseAction, tool, source }: ToolDetailsModalProps) {
  const [activeTab, setActiveTab] = useState('overview');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
  const [mermaidError, setMermaidError] = useState<string | null>(null);
  const [isMermaidLoading, setIsMermaidLoading] = useState(false);
  const [mermaidRenderAttempts, setMermaidRenderAttempts] = useState(0);
  const [mermaidLoadingState, setMermaidLoadingState] = useState<'idle' | 'loading' | 'error' | 'success'>('idle');
  const mermaidTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Debug logging for tool data
  useEffect(() => {
    if (tool) {
      console.log('Tool data:', {
        content: tool.content ? 'present' : 'missing',
        with_files: tool.with_files,
        mermaid: tool.mermaid ? 'present' : 'missing'
      });
    }
  }, [tool]);

  const fileTree = useMemo(() => {
    if (!tool) return { name: '/', path: '/', type: 'directory' as const, children: [] };

    // Helper function to guess file name from content
    const guessFileNameFromContent = (content: string): string => {
      // Look for common Python imports/patterns
      if (content.includes('import ') || content.includes('from ') || content.includes('def ')) {
        const mainFunc = content.match(/def\s+(\w+)/)?.[1];
        return mainFunc ? `/${mainFunc}.py` : '/script.py';
      }
      // Look for common JavaScript/TypeScript patterns
      if (content.includes('export ') || content.includes('import ') || content.includes('function ') || content.includes('const ')) {
        return content.includes('interface ') || content.includes(': ') ? '/script.ts' : '/script.js';
      }
      // Look for shell script patterns
      if (content.includes('#!/bin/') || content.includes('export ') || content.includes('PATH=')) {
        return '/script.sh';
      }
      // Default to txt if we can't determine
      return '/script.txt';
    };

    // Collect all files from different sources
    const allFiles: FileSpec[] = [
      // Add container entrypoint script as a special system file
      { 
        source: 'container',
        target: '/entrypoint.sh',
        content: tool.content || '# No content available',
        isReserved: true
      }
    ];

    // Process with_files array
    if (tool.with_files && Array.isArray(tool.with_files)) {
      tool.with_files.forEach((file: string | WithFile, index) => {
        // Handle string case first
        if (typeof file === 'string') {
          allFiles.push({
            source: file,
            target: file.startsWith('/') ? file : `/${file}`,
            isInjected: true
          });
          return;
        }

        // For object specifications
        const fileSpec: FileSpec = {
          source: file.source,
          // Use destination if available, fallback to target, then source
          target: file.destination || file.target || file.source || '',
          content: file.content,
          isInjected: !file.content
        };

        // If we still don't have a valid path but have content, generate one
        if (!fileSpec.target && fileSpec.content) {
          fileSpec.target = guessFileNameFromContent(fileSpec.content);
          // If multiple files might have the same generated name, add index
          if (allFiles.some(f => f.target === fileSpec.target)) {
            const ext = fileSpec.target.split('.').pop();
            fileSpec.target = fileSpec.target.replace(`.${ext}`, `_${index + 1}.${ext}`);
          }
        }

        // Ensure path starts with /
        if (fileSpec.target && !fileSpec.target.startsWith('/')) {
          fileSpec.target = `/${fileSpec.target}`;
        }

        // Only add if we have a valid target path
        if (fileSpec.target) {
          allFiles.push(fileSpec);
        } else {
          console.warn('Could not determine path for file:', file);
        }
      });
    }

    // Debug log the files being processed
    const debugInfo: FileDebugInfo[] = allFiles.map(f => ({
      path: f.target || '',
      source: f.source,
      hasContent: !!f.content,
      isInjected: f.isInjected
    }));
    console.log('Processing files:', debugInfo);

    // Build tree from files
    return buildFileTree(allFiles);
  }, [tool]);

  const getLanguageFromExtension = (extension?: string) => {
    switch (extension) {
      case 'py': return 'python';
      case 'js': return 'javascript';
      case 'ts': return 'typescript';
      case 'json': return 'json';
      case 'sh': return 'shell';
      case 'md': return 'markdown';
      default: return 'plaintext';
    }
  };

  // Add cleanup effect
  useEffect(() => {
    return () => {
      // Cleanup on unmount
      if (mermaidTimeoutRef.current) {
        clearTimeout(mermaidTimeoutRef.current);
      }
      setMermaidError(null);
      setMermaidLoadingState('idle');
      setMermaidRenderAttempts(0);
      setIsMermaidLoading(false);
    };
  }, []);

  // Reset states when tab changes
  useEffect(() => {
    setMermaidError(null);
    setMermaidLoadingState('idle');
    setMermaidRenderAttempts(0);
    setIsMermaidLoading(false);
  }, [activeTab]);

  const handleRenderError = useCallback((error: Error, isTimeout = false) => {
    console.error('Error rendering mermaid diagram:', error);
    
    // Clear timeout if it exists
    if (mermaidTimeoutRef.current) {
      clearTimeout(mermaidTimeoutRef.current);
    }

    // Reset states
    setMermaidError(error.message);
    setMermaidLoadingState('error');
    setIsMermaidLoading(false);
    setMermaidRenderAttempts(1);
    
    // Show toast for any rendering error
    toast({
      title: "Diagram Rendering Failed",
      description: isTimeout 
        ? "The flow diagram is taking too long to render and has been cancelled."
        : "Unable to render the flow diagram due to syntax or complexity issues.",
      variant: "destructive",
    });
  }, []);

  const renderMermaidDiagram = useCallback(() => {
    if (!tool.mermaid) return null;

    const MAX_RENDER_ATTEMPTS = 1;
    const RENDER_TIMEOUT_MS = 2000;

    // Clear any existing timeout
    if (mermaidTimeoutRef.current) {
      clearTimeout(mermaidTimeoutRef.current);
    }

    // If we've already tried once, don't attempt again
    if (mermaidRenderAttempts >= MAX_RENDER_ATTEMPTS) {
      return (
        <div className="p-4 bg-orange-500/10 border border-orange-500/20 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-orange-400 mt-0.5 flex-shrink-0" />
            <div className="space-y-2 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h4 className="text-sm font-medium text-orange-400">Flow diagram cannot be rendered</h4>
                <HoverCard>
                  <HoverCardTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-5 w-5 p-0">
                      <Info className="h-4 w-4 text-orange-400" />
                    </Button>
                  </HoverCardTrigger>
                  <HoverCardContent className="w-80">
                    <div className="space-y-2">
                      <div className="text-xs text-slate-400">
                        The flow diagram couldn't be rendered due to:
                      </div>
                      <ul className="text-xs text-slate-400 list-disc pl-4 space-y-1">
                        <li>Invalid diagram syntax</li>
                        <li>Excessive complexity</li>
                        <li>Browser performance constraints</li>
                      </ul>
                    </div>
                  </HoverCardContent>
                </HoverCard>
              </div>
              <div className="text-xs text-orange-400/80">
                <details className="cursor-pointer">
                  <summary className="hover:text-orange-300">View diagram code</summary>
                  <div className="mt-2 p-2 bg-slate-800/50 rounded border border-orange-500/20 overflow-auto">
                    <code className="text-slate-300 font-mono whitespace-pre-wrap break-all">
                      {tool.mermaid}
                    </code>
                  </div>
                </details>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="w-full overflow-auto">
        {/* Loading State */}
        {isMermaidLoading && (
          <div className="flex items-center justify-center p-6 bg-[#1E293B] border border-[#2D3B4E] rounded-lg">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="h-6 w-6 text-purple-400 animate-spin" />
              <div className="flex flex-col items-center text-center">
                <span className="text-sm font-medium text-slate-300">Rendering flow diagram...</span>
                <span className="text-xs text-slate-400 mt-1">This will timeout in 2 seconds if too complex</span>
              </div>
            </div>
          </div>
        )}

        {/* Mermaid Diagram wrapped in error boundary */}
        <MermaidErrorBoundary>
          <div 
            className={cn(
              "w-full overflow-auto transition-all duration-300", 
              {
                "opacity-0 scale-95": isMermaidLoading,
                "opacity-100 scale-100": !isMermaidLoading,
              }
            )}
          >
            <Mermaid 
              chart={tool.mermaid}
              onError={handleRenderError}
              onRenderStart={() => {
                setIsMermaidLoading(true);
                setMermaidLoadingState('loading');
                
                mermaidTimeoutRef.current = setTimeout(() => {
                  handleRenderError(
                    new Error('Diagram rendering timed out - complexity too high'),
                    true
                  );
                }, RENDER_TIMEOUT_MS);
              }}
              onRenderEnd={() => {
                if (mermaidTimeoutRef.current) {
                  clearTimeout(mermaidTimeoutRef.current);
                }
                setIsMermaidLoading(false);
                setMermaidLoadingState('success');
              }}
            />
          </div>
        </MermaidErrorBoundary>
      </div>
    );
  }, [tool.mermaid, mermaidRenderAttempts, handleRenderError]);

  // Clean up timeout on unmount
  useEffect(() => {
    return () => {
      if (mermaidTimeoutRef.current) {
        clearTimeout(mermaidTimeoutRef.current);
      }
    };
  }, []);

  // Add better error handling for file content
  const renderFileContent = (file: FileNode) => {
    if (!file.content && file.isInjected) {
      return (
        <div className="p-6 bg-orange-500/10 border border-orange-500/20 rounded-lg">
          <div className="flex items-start gap-3">
            <Lock className="h-5 w-5 text-orange-400 mt-0.5" />
            <div className="space-y-2">
              <p className="text-sm font-medium text-orange-400">
                This file will be injected at runtime
              </p>
              <div className="space-y-1 text-xs text-orange-400/80">
                <div className="flex items-center gap-2">
                  <FileText className="h-3.5 w-3.5" />
                  <span>Path: {file.path}</span>
                </div>
                {file.source && (
                  <div className="flex items-center gap-2">
                    <GitFork className="h-3.5 w-3.5" />
                    <span>Source: {file.source}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      );
    }

    if (!file.content) {
      return (
        <div className="p-6 bg-slate-800/50 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-slate-400 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-slate-400">
                No content available for this file
              </p>
              <p className="text-xs text-slate-500 mt-1">
                The file exists but its content is not accessible
              </p>
            </div>
          </div>
        </div>
      );
    }

    return (
      <Editor
        height="100%"
        theme="vs-dark"
        language={getLanguageFromExtension(file.extension)}
        value={file.content}
        options={{
          readOnly: true,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          fontSize: 14,
          lineNumbers: 'on',
          renderLineHighlight: 'none',
          overviewRulerLanes: 0,
          hideCursorInOverviewRuler: true,
          scrollbar: {
            vertical: 'visible',
            horizontal: 'visible'
          }
        }}
      />
    );
  };

  const renderTabContent = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 text-purple-400 animate-spin" />
            <p className={modalStyles.text.secondary}>Loading tool details...</p>
          </div>
        </div>
      );
    }

    if (error || !tool) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="flex flex-col items-center gap-3 text-red-400">
            <AlertCircle className="h-8 w-8" />
            <p>{error || 'Tool not found'}</p>
          </div>
        </div>
      );
    }

    switch (activeTab) {
      case 'overview':
        return (
          <ScrollArea className="flex-1 h-full">
            <div className="space-y-6 p-6">
              {/* Core Tool Details */}
              <div className={cn(modalStyles.cards.container, "space-y-4")}>
                <h3 className={cn(modalStyles.text.subtitle, "flex items-center gap-2")}>
                  <Wrench className="h-5 w-5 text-purple-400" />
                  Tool Information
                </h3>
                <div className="grid gap-4">
                  <div className="flex items-start gap-3 p-3 bg-[#1E293B]/50 rounded-lg border border-[#2D3B4E]">
                    <div className="p-2 rounded-md bg-purple-500/10 border border-purple-500/20">
                      <Info className="h-4 w-4 text-purple-400" />
                    </div>
                    <div className="space-y-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-slate-300">Type:</span>
                        <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/20">
                          {tool.type}
                        </Badge>
                      </div>
                      <h4 className="text-base font-medium text-slate-200">{tool.name}</h4>
                      <p className="text-sm text-slate-400">{tool.description}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    {tool.created_by && (
                      <div className="flex items-center gap-2 p-3 bg-[#1E293B]/50 rounded-lg border border-[#2D3B4E]">
                        <User2 className="h-4 w-4 text-blue-400" />
                        <div>
                          <span className="text-xs text-slate-400">Created by</span>
                          <div className="text-sm text-slate-200">{tool.created_by}</div>
                        </div>
                      </div>
                    )}
                    {tool.created_at && (
                      <div className="flex items-center gap-2 p-3 bg-[#1E293B]/50 rounded-lg border border-[#2D3B4E]">
                        <Clock className="h-4 w-4 text-emerald-400" />
                        <div>
                          <span className="text-xs text-slate-400">Created on</span>
                          <div className="text-sm text-slate-200">
                            {format(new Date(tool.created_at), 'MMM d, yyyy')}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* SDK Information */}
              <div className={cn(modalStyles.cards.container, "space-y-4")}>
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-md bg-blue-500/10 border border-blue-500/20">
                    <img 
                      src="https://www.svgrepo.com/show/376344/python.svg"
                      alt="Python"
                      className="h-5 w-5 object-contain"
                    />
                  </div>
                  <div className="space-y-2 flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-medium text-slate-200">Built with Kubiya Python SDK</h3>
                      <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20">
                        v1.0.2
                      </Badge>
                    </div>
                    <div className="flex items-center gap-3">
                      <a 
                        href="https://pypi.org/project/kubiya-sdk/" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
                      >
                        <FileCode className="h-4 w-4" />
                        SDK Documentation
                        <ExternalLink className="h-3 w-3" />
                      </a>
                      <a 
                        href="https://github.com/kubiya-engineering/kubiya-sdk" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
                      >
                        <GitPullRequest className="h-4 w-4" />
                        GitHub Repository
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                  </div>
                </div>
              </div>

              {/* Flow Diagram */}
              {tool.mermaid && renderMermaidDiagram()}
            </div>
          </ScrollArea>
        );

      case 'runtime':
        return (
          <ScrollArea className="flex-1 h-full">
            <div className="space-y-6 p-6">
              {/* Docker Configuration */}
              {tool.type === 'docker' && tool.image && (
                <div className={cn(modalStyles.cards.container, "space-y-4 relative overflow-hidden group")}>
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <div className="relative">
                    <h3 className={cn(modalStyles.text.subtitle, "flex items-center gap-2 mb-4")}>
                      <Ship className="h-5 w-5 text-purple-400" />
                      Container Configuration
                    </h3>
                    <div className="space-y-4">
                      <HoverCard>
                        <HoverCardTrigger>
                          <div className="flex items-center gap-3 p-3 bg-[#1E293B]/50 rounded-lg cursor-help border border-[#2D3B4E] hover:border-purple-500/30 transition-colors">
                            <div className="p-2 rounded-md bg-purple-500/10 border border-purple-500/20">
                              <Ship className="h-4 w-4 text-purple-400" />
                            </div>
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className={modalStyles.text.primary}>Docker Image:</span>
                                <code className="px-2 py-0.5 bg-slate-800 rounded text-sm font-mono text-slate-300">
                                  {tool.image}
                                </code>
                              </div>
                              <div className="flex gap-2 mt-2">
                                {tool.image?.includes('docker.io') && (
                                  <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20">
                                    Docker Hub
                                  </Badge>
                                )}
                                {tool.image?.includes('gcr.io') && (
                                  <Badge variant="outline" className="bg-green-500/10 text-green-400 border-green-500/20">
                                    Google Container Registry
                                  </Badge>
                                )}
                                {tool.image?.includes('ecr') && (
                                  <Badge variant="outline" className="bg-orange-500/10 text-orange-400 border-orange-500/20">
                                    Amazon ECR
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </div>
                        </HoverCardTrigger>
                        <HoverCardContent className="w-80">
                          <div className="space-y-2">
                            <h4 className="text-sm font-medium text-slate-200">Container Runtime</h4>
                            <p className="text-xs text-slate-400">
                              This tool runs in an isolated Docker container with all required dependencies. The image can be from any container registry, allowing for flexible deployment and execution environments.
                            </p>
                          </div>
                        </HoverCardContent>
                      </HoverCard>

                      {tool.workdir && (
                        <div className="flex items-center gap-3 p-3 bg-[#1E293B]/50 rounded-lg border border-[#2D3B4E]">
                          <div className="p-2 rounded-md bg-purple-500/10 border border-purple-500/20">
                            <Folder className="h-4 w-4 text-purple-400" />
                          </div>
                          <div>
                            <span className={modalStyles.text.primary}>Working Directory:</span>
                            <code className="ml-2 px-2 py-0.5 bg-slate-800 rounded text-sm font-mono text-slate-300">
                              {tool.workdir}
                            </code>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Environment Variables & Secrets */}
              <div className={cn(modalStyles.cards.container, "space-y-4 relative overflow-hidden group")}>
                <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <div className="relative">
                  <h3 className={cn(modalStyles.text.subtitle, "flex items-center gap-2 mb-4")}>
                    <Key className="h-5 w-5 text-emerald-400" />
                    Runtime Configuration
                  </h3>
                  <div className="grid gap-4">
                    <HoverCard openDelay={200}>
                      <HoverCardTrigger>
                        <div className="p-4 bg-[#1E293B]/50 rounded-lg cursor-help border border-[#2D3B4E] hover:border-emerald-500/30 transition-colors">
                          <div className="flex items-center gap-2 mb-3">
                            <Variable className="h-4 w-4 text-emerald-400" />
                            <span className={modalStyles.text.primary}>Environment Variables</span>
                          </div>
                          {tool.env && tool.env.length > 0 ? (
                            <div className="space-y-2">
                              {tool.env.map((env, idx) => (
                                <div key={idx} className="flex items-center gap-2">
                                  <code className="px-2 py-0.5 bg-slate-800 rounded text-sm font-mono text-slate-300 flex-1">
                                    {env}
                                  </code>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-sm text-slate-400">No environment variables defined</p>
                          )}
                        </div>
                      </HoverCardTrigger>
                      <HoverCardContent className="w-80">
                        <div className="space-y-2">
                          <h4 className="text-sm font-medium text-slate-200">Dynamic Environment Variables</h4>
                          <p className="text-xs text-slate-400">
                            Environment variables can be injected at runtime based on:
                          </p>
                          <ul className="text-xs text-slate-400 space-y-1 list-disc pl-4">
                            <li className="flex items-center gap-2">
                              <MessageSquare className="h-4 w-4 text-purple-400" />
                              <span>Teammate's configuration</span>
                            </li>
                            <li className="flex items-center gap-2">
                              <GitBranch className="h-4 w-4 text-emerald-400" />
                              <span>Active integrations</span>
                            </li>
                            <li className="flex items-center gap-2">
                              <Settings className="h-4 w-4 text-blue-400" />
                              <span>Runtime context and events</span>
                            </li>
                          </ul>
                        </div>
                      </HoverCardContent>
                    </HoverCard>

                    <HoverCard openDelay={200}>
                      <HoverCardTrigger>
                        <div className="p-4 bg-[#1E293B]/50 rounded-lg cursor-help border border-[#2D3B4E] hover:border-red-500/30 transition-colors">
                          <div className="flex items-center gap-2 mb-3">
                            <Key className="h-4 w-4 text-red-400" />
                            <span className={modalStyles.text.primary}>Runtime Secrets</span>
                          </div>
                          {tool.secrets && tool.secrets.length > 0 ? (
                            <div className="space-y-2">
                              {tool.secrets.map((secret, idx) => (
                                <div key={idx} className="flex items-center gap-2">
                                  <Lock className="h-3.5 w-3.5 text-red-400/70" />
                                  <code className="px-2 py-0.5 bg-slate-800 rounded text-sm font-mono text-slate-300 flex-1">
                                    {secret}
                                  </code>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-sm text-slate-400">No secrets required</p>
                          )}
                        </div>
                      </HoverCardTrigger>
                      <HoverCardContent className="w-80">
                        <div className="space-y-2">
                          <h4 className="text-sm font-medium text-slate-200">Secure Secrets Injection</h4>
                          <p className="text-xs text-slate-400">
                            Secrets are securely managed and injected from:
                          </p>
                          <ul className="text-xs text-slate-400 space-y-1 list-disc pl-4">
                            <li className="flex items-center gap-2">
                              <Lock className="h-3.5 w-3.5 text-red-400/70" />
                              <span>Teammate's secure vault</span>
                            </li>
                            <li className="flex items-center gap-2">
                              <GitBranch className="h-4 w-4 text-emerald-400" />
                              <span>Connected integration credentials</span>
                            </li>
                            <li className="flex items-center gap-2">
                              <Settings className="h-4 w-4 text-blue-400" />
                              <span>Organization's secret store</span>
                            </li>
                          </ul>
                        </div>
                      </HoverCardContent>
                    </HoverCard>

                    {/* Volumes/Mounts */}
                    <HoverCard openDelay={200}>
                      <HoverCardTrigger>
                        <div className="p-4 bg-[#1E293B]/50 rounded-lg cursor-help border border-[#2D3B4E] hover:border-purple-500/30 transition-colors">
                          <div className="flex items-center gap-2 mb-3">
                            <Database className="h-4 w-4 text-purple-400" />
                            <span className={modalStyles.text.primary}>Volume Mounts</span>
                          </div>
                          {tool.with_volumes && tool.with_volumes.length > 0 ? (
                            <div className="space-y-2">
                              {tool.with_volumes.map((mount: VolumeMount | string, idx: number) => (
                                <div key={idx} className="flex items-center gap-2">
                                  <FolderOpen className="h-3.5 w-3.5 text-purple-400/70" />
                                  <code className="px-2 py-0.5 bg-slate-800 rounded text-sm font-mono text-slate-300 flex-1">
                                    {typeof mount === 'string' ? mount : `${mount.path} (${mount.name})`}
                                  </code>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-sm text-slate-400">No volume mounts configured</p>
                          )}
                        </div>
                      </HoverCardTrigger>
                      <HoverCardContent className="w-80">
                        <div className="space-y-2">
                          <h4 className="text-sm font-medium text-slate-200">Persistent Storage</h4>
                          <p className="text-xs text-slate-400">
                            Volume mounts provide persistent storage and data sharing between:
                          </p>
                          <ul className="text-xs text-slate-400 space-y-1 list-disc pl-4">
                            <li className="flex items-center gap-2">
                              <FolderOpen className="h-3.5 w-3.5 text-purple-400/70" />
                              <span>Container executions</span>
                            </li>
                            <li className="flex items-center gap-2">
                              <FolderOpen className="h-3.5 w-3.5 text-purple-400/70" />
                              <span>Host system resources</span>
                            </li>
                            <li className="flex items-center gap-2">
                              <FolderOpen className="h-3.5 w-3.5 text-purple-400/70" />
                              <span>Shared team storage</span>
                            </li>
                          </ul>
                        </div>
                      </HoverCardContent>
                    </HoverCard>
                  </div>
                </div>
              </div>
            </div>
          </ScrollArea>
        );

      case 'inputs':
        return (
          <ScrollArea className="flex-1 h-full">
            <div className="space-y-6 p-6">
              {tool?.args?.length ? (
                <div className={cn(modalStyles.cards.container, "h-full flex flex-col")}>
                  <div className="flex items-start gap-4 mb-6">
                    <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20 flex-shrink-0">
                      <MessageSquare className="h-6 w-6 text-purple-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-lg font-medium text-slate-200">AI-Driven Parameters</h3>
                        <HoverCard>
                          <HoverCardTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-6 w-6 p-0">
                              <Info className="h-4 w-4 text-slate-400" />
                            </Button>
                          </HoverCardTrigger>
                          <HoverCardContent className="w-96">
                            <div className="space-y-4">
                              <div className="space-y-2">
                                <h4 className="text-sm font-medium text-slate-200">Contextual Intelligence</h4>
                                <p className="text-xs text-slate-400">
                                  These parameters are handled intelligently by your AI Teammate through:
                                </p>
                                <ul className="text-xs text-slate-400 space-y-2 mt-2">
                                  <li className="flex items-center gap-2">
                                    <MessageSquare className="h-4 w-4 text-purple-400" />
                                    <span>Natural conversation and dialogue</span>
                                  </li>
                                  <li className="flex items-center gap-2">
                                    <GitBranch className="h-4 w-4 text-emerald-400" />
                                    <span>Event context and system state</span>
                                  </li>
                                  <li className="flex items-center gap-2">
                                    <Settings className="h-4 w-4 text-blue-400" />
                                    <span>Automated decision making</span>
                                  </li>
                                </ul>
                              </div>
                              <div className="p-3 bg-purple-500/10 border border-purple-500/20 rounded-lg">
                                <p className="text-xs text-purple-400">
                                  Your AI Teammate can gather this information through natural conversation or automatically from context, making the interaction seamless and intuitive.
                                </p>
                              </div>
                            </div>
                          </HoverCardContent>
                        </HoverCard>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/20">
                          Conversation Driven
                        </Badge>
                        <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
                          Context Aware
                        </Badge>
                        <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20">
                          AI Powered
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <ScrollArea className="flex-1 -mx-4 px-4">
                    <div className="space-y-3 pb-4">
                      {tool.args.map((arg, idx) => (
                        <div 
                          key={idx} 
                          className="p-4 bg-[#1E293B]/50 hover:bg-[#1E293B] border border-[#2D3B4E] hover:border-[#7C3AED]/30 rounded-lg transition-colors group"
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="space-y-2 min-w-0 flex-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="font-medium text-slate-200 break-all">{arg.name}</span>
                                <HoverCard>
                                  <HoverCardTrigger asChild>
                                    <Button variant="ghost" size="icon" className="h-5 w-5 p-0 text-slate-400 hover:text-slate-300 flex-shrink-0">
                                      <Info className="h-4 w-4" />
                                    </Button>
                                  </HoverCardTrigger>
                                  <HoverCardContent side="right" align="start" className="w-80">
                                    <div className="space-y-2">
                                      <h4 className="text-sm font-medium text-slate-200">Parameter Details</h4>
                                      <div className="space-y-1">
                                        <p className="text-xs text-slate-400">{arg.description}</p>
                                        <div className="pt-2 flex flex-wrap gap-2">
                                          {arg.type && (
                                            <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20">
                                              Type: {arg.type}
                                            </Badge>
                                          )}
                                          {arg.required && (
                                            <Badge variant="outline" className="bg-red-500/10 text-red-400 border-red-500/20">
                                                Required
                                            </Badge>
                                          )}
                                          {arg.default !== undefined && (
                                            <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
                                              Default: {JSON.stringify(arg.default)}
                                            </Badge>
                                          )}
                                        </div>
                                        {arg.enum && (
                                          <div className="pt-2">
                                            <span className="text-xs font-medium text-slate-300">Allowed Values:</span>
                                            <div className="mt-1 flex flex-wrap gap-1">
                                              {arg.enum.map((value, i) => (
                                                <Badge key={i} variant="outline" className="text-[10px]">
                                                  {JSON.stringify(value)}
                                                </Badge>
                                              ))}
                                            </div>
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  </HoverCardContent>
                                </HoverCard>
                              </div>
                              <p className="text-sm text-slate-400 break-words line-clamp-2 group-hover:line-clamp-none transition-all">
                                {arg.description}
                              </p>
                            </div>
                            <div className="flex items-start gap-2 flex-shrink-0 flex-wrap justify-end" style={{ minWidth: '120px' }}>
                              <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/20 whitespace-nowrap">
                                {arg.type}
                              </Badge>
                              {arg.required && (
                                <Badge variant="outline" className="bg-red-500/10 text-red-400 border-red-500/20 whitespace-nowrap">
                                  required
                                </Badge>
                              )}
                            </div>
                          </div>
                          {(arg.pattern || arg.min !== undefined || arg.max !== undefined || arg.minLength !== undefined || arg.maxLength !== undefined) && (
                            <div className="mt-3 pt-3 border-t border-[#2D3B4E] grid grid-cols-1 md:grid-cols-2 gap-3">
                              {arg.pattern && (
                                <div className="col-span-full">
                                  <span className="text-xs font-medium text-slate-300">Pattern:</span>
                                  <code className="ml-2 text-xs text-slate-400 font-mono bg-slate-800/50 px-1.5 py-0.5 rounded break-all">
                                    {arg.pattern}
                                  </code>
                                </div>
                              )}
                              {(arg.min !== undefined || arg.max !== undefined) && (
                                <div>
                                  <span className="text-xs font-medium text-slate-300">Range:</span>
                                  <span className="ml-2 text-xs text-slate-400">
                                    {arg.min !== undefined ? arg.min : '∞'} to {arg.max !== undefined ? arg.max : '∞'}
                                  </span>
                                </div>
                              )}
                              {(arg.minLength !== undefined || arg.maxLength !== undefined) && (
                                <div>
                                  <span className="text-xs font-medium text-slate-300">Length:</span>
                                  <span className="ml-2 text-xs text-slate-400">
                                    {arg.minLength !== undefined ? arg.minLength : '0'} to {arg.maxLength !== undefined ? arg.maxLength : '∞'} chars
                                  </span>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-[400px] p-6">
                  <div className="p-4 rounded-full bg-[#1E293B] border border-purple-500/20">
                    <MessageSquare className="h-8 w-8 text-purple-400" />
                  </div>
                  <h4 className="text-lg font-medium text-slate-200 mt-4">No Parameters Required</h4>
                  <p className="text-sm text-slate-400 mt-2 text-center max-w-md">
                    This tool can be executed directly without any additional input. Your AI Teammate will handle it automatically based on the context.
                  </p>
                </div>
              )}
            </div>
          </ScrollArea>
        );

      case 'source':
        return (
          <div className="space-y-4 p-4">
            {/* Source Details */}
            {source ? (
              <div className={cn(modalStyles.cards.container, "space-y-3")}>
                <h3 className={modalStyles.text.subtitle}>Source Information</h3>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <GitPullRequest className="h-4 w-4 text-purple-400" />
                    <span className={modalStyles.text.primary}>Repository URL:</span>
                    {source.url ? (
                      <a 
                        href={source.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 flex items-center gap-1"
                      >
                        {source.url}
                        <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    ) : (
                      <span className="text-slate-400">Not available</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <FolderTree className="h-4 w-4 text-purple-400" />
                    <span className="text-slate-200">Tool Path:</span>
                    <span className="text-blue-400">
                      {source.url?.split('/').pop() || source.name || 'Unknown'}
                    </span>
                    <Badge variant="outline" className="ml-2 text-xs bg-blue-500/10 text-blue-400 border-blue-500/20">
                      Directory in repository
                    </Badge>
                  </div>
                  {source.source_meta?.branch && (
                    <div className="flex items-center gap-2">
                      <GitBranch className="h-4 w-4 text-emerald-400" />
                      <span className={modalStyles.text.primary}>Branch: {source.source_meta.branch}</span>
                    </div>
                  )}
                  {source.source_meta?.commit && (
                    <div className="flex items-center gap-2">
                      <Hash className="h-4 w-4 text-emerald-400" />
                      <span className={modalStyles.text.primary}>
                        Commit: {source.source_meta.commit.slice(0, 7)}
                      </span>
                      {source.url?.includes('github.com') && (
                        <a 
                          href={`${source.url}/commit/${source.source_meta.commit}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:text-blue-300 flex items-center gap-1 text-sm"
                        >
                          View on GitHub
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                  )}
                  {source.source_meta?.committer && (
                    <div className="flex items-center gap-2">
                      <GitCommit className="h-4 w-4 text-emerald-400" />
                      <span className={modalStyles.text.primary}>Author: {source.source_meta.committer}</span>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className={cn(modalStyles.cards.container, "space-y-3")}>
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <GitPullRequest className="h-12 w-12 text-slate-400 mb-4" />
                  <h3 className="text-lg font-medium text-slate-200 mb-2">No Source Information</h3>
                  <p className="text-sm text-slate-400 max-w-md">
                    Source information is not available for this tool. This could be because the tool hasn't been installed yet or the source data is still loading.
                  </p>
                </div>
              </div>
            )}

            {/* Dynamic Configuration with null checks */}
            {source?.dynamic_config && Object.keys(source.dynamic_config).length > 0 && (
              <div className={cn(modalStyles.cards.container, "space-y-3")}>
                <h3 className={modalStyles.text.subtitle}>Dynamic Configuration</h3>
                <div className="space-y-2">
                  <div className="bg-[#1E1E1E] p-4 rounded-lg">
                    <pre className="text-sm text-slate-300 overflow-auto">
                      {JSON.stringify(source.dynamic_config, null, 2)}
                    </pre>
                  </div>
                  {source.runner && (
                    <div className="flex items-center gap-2 mt-2">
                      <Terminal className="h-4 w-4 text-purple-400" />
                      <span className={modalStyles.text.primary}>Runner: {source.runner}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        );

      case 'code':
        return (
          <div className="p-6 h-full">
            <div className="grid grid-cols-12 gap-4 h-full bg-[#1E293B] rounded-xl overflow-hidden">
              {/* File Browser - Made narrower */}
              <div className="col-span-4 border-r border-[#2D3B4E] flex flex-col">
                <div className="p-4 border-b border-[#2D3B4E] flex-shrink-0">
                  <h3 className="text-sm font-medium text-slate-200 flex items-center gap-2">
                    <FolderTree className="h-4 w-4 text-purple-400" />
                    Files
                  </h3>
                </div>
                <ScrollArea className="flex-1 p-2">
                  <FileTreeNode node={fileTree} onSelect={setSelectedFile} />
                </ScrollArea>
              </div>

              {/* Code Editor - Made wider */}
              <div className="col-span-8 flex flex-col">
                {selectedFile ? (
                  <>
                    {/* File Header */}
                    <div className="px-4 py-3 border-b border-[#2D3B4E] flex items-center justify-between flex-shrink-0">
                      <div className="flex items-center gap-3">
                        {getFileIcon(selectedFile.name, selectedFile.isInjected, selectedFile.isReserved)}
                        <span className="text-sm font-medium text-slate-200">{selectedFile.path}</span>
                        {selectedFile.isReserved && (
                          <HoverCard>
                            <HoverCardTrigger asChild>
                              <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20">
                                tool container entrypoint - startup script
                              </Badge>
                            </HoverCardTrigger>
                            <HoverCardContent className="w-80">
                              <div className="space-y-2">
                                <h5 className="text-sm font-medium text-slate-200">Container Entrypoint</h5>
                                <p className="text-xs text-slate-400">
                                  This script is executed when the tool container starts. It sets up the environment, 
                                  handles dependencies, and manages the tool's execution flow.
                                </p>
                              </div>
                            </HoverCardContent>
                          </HoverCard>
                        )}
                        {selectedFile.isInjected && (
                          <Badge variant="outline" className="bg-orange-500/10 text-orange-400 border-orange-500/20">
                            injected
                          </Badge>
                        )}
                      </div>
                    </div>
                    
                    {/* File Content */}
                    <div className="flex-1 min-h-0">
                      {selectedFile.isInjected ? (
                        <div className="flex items-center justify-center h-full text-slate-400 bg-[#1E1E1E] p-6">
                          <div className="text-center space-y-4 max-w-md">
                            <div className="p-3 rounded-full bg-orange-500/10 border border-orange-500/20 w-fit mx-auto">
                              <Lock className="h-6 w-6 text-orange-400" />
                            </div>
                            <div>
                              <h4 className="text-lg font-medium text-orange-400 mb-2">Runtime Injection Required</h4>
                              <p className="text-sm text-slate-400 mb-4">
                                This file will be dynamically injected when the tool is executed
                              </p>
                              <div className="space-y-2 text-left bg-[#1E293B] p-4 rounded-lg">
                                <div className="flex items-center gap-2">
                                  <FileText className="h-4 w-4 text-orange-400" />
                                  <span className="text-slate-300">Path: {selectedFile.path}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <GitFork className="h-4 w-4 text-orange-400" />
                                  <span className="text-slate-300">Source: {selectedFile.source}</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <Editor
                          height="100%"
                          theme="vs-dark"
                          language={getLanguageFromExtension(selectedFile.extension)}
                          value={selectedFile.content}
                          options={{
                            readOnly: true,
                            minimap: { enabled: true },
                            scrollBeyondLastLine: false,
                            fontSize: 13,
                            lineNumbers: 'on',
                            renderLineHighlight: 'all',
                            overviewRulerLanes: 0,
                            hideCursorInOverviewRuler: true,
                            scrollbar: {
                              vertical: 'visible',
                              horizontal: 'visible',
                              verticalScrollbarSize: 12,
                              horizontalScrollbarSize: 12
                            },
                            fontFamily: 'JetBrains Mono, Menlo, Monaco, Consolas, monospace',
                            fontLigatures: true
                          }}
                        />
                      )}
                    </div>
                  </>
                ) : (
                  <div className="flex items-center justify-center h-full text-slate-400 flex-col gap-4">
                    <div className="p-3 rounded-full bg-[#2D3B4E] border border-[#2D3B4E]">
                      <Code className="h-6 w-6 text-purple-400" />
                    </div>
                    <p>Select a file to view its contents</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 text-purple-400 animate-spin" />
            <p className={modalStyles.text.secondary}>Loading tool details...</p>
          </div>
        </div>
      );
    }

    if (error || !tool) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="flex flex-col items-center gap-3 text-red-400">
            <AlertCircle className="h-8 w-8" />
            <p>{error || 'Tool not found'}</p>
          </div>
        </div>
      );
    }

    return (
      <>
        <div className="border-b border-[#2A3347] px-6 flex-shrink-0">
          <div className="flex space-x-6">
            {[
              { id: 'overview', label: 'Overview', icon: File },
              { id: 'runtime', label: 'Runtime', icon: Terminal },
              { id: 'inputs', label: 'Inputs', icon: PackageOpen },
              { id: 'source', label: 'Source', icon: GitPullRequest },
              { id: 'code', label: 'Code', icon: Code }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "flex items-center gap-2 py-4 text-sm font-medium border-b-2 transition-colors",
                  activeTab === tab.id
                    ? "border-purple-400 text-purple-400"
                    : "border-transparent text-slate-400 hover:text-slate-300"
                )}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 min-h-0 overflow-hidden">
          {renderTabContent()}
        </div>
      </>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={onCloseAction}>
      <DialogContent 
        className={modalStyles.dialog.content}
        hideCloseButton
      >
        <DialogHeader className={modalStyles.dialog.header}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center w-12 h-12">
                {tool?.icon_url ? (
                  <img 
                    src={tool.icon_url} 
                    alt={tool?.name || 'Tool'} 
                    className="h-6 w-6 object-contain"
                    style={{ imageRendering: 'crisp-edges' }}
                  />
                ) : tool?.type === 'docker' ? (
                  <Ship className="h-6 w-6 text-emerald-400" />
                ) : (
                  <Code className="h-6 w-6 text-emerald-400" />
                )}
              </div>
              <div>
                <DialogTitle className={cn("text-2xl font-semibold", modalStyles.text.primary)}>
                  {tool?.name || 'Loading...'}
                </DialogTitle>
                <DialogDescription className={cn("text-base mt-2", modalStyles.text.secondary)}>
                  {tool?.description || 'Loading tool details...'}
                </DialogDescription>
              </div>
            </div>
            <Button
              variant="ghost"
              size="lg"
              className={modalStyles.buttons.ghost}
              onClick={onCloseAction}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
        </DialogHeader>

        <div className={modalStyles.dialog.body}>
          {renderContent()}
        </div>
      </DialogContent>
    </Dialog>
  );
} 