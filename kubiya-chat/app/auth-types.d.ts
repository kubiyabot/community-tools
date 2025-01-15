import { ComponentType, ReactNode } from 'react';
import type { UserProfile, UserFetcher } from '@auth0/nextjs-auth0/client';

declare module '@auth0/nextjs-auth0/client' {
  export interface UserProviderProps {
    children: ReactNode;
    user?: UserProfile;
    loginUrl?: string;
    profileUrl?: string;
    fetcher?: UserFetcher;
  }

  export const UserProvider: ComponentType<UserProviderProps>;
} 