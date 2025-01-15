'use client';

import { type ReactNode } from 'react';
import { UserProvider } from '@auth0/nextjs-auth0/client';
import { ConfigProvider } from '@/lib/config-context';

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <UserProvider loginUrl="/api/auth/login" profileUrl="/api/auth/me">
      <ConfigProvider>
        {children}
      </ConfigProvider>
    </UserProvider>
  );
} 