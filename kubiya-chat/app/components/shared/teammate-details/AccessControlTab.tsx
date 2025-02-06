"use client";

import React, { useMemo } from 'react';
import { useEntity } from '@/app/providers/EntityProvider';
import { Badge } from '@/app/components/ui/badge';
import { ScrollArea } from '@/app/components/ui/scroll-area';
import { User, Users, AlertCircle } from 'lucide-react';
import type { TeammateDetails } from './types';

interface AccessControlTabProps {
  teammate: TeammateDetails;
}

export function AccessControlTab({ teammate }: AccessControlTabProps) {
  const { getEntityMetadata, isLoading, error } = useEntity();

  // Memoize user and group metadata to avoid unnecessary re-renders
  const usersMetadata = useMemo(() => {
    if (!teammate.allowed_users) return [];
    return teammate.allowed_users.map(userId => {
      const metadata = getEntityMetadata(userId);
      return {
        id: userId,
        ...metadata,
      };
    }).filter(user => user); // Filter out undefined entries
  }, [teammate.allowed_users, getEntityMetadata]);

  const groupsMetadata = useMemo(() => {
    if (!teammate.allowed_groups) return [];
    return teammate.allowed_groups.map(groupId => {
      const metadata = getEntityMetadata(groupId);
      return {
        id: groupId,
        ...metadata,
      };
    }).filter(group => group); // Filter out undefined entries
  }, [teammate.allowed_groups, getEntityMetadata]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-6">
        <div className="p-3 rounded-full bg-red-500/10 mb-4">
          <AlertCircle className="h-6 w-6 text-red-400" />
        </div>
        <h3 className="text-lg font-medium text-red-400 mb-2">Error Loading Access Control</h3>
        <p className="text-sm text-[#94A3B8] max-w-sm mb-4">
          {error.message}
        </p>
        {error.message.includes('Session expired') && (
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-[#7C3AED] text-white rounded-md hover:bg-[#6D28D9] transition-colors"
          >
            Refresh Page
          </button>
        )}
        <p className="text-xs text-[#94A3B8] mt-4">
          If the problem persists, please contact support at support@kubiya.ai
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-6">
        <div className="p-3 rounded-full bg-[#1E293B] animate-pulse">
          <Users className="h-6 w-6 text-[#7C3AED]" />
        </div>
        <h3 className="text-lg font-medium text-white mt-4">Loading Access Control</h3>
        <p className="text-sm text-[#94A3B8] max-w-sm mt-2">
          Fetching access control details...
        </p>
      </div>
    );
  }

  const hasNoAccessControl = 
    (!teammate.allowed_groups || teammate.allowed_groups.length === 0) &&
    (!teammate.allowed_users || teammate.allowed_users.length === 0);

  if (hasNoAccessControl) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-6">
        <div className="p-3 rounded-full bg-[#7C3AED]/10 mb-4">
          <Users className="h-6 w-6 text-[#7C3AED]" />
        </div>
        <h3 className="text-lg font-medium text-white mb-2">No Access Control</h3>
        <p className="text-sm text-[#94A3B8] max-w-sm">
          This teammate doesn't have any access control configured yet.
        </p>
      </div>
    );
  }

  return (
    <ScrollArea className="h-full">
      <div className="space-y-8 p-6">
        {/* Allowed Groups */}
        {groupsMetadata.length > 0 && (
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">Allowed Groups</h3>
              <Badge variant="secondary" className="bg-[#1E293B] text-[#94A3B8] border-[#1E293B]">
                {groupsMetadata.length} {groupsMetadata.length === 1 ? 'Group' : 'Groups'}
              </Badge>
            </div>
            <div className="grid gap-4">
              {groupsMetadata.map((group) => (
                <div key={group.id} className="p-6 rounded-lg bg-[#1E293B] border border-[#1E293B] hover:border-[#7C3AED]/20 transition-all duration-200">
                  <div className="flex items-start gap-4">
                    <div className="p-2.5 rounded-md bg-[#7C3AED]/10">
                      <Users className="h-5 w-5 text-[#7C3AED]" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-white">{group.name || 'Unknown Group'}</p>
                      {group.description && (
                        <p className="text-xs text-[#94A3B8] mt-1">{group.description}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Allowed Users */}
        {usersMetadata.length > 0 && (
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">Allowed Users</h3>
              <Badge variant="secondary" className="bg-[#1E293B] text-[#94A3B8] border-[#1E293B]">
                {usersMetadata.length} {usersMetadata.length === 1 ? 'User' : 'Users'}
              </Badge>
            </div>
            <div className="grid gap-4">
              {usersMetadata.map((user) => (
                <div key={user.id} className="p-6 rounded-lg bg-[#1E293B] border border-[#1E293B] hover:border-[#7C3AED]/20 transition-all duration-200">
                  <div className="flex items-start gap-4">
                    <div className="p-2.5 rounded-md bg-[#7C3AED]/10">
                      {user.image ? (
                        <img src={user.image} alt={user.name} className="h-5 w-5 rounded-full" />
                      ) : (
                        <User className="h-5 w-5 text-[#7C3AED]" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-white">{user.name || 'Unknown User'}</p>
                      {user.status && (
                        <Badge 
                          variant="secondary" 
                          className={`mt-2 ${
                            user.status === 'active' 
                              ? 'bg-green-500/10 text-green-400 border-green-500/20'
                              : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
                          }`}
                        >
                          {user.status}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </ScrollArea>
  );
} 