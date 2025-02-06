"use client";

import React, { useState, useEffect, useMemo } from 'react';
import { X, Loader2, Package } from 'lucide-react';
import { Dialog, DialogContent, DialogTitle } from '../ui/dialog';
import { toast } from '../ui/use-toast';
import { ScrollArea } from '../ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { VisuallyHidden } from '@radix-ui/react-visually-hidden';
import type { TeammateDetails as TeammateDetailsType } from '@/app/types/teammate';
import type { TeammateWithIntegrations } from './teammate-details/types';
import type { Integration } from '@/app/types/integration';
import type { Tool } from '@/app/types/tool';
import { generateAvatarUrl } from '@/app/components/TeammateSelector';
import type { SourceInfo } from '@/app/types/source';
import type { ExtendedSourceInfo } from './teammate-details/SourcesTab';

// Import components from teammate-details folder
import { TeammateDetails } from './teammate-details/TeammateDetails';
import { OverviewTab } from './teammate-details/OverviewTab';
import IntegrationsTab from './teammate-details/IntegrationsTab';
import { SourcesTab } from './teammate-details/SourcesTab';
import { RuntimeTab } from './teammate-details/RuntimeTab';
import { AccessControlTab } from './teammate-details/AccessControlTab';

interface TeammateDetailsModalProps {
  isOpen: boolean;
  onCloseAction: () => void;
  teammate: TeammateDetailsType | null;
  integrations?: Integration[];
}

const LoadingOverlay = () => (
  <div className="absolute inset-0 bg-[#0A0F1E]/80 backdrop-blur-sm flex items-center justify-center z-50">
    <div className="flex flex-col items-center gap-4">
      <div className="relative">
        <div className="h-12 w-12 rounded-full border-2 border-emerald-400/20 border-t-emerald-400 animate-spin" />
        <div className="absolute inset-0 h-12 w-12 rounded-full border-2 border-emerald-400/20 animate-pulse" />
      </div>
      <p className="text-sm font-medium text-emerald-400">Loading teammate details...</p>
    </div>
  </div>
);

// Add utility functions
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

export function TeammateDetailsModal({ isOpen, onCloseAction, teammate, integrations = [] }: TeammateDetailsModalProps) {
  const [activeTab, setActiveTab] = useState('overview');
  const [isLoadingIntegrations, setIsLoadingIntegrations] = useState(false);
  const [isLoadingSources, setIsLoadingSources] = useState(false);
  const [loadedTabs] = useState<Set<string>>(new Set(['overview']));
  const [tools, setTools] = useState<Tool[]>([]);
  const [sources, setSources] = useState<ExtendedSourceInfo[]>([]);

  // Handle tab changes with proper state updates
  const handleTabChange = (tab: string) => {
    console.log('Tab changed to:', tab);
    setActiveTab(tab);
    
    // Only fetch sources if we're switching to the tools tab or sources tab
    if (tab === 'tools' || tab === 'sources') {
      console.log('Switching to tools/sources tab, fetching sources...');
      setIsLoadingSources(true);
      fetchSources().catch(error => {
        console.error('Error fetching sources:', error);
        toast({
          title: "Error loading sources",
          description: error instanceof Error ? error.message : "Failed to load sources data. Please try again.",
          variant: "destructive"
        });
      }).finally(() => {
        setIsLoadingSources(false);
      });
    }
  };

  // Initial load effect
  useEffect(() => {
    if (!teammate?.uuid || !isOpen) return;
    
    // Reset state when modal opens
    if (isOpen) {
      console.log('Modal opened, resetting state for teammate:', teammate.uuid);
      setTools([]);
      setSources([]);
      loadedTabs.clear();
      loadedTabs.add('overview');
      
      // If tools or sources tab is active on open, fetch sources
      if (activeTab === 'tools' || activeTab === 'sources') {
        console.log('Tools/Sources tab is active, fetching sources...');
        setIsLoadingSources(true);
        fetchSources().catch(error => {
          console.error('Error fetching sources:', error);
          toast({
            title: "Error loading sources",
            description: error instanceof Error ? error.message : "Failed to load sources data. Please try again.",
            variant: "destructive"
          });
        }).finally(() => {
          setIsLoadingSources(false);
        });
      }
    }
  }, [teammate?.uuid, isOpen]);

  // Move useMemo here, before any conditional logic
  const extendedSources = useMemo(() => {
    if (!teammate?.sources) return [];
    return sources.map(source => ({
      ...source,
      teammate_id: teammate.id,
      sourceId: source.sourceId || source.uuid,
      type: source.type || 'unknown',
      runner: source.runner || 'automatic',
      connected_agents_count: source.connected_agents_count || 0,
      connected_tools_count: source.connected_tools_count || 0,
      connected_workflows_count: source.connected_workflows_count || 0,
      kubiya_metadata: {
        created_at: source.kubiya_metadata?.created_at || new Date().toISOString(),
        last_updated: source.kubiya_metadata?.last_updated || new Date().toISOString(),
        user_created: source.kubiya_metadata?.user_created || 'system',
        user_last_updated: source.kubiya_metadata?.user_last_updated || 'system'
      },
      errors_count: source.errors_count || 0,
      source_meta: {
        id: source.source_meta?.id || source.uuid,
        url: source.source_meta?.url || source.url,
        branch: source.source_meta?.branch || 'main',
        commit: source.source_meta?.commit || '',
        committer: source.source_meta?.committer || ''
      },
      tools: source.tools || [],
      dynamic_config: source.dynamic_config || null,
      managed_by: source.managed_by || '',
      task_id: source.task_id || ''
    }));
  }, [teammate?.id, teammate?.sources, sources]);

  // Function to load sources data
  const fetchSources = async () => {
    if (!teammate?.sources?.length) {
      console.log('No sources found for teammate:', teammate);
      setSources([]);
      setTools([]);
      return;
    }

    console.log('Fetching sources for teammate:', teammate.id, 'Sources:', teammate.sources);
    
    try {
      // First, fetch all sources and their metadata in parallel
      console.log('Fetching sources and metadata...');
      const [allSourcesResponse, ...sourceResponses] = await Promise.all([
        // First, fetch all sources
        fetch('/api/v1/sources', {
          headers: {
            'Accept': 'application/json',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          },
          credentials: 'include'
        }),
        // Then fetch each source's details in parallel
        ...(teammate?.sources || []).map(uuid => 
          fetch(`/api/v1/sources/${uuid}`, {
            headers: {
              'Accept': 'application/json',
              'Cache-Control': 'no-cache',
              'Pragma': 'no-cache'
            },
            credentials: 'include'
          })
        ),
        // Also fetch metadata for each source in parallel
        ...(teammate?.sources || []).map(uuid => 
          fetch(`/api/v1/sources/${uuid}/metadata`, {
            headers: {
              'Accept': 'application/json',
              'Cache-Control': 'no-cache',
              'Pragma': 'no-cache'
            },
            credentials: 'include'
          })
        )
      ]);

      if (!allSourcesResponse.ok) {
        const errorText = await allSourcesResponse.text();
        console.error('Failed to fetch sources:', allSourcesResponse.status, errorText);
        throw new Error(`Failed to fetch sources: ${allSourcesResponse.status} ${errorText}`);
      }

      const allSources = await allSourcesResponse.json();
      console.log('All sources response:', allSources);
      
      const sourcesArray = Array.isArray(allSources) ? allSources : Object.values(allSources);
      const relevantSources = sourcesArray.filter((s: any) => teammate?.sources?.includes(s.uuid));
      console.log('Relevant sources:', relevantSources);

      // Split responses into source details and metadata responses
      const sourceDetailsResponses = sourceResponses.slice(0, teammate.sources.length);
      const metadataResponses = sourceResponses.slice(teammate.sources.length);

      let allTools: Tool[] = [];

      // Process source responses and metadata in parallel
      const processPromises = sourceDetailsResponses.map(async (response, index) => {
        const uuid = teammate?.sources?.[index] || '';
        const metadataResponse = metadataResponses[index];

        if (!response.ok) {
          console.warn(`Source ${uuid} not found or inaccessible:`, response.status);
          return null;
        }

        try {
          const [sourceInfo, metadata] = await Promise.all([
            response.json(),
            metadataResponse.ok ? metadataResponse.json() : Promise.resolve(null)
          ]);

          console.log(`Source info for ${uuid}:`, sourceInfo);
          console.log(`Metadata for ${uuid}:`, metadata);

          const tools = metadata?.tools || [];
          console.log(`Tools for ${uuid}:`, tools);
          
          // Add tools to our collection
          allTools = [...allTools, ...tools];

          return {
            sourceId: sourceInfo.uuid,
            uuid: sourceInfo.uuid,
            name: sourceInfo.name || getSourceNameFromUrl(sourceInfo.url),
            url: sourceInfo.url,
            type: getSourceType(sourceInfo.url),
            tools: tools,
            isLoading: false,
            connected_agents_count: sourceInfo.connected_agents_count || 0,
            connected_tools_count: tools.length,
            connected_workflows_count: sourceInfo.connected_workflows_count || 0,
            kubiya_metadata: {
              created_at: sourceInfo.kubiya_metadata?.created_at || '',
              last_updated: metadata?.kubiya_metadata?.last_updated || sourceInfo.kubiya_metadata?.last_updated || '',
              user_created: sourceInfo.kubiya_metadata?.user_created || 'Unknown',
              user_last_updated: metadata?.kubiya_metadata?.user_last_updated || sourceInfo.kubiya_metadata?.user_last_updated || 'Unknown'
            },
            errors_count: sourceInfo.errors_count || 0,
            source_meta: {
              id: metadata?.source_meta?.id || sourceInfo.source_meta?.id || sourceInfo.uuid,
              url: metadata?.source_meta?.url || sourceInfo.source_meta?.url || sourceInfo.url,
              commit: metadata?.source_meta?.commit || sourceInfo.source_meta?.commit || '',
              committer: metadata?.source_meta?.committer || sourceInfo.source_meta?.committer || '',
              branch: metadata?.source_meta?.branch || sourceInfo.source_meta?.branch || ''
            },
            dynamic_config: metadata?.dynamic_config || sourceInfo.dynamic_config || null,
            runner: sourceInfo.runner || '',
            managed_by: sourceInfo.managed_by || '',
            task_id: sourceInfo.task_id || ''
          };
        } catch (error) {
          console.error(`Error processing source ${uuid}:`, error);
          return null;
        }
      });

      const loadedSources = (await Promise.all(processPromises)).filter(Boolean);
      console.log('Processed sources:', loadedSources);
      
      // Update sources state with the processed sources directly
      const processedSources = loadedSources.map(source => {
        if (!source) return null;
        const uuid = typeof source.uuid === 'object' ? source.uuid.id : source.uuid;
        return {
          ...source,
          uuid,
          teammate_id: teammate.id
        } as ExtendedSourceInfo;
      }).filter(Boolean) as ExtendedSourceInfo[];

      console.log('Setting processed sources:', processedSources);
      setSources(processedSources);

      // Update tools state
      console.log('Setting all tools:', allTools);
      setTools(allTools);
      
    } catch (err) {
      console.error('Error fetching sources:', err);
      throw err; // Re-throw to be handled by caller
    }
  };

  // Function to load data for a specific tab
  const loadTabData = async (tabName: string) => {
    if (!teammate?.uuid) return;

    if (tabName === 'integrations') {
      setIsLoadingIntegrations(true);
      try {
        const integrationsRes = await fetch(`/api/teammates/${teammate.uuid}/integrations`);
        if (!integrationsRes.ok) {
          throw new Error('Failed to load integrations');
        }
      } catch (error) {
        console.error(`Error loading integrations:`, error);
        toast({
          title: `Error loading integrations`,
          description: "Failed to load data. Please try again.",
          variant: "destructive"
        });
      } finally {
        setIsLoadingIntegrations(false);
      }
    }
  };

  // Type guard to check if teammate exists
  if (!teammate) {
    return null;
  }

  // Now TypeScript knows teammate is not null
  const teammateWithIntegrations: TeammateWithIntegrations = {
    ...teammate,
    integrations
  };

  return (
    <Dialog open={isOpen} onOpenChange={onCloseAction}>
      <DialogContent 
        className="max-w-[1200px] p-0 gap-0 bg-[#0A0F1E] border-[#1E293B] fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-full max-h-[90vh] overflow-hidden rounded-lg shadow-xl"
      >
        <DialogTitle className="sr-only">
          {teammate?.name || 'Teammate'} Details
        </DialogTitle>
        
        <div id="teammate-details-description" className="sr-only">
          Detailed information about {teammate?.name || 'teammate'}, including tools, integrations, and runtime configuration.
        </div>
        
        <div className="flex h-[calc(100vh-8rem)]">
          <div className="flex-1 flex flex-col min-w-0 bg-[#0A0F1E]">
            <div className="flex-1 overflow-y-auto">
              <TeammateDetails 
                teammate={teammate} 
                activeTab={activeTab}
                onTabChange={handleTabChange}
                integrations={integrations}
                sources={sources}
                isLoadingSources={isLoadingSources}
                onSourcesChange={async () => {
                  setIsLoadingSources(true);
                  await fetchSources();
                  setIsLoadingSources(false);
                }}
              >
                <div className="flex-1 min-h-0">
                  <Tabs value={activeTab} onValueChange={handleTabChange} className="h-full">
                    <TabsContent value="overview" className="h-full m-0 data-[state=active]:flex">
                      <ScrollArea className="flex-1">
                        <OverviewTab teammate={teammate} />
                      </ScrollArea>
                    </TabsContent>
                    <TabsContent value="integrations" className="h-full m-0 data-[state=active]:flex">
                      <ScrollArea className="flex-1">
                        <IntegrationsTab 
                          teammate={teammateWithIntegrations}
                        />
                      </ScrollArea>
                    </TabsContent>
                    <TabsContent value="tools" className="h-full m-0 data-[state=active]:flex">
                      <ScrollArea className="flex-1">
                        {isLoadingSources ? (
                          <div className="flex items-center justify-center h-full p-6">
                            <div className="flex flex-col items-center gap-3">
                              <div className="relative">
                                <div className="h-12 w-12 rounded-full border-2 border-purple-400/20 border-t-purple-400 animate-spin" />
                                <div className="absolute inset-0 h-12 w-12 rounded-full border-2 border-purple-400/20 animate-pulse" />
                              </div>
                              <p className="text-sm font-medium text-purple-400">Loading tools...</p>
                              <p className="text-xs text-purple-400/60">This may take a moment</p>
                            </div>
                          </div>
                        ) : !sources.length ? (
                          <div className="flex items-center justify-center h-full p-6">
                            <div className="flex flex-col items-center gap-3">
                              <div className="p-3 rounded-full bg-[#1E293B] border border-[#2D3B4E]">
                                <Package className="h-6 w-6 text-purple-400" />
                              </div>
                              <p className="text-sm font-medium text-purple-400">No tools available</p>
                              <p className="text-xs text-purple-400/60">This teammate has no tools installed</p>
                            </div>
                          </div>
                        ) : (
                          <SourcesTab 
                            teammate={teammate} 
                            sources={sources}
                            isLoading={isLoadingSources}
                            onSourcesChange={async () => {
                              setIsLoadingSources(true);
                              await fetchSources();
                              setIsLoadingSources(false);
                            }}
                          />
                        )}
                      </ScrollArea>
                    </TabsContent>
                    <TabsContent value="sources" className="h-full m-0 data-[state=active]:flex">
                      <ScrollArea className="flex-1">
                        {/* Remove duplicate SourcesTab since it's already rendered through TeammateDetails */}
                      </ScrollArea>
                    </TabsContent>
                    <TabsContent value="runtime" className="h-full m-0 data-[state=active]:flex">
                      <ScrollArea className="flex-1">
                        <RuntimeTab 
                          teammate={teammate}
                        />
                      </ScrollArea>
                    </TabsContent>
                    <TabsContent value="access" className="h-full m-0 data-[state=active]:flex">
                      <ScrollArea className="flex-1">
                        <AccessControlTab 
                          teammate={teammate}
                        />
                      </ScrollArea>
                    </TabsContent>
                  </Tabs>
                </div>
              </TeammateDetails>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
} 
