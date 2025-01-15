"use client";

import React, { useState, useRef, useEffect } from 'react';
import { useUser } from '@auth0/nextjs-auth0/client';
import { useOnClickOutside } from '../hooks/useOnClickOutside';

interface UserProfileButtonProps {
  onLogout: () => void;
}

interface UserProfile {
  name?: string;
  email?: string;
  picture?: string;
  sub?: string;
  org_name?: string;
  org_id?: string;
}

export function UserProfileButton({ onLogout }: UserProfileButtonProps) {
  const [mounted, setMounted] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const { user } = useUser();

  // Handle hydration
  useEffect(() => {
    setMounted(true);
  }, []);

  useOnClickOutside(menuRef, () => setShowMenu(false));

  // Don't render anything until mounted to prevent hydration mismatch
  if (!mounted) return null;
  if (!user) return null;

  const userProfile = user as UserProfile;
  const provider = userProfile.sub?.split('|')[0];
  const getProviderName = (provider: string) => {
    switch (provider) {
      case 'google-oauth2': return 'Google';
      case 'github': return 'GitHub';
      case 'auth0': return 'Auth0';
      case 'slack': return 'Slack';
      default: return provider;
    }
  };

  return (
    <div ref={menuRef} className="relative">
      <button
        onClick={() => setShowMenu(!showMenu)}
        className="flex items-center space-x-2 p-2 rounded-lg hover:bg-[#2D3B4E] transition-colors"
      >
        <img
          src={userProfile.picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(userProfile.name || 'User')}`}
          alt={userProfile.name || 'User'}
          className="w-8 h-8 rounded-full"
        />
        <svg
          className={`w-5 h-5 text-[#94A3B8] transition-transform duration-200 ${showMenu ? 'rotate-180' : ''}`}
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
        >
          <path d="M6 8l4 4 4-4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>

      {showMenu && (
        <div className="absolute right-0 mt-2 w-72 bg-[#2D3B4E] rounded-lg shadow-xl border border-[#3D4B5E] overflow-hidden z-50">
          <div className="p-4 border-b border-[#3D4B5E]">
            <div className="flex items-center space-x-3">
              <img
                src={userProfile.picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(userProfile.name || 'User')}`}
                alt={userProfile.name || 'User'}
                className="w-12 h-12 rounded-full"
              />
              <div>
                <div className="text-white font-medium">{userProfile.name}</div>
                <div className="text-[#94A3B8] text-sm">{userProfile.email}</div>
                {provider && (
                  <span className="inline-flex items-center mt-1 text-xs px-2 py-0.5 rounded-full bg-[#7C3AED]/20 text-[#7C3AED]">
                    {getProviderName(provider)}
                  </span>
                )}
              </div>
            </div>
          </div>
          
          {(userProfile.org_name || userProfile.org_id) && (
            <div className="px-4 py-3 border-b border-[#3D4B5E]">
              <h3 className="text-[#94A3B8] text-xs font-medium uppercase mb-2">Organization</h3>
              <div className="space-y-1">
                {userProfile.org_name && (
                  <p className="text-white text-sm">{userProfile.org_name}</p>
                )}
                {userProfile.org_id && (
                  <p className="text-[#94A3B8] text-xs font-mono">{userProfile.org_id}</p>
                )}
              </div>
            </div>
          )}

          <div className="p-2">
            <a
              href="https://app.kubiya.ai"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-2 p-2 rounded hover:bg-[#3D4B5E] text-[#94A3B8] hover:text-white transition-colors"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span>Management Console</span>
            </a>
            <a
              href="https://docs.kubiya.ai"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-2 p-2 rounded hover:bg-[#3D4B5E] text-[#94A3B8] hover:text-white transition-colors"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span>Documentation</span>
            </a>
            <button
              onClick={onLogout}
              className="w-full flex items-center space-x-2 p-2 rounded hover:bg-[#3D4B5E] text-red-500 hover:text-red-400 transition-colors"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span>Logout</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
} 