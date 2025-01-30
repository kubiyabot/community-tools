import React from 'react';
import { Button } from './ui/button';

export const SessionExpired = () => {
  const handleSignIn = () => {
    window.location.href = '/api/auth/login';
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-b from-[#0F172A] to-[#1E293B]">
      <div className="max-w-md w-full mx-auto p-8 rounded-lg bg-white/5 backdrop-blur-sm">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Session Expired</h2>
          <p className="text-gray-300 mb-8">
            Your session has expired. Please sign in again to continue using the application.
          </p>
          <Button
            onClick={handleSignIn}
            className="bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-semibold py-2 px-6 rounded-lg transition-colors"
          >
            Sign Back In
          </Button>
        </div>
      </div>
    </div>
  );
}; 