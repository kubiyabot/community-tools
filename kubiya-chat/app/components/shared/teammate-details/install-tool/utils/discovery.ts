import type { CommunityTool } from '@/app/types/tools';

export const discoverTools = async (tool: CommunityTool) => {
  const sourceUrl = `https://github.com/kubiyabot/community-tools/tree/main/${tool.path}`;
  const response = await fetch(
    `/api/v1/sources/load?url=${encodeURIComponent(sourceUrl)}&runner=kubiya-hosted`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dynamic_config: {} })
    }
  );

  if (!response.ok) {
    throw new Error('Failed to discover tools');
  }

  return response.json();
}; 