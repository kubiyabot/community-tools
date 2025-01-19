'use client';

import { useEffect, useState } from 'react';
import { useUser } from '@auth0/nextjs-auth0/client';
import MyRuntimeProvider from '../MyRuntimeProvider';
import type { ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useConfig } from '@/lib/config-context';

interface ClientProviderProps {
  children: ReactNode;
}

export default function ClientProvider({ children }: ClientProviderProps): JSX.Element {
  const [mounted, setMounted] = useState(false);
  const { user, isLoading: isUserLoading } = useUser();
  const router = useRouter();
  const { setApiKey, setAuthType, apiKey } = useConfig();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    async function fetchToken() {
      console.log('[ClientProvider] State:', { 
        user: user ? 'exists' : 'null', 
        isUserLoading,
        mounted,
        hasApiKey: !!apiKey
      });

      if (user && !apiKey && !isUserLoading) {
        console.log('[ClientProvider] Fetching token for user:', user.email);
        try {
          const response = await fetch('/api/auth/me', {
            credentials: 'include',
            headers: {
              'Accept': 'application/json',
              'Cache-Control': 'no-cache',
              'Pragma': 'no-cache'
            }
          });

          console.log('[ClientProvider] /me response status:', response.status);

          if (!response.ok) {
            if (response.status === 401) {
              console.log('[ClientProvider] Unauthorized, redirecting to login');
              window.location.href = '/api/auth/auth0/login';
              return;
            }
            throw new Error(`Profile fetch failed: ${response.status}`);
          }

          const data = await response.json();
          console.log('[ClientProvider] Profile data:', { 
            hasAccessToken: !!data.accessToken,
            keys: Object.keys(data)
          });

          if (!data.accessToken) {
            console.error('[ClientProvider] No access token in profile data');
            window.location.href = '/api/auth/auth0/login';
            return;
          }

          console.log('[ClientProvider] Setting access token');
          setApiKey(data.accessToken);
          setAuthType('sso');
        } catch (error) {
          console.error('[ClientProvider] Token fetch error:', error);
          window.location.href = '/api/auth/auth0/login';
        }
      } else if (!user && !isUserLoading) {
        console.log('[ClientProvider] No user and not loading, redirecting to login');
        window.location.href = '/api/auth/auth0/login';
      }
    }

    if (mounted) {
      fetchToken();
    }
  }, [user, isUserLoading, mounted, router, setApiKey, setAuthType, apiKey]);

  // Don't render anything until we're mounted
  if (!mounted) {
    console.log('[ClientProvider] Not mounted yet');
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-[#7C3AED] border-t-transparent"></div>
      </div>
    );
  }

  // Show loading while checking auth
  if (isUserLoading) {
    console.log('[ClientProvider] User loading');
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-[#7C3AED] border-t-transparent"></div>
      </div>
    );
  }

  // Show loading while getting token
  if (user && !apiKey) {
    console.log('[ClientProvider] Waiting for token');
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-[#7C3AED] border-t-transparent"></div>
      </div>
    );
  }

  // Only render the runtime provider if we have user and token
  if (!user || !apiKey) {
    console.log('[ClientProvider] Missing user or token:', { hasUser: !!user, hasToken: !!apiKey });
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-white">Please log in to continue</div>
      </div>
    );
  }

  console.log('[ClientProvider] Rendering MyRuntimeProvider with user and token');
  return <MyRuntimeProvider>{children}</MyRuntimeProvider>;
} 