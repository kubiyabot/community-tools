'use client';

import { useEffect } from 'react';
import { useUser } from '@auth0/nextjs-auth0/client';
import { AuthRedirect } from '@/app/components/AuthRedirect';

export default function SessionExpiredPage() {
  const { user, isLoading } = useUser();

  // If user is still logged in, redirect to chat
  useEffect(() => {
    if (!isLoading && user) {
      window.location.href = '/chat';
    }
  }, [user, isLoading]);

  // Show loading state while checking user status
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0F1629] flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[#7C3AED] border-t-transparent"></div>
      </div>
    );
  }

  // Show session expired message if user is not logged in
  return <AuthRedirect reason="session_expired" />;
} 