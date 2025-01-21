"use client";

import React, { useState, useRef, useEffect } from 'react';
import { useUser } from '@auth0/nextjs-auth0/client';
import { useOnClickOutside } from '../hooks/useOnClickOutside';
import { useRouter } from 'next/navigation';
import { SupportModal } from './SupportModal';

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
  nickname?: string;
  updated_at?: string;
  email_verified?: boolean;
}

export function UserProfileButton({ onLogout }: UserProfileButtonProps) {
  const [mounted, setMounted] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [showSupportModal, setShowSupportModal] = useState(false);
  const [avatarError, setAvatarError] = useState(false);
  const [profileData, setProfileData] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const menuRef = useRef<HTMLDivElement>(null);
  const { user } = useUser();
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const fetchProfileData = async () => {
      if (!user) return;

      try {
        const response = await fetch('/api/auth/me', {
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        });

        if (!response.ok) {
          if (response.status === 401) {
            console.log('Session expired, redirecting to login');
            window.location.href = '/api/auth/login';
            return;
          }
          throw new Error(`Profile fetch failed: ${response.status}`);
        }

        const data = await response.json();
        console.log('Profile data:', data);
        
        if (data.user) {
          setProfileData({
            ...data.user,
            picture: data.user.picture || user.picture,
            name: data.user.name || user.name,
            email: data.user.email || user.email,
          });
        }
      } catch (error) {
        console.error('Failed to fetch profile:', error);
        setAvatarError(true);
      }
    };

    if (mounted && user) {
      fetchProfileData();
    }
  }, [mounted, user]);

  useOnClickOutside(menuRef, () => setShowMenu(false));

  const getInitials = (name: string = 'User') => {
    return name
      .split(' ')
      .slice(0, 2) // Take only first and last name
      .map(n => n[0])
      .join('')
      .toUpperCase();
  };

  const getAvatarUrl = () => {
    const initials = getInitials(profileData?.name);
    return `https://ui-avatars.com/api/?name=${initials}&background=7C3AED&color=fff&size=128&bold=true&font-size=0.33`;
  };

  const formatOrgId = (orgId: string) => {
    if (!orgId) return '';
    return orgId.length > 20 ? `${orgId.substring(0, 20)}...` : orgId;
  };

  if (!mounted || !user || !profileData) {
    return (
      <div className="flex items-center space-x-2 p-2">
        <div className="w-9 h-9 rounded-full bg-[#2D3B4E] animate-pulse"></div>
        <div className="hidden md:flex flex-col space-y-2">
          <div className="w-20 h-3 bg-[#2D3B4E] rounded animate-pulse"></div>
          <div className="w-24 h-2 bg-[#2D3B4E] rounded animate-pulse"></div>
        </div>
      </div>
    );
  }

  const userProfile = profileData;
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

  const lastLoginDate = userProfile.updated_at 
    ? new Date(userProfile.updated_at).toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric'
      })
    : null;

  return (
    <div ref={menuRef} className="relative">
      <button
        onClick={() => setShowMenu(!showMenu)}
        className="flex items-center space-x-2 p-2 rounded-lg hover:bg-[#2D3B4E] transition-all duration-200 ease-in-out group relative"
        aria-label="User profile menu"
        aria-expanded={showMenu}
        aria-haspopup="true"
      >
        <div className="relative">
          <div className="w-9 h-9 rounded-full overflow-hidden border-2 border-transparent group-hover:border-[#7C3AED] transition-all duration-200">
            <img
              src={getAvatarUrl()}
              alt={userProfile.name || 'User avatar'}
              className="w-full h-full object-cover"
              loading="eager"
            />
          </div>
        </div>
        <div className="hidden md:flex flex-col items-start">
          <span className="text-sm font-medium text-white truncate max-w-[120px] group-hover:text-[#7C3AED] transition-colors">
            {userProfile.name || 'User'}
          </span>
          <span className="text-xs text-[#94A3B8] truncate max-w-[120px]">
            {userProfile.email}
          </span>
        </div>
        <svg
          className={`w-5 h-5 text-[#94A3B8] transform transition-transform duration-300 ease-in-out group-hover:text-[#7C3AED] ${showMenu ? 'rotate-180' : ''}`}
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
        >
          <path d="M6 8l4 4 4-4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>

      <div 
        className={`absolute right-0 mt-2 w-80 bg-[#1F2937] rounded-xl shadow-2xl border border-[#3D4B5E] overflow-hidden z-50 transition-all duration-300 transform origin-top-right ${
          showMenu 
            ? 'opacity-100 translate-y-0 scale-100' 
            : 'opacity-0 -translate-y-2 scale-95 pointer-events-none'
        }`}
      >
        <div className="p-6 border-b border-[#3D4B5E] bg-gradient-to-br from-[#2D3B4E] to-[#1F2937]">
          <div className="flex items-start space-x-4">
            <div className="relative">
              <div className="w-16 h-16 rounded-full overflow-hidden border-4 border-[#7C3AED]/20">
                <img
                  src={getAvatarUrl()}
                  alt={userProfile.name || 'User'}
                  className="w-full h-full object-cover"
                  loading="eager"
                />
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold text-white truncate">
                {userProfile.name || 'User'}
              </h3>
              <div className="mt-1 flex items-center">
                <span className="text-sm text-[#94A3B8] truncate">
                  {userProfile.email}
                </span>
              </div>
              {userProfile.org_name && (
                <span className="inline-flex items-center mt-2 text-xs px-2.5 py-1 rounded-full bg-[#7C3AED]/10 text-[#7C3AED] font-medium">
                  <svg className="w-3 h-3 mr-1" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" clipRule="evenodd"/>
                  </svg>
                  {userProfile.org_name}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="p-2 space-y-1">
          <a
            href="https://app.kubiya.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-3 p-2.5 rounded-lg hover:bg-[#3D4B5E] text-[#94A3B8] hover:text-white transition-all duration-200 group"
          >
            <div className="w-8 h-8 rounded-lg bg-[#7C3AED]/10 flex items-center justify-center group-hover:bg-[#7C3AED]/20 transition-colors">
              <svg className="w-4 h-4 text-[#7C3AED] group-hover:text-[#7C3AED] transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div className="flex-1">
              <span className="font-medium block">Management Console</span>
              <span className="text-xs text-[#94A3B8] group-hover:text-[#94A3B8]/80">Manage your workspace</span>
            </div>
          </a>

          <a
            href="#"
            onClick={(e) => {
              e.preventDefault();
              setShowSupportModal(true);
              setShowMenu(false);
            }}
            className="flex items-center space-x-3 p-2.5 rounded-lg hover:bg-[#3D4B5E] text-[#94A3B8] hover:text-white transition-all duration-200 group"
          >
            <div className="w-8 h-8 rounded-lg bg-[#7C3AED]/10 flex items-center justify-center group-hover:bg-[#7C3AED]/20 transition-colors">
              <svg className="w-4 h-4 text-[#7C3AED] group-hover:text-[#7C3AED] transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div className="flex-1">
              <span className="font-medium block">Support</span>
              <span className="text-xs text-[#94A3B8] group-hover:text-[#94A3B8]/80">Get help from our team</span>
            </div>
          </a>

          <div className="h-px bg-[#3D4B5E] my-2"></div>

          <button
            onClick={onLogout}
            className="w-full flex items-center space-x-3 p-2.5 rounded-lg hover:bg-red-500/10 text-red-400 hover:text-red-300 transition-all duration-200 group"
          >
            <div className="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center group-hover:bg-red-500/20 transition-colors">
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div className="flex-1">
              <span className="font-medium block">Logout</span>
              <span className="text-xs text-red-400/70 group-hover:text-red-300/70">Sign out of your account</span>
            </div>
          </button>
        </div>
      </div>

      <SupportModal 
        isOpen={showSupportModal} 
        onClose={() => setShowSupportModal(false)} 
      />
    </div>
  );
} 