import type { CommunityTool } from '@/app/types/tools';

export const createSourceInfo = (tool: CommunityTool, tools: any[]) => {
  return {
    name: tool.name,
    path: tool.path,
    description: tool.description || '',
    tools_count: tools.length,
    tools: tools,
    icon: tool.icon,
    readme: tool.readme,
    isDiscovering: false,
    loadingState: 'success' as const
  };
}; 