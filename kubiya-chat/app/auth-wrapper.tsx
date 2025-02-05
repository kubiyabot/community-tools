'use client';

import { useUser } from '@auth0/nextjs-auth0/client';
import { useEffect, useRef } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { toast } from 'sonner';

const PUBLIC_PATHS = ['/login', '/auth/session-expired', '/api/auth', '/'];

export default function AuthWrapper({ children }: { children: React.ReactNode }) {
  const { user, error, isLoading } = useUser();
  const router = useRouter();
  const pathname = usePathname();
  const intervalRef = useRef<number>();

  useEffect(() => {
    // Handle authentication errors
    if (error) {
      console.error('Auth error:', error);
      toast.error('Authentication error occurred');
      router.push('/auth/session-expired');
      return;
    }

    // Skip checks for public paths
    if (PUBLIC_PATHS.some(path => pathname?.startsWith(path))) {
      return;
    }

    // Handle unauthenticated state
    if (!isLoading && !user && !PUBLIC_PATHS.some(path => pathname?.startsWith(path))) {
      router.push('/');
      return;
    }

    // If user is authenticated and on the landing page, redirect to chat
    if (!isLoading && user && pathname === '/') {
      router.push('/chat');
      return;
    }

    const checkSession = async () => {
      try {
        const response = await fetch('/api/auth/me');
        if (!response.ok) {
          toast.error('Your session has expired');
          router.push('/auth/session-expired');
        }
      } catch (error) {
        console.error('Session check error:', error);
        router.push('/auth/session-expired');
      }
    };

    if (user) {
      // Initial check
      checkSession();
      // Check session every 5 minutes
      intervalRef.current = window.setInterval(checkSession, 5 * 60 * 1000);
    }

    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
      }
    };
  }, [user, error, isLoading, router, pathname]);

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-white border-t-transparent" />
      </div>
    );
  }

  return <>{children}</>;
} 