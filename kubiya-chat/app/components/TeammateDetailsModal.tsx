import { useEffect, useState } from 'react';
import { Button } from './button';
import { Box, Container, FileCode, GitBranch, Settings, Wrench, ChevronUp, ChevronDown, Link2 } from 'lucide-react';

interface Teammate {
  uuid: string;
  name: string;
  description?: string;
  llm_model?: string;
  instruction_type?: string;
  sources?: string[];
}

interface Source {
  sourceId: string;
  name?: string;
  description?: string;
}

interface TeammateDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  teammate: Teammate | null;
  capabilities: any;
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
      args?: Array<{
        name: string;
        type: string;
        description?: string;
        required?: boolean;
      }>;
      metadata?: {
        git_url?: string;
        git_branch?: string;
        git_path?: string;
        docker_image?: string;
      };
      parameters?: Array<{
        name: string;
        type: string;
        description?: string;
        required?: boolean;
      }>;
    }>;
  };
}

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

export function TeammateDetailsModal({ isOpen, onClose, teammate, capabilities }: TeammateDetailsModalProps) {
  const [sources, setSources] = useState<Source[]>([]);
  const [sourceMetadataMap, setSourceMetadataMap] = useState<Record<string, SourceMetadata>>({});
  const [expandedTool, setExpandedTool] = useState<string | null>(null);
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPreviewMode, setIsPreviewMode] = useState(true);

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

  // Remove the separate metadata fetch effect since we're fetching all metadata in parallel
  useEffect(() => {
    if (selectedSourceId && !sourceMetadataMap[selectedSourceId]) {
      console.log('Waiting for metadata to load for source:', selectedSourceId);
    }
  }, [selectedSourceId, sourceMetadataMap]);

  // Reset expanded state when switching sources
  useEffect(() => {
    setExpandedTool(null);
  }, [selectedSourceId]);

  if (!isOpen) return null;

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

  return (
    <div className="fixed inset-0 z-50" aria-modal="true" role="dialog">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity" onClick={onClose} />
      <div className="fixed inset-0 overflow-y-auto">
        <div className="flex min-h-full items-center justify-center p-4">
          <div className="relative transform overflow-hidden rounded-lg bg-[#0F1629] shadow-xl transition-all w-full max-w-3xl">
            <div className="p-6">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">
                    {teammate?.name || 'Teammate Details'}
                  </h2>
                  <p className="text-slate-400">
                    {teammate?.description || 'No description available'}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  className="text-slate-400 hover:text-white"
                  onClick={onClose}
                >
                  ✕
                </Button>
              </div>

              {error && (
                <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                  <p className="text-red-400 text-sm">{error}</p>
                </div>
              )}

              {isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Runtime Environment */}
                  {capabilities?.runner && (
                    <div className="bg-[#1E293B] rounded-lg p-4">
                      <h3 className="text-sm font-medium text-slate-300 mb-2">Runtime Environment</h3>
                      <div className="flex items-center gap-2 text-sm text-slate-400">
                        <img 
                          src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Kubernetes_logo_without_workmark.svg/2109px-Kubernetes_logo_without_workmark.svg.png" 
                          alt="Kubernetes" 
                          className="h-4 w-4 object-contain"
                        />
                        <span>{capabilities.runner}</span>
                      </div>
                    </div>
                  )}

                  {/* Integrations */}
                  {capabilities?.integrations && capabilities.integrations.length > 0 && (
                    <div className="bg-[#1E293B] rounded-lg p-4">
                      <h3 className="text-sm font-medium text-slate-300 mb-3">Available Integrations</h3>
                      <div className="flex flex-wrap gap-2">
                        {capabilities.integrations.map((integration: any, index: number) => (
                          <div
                            key={index}
                            className="flex items-center gap-2 px-3 py-2 bg-[#2A3347] rounded-md border border-[#3D4B5E]"
                          >
                            {getIcon(integration)}
                            <span className="text-sm text-slate-300">
                              {typeof integration === 'string' ? integration : integration.name}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tools Section */}
                  {sources.length > 0 && (
                    <div className="bg-[#1E293B] rounded-lg p-4">
                      <div className="flex items-center justify-between mb-6">
                        <div>
                          <h3 className="text-sm font-medium text-slate-300">Available Tools</h3>
                          <p className="text-xs text-slate-400 mt-1">
                            {selectedTools.length} tools available
                          </p>
                        </div>
                        <div className="flex gap-2">
                          {sources.length > 1 && sources.map((source) => (
                            <Button
                              key={source.sourceId}
                              variant={selectedSourceId === source.sourceId ? "default" : "secondary"}
                              size="sm"
                              onClick={() => setSelectedSourceId(source.sourceId)}
                              className={`whitespace-nowrap ${
                                selectedSourceId === source.sourceId 
                                  ? 'bg-purple-500 hover:bg-purple-600' 
                                  : 'bg-[#2A3347] hover:bg-[#374151]'
                              }`}
                            >
                              {source.name || `Source ${source.sourceId.slice(0, 8)}`}
                            </Button>
                          ))}
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => setIsPreviewMode(!isPreviewMode)}
                            className="bg-[#2A3347] hover:bg-[#374151] text-white"
                          >
                            {isPreviewMode ? 'Show All Details' : 'Show Preview'}
                          </Button>
                        </div>
                      </div>

                      {/* Tools Grid/List */}
                      <div className={`${isPreviewMode ? 'grid grid-cols-2 gap-4' : 'space-y-4'}`}>
                        {selectedTools.map((tool, index) => (
                          <div 
                            key={index} 
                            className={`bg-[#2A3347] rounded-lg border border-[#3D4B5E] transition-all duration-200 ${
                              isPreviewMode ? 'p-3 hover:bg-[#374151] cursor-pointer' : 'p-4'
                            }`}
                            onClick={() => {
                              if (isPreviewMode) {
                                setIsPreviewMode(false);
                                setExpandedTool(tool.name);
                              }
                            }}
                          >
                            <div className="flex items-start gap-3">
                              <div className="mt-0.5 p-1.5 rounded-md bg-[#1A1F2E]">
                                {tool.icon_url ? (
                                  <img src={tool.icon_url} alt={tool.name} className="h-5 w-5 object-contain" />
                                ) : (
                                  getTypeIcon(tool)
                                )}
                              </div>
                              
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium text-white text-sm">{tool.name}</span>
                                  {tool.type && (
                                    <span className="text-xs px-2 py-0.5 rounded-md bg-[#1A1F2E] text-purple-400">
                                      {tool.type}
                                    </span>
                                  )}
                                  {!isPreviewMode && (
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      className="ml-auto text-slate-400 hover:text-white"
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
                                </div>
                                
                                <p className={`text-sm text-slate-400 mt-1 ${isPreviewMode ? 'line-clamp-2' : ''}`}>
                                  {tool.description}
                                </p>

                                {/* Expanded Details */}
                                {!isPreviewMode && expandedTool === tool.name && (
                                  <div className="mt-4 space-y-4 border-t border-[#3D4B5E] pt-4">
                                    {/* Git Info */}
                                    {(tool.metadata?.git_url || tool.metadata?.git_branch || tool.metadata?.git_path) && (
                                      <div className="space-y-2">
                                        <h4 className="text-xs font-medium text-slate-300 flex items-center gap-2">
                                          <GitBranch className="h-3.5 w-3.5" />
                                          Source Details
                                        </h4>
                                        <div className="space-y-1.5 pl-5">
                                          {tool.metadata.git_url && (
                                            <div className="flex items-center gap-2 text-xs text-slate-400">
                                              <Link2 className="h-3.5 w-3.5 text-blue-400" />
                                              <a href={tool.metadata.git_url} target="_blank" rel="noopener noreferrer" 
                                                className="hover:text-white transition-colors truncate">
                                                {tool.metadata.git_url}
                                              </a>
                                            </div>
                                          )}
                                          {tool.metadata.git_branch && (
                                            <div className="flex items-center gap-2 text-xs text-slate-400">
                                              <GitBranch className="h-3.5 w-3.5 text-purple-400" />
                                              <span>{tool.metadata.git_branch}</span>
                                            </div>
                                          )}
                                          {tool.metadata.git_path && (
                                            <div className="flex items-center gap-2 text-xs text-slate-400">
                                              <FileCode className="h-3.5 w-3.5 text-blue-400" />
                                              <span className="truncate">{tool.metadata.git_path}</span>
                                            </div>
                                          )}
                                        </div>
                                      </div>
                                    )}

                                    {/* Parameters */}
                                    {tool.parameters && tool.parameters.length > 0 && (
                                      <div className="space-y-2">
                                        <h4 className="text-xs font-medium text-slate-300 flex items-center gap-2">
                                          <Settings className="h-3.5 w-3.5" />
                                          Parameters
                                        </h4>
                                        <div className="space-y-2 pl-5">
                                          {tool.parameters.map((param, pIndex) => (
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
                                  </div>
                                )}
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
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 