import { useState, useEffect } from 'react';

interface Teammate {
  id: string;
  name: string;
  description: string;
  llmModel?: string;
  instructionType?: string;
}

export function useTeammates() {
  const [teammates, setTeammates] = useState<Teammate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchTeammates() {
      try {
        const response = await fetch('/api/teammates', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('kubiya_api_key')}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch teammates');
        }

        const data = await response.json();
        
        // Transform the API response to match our Teammate interface
        const transformedTeammates: Teammate[] = data.map((teammate: any) => ({
          id: teammate.uuid,
          name: teammate.name,
          description: teammate.description || '',
          llmModel: teammate.llm_model,
          instructionType: teammate.instruction_type,
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

  return { teammates, loading, error };
} 