"use client";

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

export default function AuthCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    if (!searchParams) {
      console.error('No search parameters available');
      router.replace('/?error=Missing+authentication+parameters');
      return;
    }

    const error = searchParams.get('error');
    const errorDescription = searchParams.get('error_description');
    
    if (error) {
      console.error('Auth error from provider:', { error, errorDescription });
      router.replace(`/?error=${encodeURIComponent(errorDescription || error)}`);
      return;
    }

    // Let Auth0's handleCallback handle the token exchange
    router.replace('/api/auth/auth0/callback' + window.location.search);
  }, [searchParams, router]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#0F172A]">
      <div className="animate-spin rounded-full h-8 w-8 border-2 border-[#7C3AED] border-t-transparent mb-4"></div>
      <p className="text-white text-sm">Completing sign in...</p>
    </div>
  );
} 