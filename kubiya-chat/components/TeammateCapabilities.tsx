"use client";

import { useState, useEffect } from 'react';
import { 
  ChevronDown, Terminal, Info, Box, X, ExternalLink, GitBranch, FileCode,
  ChevronLeft, ChevronRight, Container, GitPullRequest, Wrench, Settings, Search
} from 'lucide-react';
import { useConfig } from '@/lib/config-context';

interface TeammateCapability {
  name: string;
  description: string;
  source: {
    id: string;
    name?: string;
    [key: string]: any;
  };
  schema?: any;
  parameters?: any[];
  returns?: any;
  type?: string;
  icon_url?: string;
  metadata?: {
    git_url?: string;
    git_branch?: string;
    git_path?: string;
    docker_image?: string;
    [key: string]: any;
  };
}

interface TeammateCapabilitiesProps {
  teammateId: string;
}

interface GroupedCapabilities {
  [source: string]: TeammateCapability[];
}

const ITEMS_PER_PAGE = 6;

export const TeammateCapabilities = ({ teammateId }: TeammateCapabilitiesProps) => {
  const [capabilities, setCapabilities] = useState<TeammateCapability[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSource, setExpandedSource] = useState<string | null>(null);
  const [expandedTool, setExpandedTool] = useState<string | null>(null);
  const [selectedTool, setSelectedTool] = useState<TeammateCapability | null>(null);
  const [currentPage, setCurrentPage] = useState<{ [key: string]: number }>({});
  const [searchQuery, setSearchQuery] = useState('');
  const { apiKey, authType } = useConfig();

  useEffect(() => {
    const fetchCapabilities = async () => {
      if (!apiKey) {
        setError('Not authenticated');
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch(`/api/teammates/${teammateId}/capabilities`, {
          headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (!response.ok) {
          throw new Error(await response.text());
        }
        
        const data = await response.json();
        setCapabilities(data);
        setError(null);
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Failed to fetch capabilities');
        console.error('Error fetching capabilities:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCapabilities();
  }, [teammateId, apiKey, authType]);

  const groupedCapabilities: GroupedCapabilities = capabilities.reduce((acc, capability) => {
    const sourceName = capability.source?.name || 'Other';
    if (!acc[sourceName]) {
      acc[sourceName] = [];
    }
    acc[sourceName].push(capability);
    return acc;
  }, {} as GroupedCapabilities);

  const filteredGroupedCapabilities = Object.entries(groupedCapabilities).reduce((acc, [source, tools]) => {
    const filteredTools = tools.filter(tool => 
      tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.type?.toLowerCase().includes(searchQuery.toLowerCase())
    );
    if (filteredTools.length > 0) {
      acc[source] = filteredTools;
    }
    return acc;
  }, {} as GroupedCapabilities);

  const getPageItems = (items: TeammateCapability[], sourceName: string) => {
    const page = currentPage[sourceName] || 0;
    return items.slice(page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE);
  };

  const getTypeIcon = (capability: TeammateCapability) => {
    switch (capability.type?.toLowerCase()) {
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

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
        <Terminal className="h-4 w-4 animate-pulse" />
        Loading capabilities...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 text-sm text-red-400">
        <Info className="h-4 w-4" />
        {error}
      </div>
    );
  }

  if (!capabilities.length) {
    return (
      <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
        <Info className="h-4 w-4" />
        No capabilities found
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Search Bar */}
      <div className="sticky -top-3 -mx-3 px-3 pt-3 pb-2 bg-[#2D3B4E] z-10 border-b border-[#3D4B5E]">
        <div className="relative">
          <input
            type="text"
            placeholder="Search capabilities..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#1A1F2E] text-white rounded-md px-9 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[#7C3AED] border border-[#3D4B5E] transition-all duration-200"
          />
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-[#94A3B8]" />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-2.5 p-0.5 hover:bg-[#2D3B4E] rounded-sm transition-colors"
            >
              <X className="h-3 w-3 text-[#94A3B8]" />
            </button>
          )}
        </div>
      </div>

      <div className="space-y-2 mt-2">
        {Object.entries(filteredGroupedCapabilities).map(([sourceName, sourceCapabilities]) => (
          <div key={sourceName} className="rounded-md bg-[#1A1F2E] border border-[#3D4B5E] overflow-hidden">
            <button
              onClick={() => setExpandedSource(expandedSource === sourceName ? null : sourceName)}
              className="w-full px-3 py-2 flex items-center justify-between text-left hover:bg-[#2D3B4E] transition-colors"
            >
              <div className="flex items-center gap-2">
                {sourceCapabilities[0]?.icon_url ? (
                  <img src={sourceCapabilities[0].icon_url} alt={sourceName} className="h-5 w-5 rounded" />
                ) : (
                  <Box className="h-5 w-5 text-[#7C3AED]" />
                )}
                <span className="font-medium text-white text-sm">{sourceName}</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-[#2D3B4E] text-[#94A3B8] font-medium">
                  {sourceCapabilities.length}
                </span>
              </div>
              <ChevronDown 
                className={`h-4 w-4 text-[#94A3B8] transition-transform duration-200 ${
                  expandedSource === sourceName ? 'rotate-180' : ''
                }`}
              />
            </button>

            {expandedSource === sourceName && (
              <div className="border-t border-[#3D4B5E]">
                <div className="p-2 space-y-1.5">
                  {getPageItems(sourceCapabilities, sourceName).map((capability, index) => (
                    <div
                      key={index}
                      className="rounded-md bg-[#2D3B4E] p-2.5 hover:bg-[#3D4B5E] transition-all duration-200 group"
                    >
                      <div className="flex items-start gap-2.5">
                        <div className="mt-0.5 p-1 rounded-md bg-[#1A1F2E] group-hover:bg-[#2D3B4E] transition-colors">
                          {getTypeIcon(capability)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-white text-sm">{capability.name}</span>
                              <div className="flex items-center gap-1">
                                {capability.metadata?.git_url && (
                                  <a
                                    href={capability.metadata.git_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="p-1 hover:bg-[#1A1F2E] rounded-sm transition-colors"
                                  >
                                    <GitBranch className="h-3.5 w-3.5 text-[#3B82F6]" />
                                  </a>
                                )}
                                <button
                                  onClick={() => setSelectedTool(capability)}
                                  className="p-1 hover:bg-[#1A1F2E] rounded-sm transition-colors"
                                >
                                  <Info className="h-3.5 w-3.5 text-[#7C3AED]" />
                                </button>
                              </div>
                            </div>
                          </div>
                          <p className="text-sm text-[#94A3B8] mt-1 line-clamp-2 leading-relaxed">{capability.description}</p>
                          
                          {/* Metadata Section */}
                          <div className="mt-2 space-y-1.5">
                            {/* Source & Type Info */}
                            <div className="flex flex-wrap items-center gap-1.5">
                              {capability.type && (
                                <span className="text-xs px-2 py-0.5 rounded-md bg-[#1A1F2E] text-[#7C3AED] font-medium flex items-center gap-1">
                                  {getTypeIcon(capability)}
                                  {capability.type}
                                </span>
                              )}
                              {capability.metadata?.docker_image && (
                                <span className="text-xs px-2 py-0.5 rounded-md bg-[#1A1F2E] text-[#3B82F6] font-medium flex items-center gap-1">
                                  <Container className="h-3 w-3" />
                                  {capability.metadata.docker_image.split(':')[0]}
                                </span>
                              )}
                            </div>

                            {/* Git Info */}
                            {(capability.metadata?.git_url || capability.metadata?.git_branch || capability.metadata?.git_path) && (
                              <div className="flex flex-wrap items-center gap-1.5">
                                {capability.metadata.git_branch && (
                                  <span className="text-xs px-2 py-0.5 rounded-md bg-[#1A1F2E] text-[#7C3AED] font-medium flex items-center gap-1">
                                    <GitBranch className="h-3 w-3" />
                                    {capability.metadata.git_branch}
                                  </span>
                                )}
                                {capability.metadata.git_path && (
                                  <span className="text-xs px-2 py-0.5 rounded-md bg-[#1A1F2E] text-[#3B82F6] font-medium flex items-center gap-1">
                                    <FileCode className="h-3 w-3" />
                                    {capability.metadata.git_path.split('/').pop()}
                                  </span>
                                )}
                              </div>
                            )}

                            {/* Parameters */}
                            <div className="flex flex-wrap items-center gap-1.5">
                              {capability.parameters && capability.parameters.length > 0 && (
                                <button
                                  onClick={() => setExpandedTool(expandedTool === capability.name ? null : capability.name)}
                                  className="text-xs px-2 py-0.5 rounded-md bg-[#1A1F2E] text-[#7C3AED] font-medium flex items-center gap-1 hover:bg-[#2D3B4E] transition-colors"
                                >
                                  <Settings className="h-3 w-3" />
                                  {capability.parameters.length} Parameters
                                  <ChevronDown 
                                    className={`h-3 w-3 transition-transform duration-200 ${
                                      expandedTool === capability.name ? 'rotate-180' : ''
                                    }`}
                                  />
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>

                      {expandedTool === capability.name && capability.parameters && (
                        <div className="mt-2 pt-2 border-t border-[#3D4B5E]">
                          <div className="space-y-1.5">
                            {capability.parameters.map((param: any, pIndex: number) => (
                              <div key={pIndex} className="flex items-start gap-2 bg-[#1A1F2E] p-2 rounded-md">
                                <Settings className="h-3.5 w-3.5 text-[#7C3AED] mt-0.5" />
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-1.5 flex-wrap">
                                    <span className="text-sm font-medium text-white">{param.name}</span>
                                    {param.required && (
                                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-red-500/20 text-red-400 font-medium">
                                        Required
                                      </span>
                                    )}
                                    <span className="text-xs text-[#94A3B8] font-mono">{param.type}</span>
                                  </div>
                                  {param.description && (
                                    <p className="text-sm text-[#94A3B8] mt-1">{param.description}</p>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                
                {/* Pagination */}
                {sourceCapabilities.length > ITEMS_PER_PAGE && (
                  <div className="flex items-center justify-between px-3 py-2 border-t border-[#3D4B5E] bg-[#1A1F2E]">
                    <button
                      onClick={() => setCurrentPage({
                        ...currentPage,
                        [sourceName]: Math.max(0, (currentPage[sourceName] || 0) - 1)
                      })}
                      disabled={(currentPage[sourceName] || 0) === 0}
                      className="p-1 hover:bg-[#2D3B4E] rounded-sm transition-colors disabled:opacity-50 disabled:hover:bg-transparent"
                    >
                      <ChevronLeft className="h-4 w-4 text-[#94A3B8]" />
                    </button>
                    <span className="text-xs text-[#94A3B8]">
                      Page {(currentPage[sourceName] || 0) + 1} of {Math.ceil(sourceCapabilities.length / ITEMS_PER_PAGE)}
                    </span>
                    <button
                      onClick={() => setCurrentPage({
                        ...currentPage,
                        [sourceName]: Math.min(
                          Math.ceil(sourceCapabilities.length / ITEMS_PER_PAGE) - 1,
                          (currentPage[sourceName] || 0) + 1
                        )
                      })}
                      disabled={(currentPage[sourceName] || 0) >= Math.ceil(sourceCapabilities.length / ITEMS_PER_PAGE) - 1}
                      className="p-1 hover:bg-[#2D3B4E] rounded-sm transition-colors disabled:opacity-50 disabled:hover:bg-transparent"
                    >
                      <ChevronRight className="h-4 w-4 text-[#94A3B8]" />
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Tool Details Modal */}
      {selectedTool && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-[#1A1F2E] rounded-lg border border-[#3D4B5E] w-full max-w-2xl max-h-[90vh] overflow-hidden">
            <div className="flex items-center justify-between p-3 border-b border-[#3D4B5E] bg-[#2D3B4E]">
              <div className="flex items-center gap-2.5">
                <div className="p-1 rounded-md bg-[#1A1F2E]">
                  {getTypeIcon(selectedTool)}
                </div>
                <h3 className="text-base font-medium text-white">{selectedTool.name}</h3>
              </div>
              <button
                onClick={() => setSelectedTool(null)}
                className="p-1.5 hover:bg-[#1A1F2E] rounded-sm transition-colors"
              >
                <X className="h-4 w-4 text-[#94A3B8]" />
              </button>
            </div>
            <div className="p-4 space-y-4 overflow-y-auto max-h-[calc(90vh-4rem)]">
              <div>
                <h4 className="text-sm font-medium text-white mb-2">Description</h4>
                <p className="text-sm text-[#94A3B8] leading-relaxed">{selectedTool.description}</p>
              </div>

              {selectedTool.parameters && selectedTool.parameters.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-white mb-2">Parameters</h4>
                  <div className="space-y-2">
                    {selectedTool.parameters.map((param: any, index) => (
                      <div key={index} className="bg-[#2D3B4E] rounded-md p-3">
                        <div className="flex items-start gap-2.5">
                          <Settings className="h-4 w-4 text-[#7C3AED] mt-0.5" />
                          <div className="flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-medium text-white text-sm">{param.name}</span>
                              {param.required && (
                                <span className="text-xs px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 font-medium">
                                  Required
                                </span>
                              )}
                              <span className="text-sm text-[#94A3B8] font-mono">{param.type}</span>
                            </div>
                            {param.description && (
                              <p className="text-sm text-[#94A3B8] mt-1 leading-relaxed">{param.description}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedTool.metadata?.git_url && (
                <div>
                  <h4 className="text-sm font-medium text-white mb-2">Source Details</h4>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
                      <GitBranch className="h-4 w-4 text-[#3B82F6]" />
                      <a href={selectedTool.metadata.git_url} target="_blank" rel="noopener noreferrer" 
                         className="hover:text-white transition-colors">
                        {selectedTool.metadata.git_url}
                      </a>
                    </div>
                    {selectedTool.metadata.git_branch && (
                      <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
                        <GitBranch className="h-4 w-4 text-[#7C3AED]" />
                        <span>{selectedTool.metadata.git_branch}</span>
                      </div>
                    )}
                    {selectedTool.metadata.git_path && (
                      <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
                        <FileCode className="h-4 w-4 text-[#3B82F6]" />
                        <span>{selectedTool.metadata.git_path}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {selectedTool.type && (
                <div>
                  <h4 className="text-sm font-medium text-white mb-2">Runtime Details</h4>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
                      {getTypeIcon(selectedTool)}
                      <span>Type: {selectedTool.type}</span>
                    </div>
                    {selectedTool.metadata?.docker_image && (
                      <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
                        <Container className="h-4 w-4 text-[#3B82F6]" />
                        <span>Docker Image: {selectedTool.metadata.docker_image}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}; 