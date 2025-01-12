'use client';

import { useUser } from '@auth0/nextjs-auth0/client';
import { Button } from '@/components/ui/button';

export function LoginButton() {
  const { user, error, isLoading } = useUser();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>{error.message}</div>;

  if (user) {
    return (
      <Button variant="outline" onClick={() => window.location.href = '/api/auth/logout'}>
        Logout ({user.email})
      </Button>
    );
  }

  return (
    <Button variant="outline" onClick={() => window.location.href = '/api/auth/login'}>
      Login
    </Button>
  );
} 