"use client";

import React, { useState, useRef, useMemo, useEffect } from 'react';
import { useOnClickOutside } from '../hooks/useOnClickOutside';
import { useTeammateContext } from '../MyRuntimeProvider';
import { TeammateCapabilities } from '@/app/components/TeammateCapabilities';
import { Box, Terminal, X, ChevronLeft, ChevronRight } from 'lucide-react';

interface Teammate {
  uuid: string;
  name: string;
  description?: string;
  llm_model?: string;
  instruction_type?: string;
}

function generateAvatarUrl(teammate: Teammate) {
  const model = teammate.llm_model?.toLowerCase() || '';
  const type = teammate.instruction_type?.toLowerCase() || '';
  
  let style = 'bottts';
  let backgroundColor = encodeURIComponent(
    model.includes('gpt-4') ? '7C3AED' :
    model.includes('gpt-3') ? '3B82F6' :
    '6B7280'
  );
  
  const variations: Record<string, string> = {
    'terraform': 'beam',
    'kubernetes': 'pixel',
    'aws': 'rings',
    'general': 'bottts'
  };
  
  for (const [key, value] of Object.entries(variations)) {
    if (type.includes(key)) {
      style = value;
      break;
    }
  }

  return `https://api.dicebear.com/7.x/${style}/svg?seed=${encodeURIComponent(teammate.uuid)}&backgroundColor=${backgroundColor}`;
}

export function TeammateSelector() {
  const [mounted, setMounted] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [clientSelectedTeammate, setClientSelectedTeammate] = useState<string | null>(null);
  const ref = useRef<HTMLDivElement>(null);
  const { teammates, selectedTeammate, setSelectedTeammate } = useTeammateContext();

  const TEAMMATES_PER_PAGE = 5;
  const [currentPage, setCurrentPage] = useState(0);

  // Handle initial mounting and hydration
  useEffect(() => {
    setMounted(true);
    
    // Load stored teammate after mounting
    const storedTeammate = localStorage.getItem('selectedTeammate');
    if (storedTeammate && teammates.some(t => t.uuid === storedTeammate)) {
      setClientSelectedTeammate(storedTeammate);
      if (!selectedTeammate) {
        setSelectedTeammate(storedTeammate);
      }
    } else if (teammates.length > 0 && !selectedTeammate) {
      // If no stored teammate, select the first one
      setClientSelectedTeammate(teammates[0].uuid);
      setSelectedTeammate(teammates[0].uuid);
      localStorage.setItem('selectedTeammate', teammates[0].uuid);
    }
  }, [teammates]); // Only depend on teammates array to prevent loops
  
  useOnClickOutside(ref, () => setShowDetails(false));

  // Use client-side selected teammate if available, otherwise use context value
  const effectiveSelectedTeammate = clientSelectedTeammate || selectedTeammate;
  const selected = teammates.find(t => t.uuid === effectiveSelectedTeammate);
  
  const filteredTeammates = useMemo(() => {
    if (!searchQuery) return teammates;
    const query = searchQuery.toLowerCase();
    return teammates.filter(teammate => 
      teammate.name.toLowerCase().includes(query) ||
      teammate.description?.toLowerCase().includes(query) ||
      teammate.llm_model?.toLowerCase().includes(query) ||
      teammate.instruction_type?.toLowerCase().includes(query)
    );
  }, [teammates, searchQuery]);

  // Get current teammates for pagination
  const currentTeammates = useMemo(() => {
    const start = currentPage * TEAMMATES_PER_PAGE;
    return filteredTeammates.slice(start, start + TEAMMATES_PER_PAGE);
  }, [filteredTeammates, currentPage]);

  // Reset page when search changes
  useEffect(() => {
    setCurrentPage(0);
  }, [searchQuery]);

  const handleTeammateSelect = (uuid: string) => {
    if (uuid !== effectiveSelectedTeammate) {
      setClientSelectedTeammate(uuid);
      setSelectedTeammate(uuid);
      localStorage.setItem('selectedTeammate', uuid);
    }
  };

  // Don't render anything until mounted to prevent hydration mismatch
  if (!mounted) {
    return (
      <div className="flex flex-col h-full animate-pulse">
        <div className="h-10 bg-[#2D3B4E] rounded-lg mb-4"></div>
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-[#2D3B4E] rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-0">
      {/* Search Bar - Fixed */}
      <div className="flex-shrink-0 p-2 bg-[#1E293B] border-b border-[#2D3B4E] sticky top-0 z-10">
        <div className="relative">
          <input
            type="text"
            placeholder="Search teammates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-2 bg-[#2D3B4E] text-white rounded-md placeholder-[#94A3B8] focus:outline-none focus:ring-1 focus:ring-[#7C3AED] border border-[#3D4B5E] text-sm transition-all duration-200 ease-in-out"
          />
          <svg
            className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#94A3B8]"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 p-0.5 hover:bg-[#3D4B5E] rounded-sm transition-colors"
            >
              <X className="h-3 w-3 text-[#94A3B8]" />
            </button>
          )}
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Selected Teammate Card */}
        {selected && (
          <div className="p-2">
            <div className="rounded-md bg-[#2D3B4E] border border-[#3D4B5E] overflow-hidden shadow-lg transition-all duration-200">
              <div className="p-3">
                <div className="flex items-start gap-3">
                  <img
                    src={generateAvatarUrl(selected)}
                    alt={selected.name}
                    className="w-10 h-10 rounded-md flex-shrink-0 ring-2 ring-[#7C3AED] ring-offset-1 ring-offset-[#2D3B4E]"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <h2 className="text-white font-semibold truncate text-sm">{selected.name}</h2>
                      {selected.instruction_type?.toLowerCase().includes('terraform') && (
                        <Box className="h-3.5 w-3.5 text-[#7C3AED] flex-shrink-0" />
                      )}
                    </div>
                    {selected.description && (
                      <p className="text-[#94A3B8] text-xs line-clamp-2 mt-1">{selected.description}</p>
                    )}
                    {/* Tags */}
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {selected.llm_model && (
                        <span className="inline-flex items-center text-[10px] px-2 py-0.5 rounded-full bg-[#7C3AED]/10 text-[#7C3AED] font-medium">
                          <Terminal className="w-3 h-3 mr-1" />
                          {selected.llm_model}
                        </span>
                      )}
                      {selected.instruction_type && (
                        <span className="inline-flex items-center text-[10px] px-2 py-0.5 rounded-full bg-[#3B82F6]/10 text-[#3B82F6] font-medium">
                          <Box className="w-3 h-3 mr-1" />
                          {selected.instruction_type}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div className="border-t border-[#3D4B5E] p-2">
                <button
                  type="button"
                  onClick={() => setShowDetails(!showDetails)}
                  className="w-full flex items-center justify-center px-3 py-1.5 text-xs font-medium text-[#94A3B8] hover:text-white hover:bg-[#3D4B5E] rounded transition-all duration-200"
                >
                  {showDetails ? 'Hide Details' : 'View Capabilities'}
                </button>
              </div>
            </div>

            {/* Capabilities Panel */}
            {showDetails && (
              <div className="mt-2 rounded-md bg-[#2D3B4E] border border-[#3D4B5E] overflow-hidden shadow-lg">
                <div className="p-3 space-y-4">
                  <div>
                    <h3 className="text-[#94A3B8] text-xs font-semibold uppercase tracking-wider mb-2">About</h3>
                    <p className="text-sm text-white leading-relaxed">{selected.description}</p>
                  </div>
                  <div>
                    <h3 className="text-[#94A3B8] text-xs font-semibold uppercase tracking-wider mb-2">Capabilities</h3>
                    <TeammateCapabilities teammateId={selected.uuid} />
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Teammates List */}
        <div className="px-2 pb-2">
          <div className="space-y-1.5">
            {currentTeammates.map((teammate) => (
              <button
                key={teammate.uuid}
                onClick={() => handleTeammateSelect(teammate.uuid)}
                className={`w-full flex items-center gap-x-3 p-2.5 rounded-md text-left transition-all duration-200 ${
                  teammate.uuid === effectiveSelectedTeammate
                    ? 'bg-[#7C3AED] text-white shadow-lg'
                    : 'text-[#94A3B8] hover:bg-[#2D3B4E] hover:text-white'
                }`}
              >
                <img
                  src={generateAvatarUrl(teammate)}
                  alt={teammate.name}
                  className={`w-9 h-9 rounded-md flex-shrink-0 transition-all duration-200 ${
                    teammate.uuid === effectiveSelectedTeammate
                      ? 'ring-2 ring-white ring-offset-1 ring-offset-[#7C3AED]'
                      : ''
                  }`}
                />
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate text-sm">{teammate.name}</div>
                  {teammate.description && (
                    <div className="truncate text-xs opacity-80 mt-0.5">{teammate.description}</div>
                  )}
                </div>
                {teammate.uuid === effectiveSelectedTeammate && (
                  <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            ))}
          </div>

          {/* Pagination */}
          {filteredTeammates.length > TEAMMATES_PER_PAGE && (
            <div className="flex items-center justify-between px-2 py-2 mt-2 border-t border-[#3D4B5E]">
              <button
                onClick={() => setCurrentPage(prev => Math.max(0, prev - 1))}
                disabled={currentPage === 0}
                className="p-1 hover:bg-[#2D3B4E] rounded-sm transition-colors disabled:opacity-50 disabled:hover:bg-transparent"
              >
                <ChevronLeft className="h-4 w-4 text-[#94A3B8]" />
              </button>
              <span className="text-xs text-[#94A3B8]">
                Page {currentPage + 1} of {Math.ceil(filteredTeammates.length / TEAMMATES_PER_PAGE)}
              </span>
              <button
                onClick={() => setCurrentPage(prev => Math.min(Math.ceil(filteredTeammates.length / TEAMMATES_PER_PAGE) - 1, prev + 1))}
                disabled={currentPage >= Math.ceil(filteredTeammates.length / TEAMMATES_PER_PAGE) - 1}
                className="p-1 hover:bg-[#2D3B4E] rounded-sm transition-colors disabled:opacity-50 disabled:hover:bg-transparent"
              >
                <ChevronRight className="h-4 w-4 text-[#94A3B8]" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 