"use client";

import React from 'react';
import { useState, useEffect, useRef } from 'react';
import { Button } from '../ui/button';
import { 
  ChevronDown, ChevronUp, Terminal, Info, Box, X, ExternalLink, GitBranch, FileCode,
  Container, GitPullRequest, Wrench, Settings, Search, Loader2, Link2, GitCommit,
  AlertCircle, Code2, Database, Globe, GitMerge, Key, Lock, Variable, Layers, FolderGit,
  RefreshCw, User, Calendar, Brain
} from 'lucide-react';
import dynamic from 'next/dynamic';
import { Dialog, DialogContent, DialogTitle } from '../ui/dialog';
import { toast } from '../ui/use-toast';
import { motion, AnimatePresence, LazyMotion, domAnimation } from 'framer-motion';
import type { Variants } from 'framer-motion';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

const languages = {
  python: dynamic(() => import('react-syntax-highlighter/dist/esm/languages/prism/python')),
  javascript: dynamic(() => import('react-syntax-highlighter/dist/esm/languages/prism/javascript')),
  yaml: dynamic(() => import('react-syntax-highlighter/dist/esm/languages/prism/yaml')),
  dockerfile: dynamic(() => import('react-syntax-highlighter/dist/esm/languages/prism/docker')),
  hcl: dynamic(() => import('react-syntax-highlighter/dist/esm/languages/prism/hcl')),
};

interface Teammate {
  uuid: string;
  name: string;
  description?: string;
  llm_model?: string;
  instruction_type?: string;
  environment_variables?: Record<string, string>;
  integrations?: string[];
  runners?: string[];
  sources?: string[];
  allowed_groups?: string[];
  allowed_users?: string[];
  image?: string;
  is_debug_mode?: boolean;
  metadata?: {
    created_at?: string;
    last_updated?: string;
    user_created?: string;
    user_last_updated?: string;
  };
}

interface Source {
  sourceId: string;
  name?: string;
}

interface ToolFile {
  source: string;
  target: string;
  content?: string;
}

interface SourceMetadata {
  sourceId: string;
  metadata: {
    tools?: Array<{
      name: string;
      description: string;
      type?: string;
      icon_url?: string;
      content?: string;
      source?: {
        id: string;
        url: string;
        commit?: string;
        committer?: string;
        branch?: string;
      };
      args?: Array<{
        name: string;
        type: string;
        description?: string;
        required?: boolean;
      }>;
      env?: Record<string, string> | null;
      image?: string;
      mermaid?: string;
      with_files?: Array<ToolFile>;
      with_volumes?: Array<{
        source: string;
        target: string;
      }> | null;
      metadata?: {
        git_url?: string;
        git_branch?: string;
        git_path?: string;
        git_commit?: string;
        git_author?: string;
        docker_image?: string;
        repository?: string;
        entrypoint?: string;
        last_updated?: string;
      };
      errors?: Array<{
        file: string;
        type: string;
        error: string;
        details: string;
      }>;
    }>;
    name?: string;
    description?: string;
    repository?: string;
    errors?: Array<{
      file: string;
      type: string;
      error: string;
      details: string;
    }>;
    connected_agents_count: number;
    connected_tools_count: number;
    connected_workflows_count: number;
    errors_count: number;
    last_updated?: string;
    source_meta?: {
      id: string;
      url: string;
      branch: string;
      commit: string;
      committer: string;
    };
    kubiya_metadata?: {
      created_at: string;
      last_updated: string;
      user_created?: string;
      user_last_updated?: string;
    };
  };
}

interface GitMetadata {
  commit?: string;
  branch?: string;
  lastUpdated?: string;
  author?: string;
  repository?: string;
}

interface TeammateDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  teammate: Teammate | null;
  capabilities: {
    llm_model?: string;
    instruction_type?: string;
    runner?: string;
    integrations?: Array<string | { name: string; type: string }>;
  };
}

interface IntegrationConfig {
  name: string;
  is_default: boolean;
}

interface Integration {
  uuid: string;
  name: string;
  description?: string;
  integration_type: string;
  auth_type: string;
  managed_by: string;
  configs: Array<{
    name: string;
    is_default: boolean;
  }>;
  kubiya_metadata: {
    created_at: string;
    last_updated: string;
    user_created?: string;
    user_last_updated?: string;
  };
}

interface SourceMeta {
  id: string;
  url: string;
  branch?: string;
  commit?: string;
  committer?: string;
}

interface SourceDetails {
  uuid: string;
  name: string;
  url: string;
  connected_agents_count: number;
  connected_tools_count: number;
  connected_workflows_count: number;
  errors_count: number;
  kubiya_metadata: {
    created_at: string;
    last_updated: string;
  };
  source_meta: SourceMeta;
}

// Add new interface for sync state
interface SyncState {
  isLoading: boolean;
  error: string | null;
  lastSync?: string;
}

// Add new type for tool metadata
interface ToolMetadata {
  git_url?: string;
  git_branch?: string;
  git_path?: string;
  git_commit?: string;
  git_author?: string;
  docker_image?: string;
  repository?: string;
  entrypoint?: string;
  last_updated?: string;
}

// Update the integration types
interface IntegrationType {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  features?: string[];
  docs_url?: string;
  resourceTypes?: string[];
  permissions?: string[];
  regions?: string[];
}

interface ToolArgument {
  name: string;
  type: string;
  description?: string;
  required?: boolean;
}

const INTEGRATION_TYPES: Record<string, IntegrationType> = {
  aws: {
    id: 'aws',
    name: 'AWS',
    description: 'Access AWS services and resources through AWS SDK',
    icon: 'https://uxwing.com/wp-content/themes/uxwing/download/brands-and-social-media/aws-icon.png',
    color: 'orange',
    features: ['EC2', 'S3', 'Lambda', 'ECS', 'EKS', 'IAM', 'CloudWatch', 'RDS'],
    resourceTypes: [
      'Compute', 'Storage', 'Database', 'Networking',
      'Security', 'Analytics', 'Containers', 'Serverless'
    ],
    permissions: [
      'Read', 'Write', 'List', 'Delete',
      'Create', 'Describe', 'Monitor', 'Manage'
    ],
    regions: ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1'],
    docs_url: 'https://docs.aws.amazon.com'
  },
  kubernetes: {
    id: 'kubernetes',
    name: 'Kubernetes',
    description: 'In-cluster access via Kubiya Operator',
    icon: 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Kubernetes_logo_without_workmark.svg/2109px-Kubernetes_logo_without_workmark.svg.png',
    color: 'blue',
    features: ['Pods', 'Services', 'Deployments', 'ConfigMaps', 'Secrets'],
    docs_url: 'https://kubernetes.io/docs'
  },
  github: {
    id: 'github',
    name: 'GitHub',
    description: 'Interact with GitHub repositories, issues, and pull requests',
    icon: 'https://cdn-icons-png.flaticon.com/512/25/25231.png',
    color: 'slate',
    features: ['Repositories', 'Issues', 'Pull Requests', 'Actions', 'Webhooks'],
    docs_url: 'https://docs.github.com/en/rest'
  },
  slack: {
    id: 'slack',
    name: 'Slack',
    description: 'Send messages and interact with Slack channels',
    icon: 'https://cdn4.iconfinder.com/data/icons/logos-and-brands/512/306_Slack_logo-512.png',
    color: 'purple',
    features: ['Messages', 'Channels', 'Users', 'Files', 'Apps'],
    docs_url: 'https://api.slack.com/docs'
  },
  jira: {
    id: 'jira',
    name: 'Jira',
    description: 'Manage Jira issues and projects',
    icon: 'https://cdn-icons-png.flaticon.com/512/5968/5968875.png',
    color: 'blue',
    features: ['Issues', 'Projects', 'Sprints', 'Boards', 'Users'],
    docs_url: 'https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/'
  },
  // Add other integration types...
};

const contentVariants: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 }
};

const loadingVariants: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 }
};

const MotionContainer = motion.div;

// Update ToolCardProps to remove mermaid
interface ToolCardProps {
  tool: {
    name: string;
    description?: string;
    type: string;
    icon_url?: string;
    args?: ToolArgument[];
    env?: Record<string, string> | null;
    image?: string;
    content?: string;
    with_files?: Array<ToolFile>;
    with_volumes?: Array<{
      source: string;
      target: string;
    }> | null;
  };
  isExpanded: boolean;
  onToggle: () => void;
}

const ToolCard: React.FC<ToolCardProps> = ({ tool, isExpanded, onToggle }) => {
  const getToolIcon = () => {
    if (tool.icon_url) {
      return <img src={tool.icon_url} alt={tool.name} className="h-5 w-5" />;
    }
    switch (tool.type) {
      case 'docker':
        return <img src="/images/docker-icon.png" alt="Docker" className="h-5 w-5" />;
      case 'python':
        return <img src="/images/python-icon.png" alt="Python" className="h-5 w-5" />;
      default:
        return <Wrench className="h-5 w-5 text-purple-400" />;
    }
  };

  // Update the handleCopyImage function
  const handleCopyImage = (e: React.MouseEvent<HTMLButtonElement>, image: string) => {
    e.stopPropagation();
    navigator.clipboard.writeText(image);
    toast({ title: "Docker image copied to clipboard" });
  };
    
    return (
    <div className="bg-[#1A1F2E] rounded-lg border border-[#2A3347] transition-all duration-200">
      <button 
        className="w-full text-left px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/20 rounded-lg"
        onClick={onToggle}
      >
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-md transition-colors ${
            isExpanded ? 'bg-blue-500/10' : 'bg-[#0F1629]'
          }`}>
            {getToolIcon()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-medium text-white truncate">{tool.name}</h4>
              <span className={`text-xs px-2 py-0.5 rounded-full ${
                tool.type === 'docker' ? 'bg-blue-500/10 text-blue-400' :
                tool.type === 'python' ? 'bg-green-500/10 text-green-400' :
                'bg-purple-500/10 text-purple-400'
              }`}>
                {tool.type}
              </span>
            </div>
            {tool.description && (
              <p className="text-xs text-slate-400 mt-1 line-clamp-2">{tool.description}</p>
            )}
          </div>
          <ChevronDown 
            className={`h-5 w-5 text-slate-400 transition-transform duration-200 ${
              isExpanded ? 'rotate-180' : ''
            }`} 
          />
        </div>
      </button>

      <motion.div
        animate={{ height: isExpanded ? "auto" : 0 }}
        initial={false}
        transition={{ duration: 0.2 }}
        className="overflow-hidden"
      >
        {isExpanded && (
          <div className="px-4 pb-4 space-y-3">
            {/* Tool details with simpler layout */}
            {tool.image && (
              <div className="flex items-center gap-2 p-2 bg-[#0F1629] rounded-lg">
                <Container className="h-4 w-4 text-green-400" />
                <code className="text-xs text-slate-300 font-mono flex-1 truncate">{tool.image}</code>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 px-2 text-xs hover:bg-blue-500/10 hover:text-blue-400"
                  onClick={(e) => handleCopyImage(e, tool.image!)}
                >
                  Copy
                </Button>
              </div>
            )}

            {/* Parameters */}
            {tool.args && tool.args.length > 0 && (
              <div className="space-y-2">
                {tool.args.map((arg, index) => (
                  <div key={index} className="p-2 bg-[#0F1629] rounded-lg">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-white">{arg.name}</span>
                      <span className="text-[10px] px-1.5 py-0.5 bg-purple-500/10 text-purple-400 rounded-full">
                        {arg.type}
                      </span>
                      {arg.required && (
                        <span className="text-[10px] px-1.5 py-0.5 bg-red-500/10 text-red-400 rounded-full">
                          required
                        </span>
                      )}
                    </div>
                    {arg.description && (
                      <p className="text-xs text-slate-400 mt-1">{arg.description}</p>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Files */}
            {tool.with_files && tool.with_files.length > 0 && (
              <div className="space-y-2">
                {tool.with_files.map((file, index) => (
                  <div key={index} className="flex items-center gap-2 p-2 bg-[#0F1629] rounded-lg">
                    <FileCode className="h-4 w-4 text-yellow-400 flex-shrink-0" />
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      <span className="text-xs text-slate-300 font-mono truncate">{file.source}</span>
                      <span className="text-xs text-slate-500 flex-shrink-0">→</span>
                      <span className="text-xs text-slate-400 font-mono truncate">{file.target}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </motion.div>
    </div>
  );
};

// Add new interface for expanded tool state
interface ExpandedToolState {
  sourceId: string;
  toolName: string;
}

export function TeammateDetailsModal({ isOpen, onClose, teammate, capabilities }: TeammateDetailsModalProps) {
  const [sources, setSources] = useState<Source[]>([]);
  const [sourceMetadataMap, setSourceMetadataMap] = useState<Record<string, SourceMetadata>>({});
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set());
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPreviewMode, setIsPreviewMode] = useState(true);
  const [expandedSource, setExpandedSource] = useState<string | null>(null);
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [showSyncDialog, setShowSyncDialog] = useState(false);
  const [selectedSourceForSync, setSelectedSourceForSync] = useState<string | null>(null);
  const [dynamicConfig, setDynamicConfig] = useState('');
  const [activeSection, setActiveSection] = useState('sources');
  const [isContentLoading, setIsContentLoading] = useState(false);

  // Update the sections state to ensure all sections are properly ordered and visible
  const sections = [
    { id: 'sources', title: 'Sources & Tools' },
    { id: 'integrations', title: 'Integrations' },
    { id: 'runtime', title: 'Runtime' },
    { id: 'model', title: 'Model' }
  ];

  // Enhanced loading state
  const LoadingState = () => (
    <div className="flex items-center justify-center p-8">
      <div className="flex flex-col items-center gap-3">
        <div className="relative">
          <Loader2 className="h-8 w-8 text-purple-500 animate-spin" />
          <div className="absolute inset-0 h-8 w-8 animate-ping bg-purple-500 rounded-full opacity-20" />
        </div>
        <p className="text-sm text-slate-400">Loading teammate details...</p>
      </div>
    </div>
  );

  // Enhanced error state
  const ErrorState = ({ message }: { message: string }) => (
    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
      <div className="flex items-center gap-3">
        <AlertCircle className="h-5 w-5 text-red-400" />
        <p className="text-red-400 text-sm">{message}</p>
      </div>
    </div>
  );

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setExpandedTools(new Set());
      setToolSearch('');
      setCurrentPage(1);
      setError(null);
      setSources([]);
      setSourceMetadataMap({});
      setSelectedSourceId(null);
    }
  }, [isOpen]);

  // Fetch sources and metadata when teammate changes
  useEffect(() => {
    const fetchData = async () => {
      if (!teammate?.uuid) return;
      setIsLoading(true);
      setError(null);

      try {
        // Fetch sources
        const sourcesResponse = await fetch(`/api/teammates/${teammate.uuid}/sources`);
        if (!sourcesResponse.ok) throw new Error('Failed to fetch sources');
        const sourcesData = await sourcesResponse.json();
        setSources(sourcesData);
        
        // Fetch metadata for each source
        const metadataPromises = sourcesData.map(async (source: Source) => {
          try {
            const response = await fetch(`/api/teammates/${teammate.uuid}/sources/${source.sourceId}/metadata`);
            if (!response.ok) throw new Error(`Failed to fetch metadata for ${source.sourceId}`);
            const metadata = await response.json();
            return [source.sourceId, metadata];
          } catch (error) {
            console.error(`Error fetching metadata for source ${source.sourceId}:`, error);
            return [source.sourceId, null];
          }
        });

        const metadataResults = await Promise.all(metadataPromises);
        const newMetadataMap = Object.fromEntries(
          metadataResults.filter(([_, metadata]) => metadata !== null)
        );
        setSourceMetadataMap(newMetadataMap);
      } catch (error) {
        console.error('Error fetching data:', error);
        setError(error instanceof Error ? error.message : 'Failed to load data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [teammate?.uuid]);

  // Add effect to handle initial source selection
  useEffect(() => {
    if (!isLoading && sources.length > 0 && !selectedSourceId) {
      setSelectedSourceId(sources[0].sourceId);
    }
  }, [isLoading, sources, selectedSourceId]);

  // Reset expanded state when switching sources
  useEffect(() => {
    setExpandedSource(null);
  }, [selectedSourceId]);

  // Fetch integrations when modal opens
  useEffect(() => {
    const fetchIntegrations = async () => {
      try {
        const res = await fetch('/api/integrations');
        if (!res.ok) throw new Error('Failed to fetch integrations');
        const data = await res.json();
        setIntegrations(data);
      } catch (error) {
        console.error('Error fetching integrations:', error);
      }
    };

    if (isOpen) {
      fetchIntegrations();
    }
  }, [isOpen]);

  // Add search state for tools
  const [toolSearch, setToolSearch] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const TOOLS_PER_PAGE = 5;

  // Add helper function to filter tools
  const filterTools = (tools: any[]) => {
    return tools.filter(tool => 
      tool.name.toLowerCase().includes(toolSearch.toLowerCase()) ||
      tool.description?.toLowerCase().includes(toolSearch.toLowerCase()) ||
      tool.type?.toLowerCase().includes(toolSearch.toLowerCase())
    );
  };

  // Add new state
  const [syncState, setSyncState] = useState<Record<string, SyncState>>({});

  if (!isOpen) return null;

  const getIcon = (integration: string | { name: string; type: string }) => {
    const name = typeof integration === 'string' ? integration : integration.name;
    const type = typeof integration === 'string' ? integration : integration.type;
    
    const checkType = (keyword: string) => {
      return name.toLowerCase().includes(keyword) || type.toLowerCase().includes(keyword);
    };

    if (checkType('slack')) return <img src="https://cdn4.iconfinder.com/data/icons/logos-and-brands/512/306_Slack_logo-512.png" alt="Slack" className="h-5 w-5 object-contain" />;
    if (checkType('aws')) return <img src="https://uxwing.com/wp-content/themes/uxwing/download/brands-and-social-media/aws-icon.png" alt="AWS" className="h-5 w-5 object-contain" />;
    if (checkType('github')) return <img src="https://cdn-icons-png.flaticon.com/512/25/25231.png" alt="GitHub" className="h-5 w-5 object-contain" />;
    if (checkType('jira')) return <img src="https://cdn-icons-png.flaticon.com/512/5968/5968875.png" alt="Jira" className="h-5 w-5 object-contain" />;
    if (checkType('kubernetes')) return <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Kubernetes_logo_without_workmark.svg/2109px-Kubernetes_logo_without_workmark.svg.png" alt="Kubernetes" className="h-5 w-5 object-contain" />;
    return <div className="h-5 w-5 bg-purple-400 rounded-full" />;
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTypeIcon = (tool: { type?: string }) => {
    switch (tool.type?.toLowerCase()) {
      case 'terraform':
        return <Box className="h-4 w-4 text-violet-400" />;
      case 'python':
        return <FileCode className="h-4 w-4 text-blue-400" />;
      case 'docker':
        return <Container className="h-4 w-4 text-sky-400" />;
      case 'kubernetes':
        return <Settings className="h-4 w-4 text-green-400" />;
      default:
        return <Wrench className="h-4 w-4 text-purple-400" />;
    }
  };

  const selectedTools = selectedSourceId ? sourceMetadataMap[selectedSourceId]?.metadata?.tools || [] : [];

  // Update getSourceName to include folder information
  const getSourceName = (source: Source, metadata: SourceMetadata | undefined) => {
    if (metadata?.metadata?.tools?.length) {
      const sourceUrl = metadata.metadata.tools[0]?.source?.url;
      if (sourceUrl) {
        try {
          const url = new URL(sourceUrl);
          const parts = url.pathname.split('/');
          const repoPath = parts.slice(5).join('/'); // Get path after tree/main/
          const folderName = repoPath || parts[parts.length - 1];
          return {
            name: `${parts[1]}/${parts[2]}${repoPath ? ` (${folderName})` : ''}`,
            isGithubFolder: repoPath.length > 0
          };
        } catch (e) {
          // Fall back to default naming if URL parsing fails
        }
      }
    }
    return {
      name: metadata?.metadata?.name || source.name || `Source ${source.sourceId.slice(0, 8)}`,
      isGithubFolder: false
    };
  };

  // Update the handleSync function
  const handleSync = async (sourceId: string, config?: any) => {
    try {
      setSyncState(prev => ({
        ...prev,
        [sourceId]: { isLoading: true, error: null }
      }));
      
      const response = await fetch(`/api/sources/${sourceId}/sync`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ dynamic_config: config }),
      });

      if (!response.ok) throw new Error('Failed to sync source');
      const data = await response.json();

      setSyncState(prev => ({
        ...prev,
        [sourceId]: { 
          isLoading: false, 
          error: null,
          lastSync: new Date().toISOString()
        }
      }));

      toast({
        title: 'Source synced successfully',
        description: 'The source has been updated with the latest changes.',
        variant: 'default',
      });

      // Refresh source metadata after sync
      fetchSourceMetadata(sourceId);

    } catch (error) {
      setSyncState(prev => ({
        ...prev,
        [sourceId]: { 
          isLoading: false, 
          error: error instanceof Error ? error.message : 'Failed to sync'
        }
      }));
      
      toast({
        title: 'Sync failed',
        description: 'Failed to sync source. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setShowSyncDialog(false);
      setSelectedSourceForSync(null);
      setDynamicConfig('');
    }
  };

  // Update the renderSourceCard function
  const renderSourceCard = (source: Source | undefined, metadata: SourceMetadata | undefined) => {
    if (!source || !metadata) {
      return (
        <div className="bg-[#1A1F2E] rounded-lg p-4 border border-[#2A3347]">
          <div className="flex items-center justify-center h-32">
            <p className="text-sm text-slate-400">No source information available</p>
          </div>
        </div>
      );
    }

    const tools = metadata.metadata?.tools || [];
    
    // Helper function to get all errors from tools
    const getAllErrors = () => tools.reduce((acc, tool) => {
      if (tool.errors) acc.push(...tool.errors);
      return acc;
    }, [] as Array<{ file: string; type: string; error: string; details: string; }>);
    
    const sourceInfo = tools[0]?.source || metadata.metadata?.source_meta || {
      url: '',
      branch: 'main',
      commit: '',
      committer: ''
    };
    const sourceUrl = sourceInfo.url;
    const repoName = sourceUrl
      ? sourceUrl.replace('https://github.com/', '').replace('.git', '')
      : metadata.metadata?.name || 'Unknown Repository';

    return (
      <div className="bg-[#1A1F2E] rounded-lg p-4 border border-[#2A3347] mb-4">
        {/* Source Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-md bg-[#0F1629]">
              <FolderGit className="h-5 w-5 text-blue-400" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-white flex items-center gap-2 break-all">
                {repoName}
                {sourceInfo.branch && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400">
                    {sourceInfo.branch}
                  </span>
                )}
              </h3>
              <div className="flex flex-wrap items-center gap-2 mt-2">
                {sourceInfo.commit && (
                  <div className="flex items-center gap-1 text-xs text-slate-400 bg-[#0F1629] px-2 py-1 rounded">
                    <GitCommit className="h-3.5 w-3.5" />
                    <span className="font-mono">{sourceInfo.commit.slice(0, 8)}</span>
              </div>
            )}
                {sourceInfo.committer && (
                  <div className="flex items-center gap-1 text-xs text-slate-400">
                    <User className="h-3.5 w-3.5" />
                    <span>{sourceInfo.committer}</span>
          </div>
                      )}
                    </div>
                    </div>
                  </div>
          <Button
            variant="secondary"
            size="sm"
            className="flex items-center gap-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400"
            onClick={() => {
              setSelectedSourceForSync(source.sourceId);
              setShowSyncDialog(true);
            }}
            disabled={syncState[source.sourceId]?.isLoading}
          >
            <RefreshCw className={`h-4 w-4 ${syncState[source.sourceId]?.isLoading ? 'animate-spin' : ''}`} />
            {syncState[source.sourceId]?.isLoading ? 'Syncing...' : 'Sync'}
                  </Button>
                </div>

        {/* Source Stats */}
        <div className="grid grid-cols-2 gap-2 mb-4">
          <div className="bg-[#0F1629] p-3 rounded-lg">
            <div className="flex items-center gap-2">
              <Wrench className="h-4 w-4 text-purple-400" />
              <div className="text-xs text-slate-400">Discovered Tools</div>
                            </div>
            <div className="text-lg font-medium text-white mt-1">{tools.length}</div>
                          </div>
          <div className="bg-[#0F1629] p-3 rounded-lg">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-400" />
              <div className="text-xs text-slate-400">Errors</div>
                              </div>
            <div className={`text-lg font-medium ${getAllErrors().length > 0 ? 'text-red-400' : 'text-white'} mt-1`}>
              {getAllErrors().length}
                          </div>
                      </div>
        </div>

        {/* Error Display */}
        {getAllErrors().length > 0 && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-red-400 mt-1 flex-shrink-0" />
              <div className="flex-1">
                <h4 className="text-sm font-medium text-red-400 mb-2">Source Errors</h4>
                <div className="space-y-2">
                  {getAllErrors().map((error, index) => (
                    <div key={index} className="bg-red-500/5 p-2 rounded">
                      <div className="text-xs text-red-400/90 font-medium">
                        {error.file}
                              </div>
                      <div className="text-xs text-red-400/80 mt-1">
                        {error.type}: {error.error}
                      </div>
                      {error.details && (
                        <div className="text-xs text-red-400/70 mt-1">
                          {error.details}
                        </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
            </div>
                  </div>
                )}

        {/* Tools List */}
        <div className="mt-4">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-medium text-white">Available Tools</h4>
            <div className="relative w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Filter tools..."
                value={toolSearch}
                onChange={(e) => setToolSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-[#0F1629] border border-[#2A3347] rounded-md text-sm"
              />
            </div>
          </div>
          <div className="max-h-[calc(100vh-16rem)] overflow-y-auto pr-2 custom-scrollbar">
            <div className="grid grid-cols-2 gap-4" style={{ gridAutoRows: 'min-content' }}>
              {filterTools(tools).map((tool) => (
                <div key={`${source.sourceId}-${tool.name}`} className="h-fit">
                  <ToolCard
                    tool={{
                      ...tool,
                      type: tool.type || 'unknown',
                      description: tool.description,
                      icon_url: tool.icon_url,
                      args: tool.args,
                      env: tool.env,
                      image: tool.image,
                      content: tool.content,
                      with_files: tool.with_files,
                      with_volumes: tool.with_volumes
                    }}
                    isExpanded={expandedTools.has(`${source.sourceId}-${tool.name}`)}
                    onToggle={() => {
                      const toolKey = `${source.sourceId}-${tool.name}`;
                      setExpandedTools(prev => {
                        const newSet = new Set(prev);
                        if (newSet.has(toolKey)) {
                          newSet.delete(toolKey);
                        } else {
                          newSet.add(toolKey);
                        }
                        return newSet;
                      });
                    }}
                  />
              </div>
            ))}
          </div>
          </div>
        </div>
      </div>
    );
  };

  // Update the renderIntegrationCard function
  const renderIntegrationCard = (integration: Integration | string) => {
    const integrationData = typeof integration === 'string' 
      ? integrations.find(i => i.name === integration || i.integration_type === integration)
      : integration;

    if (!integrationData) return null;

    const integrationType = INTEGRATION_TYPES[integrationData.integration_type.toLowerCase()];
    if (!integrationType) return null;

    return (
      <div className="bg-[#1A1F2E] rounded-lg p-4 border border-[#2A3347]">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-md bg-[#0F1629]">
              <img src={integrationType.icon} alt={integrationData.name} className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-medium text-white">{integrationData.name}</h4>
                <span className={`text-xs px-2 py-0.5 rounded-full bg-${integrationType.color}-500/10 text-${integrationType.color}-400`}>
                  {integrationData.integration_type}
                </span>
                  </div>
              <p className="text-xs text-slate-400 mt-1">{integrationData.description}</p>
            </div>
          </div>
        </div>

        {/* Enhanced Integration Details */}
        <div className="mt-4 space-y-4">
          {/* Authentication Type */}
          <div className="flex items-center gap-2 text-xs">
            <Key className="h-3.5 w-3.5 text-blue-400" />
            <span className="text-slate-400">Auth Type:</span>
            <span className="text-slate-300">{integrationData.auth_type}</span>
          </div>

          {/* AWS-specific details */}
          {integrationData.integration_type.toLowerCase() === 'aws' && (
            <>
              {/* Resource Types */}
              <div className="space-y-2">
                <h6 className="text-xs font-medium text-slate-300">Available Resource Types</h6>
                <div className="flex flex-wrap gap-2">
                  {integrationType.resourceTypes?.map(resource => (
                    <span key={resource} className="text-[10px] px-2 py-1 bg-blue-500/10 text-blue-400 rounded-full">
                      {resource}
                </span>
                  ))}
              </div>
            </div>

              {/* Permissions */}
              <div className="space-y-2">
                <h6 className="text-xs font-medium text-slate-300">Permission Levels</h6>
                <div className="flex flex-wrap gap-2">
                  {integrationType.permissions?.map(permission => (
                    <span key={permission} className="text-[10px] px-2 py-1 bg-purple-500/10 text-purple-400 rounded-full">
                      {permission}
                    </span>
                  ))}
          </div>
        </div>

              {/* Regions */}
              <div className="space-y-2">
                <h6 className="text-xs font-medium text-slate-300">Available Regions</h6>
                <div className="flex flex-wrap gap-2">
                  {integrationType.regions?.map(region => (
                    <span key={region} className="text-[10px] px-2 py-1 bg-green-500/10 text-green-400 rounded-full">
                      {region}
                    </span>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Configurations */}
          {integrationData.configs && integrationData.configs.length > 0 && (
            <div>
              <h6 className="text-xs font-medium text-slate-300 mb-2">Active Configurations</h6>
              <div className="flex flex-wrap gap-2">
                {integrationData.configs.map(config => (
                  <div 
                    key={config.name}
                    className="flex items-center gap-2 px-2 py-1 bg-[#0F1629] rounded text-xs"
                  >
                    <Settings className="h-3.5 w-3.5 text-blue-400" />
                    <span className="text-slate-300">{config.name}</span>
                    {config.is_default && (
                      <span className="px-1.5 py-0.5 bg-purple-500/20 text-purple-400 rounded-full text-[10px]">
                        Default
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Metadata with better formatting */}
          {integrationData.kubiya_metadata && (
            <div className="grid grid-cols-2 gap-3 p-3 bg-[#0F1629] rounded-lg">
              <div className="text-xs space-y-1">
                <span className="text-slate-400">Created</span>
                <div className="text-slate-300 font-medium">
                  {new Date(integrationData.kubiya_metadata.created_at).toLocaleDateString(undefined, {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
              </div>
            </div>
              <div className="text-xs space-y-1">
                <span className="text-slate-400">Last Updated</span>
                <div className="text-slate-300 font-medium">
                  {new Date(integrationData.kubiya_metadata.last_updated).toLocaleDateString(undefined, {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
              </div>
              </div>
                </div>
              )}
        </div>
      </div>
    );
  };

  // Add helper function to determine runner type
  const getRunnerInfo = (runner: string) => {
    const isKubiyaHosted = runner.toLowerCase().includes('hosted') && 
                          runner.toLowerCase().includes('kubiya');
    return {
      isCloud: isKubiyaHosted,
      label: isKubiyaHosted ? 'Kubiya Cloud' : 'Local (Kubernetes Operator)',
      icon: isKubiyaHosted ? Container : Settings
    };
  };

  // Add helper function for model icon
  const getModelIcon = (model?: string) => {
    if (model?.toLowerCase().includes('gpt')) {
      return <img src="https://cdn.worldvectorlogo.com/logos/openai-2.svg" 
                  alt="OpenAI" 
                  className="h-5 w-5" />;
    }
    return <Database className="h-5 w-5 text-purple-400" />;
  };

  // Add helper functions for section icons and counts
  const getSectionIcon = (sectionId: string) => {
    switch (sectionId) {
      case 'sources':
        return <FolderGit className="h-4 w-4 text-blue-400" />;
      case 'integrations':
        return <GitMerge className="h-4 w-4 text-green-400" />;
      case 'runtime':
        return <Container className="h-4 w-4 text-orange-400" />;
      case 'model':
        return <Brain className="h-4 w-4 text-purple-400" />;
      default:
        return <Info className="h-4 w-4 text-slate-400" />;
    }
  };

  const getSectionCount = (sectionId: string): number => {
    if (!teammate) return 0;
    
    switch (sectionId) {
      case 'sources':
        return teammate.sources?.length || 0;
      case 'integrations':
        return teammate.integrations?.length || 0;
      case 'runtime':
        return teammate.runners?.length || 0;
      case 'model':
        return teammate.llm_model ? 1 : 0;
      default:
        return 0;
    }
  };

  // Add helper function to render section content
  const renderSectionContent = (sectionId: string) => {
    switch (sectionId) {
      case 'overview':
        return renderOverviewContent();
      case 'sources':
        return renderSourcesContent();
      case 'integrations':
        return renderIntegrationsContent();
      case 'runtime':
        return renderRuntimeContent();
      case 'security':
        return renderSecurityContent();
      case 'model':
        return renderModelContent();
      default:
        return null;
    }
  };

  // Add section content rendering functions
  const renderOverviewContent = () => (
    <div className="p-4 grid grid-cols-2 gap-4">
      {teammate?.llm_model && (
        <div>
          <div className="text-xs text-slate-400">Language Model</div>
          <div className="text-sm text-slate-300 mt-1">{teammate.llm_model}</div>
        </div>
      )}
      {teammate?.instruction_type && (
        <div>
          <div className="text-xs text-slate-400">Instruction Type</div>
          <div className="text-sm text-slate-300 mt-1">{teammate.instruction_type}</div>
        </div>
      )}
      {teammate?.metadata?.created_at && (
        <div>
          <div className="text-xs text-slate-400">Created At</div>
          <div className="text-sm text-slate-300 mt-1">
            {formatDate(teammate.metadata.created_at)}
          </div>
        </div>
      )}
      {teammate?.metadata?.last_updated && (
        <div>
          <div className="text-xs text-slate-400">Last Updated</div>
          <div className="text-sm text-slate-300 mt-1">
            {formatDate(teammate.metadata.last_updated)}
          </div>
        </div>
      )}
    </div>
  );

  const renderSourcesContent = () => (
    <div className="p-4">
      {/* Search and filters bar */}
      <div className="sticky top-0 z-10 bg-[#0F1629] p-4 mb-6 rounded-lg border border-[#2A3347]">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-md bg-blue-500/10">
              <Wrench className="h-4 w-4 text-blue-400" />
            </div>
            <span className="text-sm text-slate-300">
              {sources.reduce(
                (acc, source) => acc + (sourceMetadataMap[source.sourceId]?.metadata?.tools?.length || 0),
                0
              )} tools available
            </span>
          </div>
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search tools..."
              value={toolSearch}
              onChange={(e) => setToolSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-[#1A1F2E] border border-[#2A3347] rounded-lg text-sm text-slate-300 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            />
          </div>
        </div>
      </div>

      {/* Tools grid with better organization */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {sources.map((source) => {
          const metadata = sourceMetadataMap[source.sourceId];
          const tools = metadata?.metadata?.tools || [];
          const filteredTools = tools.filter(tool => 
            tool.name.toLowerCase().includes(toolSearch.toLowerCase()) ||
            tool.description?.toLowerCase().includes(toolSearch.toLowerCase())
          );

          if (toolSearch && filteredTools.length === 0) return null;

          return (
            <div key={source.sourceId} className="flex flex-col">
              {/* Source header */}
              <div className="mb-3 p-3 bg-[#1A1F2E] rounded-lg border border-[#2A3347]">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-md bg-[#0F1629]">
                    <FolderGit className="h-5 w-5 text-blue-400" />
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-sm font-medium text-white truncate">
                      {getSourceDisplayName(metadata)}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-slate-400">{filteredTools.length} tools</span>
                      {metadata?.metadata?.source_meta?.branch && (
                        <span className="text-xs px-1.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400">
                          {metadata.metadata.source_meta.branch}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Tools list */}
              <div className="space-y-3">
                {filteredTools.map((tool) => (
                  <ToolCard
                    key={tool.name}
                    tool={{
                      ...tool,
                      type: tool.type || 'unknown',
                      description: tool.description,
                      icon_url: tool.icon_url,
                      args: tool.args,
                      env: tool.env,
                      image: tool.image,
                      content: tool.content,
                      with_files: tool.with_files,
                      with_volumes: tool.with_volumes
                    }}
                    isExpanded={expandedTools.has(`${source.sourceId}-${tool.name}`)}
                    onToggle={() => {
                      const toolKey = `${source.sourceId}-${tool.name}`;
                      setExpandedTools(prev => {
                        const newSet = new Set(prev);
                        if (newSet.has(toolKey)) {
                          newSet.delete(toolKey);
                        } else {
                          newSet.add(toolKey);
                        }
                        return newSet;
                      });
                    }}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  const renderIntegrationsContent = () => (
    <div className="p-4 space-y-4">
      {teammate?.integrations?.map((integration, index) => (
        <div key={`${integration}-${index}`}>
          {renderIntegrationCard(integration)}
        </div>
      ))}
    </div>
  );

  const renderRuntimeContent = () => (
    <div className="p-4 space-y-6">
      {/* Runners */}
      <div>
        <h4 className="text-sm font-medium text-slate-300 flex items-center gap-2 mb-3">
          <Container className="h-4 w-4 text-sky-400" />
          Runtime Runners
        </h4>
        <div className="grid grid-cols-2 gap-3">
          {teammate?.runners?.map((runner, index) => {
            const runnerInfo = getRunnerInfo(runner);
            const Icon = runnerInfo.icon;
            return (
              <div
                key={index}
                className="bg-[#1A1F2E] p-3 rounded-lg border border-[#2A3347] hover:bg-[#242E3F] transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-md bg-[#0F1629]">
                    <Icon className={`h-4 w-4 ${runnerInfo.isCloud ? 'text-blue-400' : 'text-green-400'}`} />
                  </div>
                  <div>
                    <div className="text-sm text-slate-300 font-medium">{runner}</div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        runnerInfo.isCloud 
                          ? 'bg-blue-500/10 text-blue-400' 
                          : 'bg-green-500/10 text-green-400'
                      }`}>
                        {runnerInfo.label}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Environment Variables */}
      {teammate?.environment_variables && Object.keys(teammate.environment_variables).length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-slate-300 flex items-center gap-2 mb-3">
            <Variable className="h-4 w-4 text-purple-400" />
            Environment Configuration
          </h4>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(teammate.environment_variables).map(([key, value]) => (
              <div key={key} className="bg-[#1A1F2E] p-3 rounded-lg">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-md bg-[#0F1629]">
                    {key.toLowerCase().includes('secret') || key.toLowerCase().includes('token') ? (
                      <Key className="h-3.5 w-3.5 text-amber-400" />
                    ) : (
                      <Variable className="h-3.5 w-3.5 text-blue-400" />
                    )}
                  </div>
                  <span className="text-sm text-slate-300 font-mono">{key}</span>
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <code className="text-xs text-slate-400 bg-[#0F1629] px-2 py-1 rounded flex-1 font-mono">
                    {key.toLowerCase().includes('secret') || key.toLowerCase().includes('token') 
                      ? '••••••••' 
                      : value}
                  </code>
                  {(key.toLowerCase().includes('secret') || key.toLowerCase().includes('token')) && (
                    <span className="text-[10px] px-1.5 py-0.5 bg-amber-500/10 text-amber-400 rounded-full">
                      Secret
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderSecurityContent = () => (
    <div className="p-4">
      {/* Access Control */}
      {teammate && ((teammate.allowed_groups && teammate.allowed_groups.length > 0) || 
                   (teammate.allowed_users && teammate.allowed_users.length > 0)) && (
        <div>
          <h4 className="text-sm font-medium text-slate-300 flex items-center gap-2 mb-3">
            <Lock className="h-4 w-4 text-purple-400" />
            Access Control
          </h4>
          <div className="grid grid-cols-2 gap-4">
            {teammate.allowed_groups && teammate.allowed_groups.length > 0 && (
              <div className="bg-[#1A1F2E] p-3 rounded-lg">
                <h5 className="text-xs text-slate-400 mb-2">Allowed Groups</h5>
                <div className="flex flex-wrap gap-2">
                  {teammate.allowed_groups.map((group) => (
                    <span key={group} className="text-xs bg-[#0F1629] text-slate-300 px-2 py-1 rounded">
                      {group}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {teammate.allowed_users && teammate.allowed_users.length > 0 && (
              <div className="bg-[#1A1F2E] p-3 rounded-lg">
                <h5 className="text-xs text-slate-400 mb-2">Allowed Users</h5>
                <div className="flex flex-wrap gap-2">
                  {teammate.allowed_users.map((user) => (
                    <span key={user} className="text-xs bg-[#0F1629] text-slate-300 px-2 py-1 rounded">
                      {user}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );

  const renderModelContent = () => (
    <div className="p-4">
      {teammate?.llm_model && (
        <div className="bg-[#1A1F2E] p-4 rounded-lg mb-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-md bg-[#0F1629]">
              {getModelIcon(teammate.llm_model)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-medium text-white">Language Model</h4>
                {teammate.llm_model.toLowerCase().includes('gpt') && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-green-500/10 text-green-400">
                    OpenAI
                  </span>
                )}
              </div>
              <p className="text-sm text-slate-300 mt-1">{teammate.llm_model}</p>
            </div>
          </div>
        </div>
      )}
      {teammate?.instruction_type && (
        <div className="bg-[#1A1F2E] p-4 rounded-lg">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-md bg-[#0F1629]">
              <Code2 className="h-5 w-5 text-purple-400" />
            </div>
            <div>
              <h4 className="text-sm font-medium text-white">Instruction Type</h4>
              <p className="text-sm text-slate-300 mt-1">{teammate.instruction_type}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  // Add Sync Dialog
  const SyncWarningDialog = () => (
    <Dialog
      open={showSyncDialog}
      onOpenChange={(open: boolean) => {
        if (!open) {
          setShowSyncDialog(false);
          setSelectedSourceForSync(null);
          setDynamicConfig('');
        }
      }}
    >
      <DialogContent
        className="max-w-md bg-[#1A1F2E] border border-[#2A3347] p-0 shadow-2xl overflow-hidden"
        aria-describedby="sync-warning-description"
      >
        <div className="p-6">
          <DialogTitle className="text-lg font-medium text-white mb-4 flex items-center gap-2">
            <div className="p-2 rounded-md bg-[#0F1629]">
              <RefreshCw className="h-5 w-5 text-blue-400" />
            </div>
            Sync Source
          </DialogTitle>
          <div className="space-y-4">
            {/* Warning Message */}
            <div className="flex items-start gap-3 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
              <div className="p-2 rounded-md bg-[#0F1629]">
                <AlertCircle className="h-5 w-5 text-amber-400" />
              </div>
              <div>
                <p id="sync-warning-description" className="text-sm text-amber-400">
                  This will pull the latest changes from the repository. Any local changes may be overwritten.
                </p>
              </div>
            </div>

            {/* Dynamic Config */}
            <div>
              <label className="text-sm text-slate-400 mb-2 block">
                Dynamic Configuration (Optional)
              </label>
              <div className="relative">
                <textarea
                  value={dynamicConfig}
                  onChange={(e) => setDynamicConfig(e.target.value)}
                  className="w-full h-32 bg-[#0F1629] border border-[#2A3347] rounded-lg p-3 text-sm text-slate-300 font-mono focus:ring-2 focus:ring-blue-500/20 focus:outline-none"
                  placeholder="Enter JSON configuration..."
                />
                {dynamicConfig && (
                  <div className="absolute top-2 right-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 px-2 text-xs hover:bg-blue-500/10 hover:text-blue-400"
                      onClick={() => {
                        try {
                          const formatted = JSON.stringify(JSON.parse(dynamicConfig), null, 2);
                          setDynamicConfig(formatted);
                        } catch (e) {
                          // Invalid JSON - ignore
                        }
                      }}
                    >
                      Format JSON
                    </Button>
                  </div>
                )}
              </div>
            </div>

            {/* Dialog Actions */}
            <div className="flex justify-end gap-3 pt-4 border-t border-[#2A3347]">
              <Button
                variant="ghost"
                className="hover:bg-red-500/10 hover:text-red-400"
                onClick={() => setShowSyncDialog(false)}
                disabled={syncState[selectedSourceForSync!]?.isLoading}
              >
                Cancel
              </Button>
              <Button
                variant="default"
                className="bg-blue-500 hover:bg-blue-600 text-white"
                onClick={() => {
                  if (selectedSourceForSync) {
                    handleSync(
                      selectedSourceForSync, 
                      dynamicConfig ? JSON.parse(dynamicConfig) : undefined
                    );
                  }
                }}
                disabled={syncState[selectedSourceForSync!]?.isLoading}
              >
                <div className="flex items-center gap-2">
                  {syncState[selectedSourceForSync!]?.isLoading && (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  )}
                  {syncState[selectedSourceForSync!]?.isLoading ? 'Syncing...' : 'Sync Now'}
                </div>
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );

  // Add fetchSourceMetadata function
  const fetchSourceMetadata = async (sourceId: string) => {
    try {
      const response = await fetch(`/api/teammates/${teammate?.uuid}/sources/${sourceId}/metadata`);
      if (!response.ok) throw new Error('Failed to fetch source metadata');
      
      const metadata = await response.json();
      setSourceMetadataMap(prev => ({
        ...prev,
        [sourceId]: metadata
      }));
    } catch (error) {
      console.error('Error fetching source metadata:', error);
    }
  };

  // Handle section change with loading state
  const handleSectionChange = (sectionId: string) => {
    setIsContentLoading(true);
    setActiveSection(sectionId);
    setExpandedTools(new Set());
    setTimeout(() => setIsContentLoading(false), 300);
  };

  // Update the getSourceDisplayName function
  const getSourceDisplayName = (metadata: SourceMetadata | undefined) => {
    if (!metadata) return 'Unknown Source';
    // Try to get URL from different possible locations
    const sourceUrl = metadata.metadata?.source_meta?.url || 
                     metadata.metadata?.tools?.[0]?.source?.url || '';
    
    if (sourceUrl.includes('github.com')) {
      const repoPath = sourceUrl.split('github.com/')[1]
        .replace('.git', '')
        .replace('/tree/', '@')
        .replace('/blob/', '@');
      return repoPath;
    }
    return metadata.metadata?.name || 'Unknown Source';
  };

  // Add custom scrollbar styles to your global CSS
  const customScrollbarStyles = `
    .custom-scrollbar::-webkit-scrollbar {
      width: 8px;
    }
    
    .custom-scrollbar::-webkit-scrollbar-track {
      background: #0F1629;
    }
    
    .custom-scrollbar::-webkit-scrollbar-thumb {
      background: #2A3347;
      border-radius: 4px;
    }
    
    .custom-scrollbar::-webkit-scrollbar-thumb:hover {
      background: #374151;
    }
  `;

  const styleSheet = document.createElement("style");
  styleSheet.innerText = customScrollbarStyles;
  document.head.appendChild(styleSheet);

  // Add helper function to determine language from filename
  const getLanguageFromFilename = (filename: string): string => {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'py': return 'python';
      case 'js': return 'javascript';
      case 'ts': return 'typescript';
      case 'yaml':
      case 'yml': return 'yaml';
      case 'json': return 'json';
      case 'sh': return 'bash';
      default: return 'text';
    }
  };

  return (
    <div className="fixed inset-0 z-50" aria-modal="true" role="dialog">
      <div 
        className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity" 
        onClick={onClose} 
      />
      <div className="fixed inset-0 flex">
        <div className="flex min-h-full w-full">
          <div className="relative flex w-full bg-[#0F1629] shadow-xl">
            {/* Sidebar */}
            <div className="w-64 border-r border-[#2A3347] flex flex-col overflow-y-auto">
              <div className="p-4 border-b border-[#2A3347]">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-purple-500/10">
                    <Brain className="h-5 w-5 text-purple-400" />
                </div>
                  <h2 className="text-lg font-medium text-white truncate">
                    {teammate?.name || 'Teammate'}
                  </h2>
                </div>
              </div>
              <nav className="p-2 flex-1 overflow-y-auto">
                {sections.map(section => (
                  <button
                    key={section.id}
                    onClick={() => handleSectionChange(section.id)}
                    className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
                      activeSection === section.id
                        ? 'bg-blue-500/10 text-blue-400'
                        : 'text-slate-400 hover:bg-[#1A1F2E] hover:text-slate-300'
                    }`}
                  >
                    <span className="flex-shrink-0">
                      {getSectionIcon(section.id)}
                    </span>
                    <span>{section.title}</span>
                    {getSectionCount(section.id) > 0 ? (
                      <span className="ml-auto text-xs bg-[#1A1F2E] px-2 py-0.5 rounded-full">
                        {getSectionCount(section.id)}
                      </span>
                    ) : null}
                  </button>
                ))}
              </nav>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col overflow-y-auto">
              {/* Header */}
              <div className="flex justify-between items-center px-6 py-4 border-b border-[#2A3347] bg-[#0F1629]">
                <h3 className="text-lg font-medium text-white">
                  {sections.find(s => s.id === activeSection)?.title}
                </h3>
                <Button variant="ghost" onClick={onClose}>
                <X className="h-5 w-5" />
              </Button>
            </div>

              {/* Content Area */}
              <div className="flex-1 p-6 space-y-6">
              {error && <ErrorState message={error} />}
              {isLoading ? (
                <LoadingState />
              ) : (
                  renderSectionContent(activeSection)
              )}
            </div>
          </div>
        </div>
      </div>
      </div>
      <SyncWarningDialog />
    </div>
  );
} 

const LoadingSourcesState = () => (
  <div className="flex-1 flex items-center justify-center">
    <div className="flex flex-col items-center gap-3">
      <div className="relative">
        <RefreshCw className="h-8 w-8 text-blue-400 animate-spin" />
        <div className="absolute inset-0 h-8 w-8 animate-ping bg-blue-400 rounded-full opacity-20" />
      </div>
      <div className="flex flex-col items-center gap-1">
        <p className="text-sm text-slate-300">Loading sources</p>
        <p className="text-xs text-slate-400">Fetching repository information...</p>
      </div>
    </div>
  </div>
); 