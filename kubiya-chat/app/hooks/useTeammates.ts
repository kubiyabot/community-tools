import { useState, useEffect } from 'react';
import { generateAvatarUrl } from '@/app/components/TeammateSelector';
import type { TeammateDetails } from '@/app/types/teammate';
import { TeammateAPI } from '@/app/api/teammates/client';

export function useTeammates() {
  const [teammates, setTeammates] = useState<TeammateDetails[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detailsCache, setDetailsCache] = useState<Record<string, TeammateDetails>>({});

  useEffect(() => {
    async function fetchTeammates() {
      try {
        const data = await TeammateAPI.list();
        
        // Transform and add avatars
        const transformedTeammates = data.map(teammate => ({
          ...teammate,
          avatar_url: generateAvatarUrl({ uuid: teammate.uuid, name: teammate.name })
        }));

        setTeammates(transformedTeammates);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch teammates');
      } finally {
        setLoading(false);
      }
    }

    fetchTeammates();
  }, []);

  // Function to fetch teammate details (with caching)
  const getTeammateDetails = async (teammateId: string) => {
    if (detailsCache[teammateId]) {
      return detailsCache[teammateId];
    }

    try {
      const { teammate, capabilities } = await TeammateAPI.getDetails(teammateId);
      const detailedTeammate = {
        ...teammate,
        ...capabilities,
        avatar_url: generateAvatarUrl({ uuid: teammate.uuid, name: teammate.name })
      };

      setDetailsCache(prev => ({
        ...prev,
        [teammateId]: detailedTeammate
      }));

      return detailedTeammate;
    } catch (error) {
      console.error('Error fetching teammate details:', error);
      throw error;
    }
  };

  // Function to get tool details
  const getToolDetails = async (teammateId: string, toolId: string) => {
    return TeammateAPI.getToolDetails(teammateId, toolId);
  };

  return { 
    teammates, 
    loading, 
    error,
    getTeammateDetails,
    getToolDetails,
    detailsCache
  };
} 