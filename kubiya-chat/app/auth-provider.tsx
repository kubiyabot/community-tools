'use client';

import { UserProvider } from '@auth0/nextjs-auth0/client';
import { type ReactNode } from 'react';

export default function AuthProvider({ children }: { children: ReactNode }) {
  return (
    // @ts-expect-error - Known issue with Auth0 types in Next.js 14
    <UserProvider>
      {children}
    </UserProvider>
  );
} 