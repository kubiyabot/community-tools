"use client";

import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from 'react';
import type { User, Group, EntityMetadata } from '../types/user';
import { useUser } from '@auth0/nextjs-auth0/client';

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

export function EntityProvider({ children }: { children: React.ReactNode }) {
  const { user } = useUser();
  const [users, setUsers] = useState<User[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [lastFetchUsers, setLastFetchUsers] = useState(0);
  const [lastFetchGroups, setLastFetchGroups] = useState(0);

  const fetchUsers = useCallback(async (force = false) => {
    const now = Date.now();
    if (!force && now - lastFetchUsers < CACHE_DURATION) {
      return; // Use cached data
    }

    try {
      const response = await fetch('/api/v2/users?limit=100&page=1');
      if (!response.ok) throw new Error('Failed to fetch users');
      const data = await response.json();
      setUsers(data);
      setLastFetchUsers(now);
    } catch (err) {
      console.error('Error fetching users:', err);
      setError(err instanceof Error ? err : new Error('Failed to fetch users'));
    }
  }, [lastFetchUsers]);

  const fetchGroups = useCallback(async (force = false) => {
    const now = Date.now();
    if (!force && now - lastFetchGroups < CACHE_DURATION) {
      return; // Use cached data
    }

    try {
      const response = await fetch('/api/v1/manage/groups');
      if (!response.ok) throw new Error('Failed to fetch groups');
      const data = await response.json();
      setGroups(data);
      setLastFetchGroups(now);
    } catch (err) {
      console.error('Error fetching groups:', err);
      setError(err instanceof Error ? err : new Error('Failed to fetch groups'));
    }
  }, [lastFetchGroups]);

  const getEntityMetadata = useCallback((uuid: string): EntityMetadata | undefined => {
    // Check if users is defined and is an array
    if (Array.isArray(users)) {
      const foundUser = users.find(u => u.uuid === uuid);
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

    // Check if groups is defined and is an array
    if (Array.isArray(groups)) {
      const foundGroup = groups.find(g => g.uuid === uuid);
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
  }, [users, groups]);

  // Initial fetch
  useEffect(() => {
    if (user) {
      setIsLoading(true);
      Promise.all([fetchUsers(), fetchGroups()])
        .finally(() => setIsLoading(false));
    }
  }, [user, fetchUsers, fetchGroups]);

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