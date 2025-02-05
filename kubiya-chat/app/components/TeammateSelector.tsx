"use client";

import React, { useState, useEffect, memo, useMemo } from 'react';
import { useTeammateContext } from '../MyRuntimeProvider';
import { Search, X, Info } from 'lucide-react';
import { Button } from './button';
import { TeammateDetailsModal } from './shared/TeammateDetailsModal';
import { useEntity } from '@/app/providers/EntityProvider';

// Avatar generation constants
const AVATAR_IMAGES = [
  'Accountant.png',
  'Chemist-scientist.png',
  'Postman.png',
  'Security-guard.png',
  'builder-1.png',
  'builder-2.png',
  'builder-3.png',
  'capitan-1.png',
  'capitan-2.png',
  'capitan-3.png'
];

interface TeammateDetails {
  uuid: string;
  id: string;
  name: string;
  description?: string;
  llm_model?: string;
  instruction_type?: string;
  metadata: any;
}

interface Teammate extends TeammateDetails {
  // Additional fields specific to Teammate if any
}

// Export the generateAvatarUrl function
export function generateAvatarUrl(input: { uuid: string; name: string }): string {
  const seed = (input.uuid + input.name).split('').reduce((acc: number, char: string, i: number) => 
    acc + (char.charCodeAt(0) * (i + 1)), 0);
  const randomIndex = Math.abs(Math.sin(seed) * AVATAR_IMAGES.length) | 0;
  return `/images/avatars/${AVATAR_IMAGES[randomIndex]}`;
}

export const TeammateSelector = memo(function TeammateSelector({ onSelect, selectedId }: {
  onSelect: (id: string) => void;
  selectedId?: string;
}) {
  const { users, groups, isLoading } = useEntity();
  const [mounted, setMounted] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [selectedTeammateDetails, setSelectedTeammateDetails] = useState<Teammate | null>(null);
  const [capabilities, setCapabilities] = useState<any>(null);
  const [integrations, setIntegrations] = useState<any>(null);
  const { teammates, selectedTeammate, setSelectedTeammate } = useTeammateContext();
  const [loadError, setLoadError] = useState<string | null>(null);

  const sortedUsers = useMemo(() => {
    if (!users || !Array.isArray(users)) return [];
    return [...users].sort((a, b) => (a.name || '').localeCompare(b.name || ''));
  }, [users]);

  useEffect(() => {
    const initializeTeammates = async () => {
      try {
        setMounted(true);
        
        // Only proceed if we have teammates
        if (teammates.length === 0) {
          // Try to force refresh teammates if none are found
          const response = await fetch('/api/teammates', {
            headers: {
              'x-force-refresh': 'true'
            }
          });
          if (!response.ok) {
            throw new Error('Failed to fetch teammates');
          }
          return;
        }

        const storedTeammate = localStorage.getItem('selectedTeammate');
        
        if (storedTeammate && teammates.some(t => t.uuid === storedTeammate)) {
          // If we have a valid stored teammate, select it
          setSelectedTeammate(storedTeammate);
          // Fetch integrations for the stored teammate
          fetchIntegrations(storedTeammate);
        } else if (teammates.length > 0) {
          // Otherwise select the first teammate and store it
          setSelectedTeammate(teammates[0].uuid);
          localStorage.setItem('selectedTeammate', teammates[0].uuid);
          // Fetch integrations for the first teammate
          fetchIntegrations(teammates[0].uuid);
        }
      } catch (error) {
        console.error('Failed to initialize teammates:', error);
        setLoadError(error instanceof Error ? error.message : 'Failed to load teammates');
      }
    };

    initializeTeammates();
  }, [teammates, setSelectedTeammate]); // Add setSelectedTeammate to dependencies

  const fetchIntegrations = async (teammateId: string) => {
    try {
      const response = await fetch(`/api/teammates/${teammateId}/integrations`);
      if (response.ok) {
        const data = await response.json();
        setIntegrations(data);
      }
    } catch (error) {
      console.error('Failed to fetch integrations:', error);
    }
  };

  const handleTeammateSelect = (uuid: string) => {
    setSelectedTeammate(uuid);
    localStorage.setItem('selectedTeammate', uuid);
    fetchIntegrations(uuid); // Fetch integrations when teammate is selected
  };

  const filteredTeammates = teammates.filter(teammate => 
    !searchQuery || 
    teammate.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    teammate.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Fetch teammate capabilities when modal is opened
  const handleInfoClick = async (teammate: Teammate, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent teammate selection when clicking info button
    setSelectedTeammateDetails({
      ...teammate,
      id: teammate.uuid
    });
    setIsDetailsModalOpen(true);

    try {
      const response = await fetch(`/api/teammates/${teammate.uuid}/capabilities`);
      if (response.ok) {
        const data = await response.json();
        setCapabilities(data);
      }
    } catch (error) {
      console.error('Failed to fetch capabilities:', error);
    }
  };

  if (!mounted || isLoading) {
    return (
      <div className="h-full bg-gray-900 animate-pulse flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-slate-400">Loading teammates...</p>
        </div>
      </div>
    );
  }

  // Show error state if loading failed
  if (loadError) {
    return (
      <div className="h-full bg-gray-900 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3 p-4 text-center">
          <p className="text-red-400">Failed to load teammates</p>
          <button 
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-purple-500 hover:bg-purple-600 rounded-lg text-sm transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-900/95 border-r border-gray-800/60 backdrop-blur-sm w-[280px]">
      <div className="flex-shrink-0 p-4 border-b border-gray-800/60">
        <div className="relative group">
          <input
            type="text"
            placeholder="Search teammates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2.5 bg-gray-800/80 text-white rounded-xl placeholder-gray-400 
                     focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:bg-gray-800/95
                     transition-all duration-200 group-hover:bg-gray-800/95"
          />
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 
                          group-hover:text-purple-400 transition-colors duration-200" />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 opacity-60 
                       hover:opacity-100 transition-all duration-200"
            >
              <X className="h-3.5 w-3.5 text-gray-400 hover:text-purple-400" />
            </button>
          )}
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto min-h-0">
        <div className="space-y-1 p-2">
          {filteredTeammates.map((teammate) => (
            <div
              key={teammate.uuid}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg
                       transition-all duration-200 group hover:bg-gray-800/80
                       ${teammate.uuid === selectedTeammate ? 'bg-gray-800/90 shadow-lg shadow-purple-500/5' : ''}`}
            >
              <button
                onClick={() => handleTeammateSelect(teammate.uuid)}
                className="flex-1 flex items-center gap-3 min-w-0"
              >
                <div className="relative flex-shrink-0">
                  <img
                    src={generateAvatarUrl({ uuid: teammate.uuid, name: teammate.name })}
                    alt={teammate.name}
                    className="w-9 h-9 rounded-lg transform transition-all duration-300 
                             group-hover:scale-105 group-hover:shadow-md group-hover:shadow-purple-500/10
                             object-cover"
                  />
                  {teammate.uuid === selectedTeammate && (
                    <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-purple-500 
                                 rounded-full ring-2 ring-gray-900 shadow-lg animate-pulse" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-white font-medium truncate text-sm tracking-wide
                                  group-hover:text-purple-100 max-w-[160px]">
                      {teammate.name}
                    </span>
                    {teammate.instruction_type && (
                      <span className="flex-shrink-0 text-[10px] px-2 py-0.5 rounded-full bg-purple-500/20 
                                    text-purple-300 transition-colors duration-200 
                                    group-hover:bg-purple-500/30 font-medium tracking-wide">
                        {teammate.instruction_type}
                      </span>
                    )}
                  </div>
                  {teammate.description && (
                    <div className="relative group/desc">
                      <p className="text-xs text-gray-400 truncate group-hover:text-gray-300 
                                transition-colors duration-200 tracking-wide max-w-[200px]">
                        {teammate.description}
                      </p>
                      {/* Hover tooltip for full description */}
                      <div className="absolute left-0 bottom-full mb-2 hidden group-hover/desc:block z-50">
                        <div className="bg-gray-900 text-white text-xs rounded-lg py-2 px-3 shadow-xl 
                                    border border-gray-700 max-w-[300px] whitespace-normal">
                          {teammate.description}
                        </div>
                        <div className="absolute -bottom-1 left-4 w-2 h-2 bg-gray-900 
                                    transform rotate-45 border-r border-b border-gray-700"></div>
                      </div>
                    </div>
                  )}
                </div>
              </button>
              <Button
                variant="ghost"
                size="sm"
                className="flex-shrink-0 text-slate-400 hover:text-white p-1.5 h-auto opacity-0 
                         group-hover:opacity-100 transition-opacity"
                onClick={(e) => handleInfoClick(teammate, e)}
              >
                <Info className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      </div>

      <TeammateDetailsModal
        isOpen={isDetailsModalOpen}
        onCloseAction={async () => {
          setIsDetailsModalOpen(false);
          setSelectedTeammateDetails(null);
        }}
        teammate={selectedTeammateDetails}
        integrations={integrations}
      />
    </div>
  );
}); 