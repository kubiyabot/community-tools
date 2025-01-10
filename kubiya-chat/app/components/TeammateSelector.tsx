import React, { useState, useRef } from 'react';
import { useOnClickOutside } from '../hooks/useOnClickOutside';

interface Teammate {
  id: string;
  name: string;
  description: string;
  llmModel?: string;
  instructionType?: string;
}

interface TeammateSelectorProps {
  teammates: Teammate[];
  selectedTeammate?: string;
  onSelect: (id: string) => void;
}

export function TeammateSelector({ teammates, selectedTeammate, onSelect }: TeammateSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useOnClickOutside(ref, () => setIsOpen(false));

  const selected = teammates.find(t => t.id === selectedTeammate);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-x-2 rounded-lg bg-[#1E293B] px-3 py-2 text-sm font-medium text-white hover:bg-[#2D3B4E] focus:outline-none focus:ring-2 focus:ring-[#7C3AED] focus:ring-offset-2 focus:ring-offset-[#0F172A]"
      >
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#7C3AED]/20 text-[#7C3AED]">
          {selected?.name.charAt(0) || '?'}
        </span>
        <span className="truncate">{selected?.name || 'Select Teammate'}</span>
        <svg
          className={`h-5 w-5 text-[#94A3B8] transition-transform duration-200 ${
            isOpen ? 'rotate-180' : ''
          }`}
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
        >
          <path
            d="M7 7l3 3 3-3"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>

      {isOpen && teammates.length > 0 && (
        <div className="absolute right-0 z-10 mt-2 w-72 origin-top-right rounded-lg bg-[#1E293B] shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
          <div className="p-1">
            {teammates.map((teammate) => (
              <button
                key={teammate.id}
                onClick={() => {
                  onSelect(teammate.id);
                  setIsOpen(false);
                }}
                className={`group relative flex w-full items-center gap-x-3 rounded-md p-2 text-left text-sm ${
                  teammate.id === selectedTeammate
                    ? 'bg-[#7C3AED] text-white'
                    : 'text-[#94A3B8] hover:bg-[#2D3B4E] hover:text-white'
                }`}
              >
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#7C3AED]/20 text-[#7C3AED] group-hover:bg-[#7C3AED]/30">
                  {teammate.name.charAt(0)}
                </span>
                <div className="flex min-w-0 flex-1 flex-col">
                  <span className="truncate font-medium">{teammate.name}</span>
                  {teammate.description && (
                    <span className="truncate text-xs opacity-80">
                      {teammate.description}
                    </span>
                  )}
                </div>
                {teammate.id === selectedTeammate && (
                  <svg
                    className="h-5 w-5 text-white"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
} 