'use client';

import { type ReactNode } from 'react';
import { UserProvider } from '@auth0/nextjs-auth0/client';
import { ConfigProvider } from '@/lib/config-context';
import { EntityProvider } from './providers/EntityProvider';

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <UserProvider loginUrl="/api/auth/login" profileUrl="/api/auth/me">
      <ConfigProvider>
        <EntityProvider>
          {children}
        </EntityProvider>
      </ConfigProvider>
    </UserProvider>
  );
} 