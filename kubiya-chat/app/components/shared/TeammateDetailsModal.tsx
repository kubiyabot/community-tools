"use client";

import { useState, useEffect } from 'react';
import { Button } from '../button';
import { 
  ChevronDown, ChevronUp, Terminal, Info, Box, X, ExternalLink, GitBranch, FileCode,
  Container, GitPullRequest, Wrench, Settings, Search, Loader2, Link2, GitCommit
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

interface TeammateDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  teammate: Teammate | null;
  capabilities: any;
}

export function TeammateDetailsModal({ isOpen, onClose, teammate, capabilities }: TeammateDetailsModalProps) {
  const [sources, setSources] = useState<Source[]>([]);
  const [sourceMetadataMap, setSourceMetadataMap] = useState<Record<string, SourceMetadata>>({});
  const [expandedTool, setExpandedTool] = useState<string | null>(null);
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPreviewMode, setIsPreviewMode] = useState(true);
  const [expandedSource, setExpandedSource] = useState<string | null>(null);

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setExpandedTool(null);
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
        // Fetch sources with correct API endpoint
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

        // Fetch metadata for all sources in parallel with correct endpoint
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

        // Wait for all metadata requests to complete
        const metadataResults = await Promise.all(metadataPromises);

        // Build metadata map from successful results
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
    setExpandedTool(null);
  }, [selectedSourceId]);

  if (!isOpen) return null;

  const getIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'terraform': return <Box className="h-5 w-5 text-violet-400" />;
      case 'python': return <FileCode className="h-5 w-5 text-blue-400" />;
      case 'docker': return <Container className="h-5 w-5 text-sky-400" />;
      case 'kubernetes': return <Settings className="h-5 w-5 text-green-400" />;
      default: return <Wrench className="h-5 w-5 text-purple-400" />;
    }
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

  const getTypeIcon = (tool: any) => {
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

  // Update renderSourceDetails to include commit information and better URL display
  const renderSourceDetails = (source: Source, metadata: SourceMetadata | undefined) => {
    if (!metadata) return null;

    const sourceUrl = getSourceUrl(metadata);
    const { name, isGithubFolder } = getSourceName(source, metadata);

    return (
      <div className="mt-3 pt-3 border-t border-[#3D4B5E]">
        {metadata.metadata.description && (
          <p className="text-sm text-slate-400 mb-3">{metadata.metadata.description}</p>
        )}
        
        {sourceUrl && (
          <div className="space-y-2 mb-4">
            <div className="flex items-center gap-2 text-sm">
              <GitBranch className="h-4 w-4 text-blue-400" />
              <a 
                href={sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-slate-300 hover:text-white transition-colors truncate max-w-[300px] font-medium"
              >
                {name}
              </a>
              {isGithubFolder && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-[#1A1F2E] text-purple-400">
                  GitHub Folder
                </span>
              )}
            </div>
            <div className="text-xs text-slate-400 pl-6">
              <a 
                href={sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-white transition-colors truncate block"
              >
                {sourceUrl}
              </a>
            </div>
            {metadata.metadata.tools?.[0]?.metadata?.git_branch && (
              <div className="flex items-center gap-2 text-xs text-slate-400 pl-6">
                <GitCommit className="h-3.5 w-3.5" />
                <span>Branch: {metadata.metadata.tools[0].metadata.git_branch}</span>
              </div>
            )}
          </div>
        )}

        {metadata.metadata.tools && metadata.metadata.tools.length > 0 && (
          <div>
            <div className="text-xs font-medium text-slate-400 mb-2">Available Tools</div>
            <div className="grid grid-cols-2 gap-2">
              {metadata.metadata.tools.map((tool, index) => (
                <div
                  key={index}
                  onClick={() => {
                    setIsPreviewMode(false);
                    setSelectedSourceId(source.sourceId);
                    setExpandedTool(tool.name);
                  }}
                  className="flex items-start gap-2 bg-[#1A1F2E] p-2 rounded-md cursor-pointer hover:bg-[#242E3F] transition-colors"
                >
                  <div className="mt-0.5 p-1.5 rounded-md bg-[#0F1629] flex-shrink-0">
                    {tool.icon_url ? (
                      <img src={tool.icon_url} alt={tool.name} className="h-4 w-4 object-contain" />
                    ) : (
                      getTypeIcon(tool)
                    )}
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-white truncate">{tool.name}</div>
                    <div className="text-xs text-slate-400 line-clamp-1">{tool.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Update renderToolDetails to use basic syntax highlighting
  const renderToolDetails = (tool: any) => {
    const getLanguageFromType = (type: string) => {
      switch (type?.toLowerCase()) {
        case 'python': return 'language-python';
        case 'typescript':
        case 'javascript': return 'language-javascript';
        case 'terraform': return 'language-hcl';
        case 'docker': return 'language-dockerfile';
        case 'kubernetes': return 'language-yaml';
        default: return 'language-plaintext';
      }
    };

    return (
      <div className="mt-4 space-y-4 border-t border-[#3D4B5E] pt-4">
        {/* Source URL and Git Info */}
        {(tool.source?.url || tool.metadata?.git_branch) && (
          <div className="space-y-2">
            <h4 className="text-xs font-medium text-slate-300 flex items-center gap-2">
              <GitBranch className="h-3.5 w-3.5" />
              Source Details
            </h4>
            <div className="space-y-1.5 pl-5">
              {tool.source?.url && (
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <Link2 className="h-3.5 w-3.5 text-blue-400" />
                  <a 
                    href={tool.source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-white transition-colors truncate"
                  >
                    {tool.source.url}
                  </a>
                </div>
              )}
              {tool.metadata?.git_branch && (
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <GitCommit className="h-3.5 w-3.5 text-purple-400" />
                  <span>Branch: {tool.metadata.git_branch}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Docker/Runtime Info */}
        {(tool.type === 'docker' || tool.image) && (
          <div className="space-y-2">
            <h4 className="text-xs font-medium text-slate-300 flex items-center gap-2">
              <Container className="h-3.5 w-3.5" />
              Runtime Details
            </h4>
            <div className="space-y-1.5 pl-5">
              {tool.image && (
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <Container className="h-3.5 w-3.5 text-sky-400" />
                  <span className="font-mono">{tool.image}</span>
                </div>
              )}
              {tool.type && (
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <Settings className="h-3.5 w-3.5 text-purple-400" />
                  <span>Type: {tool.type}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Parameters/Arguments */}
        {(tool.parameters || tool.args) && (
          <div className="space-y-2">
            <h4 className="text-xs font-medium text-slate-300 flex items-center gap-2">
              <Settings className="h-3.5 w-3.5" />
              Parameters
            </h4>
            <div className="space-y-2 pl-5">
              {(tool.parameters || tool.args).map((param: any, pIndex: number) => (
                <div key={pIndex} className="flex items-start gap-2 bg-[#1A1F2E] p-2 rounded-md">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-sm font-medium text-white">{param.name}</span>
                      {param.required && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-red-500/20 text-red-400 font-medium">
                          Required
                        </span>
                      )}
                      <span className="text-xs text-slate-400 font-mono">{param.type}</span>
                    </div>
                    {param.description && (
                      <p className="text-xs text-slate-400 mt-1">{param.description}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Files and Volumes */}
        {(tool.with_files || tool.with_volumes) && (
          <div className="space-y-2">
            <h4 className="text-xs font-medium text-slate-300 flex items-center gap-2">
              <FileCode className="h-3.5 w-3.5" />
              Mounted Resources
            </h4>
            <div className="space-y-3 pl-5">
              {tool.with_files && tool.with_files.length > 0 && (
                <div>
                  <div className="text-xs text-slate-400 mb-1">Files</div>
                  <div className="space-y-1">
                    {tool.with_files.map((file: any, index: number) => (
                      <div key={index} className="flex items-center gap-2 text-xs bg-[#1A1F2E] p-1.5 rounded">
                        <FileCode className="h-3.5 w-3.5 text-blue-400" />
                        <span className="font-mono text-slate-300">{file.source}</span>
                        <span className="text-slate-500">→</span>
                        <span className="font-mono text-slate-300">{file.target}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {tool.with_volumes && tool.with_volumes.length > 0 && (
                <div>
                  <div className="text-xs text-slate-400 mb-1">Volumes</div>
                  <div className="space-y-1">
                    {tool.with_volumes.map((volume: any, index: number) => (
                      <div key={index} className="flex items-center gap-2 text-xs bg-[#1A1F2E] p-1.5 rounded">
                        <Container className="h-3.5 w-3.5 text-purple-400" />
                        <span className="font-mono text-slate-300">{volume.source}</span>
                        <span className="text-slate-500">→</span>
                        <span className="font-mono text-slate-300">{volume.target}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Source Code Preview */}
        {tool.content && (
          <div className="space-y-2">
            <h4 className="text-xs font-medium text-slate-300 flex items-center gap-2">
              <FileCode className="h-3.5 w-3.5" />
              Source Code
            </h4>
            <div className="bg-[#1A1F2E] rounded-md overflow-hidden">
              <pre className={`${getLanguageFromType(tool.type)} text-xs text-slate-300 font-mono p-4 overflow-x-auto`}>
                <code>{tool.content}</code>
              </pre>
            </div>
          </div>
        )}
      </div>
    );
  };

  // Add helper function to get source URL from tools
  const getSourceUrl = (metadata: SourceMetadata | undefined) => {
    if (!metadata?.metadata?.tools?.length) return null;
    return metadata.metadata.tools[0]?.source?.url || null;
  };

  return (
    <div className="fixed inset-0 z-50" aria-modal="true" role="dialog">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity" onClick={onClose} />
      <div className="fixed inset-0 overflow-y-auto">
        <div className="flex min-h-full items-center justify-center p-4">
          <div className="relative transform overflow-hidden rounded-lg bg-[#0F1629] shadow-xl transition-all w-full max-w-4xl">
            {isLoading ? (
              <div className="flex items-center justify-center p-8">
                <div className="flex flex-col items-center gap-3">
                  <Loader2 className="h-8 w-8 text-purple-500 animate-spin" />
                  <p className="text-sm text-slate-400">Loading teammate details...</p>
                </div>
              </div>
            ) : (
              <div className="p-6">
                {/* Header */}
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <h2 className="text-2xl font-bold text-white">{teammate?.name}</h2>
                      {teammate?.instruction_type && (
                        <span className="px-2.5 py-1 rounded-full bg-purple-500/20 text-purple-300 text-sm font-medium">
                          {teammate.instruction_type}
                        </span>
                      )}
                    </div>
                    <p className="text-slate-400">{teammate?.description}</p>
                  </div>
                  <Button
                    variant="ghost"
                    className="text-slate-400 hover:text-white"
                    onClick={onClose}
                  >
                    ✕
                  </Button>
                </div>

                <div className="space-y-6">
                  {/* Core Details */}
                  <div className="bg-[#1E293B] rounded-lg p-4">
                    <h3 className="text-sm font-medium text-slate-300 mb-3">Core Information</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-xs text-slate-400">Language Model</div>
                        <div className="text-sm text-slate-300">{teammate?.llm_model || 'Not specified'}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-400">Docker Image</div>
                        <div className="text-sm text-slate-300">{teammate?.image || 'Not specified'}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-400">Created At</div>
                        <div className="text-sm text-slate-300">{formatDate(teammate?.metadata?.created_at)}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-400">Last Updated</div>
                        <div className="text-sm text-slate-300">{formatDate(teammate?.metadata?.last_updated)}</div>
                      </div>
                    </div>
                  </div>

                  {/* Integrations */}
                  {teammate?.integrations && teammate.integrations.length > 0 && (
                    <div className="bg-[#1E293B] rounded-lg p-4">
                      <h3 className="text-sm font-medium text-slate-300 mb-3">Integrations</h3>
                      <div className="flex flex-wrap gap-2">
                        {teammate.integrations.map((integration, index) => (
                          <div
                            key={index}
                            className="flex items-center gap-2 px-3 py-2 bg-[#2A3347] rounded-md border border-[#3D4B5E]"
                          >
                            {getIcon(integration)}
                            <span className="text-sm text-slate-300">{integration}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Runners */}
                  {teammate?.runners && teammate.runners.length > 0 && (
                    <div className="bg-[#1E293B] rounded-lg p-4">
                      <h3 className="text-sm font-medium text-slate-300 mb-3">Runtime Environment</h3>
                      <div className="flex flex-wrap gap-2">
                        {teammate.runners.map((runner, index) => (
                          <div
                            key={index}
                            className="flex items-center gap-2 px-3 py-2 bg-[#2A3347] rounded-md border border-[#3D4B5E]"
                          >
                            <Container className="h-4 w-4 text-sky-400" />
                            <span className="text-sm text-slate-300">{runner}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Unified Tools Section */}
                  {sources.length > 0 && (
                    <div className="bg-[#1E293B] rounded-lg p-4">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h3 className="text-sm font-medium text-slate-300">Tools & Integrations</h3>
                          <p className="text-xs text-slate-400 mt-1">
                            {selectedSourceId && (
                              <>
                                {getSourceName(
                                  sources.find(s => s.sourceId === selectedSourceId)!,
                                  sourceMetadataMap[selectedSourceId]
                                ).name}
                              </>
                            )}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => setIsPreviewMode(!isPreviewMode)}
                            className="bg-[#2A3347] hover:bg-[#374151] text-white"
                          >
                            {isPreviewMode ? (
                              <>
                                <FileCode className="h-4 w-4 mr-1.5" />
                                Show Details
                              </>
                            ) : (
                              <>
                                <Box className="h-4 w-4 mr-1.5" />
                                Show Preview
                              </>
                            )}
                          </Button>
                        </div>
                      </div>

                      {/* Source Selection */}
                      {sources.length > 1 && (
                        <div className="mb-4">
                          <div className="text-xs font-medium text-slate-400 mb-2">Available Sources</div>
                          <div className="flex flex-wrap gap-2 p-2 bg-[#1A1F2E] rounded-lg">
                            {sources.map((source) => {
                              const metadata = sourceMetadataMap[source.sourceId];
                              const { name, isGithubFolder } = getSourceName(source, metadata);
                              const isSelected = selectedSourceId === source.sourceId;
                              const sourceUrl = metadata?.metadata?.tools?.[0]?.source?.url;
                              const gitBranch = metadata?.metadata?.tools?.[0]?.metadata?.git_branch;
                              
                              return (
                                <button
                                  key={source.sourceId}
                                  onClick={() => setSelectedSourceId(source.sourceId)}
                                  className={`group relative flex items-center gap-2 px-3 py-2 rounded-md transition-all ${
                                    isSelected 
                                      ? 'bg-purple-500 text-white shadow-lg shadow-purple-500/20' 
                                      : 'bg-[#2A3347] text-slate-300 hover:bg-[#374151] hover:text-white hover:shadow-md'
                                  }`}
                                >
                                  <div className="flex items-center gap-2 min-w-0">
                                    <div className={`p-1.5 rounded-md ${isSelected ? 'bg-purple-400/20' : 'bg-[#1A1F2E]'}`}>
                                      <GitBranch className={`h-4 w-4 ${isSelected ? 'text-white' : 'text-purple-400'}`} />
                                    </div>
                                    <div className="min-w-0">
                                      <div className="font-medium truncate max-w-[150px]">{name}</div>
                                      {gitBranch && (
                                        <div className="flex items-center gap-1 text-xs opacity-80">
                                          <GitCommit className="h-3 w-3" />
                                          <span className="truncate">{gitBranch}</span>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                  {isGithubFolder && (
                                    <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                                      isSelected ? 'bg-purple-400/20 text-white' : 'bg-[#1A1F2E] text-purple-400'
                                    }`}>
                                      Folder
                                    </span>
                                  )}
                                  {sourceUrl && (
                                    <a
                                      href={sourceUrl}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      onClick={(e) => e.stopPropagation()}
                                      className={`absolute hidden group-hover:flex items-center gap-2 -right-2 top-1/2 -translate-y-1/2 translate-x-full 
                                        px-2 py-1 ml-2 rounded-md ${
                                        isSelected 
                                          ? 'bg-purple-400/20 text-white hover:bg-purple-400/30' 
                                          : 'bg-[#1A1F2E] text-slate-400 hover:text-white hover:bg-[#242E3F]'
                                      }`}
                                    >
                                      <ExternalLink className="h-3.5 w-3.5" />
                                    </a>
                                  )}
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Source Info */}
                      {selectedSourceId && (
                        <div className="mb-4 p-3 bg-[#1A1F2E] rounded-lg">
                          <div className="flex items-start gap-3">
                            <div className="p-2 rounded-md bg-[#2A3347]">
                              <GitBranch className="h-5 w-5 text-purple-400" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-2">
                                <h4 className="text-sm font-medium text-white">Repository Details</h4>
                                {sourceMetadataMap[selectedSourceId]?.metadata?.tools?.[0]?.source?.url && (
                                  <a 
                                    href={sourceMetadataMap[selectedSourceId].metadata.tools[0].source.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors px-2 py-1 rounded-md bg-[#2A3347] hover:bg-[#374151]"
                                  >
                                    <ExternalLink className="h-3.5 w-3.5" />
                                    <span>Open in GitHub</span>
                                  </a>
                                )}
                              </div>
                              {sourceMetadataMap[selectedSourceId]?.metadata?.description && (
                                <p className="text-sm text-slate-400 mb-3">
                                  {sourceMetadataMap[selectedSourceId].metadata.description}
                                </p>
                              )}
                              <div className="flex flex-wrap gap-3 text-xs">
                                {sourceMetadataMap[selectedSourceId]?.metadata?.tools?.[0]?.metadata?.git_branch && (
                                  <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-[#2A3347] text-slate-300">
                                    <GitBranch className="h-3.5 w-3.5 text-purple-400" />
                                    <span>Branch: {sourceMetadataMap[selectedSourceId].metadata.tools[0].metadata.git_branch}</span>
                                  </div>
                                )}
                                <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-[#2A3347] text-slate-300">
                                  <Wrench className="h-3.5 w-3.5 text-purple-400" />
                                  <span>{selectedTools.length} tools available</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Tools Grid/List */}
                      <div className={`${isPreviewMode ? 'grid grid-cols-2 gap-4' : 'space-y-4'} max-h-[400px] overflow-y-auto pr-2`}>
                        {selectedTools.map((tool, index) => (
                          <div 
                            key={index} 
                            className={`group bg-[#2A3347] rounded-lg border border-[#3D4B5E] transition-all duration-200 ${
                              isPreviewMode 
                                ? 'p-3 hover:bg-[#374151] cursor-pointer hover:border-purple-500/50 hover:shadow-lg' 
                                : 'p-4'
                            }`}
                            onClick={() => {
                              if (isPreviewMode) {
                                setIsPreviewMode(false);
                                setExpandedTool(tool.name);
                              }
                            }}
                          >
                            <div className="flex items-start gap-3">
                              <div className="mt-0.5 p-1.5 rounded-md bg-[#1A1F2E] flex-shrink-0">
                                {tool.icon_url ? (
                                  <img src={tool.icon_url} alt={tool.name} className="h-5 w-5 object-contain" />
                                ) : (
                                  getTypeIcon(tool)
                                )}
                              </div>
                              
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium text-white text-sm truncate">{tool.name}</span>
                                  {tool.type && (
                                    <span className="text-xs px-2 py-0.5 rounded-md bg-[#1A1F2E] text-purple-400 flex-shrink-0">
                                      {tool.type}
                                    </span>
                                  )}
                                  {!isPreviewMode && (
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      className="ml-auto flex-shrink-0 text-slate-400 hover:text-white"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setExpandedTool(expandedTool === tool.name ? null : tool.name);
                                      }}
                                    >
                                      {expandedTool === tool.name ? (
                                        <ChevronUp className="h-4 w-4" />
                                      ) : (
                                        <ChevronDown className="h-4 w-4" />
                                      )}
                                    </Button>
                                  )}
                                  {isPreviewMode && (
                                    <div className="ml-auto flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 text-xs text-slate-400">
                                      <FileCode className="h-3.5 w-3.5" />
                                      <span>View Details</span>
                                    </div>
                                  )}
                                </div>
                                
                                <p className={`text-sm text-slate-400 mt-1 ${isPreviewMode ? 'line-clamp-2' : ''}`}>
                                  {tool.description}
                                </p>

                                {/* Quick Info */}
                                {isPreviewMode && (
                                  <div className="mt-2 flex items-center gap-3 text-xs text-slate-500">
                                    {tool.type && (
                                      <div className="flex items-center gap-1">
                                        <Settings className="h-3 w-3" />
                                        <span>{tool.type}</span>
                                      </div>
                                    )}
                                    {tool.args && tool.args.length > 0 && (
                                      <div className="flex items-center gap-1">
                                        <Terminal className="h-3 w-3" />
                                        <span>{tool.args.length} parameters</span>
                                      </div>
                                    )}
                                  </div>
                                )}

                                {/* Expanded Details */}
                                {!isPreviewMode && expandedTool === tool.name && renderToolDetails(tool)}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Model Information */}
                  {(capabilities?.llm_model || capabilities?.instruction_type) && (
                    <div className="bg-[#1E293B] rounded-lg p-4">
                      <h3 className="text-sm font-medium text-slate-300 mb-2">Model Information</h3>
                      <div className="grid grid-cols-2 gap-4">
                        {capabilities.llm_model && (
                          <div>
                            <div className="text-xs text-slate-400">Language Model</div>
                            <div className="text-sm text-slate-300">{capabilities.llm_model}</div>
                          </div>
                        )}
                        {capabilities.instruction_type && (
                          <div>
                            <div className="text-xs text-slate-400">Instruction Type</div>
                            <div className="text-sm text-slate-300">{capabilities.instruction_type}</div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 