'use client';

import { useEffect, useState } from 'react';
import { useUser } from '@auth0/nextjs-auth0/client';
import { useRouter } from 'next/navigation';
import { AlertCircle } from 'lucide-react';

export function SessionHandler() {
  const { user, isLoading, error } = useUser();
  const router = useRouter();
  const [showWarning, setShowWarning] = useState(false);

  useEffect(() => {
    // Function to check token expiration
    const checkTokenExpiration = () => {
      if (!user) return;

      // Auth0 stores exp claim in seconds, convert to milliseconds
      const expirationTime = (user as any).exp * 1000;
      const currentTime = Date.now();
      const timeUntilExpiry = expirationTime - currentTime;

      if (timeUntilExpiry <= 0) {
        // Token has expired, redirect to session expired page
        router.push('/auth/session-expired');
      } else if (timeUntilExpiry <= 5 * 60 * 1000) { // 5 minutes before expiry
        setShowWarning(true);
      }
    };

    // Check immediately and then every minute
    if (user && !isLoading) {
      checkTokenExpiration();
      const interval = setInterval(checkTokenExpiration, 60 * 1000);
      return () => clearInterval(interval);
    }
  }, [user, isLoading, router]);

  if (!showWarning) return null;

  return (
    <div className="fixed bottom-4 right-4 max-w-sm bg-[#1E293B] text-white p-4 rounded-lg shadow-lg border border-[#2A3347] animate-slide-up">
      <div className="flex items-start space-x-3">
        <AlertCircle className="h-5 w-5 text-yellow-400 mt-0.5" />
        <div>
          <h3 className="font-medium">Session Expiring Soon</h3>
          <p className="text-sm text-slate-400 mt-1">
            Your session will expire in less than 5 minutes. Please save your work and refresh the page.
          </p>
          <div className="mt-3 flex space-x-3">
            <button
              onClick={() => window.location.reload()}
              className="text-sm px-3 py-1.5 bg-[#7C3AED] hover:bg-[#6D28D9] rounded-md transition-colors"
            >
              Refresh Now
            </button>
            <button
              onClick={() => setShowWarning(false)}
              className="text-sm px-3 py-1.5 text-slate-400 hover:text-white transition-colors"
            >
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>
  );
} 