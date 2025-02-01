"use client";

import React, { useEffect } from 'react';
import { Calendar, User, Code, GitBranch, Settings, Brain } from 'lucide-react';
import { Badge } from '@/app/components/ui/badge';
import type { TeammateDetails } from './types';
import mermaid from 'mermaid';
import { useEntity } from '@/app/providers/EntityProvider';
import { Avatar, AvatarImage, AvatarFallback } from '@/app/components/ui/avatar';
import { Skeleton } from '@/app/components/ui/skeleton';

interface OverviewTabProps {
  teammate: TeammateDetails;
}

export function OverviewTab({ teammate }: OverviewTabProps) {
  const { getEntityMetadata, isLoading: isEntityLoading } = useEntity();

  // Get owner metadata if available
  const ownerMetadata = teammate.metadata?.user_created ? 
    getEntityMetadata(teammate.metadata.user_created) : null;

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: true,
      theme: 'dark',
      securityLevel: 'loose',
      themeVariables: {
        primaryColor: '#6366f1',
        primaryTextColor: '#fff',
        primaryBorderColor: '#4f46e5',
        lineColor: '#6366f1',
        secondaryColor: '#3730a3',
        tertiaryColor: '#312e81'
      }
    });

    // Re-render mermaid diagrams when they are added to the DOM
    const renderMermaid = async () => {
      try {
        await mermaid.run({
          querySelector: '.mermaid'
        });
      } catch (error) {
        console.error('Error rendering mermaid diagrams:', error);
      }
    };

    renderMermaid();
  }, []);

  // Function to render owner information
  const renderOwnerInfo = () => {
    if (isEntityLoading) {
      return (
        <div className="flex items-center gap-2">
          <Skeleton className="h-8 w-8 rounded-full" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-3 w-16" />
          </div>
        </div>
      );
    }

    if (!ownerMetadata) {
      return (
        <p className="text-sm font-medium text-slate-400">
          Not available
        </p>
      );
    }

    return (
      <div className="flex items-center gap-2">
        <Avatar className="h-8 w-8">
          {ownerMetadata.image ? (
            <AvatarImage src={ownerMetadata.image} alt={ownerMetadata.name} />
          ) : (
            <AvatarFallback className="bg-purple-500/10 text-purple-400">
              {ownerMetadata.name?.charAt(0)?.toUpperCase() || '?'}
            </AvatarFallback>
          )}
        </Avatar>
        <div>
          <p className="text-sm font-medium text-white">
            {ownerMetadata.name}
          </p>
          {ownerMetadata.create_at && (
            <p className="text-xs text-slate-400">
              Since {new Date(ownerMetadata.create_at).toLocaleDateString()}
            </p>
          )}
        </div>
      </div>
    );
  };

  // Function to render mermaid diagrams for tools
  const renderMermaidDiagrams = () => {
    if (!teammate.tools?.length) return null;

    return teammate.tools.map((tool, index) => {
      if (!tool.mermaid) return null;

      return (
        <div key={`${tool.name}-${index}`} className="p-4 rounded-lg bg-[#1E293B] border border-[#2A3347]">
          <h4 className="text-sm font-medium text-white mb-3">{tool.name} Flow Diagram</h4>
          <div className="mermaid bg-[#1E293B] p-4 rounded-lg overflow-x-auto">
            {tool.mermaid}
          </div>
        </div>
      );
    });
  };

  return (
    <div className="space-y-8">
      {/* Basic Information */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">Basic Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-start gap-3 p-4 rounded-lg bg-[#1E293B] border border-[#2A3347]">
            <div className="p-2 rounded-md bg-purple-500/10">
              <User className="h-4 w-4 text-purple-400" />
            </div>
            <div>
              <p className="text-xs text-slate-400">Created By</p>
              <div className="mt-1">
                {renderOwnerInfo()}
              </div>
            </div>
          </div>

          <div className="flex items-start gap-3 p-4 rounded-lg bg-[#1E293B] border border-[#2A3347]">
            <div className="p-2 rounded-md bg-purple-500/10">
              <Calendar className="h-4 w-4 text-purple-400" />
            </div>
            <div>
              <p className="text-xs text-slate-400">Created At</p>
              <p className="text-sm font-medium text-white mt-1">
                {teammate.metadata?.created_at ? 
                  new Date(teammate.metadata.created_at).toLocaleDateString() : 
                  'Unknown'
                }
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-4 rounded-lg bg-[#1E293B] border border-[#2A3347]">
            <div className="p-2 rounded-md bg-purple-500/10">
              <Brain className="h-4 w-4 text-purple-400" />
            </div>
            <div>
              <p className="text-xs text-slate-400">LLM Model</p>
              <p className="text-sm font-medium text-white mt-1">
                {teammate.llm_model || 'Not specified'}
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-4 rounded-lg bg-[#1E293B] border border-[#2A3347] group hover:border-green-500/30 transition-all duration-300">
            <div className="p-2 rounded-md bg-green-500/10 group-hover:bg-green-500/20 transition-all duration-300">
              <Settings className="h-4 w-4 text-green-400" />
            </div>
            <div>
              <p className="text-xs text-slate-400">Status</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="absolute inline-flex h-full w-full rounded-full bg-green-500 opacity-75 animate-ping" />
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500" />
                </span>
                <p className="text-sm font-medium text-white group-hover:text-green-400 transition-colors duration-300">
                  ACTIVE
                </p>
                <Badge 
                  variant="outline" 
                  className="bg-green-500/10 text-green-400 border-green-500/20 text-[10px] px-1.5 ml-1"
                >
                  Ready to help
                </Badge>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Capabilities */}
      {teammate.metadata?.capabilities && teammate.metadata.capabilities.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-white mb-4">Capabilities</h3>
          <div className="p-4 rounded-lg bg-[#1E293B] border border-[#2A3347]">
            <div className="flex flex-wrap gap-2">
              {teammate.metadata.capabilities.map((capability: string) => (
                <Badge 
                  key={capability}
                  variant="secondary" 
                  className="bg-purple-500/10 text-purple-400 border border-purple-500/20"
                >
                  {capability}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Flow Diagrams */}
      {teammate.tools?.some(tool => tool.mermaid) && (
        <div>
          <h3 className="text-lg font-semibold text-white mb-4">Flow Diagrams</h3>
          <div className="grid grid-cols-1 gap-4">
            {renderMermaidDiagrams()}
          </div>
        </div>
      )}
    </div>
  );
} 