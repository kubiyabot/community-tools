"use client";

import * as React from 'react';
import { useState, useEffect, useCallback } from 'react';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import type { TeammateDetails } from '@/app/types/teammate';
import { 
  Loader2, 
  Info, 
  Code, 
  FolderGit, 
  ChevronRight, 
  Settings, 
  ArrowLeft, 
  Check,
  X,
  Ship,
  GitBranch,
  Clock,
  Terminal,
  Database,
  Key,
  Variable,
  FileJson,
  PackageOpen,
  GitPullRequest,
  AlertCircle,
  ExternalLink,
  Search,
  Box,
  Wrench,
  MessageSquare,
  RefreshCw
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../../ui/dialog";
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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../../ui/tooltip";
import { Button } from "../../ui/button";
import { Textarea } from "../../ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../ui/card";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../ui/tabs";
import { Badge } from "../../ui/badge";
import { Separator } from "../../ui/separator";
import { ScrollArea } from "../../ui/scroll-area";
import { HoverCard, HoverCardContent, HoverCardTrigger } from "../../ui/hover-card";
import { ToolDetailsModal } from "../tool-details/ToolDetailsModal";

const sourceFormSchema = z.object({
  url: z.string().url("Must be a valid URL"),
  name: z.string().optional().transform(val => val || ''),
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

export type SourceFormValues = z.infer<typeof sourceFormSchema>;

interface InstallToolFormProps {
  isOpen: boolean;
  onClose: () => void;
  onInstall: (values: SourceFormValues) => Promise<void>;
  teammate: TeammateDetails;
}

interface CommunityTool {
  name: string;
  path: string;
  description: string;
  tools_count: number;
  icon?: string;
  readme?: string;
  tools?: any[];
  isDiscovering?: boolean;
  error?: string;
  lastUpdated?: string;
  stars?: number;
}

interface GitHubContentsResponse {
  type: string;
  name: string;
  path: string;
  [key: string]: any;
}

interface Runner {
  name: string;
  description: string;
  runner_type: string;
}

interface ToolState {
  isLoading: boolean;
  error: string | null;
  data: any | null;
}

interface FormState {
  communityTools: {
    isLoading: boolean;
    error: string | null;
    data: CommunityTool[];
  };
  preview: ToolState;
  installation: {
    isLoading: boolean;
    error: string | null;
  };
}

interface Step {
  id: string;
  title: string;
  description: string;
  icon: React.ReactElement;
}

const STEPS: Step[] = [
  { 
    id: 'source', 
    title: 'Choose Source',
    description: 'Select a tool source from our community or add your own',
    icon: <GitBranch className="h-5 w-5" /> as React.ReactElement
  },
  { 
    id: 'preview', 
    title: 'Preview Tools',
    description: 'Review the available tools from this source',
    icon: <Search className="h-5 w-5" /> as React.ReactElement
  },
  { 
    id: 'configure', 
    title: 'Configure',
    description: 'Configure optional settings for installation',
    icon: <Settings className="h-5 w-5" /> as React.ReactElement
  }
];

// Styles object for consistent theming
const styles = {
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

const PYTHON_ICON_URL = 'https://www.svgrepo.com/show/376344/python.svg';

const CACHE_KEY = 'kubiya_community_tools_cache';
const CACHE_EXPIRY = 1000 * 60 * 60; // 1 hour

const getCachedTools = (): CommunityTool[] | null => {
  try {
    const cached = localStorage.getItem(CACHE_KEY);
    if (!cached) return null;
    
    const { data, timestamp } = JSON.parse(cached);
    if (Date.now() - timestamp > CACHE_EXPIRY) {
      localStorage.removeItem(CACHE_KEY);
      return null;
    }
    
    return data;
  } catch {
    return null;
  }
};

const setCachedTools = (tools: CommunityTool[]) => {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({
      data: tools,
      timestamp: Date.now()
    }));
  } catch {
    // Ignore storage errors
  }
};

export function InstallToolForm({ isOpen, onClose, onInstall, teammate }: InstallToolFormProps) {
  const [formState, setFormState] = useState<FormState>({
    communityTools: {
      isLoading: false,
      error: null,
      data: []
    },
    preview: {
      isLoading: false,
      error: null,
      data: null
    },
    installation: {
      isLoading: false,
      error: null
    }
  });

  const [selectedCommunityTool, setSelectedCommunityTool] = useState<CommunityTool | null>(null);
  const [selectedTool, setSelectedTool] = useState<any>(null);
  const [showToolDetails, setShowToolDetails] = useState(false);
  const [runners, setRunners] = useState<Runner[]>([]);
  const [currentStep, setCurrentStep] = useState<string>('source');

  const methods = useForm<SourceFormValues>({
    resolver: zodResolver(sourceFormSchema),
    defaultValues: {
      name: "",
      url: "",
      runner: teammate?.runners?.[0] || "kubiya-hosted",
      dynamic_config: "",
    },
  });

  useEffect(() => {
    // Fetch runners
    fetch('/api/v3/runners')
      .then(res => res.json())
      .then(data => setRunners(data))
      .catch(err => console.error('Failed to fetch runners:', err));

    // Initial fetch of community tools
    const fetchCommunityTools = async () => {
      try {
        setFormState(prev => ({
          ...prev,
          communityTools: {
            ...prev.communityTools,
            isLoading: true,
            error: null
          }
        }));
        
        // Try to get cached tools first
        const cached = getCachedTools();
        if (cached) {
          setFormState(prev => ({
            ...prev,
            communityTools: {
              isLoading: false,
              error: null,
              data: cached
            }
          }));
          return;
        }

        const response = await fetch('/api/v1/sources/community', {
          headers: {
            'Accept': 'application/json',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        });
        
        if (!response.ok) {
          const error = await response.json().catch(() => ({ error: 'Failed to fetch community tools' }));
          throw new Error(error.details || error.error || 'Failed to fetch community tools');
        }
        
        const tools = await response.json();
        if (!Array.isArray(tools)) {
          throw new Error('Invalid response format');
        }
        
        // Cache the tools
        setCachedTools(tools);
        
        setFormState(prev => ({
          ...prev,
          communityTools: {
            isLoading: false,
            error: null,
            data: tools
          }
        }));
      } catch (err) {
        console.error('Failed to fetch community tools:', err);
        setFormState(prev => ({
          ...prev,
          communityTools: {
            isLoading: false,
            error: err instanceof Error ? err.message : 'Failed to fetch community tools',
            data: []
          }
        }));
      }
    };

    fetchCommunityTools();
  }, []);

  const handleRefresh = useCallback(async () => {
    try {
      setFormState(prev => ({
        ...prev,
        communityTools: {
          ...prev.communityTools,
          isLoading: true,
          error: null
        }
      }));
      
      // Clear cache on manual refresh
      localStorage.removeItem(CACHE_KEY);
      
      const response = await fetch('/api/v1/sources/community', {
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Failed to fetch community tools' }));
        throw new Error(error.details || error.error || 'Failed to fetch community tools');
      }
      
      const tools = await response.json();
      if (!Array.isArray(tools)) {
        throw new Error('Invalid response format');
      }
      
      // Cache the new tools
      setCachedTools(tools);
      
      setFormState(prev => ({
        ...prev,
        communityTools: {
          isLoading: false,
          error: null,
          data: tools
        }
      }));
    } catch (err) {
      console.error('Failed to fetch community tools:', err);
      setFormState(prev => ({
        ...prev,
        communityTools: {
          isLoading: false,
          error: err instanceof Error ? err.message : 'Failed to fetch community tools',
          data: []
        }
      }));
    }
  }, []);

  const handlePreview = useCallback(async (url: string, runner?: string) => {
    try {
      setFormState(prev => ({
        ...prev,
        preview: {
          ...prev.preview,
          isLoading: true,
          error: null
        }
      }));

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);

      const response = await fetch(
        `/api/v1/sources/load?url=${encodeURIComponent(url)}&runner=${encodeURIComponent(runner || teammate?.runners?.[0] || 'kubiya-hosted')}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            dynamic_config: {}
          }),
          signal: controller.signal
        }
      );

      clearTimeout(timeoutId);

      let data;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const text = await response.text();
        try {
          data = JSON.parse(text);
        } catch {
          throw new Error(text || 'Failed to discover tools');
        }
      }

      if (!response.ok) {
        throw new Error(data.error || data.details || 'Failed to discover tools');
      }

      setFormState(prev => ({
        ...prev,
        preview: {
          isLoading: false,
          error: null,
          data: data
        }
      }));
    } catch (error) {
      console.error('Preview error:', error);
      setFormState(prev => ({
        ...prev,
        preview: {
          isLoading: false,
          error: error instanceof Error ? error.message : 'Failed to discover tools',
          data: null
        }
      }));
    }
  }, [teammate?.runners]);

  const handleSubmit = async (values: SourceFormValues) => {
    try {
      setFormState(prev => ({
        ...prev,
        installation: {
          isLoading: true,
          error: null
        }
      }));

      await onInstall({
        ...values,
        name: values.name || getSourceNameFromUrl(values.url),
      });
      onClose();
    } catch (error) {
      console.error('Failed to install tool:', error);
      setFormState(prev => ({
        ...prev,
        installation: {
          isLoading: false,
          error: error instanceof Error ? error.message : 'Failed to install tools'
        }
      }));
    }
  };

  const getSourceNameFromUrl = (url: string): string => {
    try {
      const urlObj = new URL(url);
      if (urlObj.hostname === 'github.com') {
        const parts = urlObj.pathname.split('/');
        if (parts.length >= 3) {
          return `${parts[1]}-${parts[2]}`;
        }
      }
      return urlObj.hostname;
    } catch {
      return '';
    }
  };

  const discoverTools = async (tool: CommunityTool) => {
    const cacheKey = `kubiya_tool_discovery_${tool.path}`;
    try {
      // Check cache first
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < CACHE_EXPIRY) {
          setFormState(prev => ({
            ...prev,
            communityTools: {
              ...prev.communityTools,
              data: prev.communityTools.data.map(t => t.name === tool.name ? {
                ...t,
                tools: data.tools || [],
                tools_count: (data.tools || []).length
              } : t)
            }
          }));
          return data;
        }
      }

      // Update tool state to show discovering
      setFormState(prev => ({
        ...prev,
        communityTools: {
          ...prev.communityTools,
          data: prev.communityTools.data.map(t => t.name === tool.name ? { ...t, isDiscovering: true, error: undefined } : t)
        }
      }));

      const response = await fetch(`/api/v1/sources/load?url=${encodeURIComponent(`https://github.com/kubiyabot/community-tools/tree/main/${tool.path}`)}&runner=${encodeURIComponent(teammate?.runners?.[0] || 'kubiya-hosted')}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          dynamic_config: {}
        })
      });

      let data;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const text = await response.text();
        try {
          data = JSON.parse(text);
        } catch {
          throw new Error(text || 'Failed to discover tools');
        }
      }

      if (!response.ok) {
        throw new Error(data.error || data.details || 'Failed to discover tools');
      }

      // Ensure we have a valid tools array
      const tools = Array.isArray(data.tools) ? data.tools :
                   Array.isArray(data) ? data :
                   [];

      const formattedData = {
        tools,
        source: {
          url: `https://github.com/kubiyabot/community-tools/tree/main/${tool.path}`,
          runner: teammate?.runners?.[0] || 'kubiya-hosted'
        }
      };

      // Cache the discovered tools
      localStorage.setItem(cacheKey, JSON.stringify({
        data: formattedData,
        timestamp: Date.now()
      }));

      // Update tool with discovered tools
      setFormState(prev => ({
        ...prev,
        communityTools: {
          ...prev.communityTools,
          data: prev.communityTools.data.map(t => t.name === tool.name ? {
            ...t,
            isDiscovering: false,
            tools: formattedData.tools,
            tools_count: formattedData.tools.length
          } : t)
        }
      }));

      return formattedData;
    } catch (error) {
      console.error('Discovery error:', error);
      setFormState(prev => ({
        ...prev,
        communityTools: {
          ...prev.communityTools,
          data: prev.communityTools.data.map(t => t.name === tool.name ? {
            ...t,
            isDiscovering: false,
            error: error instanceof Error ? error.message : 'Failed to discover tools'
          } : t)
        }
      }));
      throw error;
    }
  };

  const handleCommunityToolSelect = async (tool: CommunityTool) => {
    setSelectedCommunityTool(tool);
    
    if (!tool.tools) {
      try {
        const data = await discoverTools(tool);
        if (data && (Array.isArray(data.tools) || Array.isArray(data))) {
          setFormState(prev => ({
            ...prev,
            preview: {
              ...prev.preview,
              data: {
                tools: data.tools || data,
                source: {
                  url: `https://github.com/kubiyabot/community-tools/tree/main/${tool.path}`,
                  runner: teammate?.runners?.[0] || 'kubiya-hosted'
                }
              }
            }
          }));
        } else {
          console.error('Invalid response format:', data);
          throw new Error('Invalid response format from server');
        }
      } catch (error) {
        console.error('Failed to discover tools:', error);
        setFormState(prev => ({
          ...prev,
          preview: {
            ...prev.preview,
            error: error instanceof Error ? error.message : 'Failed to discover tools'
          }
        }));
      }
    } else {
      setFormState(prev => ({
        ...prev,
        preview: {
          ...prev.preview,
          data: {
            tools: tool.tools,
            source: {
              url: `https://github.com/kubiyabot/community-tools/tree/main/${tool.path}`,
              runner: teammate?.runners?.[0] || 'kubiya-hosted'
            }
          }
        }
      }));
    }
  };

  const renderCommunityToolCard = (tool: CommunityTool) => {
    const hasPythonCode = tool.tools?.some(t => t.files?.some((file: string) => file.endsWith('.py'))) || false;
    const isSelected = selectedCommunityTool?.name === tool.name;
    
    return (
      <Card
        key={tool.name}
        className={cn(
          styles.cards.base,
          "cursor-pointer transition-all duration-200 group overflow-hidden",
          isSelected ? "ring-2 ring-purple-500 border-purple-500" : "hover:border-purple-500/30",
          tool.error && "border-red-500/30"
        )}
        onClick={() => handleCommunityToolSelect(tool)}
      >
        <CardHeader className="flex flex-row items-start gap-4 p-4">
          <div className={cn(
            "p-2 rounded-md transition-colors",
            isSelected ? "bg-purple-500/20" : "bg-purple-500/10",
            "border border-purple-500/20"
          )}>
            {tool.icon ? (
              <img src={tool.icon} alt={tool.name} className="h-8 w-8" />
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
                {hasPythonCode && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className="flex items-center">
                          <img 
                            src={PYTHON_ICON_URL} 
                            alt="Python" 
                            className="h-5 w-5 opacity-70 hover:opacity-100 transition-opacity"
                          />
                        </div>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="bg-slate-800 text-slate-200 text-xs">
                        Built using Kubiya Python SDK
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
                {isSelected && (
                  <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/20">
                    Selected
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-2">
                {tool.stars !== undefined && (
                  <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/20">
                    ★ {tool.stars}
                  </Badge>
                )}
                {tool.tools_count > 0 && (
                  <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/20">
                    {tool.tools_count} tools
                  </Badge>
                )}
              </div>
            </div>
            <CardDescription className="text-slate-400 mt-1">
              {tool.description}
            </CardDescription>
            {tool.readme && (
              <div className="mt-2 text-xs text-slate-400 line-clamp-2">
                {tool.readme.split('\n')[0]}
              </div>
            )}
            {tool.lastUpdated && (
              <div className="mt-2 flex items-center gap-2 text-xs text-slate-500">
                <Clock className="h-3 w-3" />
                Updated {new Date(tool.lastUpdated).toLocaleDateString()}
              </div>
            )}
          </div>
        </CardHeader>
        {isSelected && tool.tools && (
          <div className="border-t border-[#2A3347] p-4 bg-[#1E293B]/50">
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-purple-400 flex items-center gap-2">
                <Wrench className="h-4 w-4" />
                Available Tools
              </h4>
              <div className="grid grid-cols-1 gap-2 max-h-48 overflow-y-auto pr-2">
                {tool.tools.map((t: any) => (
                  <div 
                    key={t.name}
                    className="flex items-start gap-3 p-2 rounded-md bg-[#0F172A]/50 border border-[#2A3347] hover:border-purple-500/30 transition-colors"
                  >
                    <div className="p-1.5 rounded-md bg-purple-500/10 border border-purple-500/20">
                      <Code className="h-4 w-4 text-purple-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-slate-200">{t.name}</p>
                        {t.type && (
                          <Badge variant="outline" className="text-xs bg-purple-500/10 text-purple-400 border-purple-500/20">
                            {t.type}
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">{t.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </Card>
    );
  };

  const renderToolCard = (tool: any, isPreview = false) => {
    const hasPythonCode = tool.files?.some((file: string) => file.endsWith('.py')) || false;
    
    return (
      <Card
        key={tool.name}
        className={cn(
          styles.cards.base,
          "cursor-pointer transition-all duration-200 group relative",
          isPreview ? "hover:border-emerald-500/30" : "hover:border-purple-500/30"
        )}
        onClick={() => setSelectedTool(tool)}
      >
        <CardHeader className="flex flex-row items-start gap-4 p-4">
          <div className={cn(
            "p-2 rounded-md border transition-colors",
            isPreview 
              ? "bg-emerald-500/10 border-emerald-500/20" 
              : "bg-purple-500/10 border-purple-500/20"
          )}>
            {tool.icon_url ? (
              <img src={tool.icon_url} alt={tool.name} className="h-5 w-5" />
            ) : (
              <Code className={cn(
                "h-5 w-5",
                isPreview ? "text-emerald-400" : "text-purple-400"
              )} />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CardTitle className="text-sm font-medium text-slate-200">
                  {tool.name}
                </CardTitle>
                {hasPythonCode && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className="flex items-center">
                          <img 
                            src={PYTHON_ICON_URL} 
                            alt="Python" 
                            className="h-4 w-4 opacity-70 hover:opacity-100 transition-opacity"
                          />
                        </div>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="bg-slate-800 text-slate-200 text-xs">
                        Built using Kubiya Python SDK
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </div>
              <div className="flex items-center gap-2">
                {tool.type && (
                  <Badge 
                    variant="outline" 
                    className={cn(
                      "text-xs",
                      isPreview 
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        : "bg-purple-500/10 text-purple-400 border-purple-500/20"
                    )}
                  >
                    {tool.type}
                  </Badge>
                )}
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedTool(tool);
                    setShowToolDetails(true);
                  }}
                >
                  <Info className="h-4 w-4 text-slate-400" />
                </Button>
              </div>
            </div>
            <CardDescription className="text-xs text-slate-400 mt-1 line-clamp-2">
              {tool.description}
            </CardDescription>
            {tool.args && tool.args.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {tool.args.map((arg: any, index: number) => (
                  <Badge 
                    key={index}
                    variant="outline" 
                    className="text-[10px] bg-slate-800/50 text-slate-400 border-slate-700"
                  >
                    {arg.name}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </CardHeader>
      </Card>
    );
  };

  const renderRunnerSelect = () => (
    <FormField
      control={methods.control}
      name="runner"
      render={({ field }) => (
        <FormItem>
          <FormLabel className="text-slate-200 flex items-center gap-2">
            Runner
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Info className="h-4 w-4 text-slate-400" />
                </TooltipTrigger>
                <TooltipContent className="max-w-sm p-4 bg-[#1E293B] border border-[#2D3B4E]">
                  <div className="space-y-2">
                    <h4 className="font-medium text-slate-200">What is a Runner?</h4>
                    <p className="text-sm text-slate-400">A runner is a Kubernetes-based executor that clones and processes your repository to extract tools. It handles the discovery and validation of your tools.</p>
                    <div className="flex items-center gap-2 mt-2 pt-2 border-t border-[#2D3B4E]">
                      <img src="/kubernetes-icon.svg" alt="Kubernetes" className="h-4 w-4" />
                      <span className="text-xs text-slate-400">Runs on Kubernetes</span>
                    </div>
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </FormLabel>
          <FormControl>
            <Select onValueChange={field.onChange} defaultValue={field.value}>
              <SelectTrigger className="bg-[#1E293B] border-[#2D3B4E] text-slate-200">
                <SelectValue placeholder="Select a runner" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="kubiya-hosted" className="flex items-center gap-2">
                  <Ship className="h-4 w-4 text-purple-400" />
                  <span>Kubiya Hosted Runner</span>
                </SelectItem>
                {runners.map((runner: Runner) => (
                  <SelectItem key={runner.name} value={runner.name} className="flex items-center gap-2">
                    <Terminal className="h-4 w-4 text-slate-400" />
                    <span>{runner.name}</span>
                    {teammate?.runners?.includes(runner.name) && (
                      <Badge className="ml-2 bg-purple-500/10 text-purple-400 border-purple-500/20">
                        Default
                      </Badge>
                    )}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormControl>
          <FormDescription className="text-slate-400 flex items-center gap-2">
            {field.value === 'kubiya-hosted' ? (
              <>
                <Ship className="h-3.5 w-3.5 text-purple-400" />
                <span>Managed by Kubiya - recommended for most users</span>
              </>
            ) : (
              <>
                <Terminal className="h-3.5 w-3.5 text-slate-400" />
                <span>Self-hosted runner in your cluster</span>
              </>
            )}
          </FormDescription>
        </FormItem>
      )}
    />
  );

  const renderCommunityToolsContent = () => {
    const { isLoading, error, data } = formState.communityTools;

    if (isLoading) {
      return (
        <div className="flex flex-col items-center justify-center gap-4 p-8">
          <div className="relative flex flex-col items-center">
            <div className="relative">
              <div className="absolute inset-0 animate-ping rounded-full bg-purple-400/20" />
              <Loader2 className="h-8 w-8 text-purple-400 animate-spin relative" />
            </div>
            <div className="mt-4 text-center">
              <p className="text-sm font-medium text-slate-200">Loading Community Tools</p>
              <p className="text-xs text-slate-400 mt-1">Fetching available tools from the official community repository...</p>
            </div>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex flex-col items-center justify-center gap-4 p-8 text-center">
          <AlertCircle className="h-8 w-8 text-red-400" />
          <div>
            <p className="text-sm font-medium text-slate-200">Failed to Load Tools</p>
            <p className="text-sm text-slate-400 mt-1">{error}</p>
          </div>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => handleRefresh()}
            className="mt-2"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      );
    }

    if (data.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center gap-4 p-8 text-center">
          <Box className="h-8 w-8 text-slate-400" />
          <div>
            <p className="text-sm font-medium text-slate-200">No Community Tools Available</p>
            <p className="text-sm text-slate-400 mt-1">Please try again later or use a custom source.</p>
          </div>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => handleRefresh()}
            className="mt-2"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-2 gap-4 relative">
        {data.map(tool => (
          <div key={tool.name} className="relative">
            {tool.isDiscovering && (
              <div className="absolute inset-0 z-10 bg-[#0F172A]/90 backdrop-blur-sm rounded-lg flex items-center justify-center">
                <div className="flex flex-col items-center gap-3 p-4 text-center">
                  <div className="relative">
                    <div className="absolute inset-0 animate-ping rounded-full bg-purple-400/20" />
                    <Loader2 className="h-8 w-8 text-purple-400 animate-spin relative" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-purple-400">Reading Code</p>
                    <p className="text-xs text-purple-400/70 mt-1">Analyzing tool definitions...</p>
                  </div>
                </div>
              </div>
            )}
            {renderCommunityToolCard(tool)}
          </div>
        ))}
      </div>
    );
  };

  const renderPreviewContent = () => {
    const { isLoading, error, data } = formState.preview;

    if (isLoading) {
      return (
        <div className="flex flex-col items-center justify-center gap-4 p-8">
          <div className="relative flex flex-col items-center">
            <div className="relative">
              <div className="absolute inset-0 animate-ping rounded-full bg-emerald-400/20" />
              <Loader2 className="h-8 w-8 text-emerald-400 animate-spin relative" />
            </div>
            <div className="mt-4 text-center">
              <p className="text-sm font-medium text-slate-200">Discovering Tools</p>
              <p className="text-xs text-slate-400 mt-1">Analyzing repository and extracting tool definitions...</p>
              <div className="flex items-center justify-center gap-2 mt-4">
                <div className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <div className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse delay-100" />
                <div className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse delay-200" />
              </div>
            </div>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-400 mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-red-400">Error Loading Tools</p>
              <p className="text-sm text-red-400/80">{error}</p>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => handlePreview(methods.getValues('url'), methods.getValues('runner'))}
                className="mt-2"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          </div>
        </div>
      );
    }

    if (!data?.tools?.length) {
      return (
        <div className="flex flex-col items-center justify-center gap-4 p-8 text-center">
          <Box className="h-8 w-8 text-slate-400" />
          <div>
            <p className="text-sm font-medium text-slate-200">No Tools Found</p>
            <p className="text-sm text-slate-400 mt-1">
              This source doesn't contain any compatible tools.
            </p>
          </div>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-2 gap-4">
        {data.tools.map((tool: any) => renderToolCard(tool, true))}
      </div>
    );
  };

  const goToNextStep = useCallback(() => {
    const currentIndex = STEPS.findIndex(step => step.id === currentStep);
    if (currentIndex < STEPS.length - 1) {
      setCurrentStep(STEPS[currentIndex + 1].id);
    }
  }, [currentStep]);

  const goToPreviousStep = useCallback(() => {
    const currentIndex = STEPS.findIndex(step => step.id === currentStep);
    if (currentIndex > 0) {
      setCurrentStep(STEPS[currentIndex - 1].id);
    }
  }, [currentStep]);

  const canProceed = useCallback(() => {
    switch (currentStep) {
      case 'source':
        const toolsLength = selectedCommunityTool?.tools?.length ?? 0;
        return (selectedCommunityTool && toolsLength > 0) || 
               (methods.getValues('url') && !formState.preview.isLoading);
      case 'preview':
        return formState.preview.data?.tools?.length > 0;
      case 'configure':
        return true;
      default:
        return false;
    }
  }, [currentStep, selectedCommunityTool, formState.preview, methods]);

  const StepIndicator = () => (
    <div className="mb-6 px-6">
      <div className="flex items-center justify-between">
        {STEPS.map((step, index) => (
          <React.Fragment key={step.id}>
            <div className="flex items-center">
              <div 
                className={cn(
                  "flex items-center justify-center w-10 h-10 rounded-full border-2",
                  currentStep === step.id 
                    ? "bg-purple-500/10 border-purple-500 text-purple-400"
                    : index < STEPS.findIndex(s => s.id === currentStep)
                      ? "bg-emerald-500/10 border-emerald-500 text-emerald-400"
                      : "bg-slate-800/50 border-slate-700 text-slate-400"
                )}
              >
                {step.icon}
              </div>
              <div className="ml-3">
                <p className={cn(
                  "text-sm font-medium",
                  currentStep === step.id 
                    ? "text-purple-400"
                    : index < STEPS.findIndex(s => s.id === currentStep)
                      ? "text-emerald-400"
                      : "text-slate-400"
                )}>
                  {step.title}
                </p>
                <p className="text-xs text-slate-500">{step.description}</p>
              </div>
            </div>
            {index < STEPS.length - 1 && (
              <div className="flex-1 mx-4">
                <div className={cn(
                  "h-0.5 w-full",
                  index < STEPS.findIndex(s => s.id === currentStep)
                    ? "bg-emerald-500/30"
                    : "bg-slate-700"
                )} />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );

  const StepContent = () => {
    switch (currentStep) {
      case 'source':
        return (
          <div className="space-y-6">
            <Tabs defaultValue="community" className="w-full">
              <TabsList className="w-full grid grid-cols-2">
                <TabsTrigger 
                  value="community" 
                  className="flex items-center gap-2"
                  disabled={formState.communityTools.isLoading || Boolean(selectedCommunityTool?.isDiscovering)}
                >
                  <GitBranch className="h-4 w-4" />
                  Community Tools
                  {formState.communityTools.isLoading && (
                    <Loader2 className="h-3 w-3 animate-spin ml-2" />
                  )}
                </TabsTrigger>
                <TabsTrigger 
                  value="custom" 
                  className="flex items-center gap-2"
                  disabled={formState.communityTools.isLoading || Boolean(selectedCommunityTool?.isDiscovering)}
                >
                  <GitPullRequest className="h-4 w-4" />
                  Custom Source
                </TabsTrigger>
              </TabsList>

              <TabsContent value="community" className="mt-6">
                {renderCommunityToolsContent()}
              </TabsContent>

              <TabsContent value="custom" className="mt-6">
                <Card className={cn(
                  styles.cards.base,
                  formState.preview.isLoading && "opacity-50 pointer-events-none"
                )}>
                  <CardContent className="space-y-4 p-6">
                    <FormField
                      control={methods.control}
                      name="url"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-slate-200">Source URL</FormLabel>
                          <FormControl>
                            <div className="relative">
                              <Input 
                                placeholder="https://github.com/org/repo" 
                                {...field}
                                className="bg-[#1E293B] border-[#2D3B4E] text-slate-200 pr-10"
                                disabled={formState.preview.isLoading}
                              />
                              {formState.preview.isLoading && (
                                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                                  <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
                                </div>
                              )}
                            </div>
                          </FormControl>
                          <FormDescription className="text-slate-400">
                            URL to the Git repository containing the tools
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    {renderRunnerSelect()}
                  </CardContent>
                </Card>
                {formState.preview.data?.tools && (
                  <div className="mt-6">
                    <Card className={styles.cards.base}>
                      <CardHeader>
                        <CardTitle className="text-lg text-slate-200 flex items-center gap-2">
                          <Wrench className="h-5 w-5 text-purple-400" />
                          Available Tools
                        </CardTitle>
                        <CardDescription>
                          {formState.preview.data.tools.length} tools found in repository
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-1 gap-3">
                          {formState.preview.data.tools.map((tool: any) => (
                            <div 
                              key={tool.name}
                              className="flex items-start gap-3 p-3 rounded-md bg-[#0F172A]/50 border border-[#2A3347] hover:border-purple-500/30 transition-colors"
                            >
                              <div className="p-2 rounded-md bg-purple-500/10 border border-purple-500/20">
                                <Code className="h-5 w-5 text-purple-400" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between">
                                  <p className="text-sm font-medium text-slate-200">{tool.name}</p>
                                  {tool.type && (
                                    <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/20">
                                      {tool.type}
                                    </Badge>
                                  )}
                                </div>
                                <p className="text-sm text-slate-400 mt-1">{tool.description}</p>
                                {tool.args && tool.args.length > 0 && (
                                  <div className="flex flex-wrap gap-1.5 mt-2">
                                    {tool.args.map((arg: any) => (
                                      <Badge 
                                        key={arg.name}
                                        variant="outline" 
                                        className="text-xs bg-slate-800/50 text-slate-400 border-slate-700"
                                      >
                                        {arg.name}
                                      </Badge>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </div>
        );
      
      case 'preview':
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={cn(
                  "p-2 rounded-md transition-colors",
                  formState.preview.isLoading 
                    ? "bg-emerald-500/10 border border-emerald-500/20" 
                    : "bg-purple-500/10 border border-purple-500/20"
                )}>
                  <PackageOpen className={cn(
                    "h-5 w-5",
                    formState.preview.isLoading ? "text-emerald-400" : "text-purple-400"
                  )} />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-slate-200">
                    {formState.preview.isLoading ? "Discovering Tools" : "Available Tools"}
                  </h3>
                  <p className="text-sm text-slate-400">
                    {formState.preview.isLoading 
                      ? "Analyzing repository and extracting tools..." 
                      : `${formState.preview.data?.tools?.length || 0} tools found`
                    }
                  </p>
                </div>
              </div>
            </div>
            {renderPreviewContent()}
          </div>
        );
      
      case 'configure':
        return (
          <div className="space-y-6">
            <Card className={styles.cards.base}>
              <CardHeader>
                <CardTitle className="text-lg text-slate-200 flex items-center gap-2">
                  <Settings className="h-5 w-5 text-purple-400" />
                  Advanced Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {renderRunnerSelect()}
                <FormField
                  control={methods.control}
                  name="dynamic_config"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-slate-200">Dynamic Configuration</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="{}"
                          className="font-mono bg-[#1E293B] border-[#2D3B4E] text-slate-200"
                          {...field}
                        />
                      </FormControl>
                      <FormDescription className="text-slate-400">
                        Optional JSON configuration for the source
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </CardContent>
            </Card>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <>
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className={styles.dialog.content}>
          <FormProvider {...methods}>
            <DialogHeader className={styles.dialog.header}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
                    <PackageOpen className="h-6 w-6 text-purple-400" />
                  </div>
                  <div>
                    <DialogTitle className="text-xl font-semibold text-slate-200">
                      Install Tools
                    </DialogTitle>
                    <DialogDescription className="text-slate-400 mt-1">
                      Add tools to your teammate from a Git repository or choose from our community tools.
                    </DialogDescription>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className={styles.buttons.ghost}
                  onClick={onClose}
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>
            </DialogHeader>

            <div className={styles.dialog.body}>
              <StepIndicator />
              
              <ScrollArea className="flex-1">
                <div className="p-6">
                  <StepContent />
                </div>
              </ScrollArea>

              <DialogFooter className="p-6 border-t border-[#2A3347]">
                <div className="flex justify-between w-full">
                  {currentStep === 'source' ? (
                    <Button
                      type="button"
                      variant="outline"
                      onClick={onClose}
                      className="bg-[#1E293B] border-[#2D3B4E] text-slate-200 hover:bg-[#2D3B4E]"
                    >
                      Cancel
                    </Button>
                  ) : (
                    <Button
                      type="button"
                      variant="outline"
                      onClick={goToPreviousStep}
                      className="bg-[#1E293B] border-[#2D3B4E] text-slate-200 hover:bg-[#2D3B4E]"
                    >
                      <ArrowLeft className="h-4 w-4 mr-2" />
                      Back
                    </Button>
                  )}
                  
                  {currentStep === 'configure' ? (
                    <Button
                      type="submit"
                      className={styles.buttons.primary}
                      disabled={formState.installation.isLoading || !canProceed()}
                      onClick={methods.handleSubmit(handleSubmit)}
                    >
                      {formState.installation.isLoading ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Installing...
                        </>
                      ) : (
                        <>
                          <Check className="h-4 w-4 mr-2" />
                          Install Tools
                        </>
                      )}
                    </Button>
                  ) : (
                    <Button
                      type="button"
                      className={styles.buttons.primary}
                      disabled={!canProceed()}
                      onClick={goToNextStep}
                    >
                      Continue
                      <ChevronRight className="h-4 w-4 ml-2" />
                    </Button>
                  )}
                </div>
              </DialogFooter>
            </div>
          </FormProvider>
        </DialogContent>
      </Dialog>

      {/* Tool Details Modal */}
      {selectedTool && showToolDetails && (
        <ToolDetailsModal
          isOpen={showToolDetails}
          onCloseAction={() => {
            setShowToolDetails(false);
            setSelectedTool(null);
          }}
          tool={selectedTool}
          source={formState.preview.data?.source}
        />
      )}
    </>
  );
} 