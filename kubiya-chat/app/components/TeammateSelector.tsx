"use client";

import React, { useState, useEffect } from 'react';
import { useTeammateContext } from '../MyRuntimeProvider';
import { Search, X, Terminal, Box } from 'lucide-react';

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
  const [searchQuery, setSearchQuery] = useState('');
  const { teammates, selectedTeammate, setSelectedTeammate } = useTeammateContext();

  useEffect(() => {
    setMounted(true);
    const storedTeammate = localStorage.getItem('selectedTeammate');
    if (storedTeammate && teammates.some(t => t.uuid === storedTeammate)) {
      setSelectedTeammate(storedTeammate);
    } else if (teammates.length > 0 && !selectedTeammate) {
      setSelectedTeammate(teammates[0].uuid);
      localStorage.setItem('selectedTeammate', teammates[0].uuid);
    }
  }, [teammates]);

  const filteredTeammates = teammates.filter(teammate => 
    !searchQuery || 
    teammate.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    teammate.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleTeammateSelect = (uuid: string) => {
    setSelectedTeammate(uuid);
    localStorage.setItem('selectedTeammate', uuid);
  };

  if (!mounted) {
    return <div className="h-full bg-gray-900 animate-pulse" />;
  }

  return (
    <div className="flex flex-col h-full bg-gray-900 border-r border-gray-700">
      <div className="p-3 border-b border-gray-700">
        <div className="relative">
          <input
            type="text"
            placeholder="Search teammates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-gray-800 text-white rounded-lg placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-purple-500"
          />
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2"
            >
              <X className="h-4 w-4 text-gray-400 hover:text-white" />
            </button>
          )}
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        {filteredTeammates.map((teammate) => (
          <button
            key={teammate.uuid}
            onClick={() => handleTeammateSelect(teammate.uuid)}
            className={`w-full flex items-center gap-3 p-3 hover:bg-gray-800 transition-colors ${
              teammate.uuid === selectedTeammate ? 'bg-gray-800' : ''
            }`}
          >
            <img
              src={generateAvatarUrl(teammate)}
              alt={teammate.name}
              className="w-10 h-10 rounded-lg"
            />
            <div className="flex-1 text-left min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-white font-medium truncate">{teammate.name}</span>
                {teammate.instruction_type && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-400">
                    {teammate.instruction_type}
                  </span>
                )}
              </div>
              {teammate.description && (
                <p className="text-sm text-gray-400 truncate">{teammate.description}</p>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
} 