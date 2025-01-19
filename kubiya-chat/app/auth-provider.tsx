'use client';

import { UserProvider } from '@auth0/nextjs-auth0/client';

export default function AuthProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <UserProvider loginUrl="/api/auth/auth0/login" profileUrl="/api/auth/me">
      {children}
    </UserProvider>
  );
} 