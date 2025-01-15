"use client";

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import type { UserProfile as Auth0UserProfile } from '@auth0/nextjs-auth0/client';

interface UserProfileProps {
  user: Auth0UserProfile;
  onLogout: () => void;
}

export function UserProfile({ user, onLogout }: UserProfileProps) {
  const [isOpen, setIsOpen] = useState(false);
  const provider = user.sub?.split('|')[0];

  const getProviderName = (provider: string) => {
    switch (provider) {
      case 'google-oauth2':
        return 'Google';
      case 'github':
        return 'GitHub';
      case 'auth0':
        return 'Auth0';
      case 'slack':
        return 'Slack';
      default:
        return provider;
    }
  };

  const userName = user.name || user.nickname || 'User';
  const userEmail = user.email || '';
  const userPicture = user.picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(userName)}`;
  const orgName = user.org_name as string | undefined;
  const orgId = user.org_id as string | undefined;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center space-x-3 p-3 w-full rounded-lg transition-colors",
          "hover:bg-[#2D3B4E] focus:outline-none focus:ring-2 focus:ring-[#7C3AED] focus:ring-offset-2 focus:ring-offset-[#1E293B]"
        )}
      >
        <img
          src={userPicture}
          alt={userName}
          className="w-10 h-10 rounded-full"
        />
        <div className="flex-1 min-w-0 text-left">
          <p className="text-white font-medium truncate">{userName}</p>
          <p className="text-[#94A3B8] text-sm truncate">{userEmail}</p>
        </div>
        <svg 
          className={cn(
            "w-5 h-5 text-[#94A3B8] transition-transform duration-200",
            isOpen && "rotate-180"
          )}
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
        >
          <path d="M6 8l4 4 4-4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>

      {isOpen && (
        <div className="absolute bottom-full left-0 w-full mb-2 bg-[#2D3B4E] rounded-lg shadow-xl border border-[#3D4B5E] overflow-hidden">
          <div className="p-4 space-y-4">
            {/* User Info */}
            <div className="space-y-2">
              <h3 className="text-[#94A3B8] text-xs font-medium uppercase">Account</h3>
              <div className="flex items-center space-x-3 p-2 rounded-lg bg-[#1E293B]">
                <img
                  src={userPicture}
                  alt={userName}
                  className="w-12 h-12 rounded-full"
                />
                <div>
                  <p className="text-white font-medium">{userName}</p>
                  <p className="text-[#94A3B8] text-sm">{userEmail}</p>
                  {provider && (
                    <div className="flex items-center mt-1">
                      <span className="text-xs px-2 py-1 rounded-full bg-[#7C3AED]/20 text-[#7C3AED]">
                        {getProviderName(provider)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Organization Info */}
            {(orgName || orgId) && (
              <div className="space-y-2">
                <h3 className="text-[#94A3B8] text-xs font-medium uppercase">Organization</h3>
                <div className="p-2 rounded-lg bg-[#1E293B] space-y-1">
                  {orgName && (
                    <p className="text-white text-sm">{orgName}</p>
                  )}
                  {orgId && (
                    <p className="text-[#94A3B8] text-xs font-mono">{orgId}</p>
                  )}
                </div>
              </div>
            )}

            {/* Quick Links */}
            <div className="space-y-2">
              <h3 className="text-[#94A3B8] text-xs font-medium uppercase">Quick Links</h3>
              <div className="space-y-1">
                <a
                  href="https://app.kubiya.ai"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-2 p-2 rounded-lg hover:bg-[#1E293B] text-white transition-colors group"
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
                  className="flex items-center space-x-2 p-2 rounded-lg hover:bg-[#1E293B] text-white transition-colors group"
                >
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  <span>Documentation</span>
                </a>
              </div>
            </div>

            {/* Logout Button */}
            <button
              onClick={onLogout}
              className="w-full flex items-center justify-center space-x-2 p-2 rounded-lg bg-red-500/10 text-red-500 hover:bg-red-500/20 transition-colors"
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