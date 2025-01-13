"use client";

import { useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useConfig } from '@/lib/config-context';

export default function AuthCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setApiKey } = useConfig();

  const handleCallback = useCallback(async () => {
    try {
      const params = Object.fromEntries(searchParams.entries());
      console.log('Auth callback started:', { 
        params,
        origin: window.location.origin,
        hasSearchParams: !!searchParams,
        url: window.location.href
      });

      const error = searchParams.get('error');
      const errorDescription = searchParams.get('error_description');
      
      if (error) {
        console.error('Auth error from provider:', { error, errorDescription });
        throw new Error(errorDescription || error);
      }

      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const storedState = localStorage.getItem('auth_state');

      console.log('Auth parameters:', {
        hasCode: !!code,
        hasState: !!state,
        hasStoredState: !!storedState,
        stateMatch: state === storedState
      });

      if (!code || !state) {
        throw new Error('Missing authentication parameters');
      }

      if (state !== storedState) {
        console.error('State mismatch:', {
          receivedState: state,
          storedState,
          localStorage: { ...localStorage }
        });
        throw new Error('Invalid state parameter');
      }

      console.log('Exchanging code for token...');
      const tokenEndpoint = 'https://api.kubiya.ai/api/v1/auth/token';
      const redirectUri = `${window.location.origin}/auth/callback`;
      
      console.log('Token request details:', {
        endpoint: tokenEndpoint,
        redirectUri,
        code: code.substring(0, 10) + '...'
      });

      // Exchange code for token
      const response = await fetch(tokenEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Origin': window.location.origin
        },
        body: JSON.stringify({
          code,
          redirect_uri: redirectUri
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('Token exchange failed:', {
          status: response.status,
          statusText: response.statusText,
          error: errorData,
          headers: Object.fromEntries(response.headers.entries())
        });
        throw new Error(`Failed to exchange code for token: ${response.status} ${errorData.message || response.statusText}`);
      }

      const data = await response.json();
      console.log('Token exchange response:', {
        hasToken: !!data.access_token,
        tokenPreview: data.access_token ? `${data.access_token.substring(0, 10)}...` : null,
        responseKeys: Object.keys(data)
      });
      
      if (!data.access_token) {
        console.error('No token in response:', { data });
        throw new Error('No access token in response');
      }

      // Set the API key with SSO type
      console.log('Setting API key with SSO type...');
      setApiKey(data.access_token, 'sso');
      
      // Clean up
      localStorage.removeItem('auth_state');
      
      // Use replace instead of push to prevent back navigation to callback
      console.log('Redirecting to home...');
      router.replace('/');
    } catch (error) {
      console.error('Auth callback error:', {
        error,
        message: error instanceof Error ? error.message : 'Authentication failed',
        stack: error instanceof Error ? error.stack : undefined
      });
      const errorMessage = error instanceof Error ? error.message : 'Authentication failed';
      router.replace(`/?error=${encodeURIComponent(errorMessage)}&time=${Date.now()}`);
    }
  }, [searchParams, router, setApiKey]);

  useEffect(() => {
    console.log('Auth callback component mounted');
    handleCallback();
  }, [handleCallback]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#0F172A]">
      <div className="animate-spin rounded-full h-8 w-8 border-2 border-[#7C3AED] border-t-transparent mb-4"></div>
      <p className="text-white text-sm">Completing sign in...</p>
    </div>
  );
} 