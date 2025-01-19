'use client';

import { useEffect } from 'react';
import { useUser } from '@auth0/nextjs-auth0/client';
import { useRouter } from 'next/navigation';

export default function ChatPage() {
  const { user, isLoading } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace('/api/auth/login');
    }
  }, [user, isLoading, router]);

  // Return an empty div to avoid hydration issues
  return <div className="h-full" />;
} 