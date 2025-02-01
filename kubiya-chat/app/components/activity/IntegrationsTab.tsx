import React, { useEffect, useState } from 'react';
import type { TeammateInfo } from '@/app/types/teammate';
import type { Integration } from '@/app/types/integration';

const IntegrationsTab: React.FC = () => {
  const [teammate, setTeammate] = useState<TeammateInfo | null>(null);
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchIntegrationDetails = async () => {
      try {
        if (!teammate?.uuid) {
          console.error('No teammate UUID provided to IntegrationsTab');
          setError('No teammate ID available');
          setIsLoading(false);
          return;
        }

        setIsLoading(true);
        console.log('Fetching integrations for teammate:', {
          uuid: teammate.uuid,
          name: teammate.name
        });
        
        const res = await fetch(`/api/teammates/${teammate.uuid}/integrations`);
        if (!res.ok) {
          const errorData = await res.json().catch(() => null);
          console.error('Failed to fetch integrations:', {
            status: res.status,
            statusText: res.statusText,
            errorData
          });
          throw new Error(errorData?.details || `Failed to fetch integrations: ${res.statusText}`);
        }
        
        const data = await res.json();
        console.log('Received integrations data:', {
          count: data.length,
          integrations: data.map((i: Integration) => ({
            uuid: i.uuid,
            name: i.name,
            type: i.integration_type
          }))
        });
        
        // Filter integrations based on teammate's assigned integrations
        const filteredIntegrations = data.filter((integration: Integration) => {
          // Check if the integration exists in teammate's integrations array
          return teammate.integrations?.some((teamInt: Integration | string) => {
            // Handle both string (uuid) and Integration object cases
            if (typeof teamInt === 'string') {
              return teamInt === integration.uuid;
            }
            return teamInt.uuid === integration.uuid;
          });
        });
        
        setIntegrations(filteredIntegrations);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch integration details:', err);
        setError(err instanceof Error ? err.message : 'Failed to load integration details');
      } finally {
        setIsLoading(false);
      }
    };

    if (teammate?.uuid) {
      fetchIntegrationDetails();
    } else {
      setIsLoading(false);
    }
  }, [teammate?.uuid, teammate?.integrations]); // Added teammate.integrations as dependency

  return (
    <div>
      {/* Render your component content here */}
    </div>
  );
};

export default IntegrationsTab; 