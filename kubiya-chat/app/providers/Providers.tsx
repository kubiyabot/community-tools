'use client';

import { type ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from 'next-themes';
import ErrorWrapper from '@/app/components/error-wrapper';
import AuthProvider from '@/app/auth-provider';
import AuthWrapper from '@/app/auth-wrapper';
import { ConfigProvider } from '@/lib/config-context';
import { EntityProvider } from './EntityProvider';
import ClientProvider from '../components/ClientProvider';
import { SessionHandler } from '../components/SessionHandler';

// Create a client
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

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider
        attribute="class"
        defaultTheme="dark"
        enableSystem={false}
      >
        <ErrorWrapper>
          <AuthProvider>
            <AuthWrapper>
              <ConfigProvider>
                <EntityProvider>
                  <ClientProvider>
                    <SessionHandler />
                    {children}
                  </ClientProvider>
                </EntityProvider>
              </ConfigProvider>
            </AuthWrapper>
          </AuthProvider>
        </ErrorWrapper>
      </ThemeProvider>
    </QueryClientProvider>
  );
} 