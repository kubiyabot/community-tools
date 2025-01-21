'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

interface AuthRedirectProps {
  reason?: 'login' | 'session_expired' | 'unauthorized';
  redirectPath?: string;
}

export function AuthRedirect({ 
  reason = 'login',
  redirectPath = '/api/auth/auth0/login'
}: AuthRedirectProps) {
  const router = useRouter();
  const [countdown, setCountdown] = useState(5);

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          router.push(redirectPath);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [router, redirectPath]);

  const messages = {
    login: {
      title: 'Authentication Required',
      description: 'You are being redirected to the sign in page to authenticate.',
      action: 'Sign In Now'
    },
    session_expired: {
      title: 'Session Expired',
      description: 'Your session has expired. Please sign in again to continue.',
      action: 'Sign In Again'
    },
    unauthorized: {
      title: 'Access Denied',
      description: 'You do not have permission to access this page. Please sign in with an authorized account.',
      action: 'Sign In'
    }
  };

  const currentMessage = messages[reason];

  return (
    <div className="min-h-screen bg-[#0F1629] flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-[#1E293B] flex items-center justify-center">
            <Loader2 className="w-8 h-8 text-[#7C3AED] animate-spin" />
          </div>
          <h2 className="text-2xl font-semibold text-white mb-2">
            {currentMessage.title}
          </h2>
          <p className="text-slate-400 mb-6">
            {currentMessage.description}
          </p>
          <div className="text-sm text-slate-500 mb-4">
            Redirecting in {countdown} seconds...
          </div>
          <button
            onClick={() => router.push(redirectPath)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-[#7C3AED] hover:bg-[#6D28D9] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#7C3AED] transition-colors"
          >
            {currentMessage.action}
          </button>
        </div>
      </div>
    </div>
  );
} 