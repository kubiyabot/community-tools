"use client";

import React, { createContext, useContext, useEffect, useState, useCallback, useRef, useMemo } from 'react';
import type { User, Group, EntityMetadata } from '../types/user';
import { useUser } from '@auth0/nextjs-auth0/client';
import { toast } from '../components/ui/use-toast';

interface EntityContextType {
  users: User[];
  groups: Group[];
  isLoading: boolean;
  error: Error | null;
  refetchUsers: () => Promise<void>;
  refetchGroups: () => Promise<void>;
  getEntityMetadata: (uuid: string) => EntityMetadata | undefined;
}

const EntityContext = createContext<EntityContextType | undefined>(undefined);

const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes in milliseconds
const THROTTLE_DURATION = 2000; // 2 seconds throttle between requests
const MAX_AUTH_RETRIES = 2; // Maximum number of retries for auth errors

interface CacheData<T> {
  data: T[];
  timestamp: number;
}

export function EntityProvider({ children }: { children: React.ReactNode }) {
  const { user } = useUser();
  const [users, setUsers] = useState<User[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [authError, setAuthError] = useState(false);
  const authRetryCount = useRef(0);
  
  // Use refs for caching and throttling
  const cache = useRef<{
    users: CacheData<User> | null;
    groups: CacheData<Group> | null;
  }>({
    users: null,
    groups: null
  });
  
  const fetchTimers = useRef<{
    users: NodeJS.Timeout | null;
    groups: NodeJS.Timeout | null;
  }>({
    users: null,
    groups: null
  });

  const isFetching = useRef<{
    users: boolean;
    groups: boolean;
  }>({
    users: false,
    groups: false
  });

  const handleAuthError = useCallback(() => {
    authRetryCount.current += 1;
    setAuthError(true);
    
    if (authRetryCount.current >= MAX_AUTH_RETRIES) {
      // Show toast for auth error
      toast({
        title: "Authentication Error",
        description: "Please refresh the page or sign in again.",
        variant: "destructive",
      });
      
      // Clear any pending timers
      if (fetchTimers.current.users) clearTimeout(fetchTimers.current.users);
      if (fetchTimers.current.groups) clearTimeout(fetchTimers.current.groups);
      
      // Reset fetching states
      isFetching.current.users = false;
      isFetching.current.groups = false;
      
      setIsLoading(false);
    }
  }, []);

  const fetchUsers = useCallback(async (force = false) => {
    // Don't fetch if we have an auth error and exceeded retries
    if (authError && authRetryCount.current >= MAX_AUTH_RETRIES) {
      return;
    }

    const now = Date.now();
    
    // Check cache and throttle
    if (!force && cache.current.users && (now - cache.current.users.timestamp < CACHE_DURATION)) {
      return;
    }

    // Prevent concurrent requests
    if (isFetching.current.users) {
      return;
    }

    // Clear any existing timer
    if (fetchTimers.current.users) {
      clearTimeout(fetchTimers.current.users);
    }

    isFetching.current.users = true;

    try {
      const response = await fetch('/api/v2/users?limit=100&page=1');
      
      if (response.status === 401 || response.status === 403) {
        handleAuthError();
        return;
      }
      
      if (!response.ok) {
        throw new Error('Failed to fetch users');
      }
      
      const data = await response.json();
      
      // Reset auth error state on successful fetch
      setAuthError(false);
      authRetryCount.current = 0;
      
      // Update cache and state
      cache.current.users = {
        data,
        timestamp: now
      };
      setUsers(data);
    } catch (err) {
      console.error('Error fetching users:', err);
      setError(err instanceof Error ? err : new Error('Failed to fetch users'));
    } finally {
      isFetching.current.users = false;
      
      // Set throttle timer only if we don't have an auth error
      if (!authError) {
        fetchTimers.current.users = setTimeout(() => {
          fetchTimers.current.users = null;
        }, THROTTLE_DURATION);
      }
    }
  }, [authError, handleAuthError]);

  const fetchGroups = useCallback(async (force = false) => {
    // Don't fetch if we have an auth error and exceeded retries
    if (authError && authRetryCount.current >= MAX_AUTH_RETRIES) {
      return;
    }

    const now = Date.now();
    
    // Check cache and throttle
    if (!force && cache.current.groups && (now - cache.current.groups.timestamp < CACHE_DURATION)) {
      return;
    }

    // Prevent concurrent requests
    if (isFetching.current.groups) {
      return;
    }

    // Clear any existing timer
    if (fetchTimers.current.groups) {
      clearTimeout(fetchTimers.current.groups);
    }

    isFetching.current.groups = true;

    try {
      const response = await fetch('/api/v1/manage/groups');
      
      if (response.status === 401 || response.status === 403) {
        handleAuthError();
        return;
      }
      
      if (!response.ok) {
        throw new Error('Failed to fetch groups');
      }
      
      const data = await response.json();
      
      // Reset auth error state on successful fetch
      setAuthError(false);
      authRetryCount.current = 0;
      
      // Update cache and state
      cache.current.groups = {
        data,
        timestamp: now
      };
      setGroups(data);
    } catch (err) {
      console.error('Error fetching groups:', err);
      setError(err instanceof Error ? err : new Error('Failed to fetch groups'));
    } finally {
      isFetching.current.groups = false;
      
      // Set throttle timer only if we don't have an auth error
      if (!authError) {
        fetchTimers.current.groups = setTimeout(() => {
          fetchTimers.current.groups = null;
        }, THROTTLE_DURATION);
      }
    }
  }, [authError, handleAuthError]);

  const getEntityMetadata = useCallback((uuid: string): EntityMetadata | undefined => {
    // Use cached data if available
    const cachedUsers = cache.current.users?.data || users;
    const cachedGroups = cache.current.groups?.data || groups;

    if (Array.isArray(cachedUsers)) {
      const foundUser = cachedUsers.find(u => u.uuid === uuid);
      if (foundUser) {
        return {
          uuid: foundUser.uuid,
          name: foundUser.name || foundUser.email,
          image: foundUser.image,
          type: 'user',
          status: foundUser.user_status,
          create_at: foundUser.create_at
        };
      }
    }

    if (Array.isArray(cachedGroups)) {
      const foundGroup = cachedGroups.find(g => g.uuid === uuid);
      if (foundGroup) {
        return {
          uuid: foundGroup.uuid,
          name: foundGroup.name,
          description: foundGroup.description,
          type: 'group',
          create_at: foundGroup.create_at
        };
      }
    }

    return undefined;
  }, [users, groups]); // Dependencies still needed for state updates

  // Initial fetch
  useEffect(() => {
    if (user && !authError) {
      setIsLoading(true);
      Promise.all([fetchUsers(), fetchGroups()])
        .finally(() => setIsLoading(false));

      // Set up periodic refresh only if no auth errors
      const refreshInterval = setInterval(() => {
        if (!document.hidden && !authError) {
          fetchUsers();
          fetchGroups();
        }
      }, CACHE_DURATION);

      return () => {
        clearInterval(refreshInterval);
        if (fetchTimers.current.users) clearTimeout(fetchTimers.current.users);
        if (fetchTimers.current.groups) clearTimeout(fetchTimers.current.groups);
      };
    }
  }, [user, fetchUsers, fetchGroups, authError]);

  const refetchUsers = useCallback(async () => {
    await fetchUsers(true);
  }, [fetchUsers]);

  const refetchGroups = useCallback(async () => {
    await fetchGroups(true);
  }, [fetchGroups]);

  const value = useMemo(() => ({
    users,
    groups,
    isLoading,
    error,
    refetchUsers,
    refetchGroups,
    getEntityMetadata
  }), [users, groups, isLoading, error, refetchUsers, refetchGroups, getEntityMetadata]);

  return (
    <EntityContext.Provider value={value}>
      {children}
    </EntityContext.Provider>
  );
}

export function useEntity() {
  const context = useContext(EntityContext);
  if (context === undefined) {
    throw new Error('useEntity must be used within an EntityProvider');
  }
  return context;
} 