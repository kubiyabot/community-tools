'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function SessionExpiredPage() {
  const router = useRouter();
  const [countdown, setCountdown] = useState(5);

  useEffect(() => {
    // Clear any existing auth state
    localStorage.removeItem('user');
    sessionStorage.clear();
    
    // Setup countdown timer
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          router.push('/api/auth/login');
          return 0;
        }
        return prev - 1;
      });
    }, 1000) as unknown as number;

    return () => clearInterval(timer);
  }, [router]);

  const handleLogin = () => {
    const loginUrl = new URL('/api/auth/login', window.location.origin);
    loginUrl.searchParams.set('returnTo', '/chat');
    router.push(loginUrl.toString());
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-gray-900 to-gray-800">
      <div className="mx-auto flex w-full max-w-[400px] flex-col items-center space-y-8 rounded-xl bg-white/10 p-8 backdrop-blur-lg">
        {/* Icon */}
        <div className="rounded-full bg-red-500/10 p-4">
          <svg 
            className="h-12 w-12 text-red-500" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
            />
          </svg>
        </div>
        
        {/* Text Content */}
        <div className="flex flex-col space-y-3 text-center">
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Session Expired
          </h1>
          <p className="text-gray-400">
            Your session has timed out for security reasons.
            <br />
            Please log in again to continue.
          </p>
        </div>

        {/* Button */}
        <button 
          className="group relative w-full overflow-hidden rounded-lg bg-indigo-600 px-4 py-3 text-white transition-all hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          onClick={handleLogin}
        >
          <span className="relative z-10 flex items-center justify-center font-medium">
            <svg 
              className="mr-2 h-5 w-5 transition-transform group-hover:rotate-180" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" 
              />
            </svg>
            Log In Again
          </span>
        </button>

        {/* Timer */}
        <p className="text-sm text-gray-400">
          Redirecting to login in 
          <span className="font-mono text-white"> {countdown} </span> 
          seconds...
        </p>
      </div> 
    </div>
  );
} 