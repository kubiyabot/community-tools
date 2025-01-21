'use client';

import { useUser } from '@auth0/nextjs-auth0/client';
import { useRouter, usePathname } from 'next/navigation';
import { useEffect } from 'react';
import { useConfig } from '@/lib/config-context';

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading, error } = useUser();
  const router = useRouter();
  const pathname = usePathname();
  const { setAuthType } = useConfig();

  useEffect(() => {
    // Only redirect if we're definitely not loading and definitely have no user
    if (!isLoading && !error && !user) {
      console.log('No user found, redirecting to login');
      window.location.href = '/api/auth/login?returnTo=/chat';
    }
  }, [user, isLoading, error]);

  useEffect(() => {
    // When we have a user, set the auth type to SSO
    if (user) {
      console.log('Setting auth type to SSO');
      setAuthType('sso');
    }
  }, [user, setAuthType]);

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-[#7C3AED] border-t-transparent"></div>
      </div>
    );
  }

  // If we have a user, render the children directly since providers are in root layout
  if (user) {
    return children;
  }

  // Return null while redirecting to avoid flash of content
  return null;
} 