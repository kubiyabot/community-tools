'use client';

import { UserProvider } from '@auth0/nextjs-auth0/client';

export default function AuthProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <UserProvider loginUrl="/api/auth/login" profileUrl="/api/auth/me">
      {children}
    </UserProvider>
  );
} 