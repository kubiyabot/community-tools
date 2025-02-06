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

const CACHE_DURATION = 60 * 60 * 1000; // Increase to 60 minutes
const REFRESH_INTERVAL = 30 * 60 * 1000; // Increase refresh to 30 minutes
const THROTTLE_DURATION = 30000; // Increase throttle to 30 seconds
const DEBOUNCE_DURATION = 1000; // Add debounce duration
const MAX_AUTH_RETRIES = 3; // Increase max retries

// Add session storage keys
const SESSION_STORAGE_KEYS = {
  USERS: 'entity_provider_users',
  GROUPS: 'entity_provider_groups',
  TIMESTAMP: 'entity_provider_timestamp'
};

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

  // Optimize saveToSessionStorage to avoid recreating on every render
  const saveToSessionStorage = useCallback((key: string, data: unknown) => {
    try {
      sessionStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
      console.warn('Failed to save to session storage:', error);
    }
  }, []); // Empty dependency array since it doesn't depend on any props or state

  // Move loadFromSessionStorage inside useEffect to avoid stale closure issues
  useEffect(() => {
    function loadFromSessionStorage() {
      try {
        const timestamp = sessionStorage.getItem(SESSION_STORAGE_KEYS.TIMESTAMP);
        if (timestamp && (Date.now() - Number(timestamp) < CACHE_DURATION)) {
          const users = JSON.parse(sessionStorage.getItem(SESSION_STORAGE_KEYS.USERS) || '[]');
          const groups = JSON.parse(sessionStorage.getItem(SESSION_STORAGE_KEYS.GROUPS) || '[]');
          return { users, groups };
        }
      } catch (error) {
        console.warn('Failed to load from session storage:', error);
      }
      return null;
    }

    const cachedData = loadFromSessionStorage();
    if (cachedData) {
      setUsers(cachedData.users);
      setGroups(cachedData.groups);
      setIsLoading(false);
    }
  }, []); // Run only once on mount

  const fetchUsers = useCallback(async (force = false) => {
    // Don't fetch if we have an auth error and exceeded retries
    if (authError && authRetryCount.current >= MAX_AUTH_RETRIES) {
      return users;
    }

    const now = Date.now();
    
    // Enhanced cache check with session storage
    if (!force) {
      // First check memory cache
      if (cache.current.users && (now - cache.current.users.timestamp < CACHE_DURATION)) {
        console.log('Using cached users:', cache.current.users.data);
        return cache.current.users.data;
      }
      
      // Then check session storage
      try {
        const storedData = sessionStorage.getItem(SESSION_STORAGE_KEYS.USERS);
        const timestamp = sessionStorage.getItem(SESSION_STORAGE_KEYS.TIMESTAMP);
        if (storedData && timestamp && (now - Number(timestamp) < CACHE_DURATION)) {
          const parsedData = JSON.parse(storedData);
          cache.current.users = { data: parsedData, timestamp: Number(timestamp) };
          setUsers(parsedData);
          console.log('Using session storage users:', parsedData);
          return parsedData;
        }
      } catch (error) {
        console.warn('Failed to load from session storage:', error);
      }
    }

    // Prevent concurrent requests
    if (isFetching.current.users) {
      return users;
    }

    // Clear existing timer
    if (fetchTimers.current.users) {
      clearTimeout(fetchTimers.current.users);
    }

    isFetching.current.users = true;

    try {
      console.log('Fetching users from API...');
      const response = await fetch('/api/v2/users?limit=100&page=1');
      
      if (response.status === 401 || response.status === 403) {
        handleAuthError();
        return users;
      }
      
      if (!response.ok) {
        throw new Error('Failed to fetch users');
      }
      
      const responseData = await response.json();
      console.log('Users API response received');
      
      // Extract users from the paginated response
      const data = responseData.items || [];
      console.log('Extracted users count:', data.length);
      
      // Reset auth error state
      setAuthError(false);
      authRetryCount.current = 0;
      
      // Update cache, session storage, and state
      cache.current.users = { data, timestamp: now };
      saveToSessionStorage(SESSION_STORAGE_KEYS.USERS, data);
      saveToSessionStorage(SESSION_STORAGE_KEYS.TIMESTAMP, now);
      setUsers(data);
      console.log('Users data stored in cache and state');
      return data;
    } catch (err) {
      console.error('Error fetching users:', err);
      setError(err instanceof Error ? err : new Error('Failed to fetch users'));
      return users;
    } finally {
      isFetching.current.users = false;
      
      if (!authError) {
        fetchTimers.current.users = setTimeout(() => {
          fetchTimers.current.users = null;
        }, THROTTLE_DURATION);
      }
    }
  }, [authError, handleAuthError, users, saveToSessionStorage]);

  const fetchGroups = useCallback(async (force = false) => {
    if (authError && authRetryCount.current >= MAX_AUTH_RETRIES) {
      return groups;
    }

    const now = Date.now();
    
    // Enhanced cache check with session storage
    if (!force) {
      // First check memory cache
      if (cache.current.groups && (now - cache.current.groups.timestamp < CACHE_DURATION)) {
        return cache.current.groups.data;
      }
      
      // Then check session storage
      try {
        const storedData = sessionStorage.getItem(SESSION_STORAGE_KEYS.GROUPS);
        const timestamp = sessionStorage.getItem(SESSION_STORAGE_KEYS.TIMESTAMP);
        if (storedData && timestamp && (now - Number(timestamp) < CACHE_DURATION)) {
          const parsedData = JSON.parse(storedData);
          cache.current.groups = { data: parsedData, timestamp: Number(timestamp) };
          setGroups(parsedData);
          return parsedData;
        }
      } catch (error) {
        console.warn('Failed to load from session storage:', error);
      }
    }

    // Prevent concurrent requests
    if (isFetching.current.groups) {
      return groups;
    }

    if (fetchTimers.current.groups) {
      clearTimeout(fetchTimers.current.groups);
    }

    isFetching.current.groups = true;

    try {
      const response = await fetch('/api/v1/manage/groups');
      
      if (response.status === 401 || response.status === 403) {
        handleAuthError();
        return groups;
      }
      
      if (!response.ok) {
        throw new Error('Failed to fetch groups');
      }
      
      const data = await response.json();
      
      setAuthError(false);
      authRetryCount.current = 0;
      
      // Update cache, session storage, and state
      cache.current.groups = { data, timestamp: now };
      saveToSessionStorage(SESSION_STORAGE_KEYS.GROUPS, data);
      saveToSessionStorage(SESSION_STORAGE_KEYS.TIMESTAMP, now);
      setGroups(data);
      return data;
    } catch (err) {
      console.error('Error fetching groups:', err);
      setError(err instanceof Error ? err : new Error('Failed to fetch groups'));
      return groups;
    } finally {
      isFetching.current.groups = false;
      
      if (!authError) {
        fetchTimers.current.groups = setTimeout(() => {
          fetchTimers.current.groups = null;
        }, THROTTLE_DURATION);
      }
    }
  }, [authError, handleAuthError, groups, saveToSessionStorage]);

  const getEntityMetadata = useCallback((uuid: string): EntityMetadata | undefined => {
    // Use cached data if available
    const cachedUsers = cache.current.users?.data || users;
    const cachedGroups = cache.current.groups?.data || groups;

    console.log('getEntityMetadata called:', {
      uuid,
      cachedUsersCount: cachedUsers?.length,
      cachedGroupsCount: cachedGroups?.length,
      usersCount: users.length,
      groupsCount: groups.length
    });

    if (Array.isArray(cachedUsers)) {
      console.log('Searching through users for uuid:', uuid);
      const foundUser = cachedUsers.find(u => {
        const matches = u.uuid === uuid;
        if (matches) {
          console.log('Found matching user:', u);
        }
        return matches;
      });
      
      if (foundUser) {
        const metadata: EntityMetadata = {
          uuid: foundUser.uuid,
          name: foundUser.name || foundUser.email,
          image: foundUser.image,
          type: 'user',
          status: foundUser.user_status,
          create_at: foundUser.create_at
        };
        console.log('Returning user metadata:', metadata);
        return metadata;
      }
    }

    if (Array.isArray(cachedGroups)) {
      console.log('Searching through groups for uuid:', uuid);
      const foundGroup = cachedGroups.find(g => {
        const matches = g.uuid === uuid;
        if (matches) {
          console.log('Found matching group:', g);
        }
        return matches;
      });
      
      if (foundGroup) {
        const metadata: EntityMetadata = {
          uuid: foundGroup.uuid,
          name: foundGroup.name,
          description: foundGroup.description,
          type: 'group',
          create_at: foundGroup.create_at
        };
        console.log('Returning group metadata:', metadata);
        return metadata;
      }
    }

    console.log('No entity found for uuid:', uuid);
    return undefined;
  }, [users, groups]); // Dependencies still needed for state updates

  // Add debounce function
  const debounce = useCallback((fn: Function, delay: number) => {
    let timeoutId: NodeJS.Timeout;
    return (...args: any[]) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => fn(...args), delay);
    };
  }, []);

  // Optimize the main data fetching effect
  useEffect(() => {
    if (!user || authError) return;

    let mounted = true;
    let refreshTimeout: NodeJS.Timeout;

    const debouncedFetch = debounce(async () => {
      if (mounted && !authError) {
        // Changed condition to fetch if we have no data
        if (!cache.current.users?.data?.length || !cache.current.groups?.data?.length) {
          console.log('Initial fetch triggered - no cached data');
          setIsLoading(true);
          try {
            await Promise.all([fetchUsers(true), fetchGroups()]);
          } finally {
            if (mounted) {
              setIsLoading(false);
            }
          }
        }
      }
    }, DEBOUNCE_DURATION);

    // Immediate fetch if no data
    if (!cache.current.users?.data?.length || !cache.current.groups?.data?.length) {
      console.log('Triggering immediate fetch - no cached data');
      debouncedFetch();
    }

    const scheduleNextRefresh = () => {
      if (mounted && !authError) {
        refreshTimeout = setTimeout(() => {
          if (!document.hidden && !isFetching.current.users && !isFetching.current.groups) {
            const now = Date.now();
            const shouldRefreshUsers = !cache.current.users?.timestamp || 
              (now - cache.current.users.timestamp >= REFRESH_INTERVAL);
            const shouldRefreshGroups = !cache.current.groups?.timestamp || 
              (now - cache.current.groups.timestamp >= REFRESH_INTERVAL);

            if (shouldRefreshUsers) fetchUsers();
            if (shouldRefreshGroups) fetchGroups();
          }
          scheduleNextRefresh();
        }, REFRESH_INTERVAL);
      }
    };

    scheduleNextRefresh();

    const handleVisibilityChange = debounce(() => {
      if (mounted && !document.hidden) {
        const now = Date.now();
        if (now - (cache.current.users?.timestamp || 0) >= REFRESH_INTERVAL) {
          fetchUsers();
          fetchGroups();
        }
      }
    }, DEBOUNCE_DURATION);

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      mounted = false;
      clearTimeout(refreshTimeout);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      if (fetchTimers.current.users) clearTimeout(fetchTimers.current.users);
      if (fetchTimers.current.groups) clearTimeout(fetchTimers.current.groups);
    };
  }, [user, authError, fetchUsers, fetchGroups, users.length, groups.length, debounce]);

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