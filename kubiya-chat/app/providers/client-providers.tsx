'use client';

import { type ReactNode } from 'react';
import ErrorWrapper from '../components/error-wrapper';
import { ConfigProvider } from '@/lib/config-context';
import { EntityProvider } from './EntityProvider';
import ClientProvider from '../components/ClientProvider';
import { SessionHandler } from '../components/SessionHandler';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from 'next-themes';
import AuthProvider from '../auth-provider';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

interface ProviderProps {
  children: ReactNode;
}

export function Providers({ children }: ProviderProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider
        attribute="class"
        defaultTheme="dark"
        enableSystem={false}
      >
        <ErrorWrapper>
          <AuthProvider>
            <ConfigProvider>
              <EntityProvider>
                <ClientProvider>
                  <SessionHandler />
                  {children}
                </ClientProvider>
              </EntityProvider>
            </ConfigProvider>
          </AuthProvider>
        </ErrorWrapper>
      </ThemeProvider>
    </QueryClientProvider>
  );
} 