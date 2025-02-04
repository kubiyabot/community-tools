'use client';

import { type ReactNode } from 'react';
import { UserProvider } from '@auth0/nextjs-auth0/client';
import { ConfigProvider } from '@/lib/config-context';
import { EntityProvider } from './providers/EntityProvider';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from 'next-themes';

interface ProvidersProps {
  children: ReactNode;
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 30, // 30 minutes
      refetchOnWindowFocus: false,
      retry: 1
    },
  },
});

// Use AuthProvider for Auth0 authentication
import AuthProvider from './auth-provider';

export function Providers({ children }: ProvidersProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider
        attribute="class"
        defaultTheme="dark"
        enableSystem={false}
      >
        <AuthProvider>
          <ConfigProvider>
            <EntityProvider>
              {children}
            </EntityProvider>
          </ConfigProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
} 