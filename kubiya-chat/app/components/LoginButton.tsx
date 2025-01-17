'use client';

import { useUser } from '@auth0/nextjs-auth0/client';
import { Button } from '@/app/components/button';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { toast } from '@/app/components/use-toast';

export function LoginButton() {
  const { user, error: userError, isLoading } = useUser();
  const router = useRouter();
  const [isAuthenticating, setIsAuthenticating] = useState(false);

  useEffect(() => {
    if (user && window.location.pathname === '/') {
      router.push('/chat');
    }
  }, [user, router]);

  useEffect(() => {
    if (userError) {
      toast({
        title: 'Authentication Error',
        description: userError.message || 'Failed to authenticate',
        variant: 'destructive',
      });
    }
  }, [userError]);

  const handleLogin = async () => {
    try {
      setIsAuthenticating(true);
      const returnTo = window.location.pathname;
      const loginUrl = `/api/auth/login?returnTo=${encodeURIComponent(returnTo)}`;
      
      // Use fetch to check if the auth endpoint is responding
      const response = await fetch(loginUrl, { method: 'HEAD' });
      
      if (!response.ok) {
        throw new Error('Authentication service is not available');
      }
      
      // If the service is available, redirect
      window.location.href = loginUrl;
    } catch (error) {
      console.error('Login error:', error);
      toast({
        title: 'Unable to Login',
        description: error instanceof Error ? error.message : 'Failed to start login process',
        variant: 'destructive',
      });
      setIsAuthenticating(false);
    }
  };

  const handleLogout = async () => {
    try {
      setIsAuthenticating(true);
      window.location.href = '/api/auth/logout';
    } catch (error) {
      console.error('Logout error:', error);
      toast({
        title: 'Unable to Logout',
        description: error instanceof Error ? error.message : 'Failed to logout',
        variant: 'destructive',
      });
      setIsAuthenticating(false);
    }
  };

  if (isLoading || isAuthenticating) {
    return (
      <Button variant="outline" disabled>
        <span className="animate-pulse">Loading...</span>
      </Button>
    );
  }

  if (userError) {
    return (
      <Button 
        variant="destructive" 
        onClick={() => window.location.reload()}
        title={userError.message}
      >
        Retry Login
      </Button>
    );
  }

  if (user) {
    return (
      <Button variant="outline" onClick={handleLogout}>
        Logout ({user.email})
      </Button>
    );
  }

  return (
    <Button variant="outline" onClick={handleLogin}>
      Login
    </Button>
  );
} 