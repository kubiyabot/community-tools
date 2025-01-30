import type { TeammateDetails, Tool } from '@/app/types/teammate';

const BASE_URL = '/api/teammates';

interface TeammateResponse {
  teammate: TeammateDetails;
  capabilities: {
    tools: Tool[];
    integrations: any[];
    sources: any[];
  };
}

export const TeammateAPI = {
  // Get all teammates with their basic info
  async list(): Promise<TeammateDetails[]> {
    const res = await fetch(`${BASE_URL}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    if (!res.ok) throw new Error('Failed to fetch teammates');
    return res.json();
  },

  // Get detailed info for a specific teammate including capabilities
  async getDetails(teammateId: string): Promise<TeammateResponse> {
    const [teammateRes, capabilitiesRes] = await Promise.all([
      fetch(`${BASE_URL}/${teammateId}`),
      fetch(`${BASE_URL}/${teammateId}/capabilities`)
    ]);

    if (!teammateRes.ok || !capabilitiesRes.ok) {
      throw new Error('Failed to fetch teammate details');
    }

    const [teammate, capabilities] = await Promise.all([
      teammateRes.json(),
      capabilitiesRes.json()
    ]);

    return {
      teammate,
      capabilities
    };
  },

  // Get tool details for a specific teammate
  async getToolDetails(teammateId: string, toolId: string): Promise<Tool> {
    const res = await fetch(`${BASE_URL}/${teammateId}/tools/${toolId}`);
    if (!res.ok) throw new Error('Failed to fetch tool details');
    return res.json();
  },

  // Get all tools for a teammate
  async getTools(teammateId: string): Promise<Tool[]> {
    const res = await fetch(`${BASE_URL}/${teammateId}/tools`);
    if (!res.ok) throw new Error('Failed to fetch tools');
    return res.json();
  }
}; 