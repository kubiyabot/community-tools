"use client";

import React from 'react';
import { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { 
  ChevronDown, ChevronUp, Terminal, Info, Box, X, ExternalLink, GitBranch, FileCode,
  Container, GitPullRequest, Wrench, Settings, Search, Loader2, Link2, GitCommit,
  AlertCircle, Code2, Database, Globe, GitMerge, Key, Lock, Variable, Layers, FolderGit
} from 'lucide-react';
import dynamic from 'next/dynamic';

const SyntaxHighlighter = dynamic(
  () => import('react-syntax-highlighter').then((mod) => {
    const { PrismLight } = mod;
    return PrismLight;
  }) as any,
  { ssr: false }
);

const languages = {
  python: dynamic(() => import('react-syntax-highlighter/dist/esm/languages/prism/python')),
  javascript: dynamic(() => import('react-syntax-highlighter/dist/esm/languages/prism/javascript')),
  yaml: dynamic(() => import('react-syntax-highlighter/dist/esm/languages/prism/yaml')),
  dockerfile: dynamic(() => import('react-syntax-highlighter/dist/esm/languages/prism/docker')),
  hcl: dynamic(() => import('react-syntax-highlighter/dist/esm/languages/prism/hcl')),
};

const oneDark = dynamic(
  () => import('react-syntax-highlighter/dist/esm/styles/prism/one-dark').then(mod => mod.default) as any,
  { ssr: false }
);

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
      with_files?: Array<{
        source: string;
        target: string;
      }>;
      with_volumes?: Array<{
        source: string;
        target: string;
      }> | null;
      metadata?: {
        git_url?: string;
        git_branch?: string;
        git_path?: string;
        docker_image?: string;
        repository?: string;
        entrypoint?: string;
      };
    }>;
    name?: string;
    description?: string;
    repository?: string;
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

export function TeammateDetailsModal({ isOpen, onClose, teammate, capabilities }: TeammateDetailsModalProps) {
  const [sources, setSources] = useState<Source[]>([]);
  const [sourceMetadataMap, setSourceMetadataMap] = useState<Record<string, SourceMetadata>>({});
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({});
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPreviewMode, setIsPreviewMode] = useState(true);
  const [expandedSource, setExpandedSource] = useState<string | null>(null);
  const [integrations, setIntegrations] = useState<Integration[]>([]);

  // Update the sections state to ensure all sections are properly ordered and visible
  const [sections, setSections] = useState([
    { id: 'overview', title: 'Overview', isExpanded: true },
    { id: 'sources', title: 'Sources & Tools', isExpanded: true },
    { id: 'integrations', title: 'Connected Platforms', isExpanded: false },
    { id: 'runtime', title: 'Runtime & Environment', isExpanded: false },
    { id: 'security', title: 'Security & Access', isExpanded: false },
    { id: 'model', title: 'Model Information', isExpanded: false }
  ]);

  const toggleSection = (sectionId: string) => {
    setSections(prevSections => 
      prevSections.map(section => ({
        ...section,
        isExpanded: section.id === sectionId ? !section.isExpanded : section.isExpanded
      }))
    );
  };

  // Enhanced section header component
  const SectionHeader = ({ 
    title, 
    sectionId, 
    count, 
    icon: Icon 
  }: { 
    title: string; 
    sectionId: string; 
    count?: number;
    icon?: any;
  }) => {
    const isExpanded = sections.find(s => s.id === sectionId)?.isExpanded;
    
    return (
      <div
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-[#2A3347] transition-colors rounded-lg group"
        onClick={() => toggleSection(sectionId)}
      >
        <div className="flex items-center gap-3">
          {Icon && (
            <div className={`p-2 rounded-md bg-[#1A1F2E] group-hover:bg-[#2A3347] transition-colors`}>
              <Icon className="h-4 w-4 text-purple-400" />
            </div>
          )}
          <div>
            <h3 className="text-sm font-medium text-slate-300">{title}</h3>
            {count !== undefined && (
              <p className="text-xs text-slate-400 mt-0.5">
                {count} {count === 1 ? 'item' : 'items'} available
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="text-xs text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity">
            Click to {isExpanded ? 'collapse' : 'expand'}
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="text-slate-400 hover:text-white"
          >
            {isExpanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    );
  };

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
      setSections(prevSections => 
        prevSections.map(section => ({
          ...section,
          isExpanded: section.id === 'overview' || section.id === 'sources'
        }))
      );
      setExpandedTools({});
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
    const fetchSourcesAndMetadata = async () => {
      if (!teammate?.uuid || !isOpen) return;

      setIsLoading(true);
      setError(null);

      try {
        const sourcesRes = await fetch(`/api/teammates/${teammate.uuid}/sources`);
        if (!sourcesRes.ok) {
          throw new Error(`Failed to fetch sources: ${sourcesRes.status}`);
        }

        const sourcesData = await sourcesRes.json();
        if (!Array.isArray(sourcesData)) {
          throw new Error('Invalid sources data received');
        }

        setSources(sourcesData);
        
        if (sourcesData.length === 0) {
          setIsLoading(false);
          return;
        }

        // Set initial selected source
        setSelectedSourceId(sourcesData[0].sourceId);

        // Fetch metadata for all sources in parallel
        const metadataPromises = sourcesData.map(async (source) => {
          try {
            const metadataRes = await fetch(`/api/teammates/${teammate.uuid}/sources/${source.sourceId}/metadata`);
            if (!metadataRes.ok) {
              console.error('Failed to fetch metadata:', {
                sourceId: source.sourceId,
                status: metadataRes.status
              });
              return null;
            }

            const metadata = await metadataRes.json();
            return { sourceId: source.sourceId, metadata };
          } catch (error) {
            console.error('Error fetching metadata for source:', source.sourceId, error);
            return null;
          }
        });

        const metadataResults = await Promise.all(metadataPromises);
        const newMetadataMap = metadataResults.reduce((acc, result) => {
          if (result && result.metadata) {
            acc[result.sourceId] = result.metadata;
          }
          return acc;
        }, {} as Record<string, SourceMetadata>);

        setSourceMetadataMap(newMetadataMap);
      } catch (error) {
        console.error('Error fetching sources:', error);
        setError(error instanceof Error ? error.message : 'Failed to load sources. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSourcesAndMetadata();
  }, [teammate?.uuid, isOpen]);

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

  // Update the renderSourceCard function to handle tools better
  const renderSourceCard = (source: Source, metadata: SourceMetadata | undefined) => {
    if (!metadata) return null;
    const tools = metadata.metadata?.tools || [];
    const gitMetadata = tools[0]?.metadata || {};

    const toggleTool = (toolName: string) => {
      setExpandedTools(prev => ({
        ...prev,
        [toolName]: !prev[toolName]
      }));
    };

    return (
      <div className="bg-[#1A1F2E] rounded-lg p-4 border border-[#2A3347] mb-4">
        {/* Source Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-md bg-[#0F1629]">
              <FolderGit className="h-5 w-5 text-purple-400" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-white">{getSourceName(source, metadata).name}</h3>
              <p className="text-xs text-slate-400 mt-1">{metadata.metadata?.description}</p>
            </div>
          </div>
        </div>

        {/* Git Metadata */}
        {gitMetadata && (
          <div className="grid grid-cols-2 gap-3 mb-4 p-3 bg-[#0F1629] rounded-lg">
            {gitMetadata.git_branch && (
              <div className="flex items-center gap-2">
                <GitBranch className="h-4 w-4 text-blue-400" />
                <span className="text-xs text-slate-300">Branch: {gitMetadata.git_branch}</span>
              </div>
            )}
            {gitMetadata.repository && (
              <div className="flex items-center gap-2">
                <GitMerge className="h-4 w-4 text-purple-400" />
                <span className="text-xs text-slate-300">Repo: {gitMetadata.repository}</span>
              </div>
            )}
          </div>
        )}

        {/* Tools List */}
        {tools.length > 0 && (
          <div className="space-y-3">
            <div className="text-xs font-medium text-slate-400">Available Tools</div>
            {tools.map((tool, index) => (
              <div key={`${source.sourceId}-${tool.name}`} className="bg-[#242E3F] rounded-lg">
                {/* Tool Header */}
                <div 
                  className="flex items-center justify-between p-4 cursor-pointer hover:bg-[#2A3347] transition-colors"
                  onClick={() => toggleTool(tool.name)}
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-md bg-[#1A1F2E]">
                      {tool.icon_url ? (
                        <img src={tool.icon_url} alt={tool.name} className="h-5 w-5" />
                      ) : (
                        getTypeIcon(tool)
                      )}
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-white">{tool.name}</h4>
                      <p className="text-xs text-slate-400 mt-1">{tool.description}</p>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm">
                    {expandedTools[tool.name] ? (
                      <ChevronUp className="h-4 w-4" />
                    ) : (
                      <ChevronDown className="h-4 w-4" />
                    )}
                  </Button>
                </div>

                {/* Tool Details (Expanded) */}
                {expandedTools[tool.name] && (
                  <div className="border-t border-[#1A1F2E] p-4 space-y-4">
                    {/* Runtime Info */}
                    {(tool.image || tool.env) && (
                      <div className="p-3 bg-[#1A1F2E] rounded-lg">
                        <h5 className="text-xs font-medium text-slate-300 mb-2 flex items-center gap-2">
                          <Container className="h-4 w-4 text-sky-400" />
                          Runtime Configuration
                        </h5>
                        {tool.image && (
                          <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
                            <div className="p-1.5 rounded-md bg-[#0F1629]">
                              <img 
                                src="https://cdn4.iconfinder.com/data/icons/logos-and-brands/512/97_Docker_logo_logos-512.png" 
                                alt="Docker" 
                                className="h-4 w-4"
                              />
                            </div>
                            <code className="bg-[#0F1629] px-2 py-1 rounded flex-1">{tool.image}</code>
                            <span className="px-1.5 py-0.5 bg-blue-500/10 text-blue-400 rounded-full text-[10px]">
                              Docker Image
                            </span>
                          </div>
                        )}
                        {tool.env && Object.keys(tool.env).length > 0 && (
                          <div className="space-y-1">
                            <div className="text-xs text-slate-400">Environment Variables</div>
                            {Object.entries(tool.env).map(([key, value]) => (
                              <div key={key} className="flex items-center gap-2 text-xs">
                                <Variable className="h-3.5 w-3.5 text-purple-400" />
                                <span className="text-slate-300">{key}</span>
                                <span className="text-slate-500">=</span>
                                <code className="text-slate-400 bg-[#0F1629] px-2 py-0.5 rounded">
                                  {value}
                                </code>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Parameters */}
                    {tool.args && tool.args.length > 0 && (
                      <div className="p-3 bg-[#1A1F2E] rounded-lg">
                        <h5 className="text-xs font-medium text-slate-300 mb-2 flex items-center gap-2">
                          <Settings className="h-4 w-4 text-purple-400" />
                          Parameters
                        </h5>
                        <div className="grid grid-cols-2 gap-2">
                          {tool.args.map((arg: any, index: number) => (
                            <div key={index} className="bg-[#0F1629] p-2 rounded">
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-medium text-white">{arg.name}</span>
                                {arg.required && (
                                  <span className="text-[10px] px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded-full">
                                    Required
                                  </span>
                                )}
                              </div>
                              <div className="text-xs text-slate-400 mt-1">{arg.type}</div>
                              {arg.description && (
                                <div className="text-xs text-slate-500 mt-1">{arg.description}</div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  // Add new helper function for integration details
  const getIntegrationDetails = (integration: string) => {
    return integrations.find(i => 
      i.name.toLowerCase() === integration.toLowerCase() ||
      i.integration_type.toLowerCase() === integration.toLowerCase()
    );
  };

  // Update the integrations section render
  const renderIntegrationCard = (integration: string) => {
    const details = getIntegrationDetails(integration);
    const isOAuth = details?.auth_type === 'oauth';
    const isManagedByTerraform = details?.managed_by === 'terraform';

    return (
      <div className="bg-[#1A1F2E] rounded-lg p-4 border border-[#2A3347]">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-md bg-[#0F1629]">
              {getIcon(integration)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-medium text-white">
                  {details?.name || integration}
                </h4>
                {isManagedByTerraform && (
                  <div className="flex items-center gap-1 px-2 py-1 rounded-md bg-[#0F1629]">
                    <img src="/terraform-icon.svg" alt="Terraform" className="h-4 w-4" />
                    <span className="text-xs text-purple-400">Terraform Managed</span>
                  </div>
                )}
                <span className="text-xs px-2 py-1 rounded-full bg-[#0F1629] text-blue-400">
                  {details?.integration_type || 'Unknown Type'}
                </span>
              </div>
              {details?.description && (
                <p className="text-xs text-slate-400 mt-1">{details.description}</p>
              )}
            </div>
          </div>
        </div>

        {/* Integration Details */}
        <div className="mt-4 space-y-3">
          {/* Configurations */}
          {details?.configs && details.configs.length > 0 && (
            <div>
              <h5 className="text-xs font-medium text-slate-300 mb-2">Configurations</h5>
              <div className="flex flex-wrap gap-2">
                {details.configs.map(config => (
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

          {/* OAuth Warning */}
          {isOAuth && (
            <div className="flex items-start gap-2 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
              <Info className="h-4 w-4 text-blue-400 mt-0.5" />
              <div>
                <p className="text-xs text-blue-400 font-medium mb-1">OAuth Authentication Required</p>
                <p className="text-xs text-blue-400/80">
                  You'll be prompted to authenticate through OAuth when you first use this integration.
                  This ensures secure access to the service.
                </p>
              </div>
            </div>
          )}

          {/* Metadata */}
          {details?.kubiya_metadata && (
            <div className="grid grid-cols-2 gap-2 p-3 bg-[#0F1629] rounded-lg">
              <div className="text-xs">
                <span className="text-slate-400">Created: </span>
                <span className="text-slate-300">
                  {new Date(details.kubiya_metadata.created_at).toLocaleDateString()}
                </span>
              </div>
              <div className="text-xs">
                <span className="text-slate-400">Last Updated: </span>
                <span className="text-slate-300">
                  {new Date(details.kubiya_metadata.last_updated).toLocaleDateString()}
                </span>
              </div>
              {details.kubiya_metadata.user_created && (
                <div className="text-xs">
                  <span className="text-slate-400">Created By: </span>
                  <span className="text-slate-300">{details.kubiya_metadata.user_created}</span>
                </div>
              )}
              {details.kubiya_metadata.user_last_updated && (
                <div className="text-xs">
                  <span className="text-slate-400">Updated By: </span>
                  <span className="text-slate-300">{details.kubiya_metadata.user_last_updated}</span>
                </div>
              )}
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
      case 'overview': return Info;
      case 'sources': return FolderGit;
      case 'integrations': return Globe;
      case 'runtime': return Container;
      case 'security': return Lock;
      case 'model': return Database;
      default: return undefined;
    }
  };

  const getSectionCount = (sectionId: string): number | undefined => {
    switch (sectionId) {
      case 'sources':
        return sources.length;
      case 'integrations':
        return teammate?.integrations?.length || 0;
      case 'runtime':
        return (teammate?.runners?.length || 0) + 
               (Object.keys(teammate?.environment_variables || {}).length || 0);
      case 'security':
        return ((teammate?.allowed_groups?.length || 0) + 
                (teammate?.allowed_users?.length || 0));
      default:
        return undefined;
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
    <>
      {/* Git Repository Info Banner */}
      <div className="px-4 py-3 bg-blue-500/10 border-y border-blue-500/20">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-md bg-[#0F1629]">
            <GitBranch className="h-5 w-5 text-blue-400" />
          </div>
          <div>
            <h4 className="text-sm font-medium text-blue-400">Source Control Integration</h4>
            <p className="text-xs text-blue-400/80 mt-0.5">
              Tools and configurations are managed through Git repositories
            </p>
          </div>
        </div>
      </div>

      <div className="p-4">
        {/* Search with tool count */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-md bg-[#0F1629]">
              <Wrench className="h-4 w-4 text-purple-400" />
            </div>
            <span className="text-sm text-slate-300">
              {sources.reduce((acc, source) => 
                acc + (sourceMetadataMap[source.sourceId]?.metadata?.tools?.length || 0), 0
              )} tools available
            </span>
          </div>
          <div className="relative w-64">
            <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Filter tools..."
              value={toolSearch}
              onChange={(e) => setToolSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-[#0F1629] border border-[#2A3347] rounded-md text-sm text-slate-300 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/20"
            />
          </div>
        </div>

        {/* Sources and Tools List */}
        <div className="space-y-4">
          {sources.map((source) => {
            const metadata = sourceMetadataMap[source.sourceId];
            const tools = metadata?.metadata?.tools || [];
            const filteredTools = tools.filter(tool => 
              tool.name.toLowerCase().includes(toolSearch.toLowerCase()) ||
              tool.description?.toLowerCase().includes(toolSearch.toLowerCase())
            );

            if (toolSearch && filteredTools.length === 0) return null;

            return (
              <div key={source.sourceId}>
                {renderSourceCard(source, metadata)}
              </div>
            );
          })}
        </div>
      </div>
    </>
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

  return (
    <div className="fixed inset-0 z-50" aria-modal="true" role="dialog">
      <div 
        className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity" 
        onClick={onClose} 
      />
      <div className="fixed inset-0 overflow-y-auto">
        <div className="flex min-h-full items-center justify-center p-4">
          <div className="relative transform overflow-hidden rounded-lg bg-[#0F1629] shadow-xl transition-all w-full max-w-4xl">
            {/* Modal Header */}
            <div className="flex justify-between items-start p-6 border-b border-[#2A3347]">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-lg bg-purple-500/10">
                  <Code2 className="h-6 w-6 text-purple-400" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">
                    {teammate?.name || 'Teammate Details'}
                  </h2>
                  <p className="text-slate-400">
                    {teammate?.description || 'No description available'}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                className="text-slate-400 hover:text-white"
                onClick={onClose}
              >
                <X className="h-5 w-5" />
              </Button>
            </div>

            {/* Modal Content */}
            <div className="p-6">
              {error && <ErrorState message={error} />}
              
              {isLoading ? (
                <LoadingState />
              ) : (
                <div className="space-y-4">
                  {sections.map(section => (
                    <div key={section.id} className="bg-[#1E293B] rounded-lg overflow-hidden">
                      <SectionHeader 
                        title={section.title} 
                        sectionId={section.id} 
                        icon={getSectionIcon(section.id)}
                        count={getSectionCount(section.id)}
                      />
                      {section.isExpanded && renderSectionContent(section.id)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 