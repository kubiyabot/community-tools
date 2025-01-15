'use client';

import { UserProvider } from '@auth0/nextjs-auth0/client';

function AuthWrapper({ children }: { children: React.ReactNode }) {
  return <UserProvider>{children}</UserProvider>;
}

export default AuthWrapper; 