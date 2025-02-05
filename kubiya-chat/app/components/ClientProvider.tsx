'use client';

import { useEffect, useState } from 'react';
import { useUser } from '@auth0/nextjs-auth0/client';
import { MyRuntimeProvider } from '../MyRuntimeProvider';
import type { ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useConfig } from '../../lib/config-context';
import { TeammateSelector } from './TeammateSelector';

interface ClientProviderProps {
  children: ReactNode;
}

export default function ClientProvider({ children }: ClientProviderProps): JSX.Element {
  const [mounted, setMounted] = useState(false);
  const { user, isLoading: isUserLoading } = useUser();
  const router = useRouter();
  const { setApiKey, setAuthType, apiKey } = useConfig();
  const [isRedirecting, setIsRedirecting] = useState(false);

  // Mount effect
  useEffect(() => {
    console.log('ClientProvider: Mounting');
    setMounted(true);
    return () => setMounted(false);
  }, []);

  // Token fetch effect
  useEffect(() => {
    async function fetchToken() {
      if (!mounted || isRedirecting || isUserLoading) return;

      console.log('ClientProvider: Token fetch check', { 
        user: user ? 'exists' : 'null', 
        isUserLoading,
        mounted,
        hasApiKey: !!apiKey,
        pathname: window.location.pathname
      });

      // If we have a user but no API key, fetch it
      if (user && !apiKey) {
        console.log('ClientProvider: Fetching token for user:', user.email);
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
              console.log('ClientProvider: Auth failed, redirecting to login');
              setIsRedirecting(true);
              const loginUrl = new URL('/api/auth/login', window.location.origin);
              loginUrl.searchParams.set('returnTo', '/chat');
              router.push(loginUrl.toString());
              return;
            }
            throw new Error(`Profile fetch failed: ${response.status}`);
          }

          const data = await response.json();
          if (!data.accessToken) {
            console.error('ClientProvider: No access token in response');
            setIsRedirecting(true);
            const loginUrl = new URL('/api/auth/login', window.location.origin);
            loginUrl.searchParams.set('returnTo', '/chat');
            router.push(loginUrl.toString());
            return;
          }

          console.log('ClientProvider: Setting access token');
          setApiKey(data.accessToken);
          setAuthType('sso');

          // After setting token, ensure we're on the chat page
          if (window.location.pathname === '/') {
            console.log('ClientProvider: Redirecting to chat after token set');
            router.push('/chat');
          }
        } catch (error) {
          console.error('ClientProvider: Token fetch error:', error);
          setIsRedirecting(true);
          const loginUrl = new URL('/api/auth/login', window.location.origin);
          loginUrl.searchParams.set('returnTo', '/chat');
          router.push(loginUrl.toString());
        }
      }
      
      // If we have no user and we're not loading, redirect to login
      if (!user && mounted) {
        console.log('ClientProvider: No user, redirecting to login');
        setIsRedirecting(true);
        const loginUrl = new URL('/api/auth/login', window.location.origin);
        loginUrl.searchParams.set('returnTo', '/chat');
        router.push(loginUrl.toString());
      }
    }

    fetchToken();
  }, [user, isUserLoading, mounted, router, setApiKey, setAuthType, apiKey, isRedirecting]);

  // Show loading states with proper messaging
  if (!mounted) {
    console.log('ClientProvider: Not mounted');
    return <LoadingSpinner message="Initializing..." />;
  }

  if (isUserLoading) {
    console.log('ClientProvider: Loading user');
    return <LoadingSpinner message="Loading user..." />;
  }

  if (isRedirecting) {
    console.log('ClientProvider: Redirecting');
    return <LoadingSpinner message="Redirecting..." />;
  }

  if (user && !apiKey) {
    console.log('ClientProvider: Loading token');
    return <LoadingSpinner message="Loading credentials..." />;
  }

  if (!user || !apiKey) {
    console.log('ClientProvider: No auth');
    return <LoadingSpinner message="Please log in to continue" />;
  }

  console.log('ClientProvider: Rendering MyRuntimeProvider');
  return <MyRuntimeProvider>{children}</MyRuntimeProvider>;
}

// Loading spinner component
function LoadingSpinner({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-screen gap-4">
      <div className="animate-spin rounded-full h-12 w-12 border-4 border-[#7C3AED] border-t-transparent"></div>
      <div className="text-white text-sm">{message}</div>
    </div>
  );
} 