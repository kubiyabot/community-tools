'use client';

import { useEffect, useState } from 'react';
import { useUser } from '@auth0/nextjs-auth0/client';
import MyRuntimeProvider from '../MyRuntimeProvider';
import type { ReactNode } from 'react';
import { useRouter } from 'next/navigation';

interface ClientProviderProps {
  children: ReactNode;
}

export default function ClientProvider({ children }: ClientProviderProps): JSX.Element {
  const [mounted, setMounted] = useState(false);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const { user, isLoading: isUserLoading } = useUser();
  const router = useRouter();

  useEffect(() => {
    async function fetchToken() {
      console.log('[ClientProvider] State:', { 
        user: user ? 'exists' : 'null', 
        isUserLoading, 
        accessToken: accessToken ? 'exists' : 'null',
        mounted
      });

      if (user && !accessToken) {
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
              const form = document.createElement('form');
              form.method = 'GET';
              form.action = '/api/auth/auth0/login';
              document.body.appendChild(form);
              form.submit();
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
            const form = document.createElement('form');
            form.method = 'GET';
            form.action = '/api/auth/auth0/login';
            document.body.appendChild(form);
            form.submit();
            return;
          }

          console.log('[ClientProvider] Setting access token and mounted state');
          setAccessToken(data.accessToken);
          setMounted(true);
        } catch (error) {
          console.error('[ClientProvider] Token fetch error:', error);
          const form = document.createElement('form');
          form.method = 'GET';
          form.action = '/api/auth/auth0/login';
          document.body.appendChild(form);
          form.submit();
        }
      } else if (!user && !isUserLoading) {
        console.log('[ClientProvider] No user and not loading, redirecting to login');
        const form = document.createElement('form');
        form.method = 'GET';
        form.action = '/api/auth/auth0/login';
        document.body.appendChild(form);
        form.submit();
      }
    }

    fetchToken();
  }, [user, isUserLoading, accessToken, router]);

  // Don't render anything until we're mounted and have all required data
  if (!mounted || isUserLoading || (user && !accessToken)) {
    console.log('[ClientProvider] Showing loading state:', { mounted, isUserLoading, hasUser: !!user, hasToken: !!accessToken });
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-[#7C3AED] border-t-transparent"></div>
      </div>
    );
  }

  // Only render the runtime provider if we have both user and token
  if (!user || !accessToken) {
    console.log('[ClientProvider] Missing user or token:', { hasUser: !!user, hasToken: !!accessToken });
    return <>{children}</>;
  }

  console.log('[ClientProvider] Rendering MyRuntimeProvider with user and token');
  return <MyRuntimeProvider>{children}</MyRuntimeProvider>;
} 