'use client';

import MyAssistant from "@/app/components/MyAssistant";
import { useUser } from '@auth0/nextjs-auth0/client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function ChatDashboard() {
  const { user, error, isLoading } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (error) {
        router.push('/auth/session-expired');
        return;
      }
      if (!user) {
        router.push('/');
        return;
      }
    }
  }, [user, error, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-white border-t-transparent" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <main className="flex-1 flex flex-col">
      <MyAssistant />
    </main>
  );
} 