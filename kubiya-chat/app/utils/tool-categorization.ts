import type { CommunityTool } from '../components/shared/teammate-details/install-tool/types';

// Tool category matchers
export const toolCategoryMatchers = {
  // Infrastructure Tools
  infrastructure: (tool: CommunityTool) => {
    const keywords = [
      'kubernetes', 'k8s', 'aws', 'azure', 'gcp', 'cloud', 'terraform', 
      'infrastructure', 'docker', 'container', 'cluster', 'deployment',
      'helm', 'pod', 'node', 'service', 'ingress'
    ];
    return hasKeywords(tool, keywords) || 
           tool.tools?.some(t => t.type === 'kubernetes' || t.type === 'infrastructure');
  },

  // Development Tools
  development: (tool: CommunityTool) => {
    const keywords = [
      'git', 'github', 'gitlab', 'bitbucket', 'code', 'development', 
      'build', 'test', 'ci', 'cd', 'pipeline', 'jenkins', 'sonar',
      'artifact', 'repository', 'package', 'dependency'
    ];
    return hasKeywords(tool, keywords) || 
           tool.tools?.some(t => t.type === 'development' || t.type === 'cicd');
  },

  // Security Tools
  security: (tool: CommunityTool) => {
    const keywords = [
      'security', 'auth', 'authentication', 'authorization', 'encryption',
      'secret', 'certificate', 'vault', 'key', 'permission', 'role',
      'policy', 'compliance', 'audit', 'scan'
    ];
    return hasKeywords(tool, keywords) || 
           tool.tools?.some(t => t.type === 'security');
  },

  // Monitoring Tools
  monitoring: (tool: CommunityTool) => {
    const keywords = [
      'monitor', 'metrics', 'logging', 'log', 'alert', 'notification',
      'dashboard', 'grafana', 'prometheus', 'trace', 'apm', 'health',
      'status', 'performance', 'analytics'
    ];
    return hasKeywords(tool, keywords) || 
           tool.tools?.some(t => t.type === 'monitoring');
  },

  // Database Tools
  database: (tool: CommunityTool) => {
    const keywords = [
      'database', 'db', 'sql', 'nosql', 'mysql', 'postgresql', 'mongo',
      'redis', 'cache', 'storage', 'backup', 'restore', 'migration'
    ];
    return hasKeywords(tool, keywords) || 
           tool.tools?.some(t => t.type === 'database');
  },

  // Integration Tools
  integration: (tool: CommunityTool) => {
    const keywords = [
      'integration', 'connect', 'api', 'webhook', 'sync', 'bridge',
      'interface', 'communication', 'messaging', 'queue', 'event'
    ];
    return hasKeywords(tool, keywords) || 
           tool.tools?.some(t => t.type === 'integration');
  }
};

// Helper function to check if tool matches keywords
function hasKeywords(tool: CommunityTool, keywords: string[]): boolean {
  const searchText = [
    tool.name,
    tool.description,
    tool.readme,
    ...(tool.tools?.map(t => [t.name, t.description, t.type].filter(Boolean)) || [])
  ].join(' ').toLowerCase();

  return keywords.some(keyword => searchText.includes(keyword.toLowerCase()));
}

// Function to determine the primary category for a tool
export function determineToolCategory(tool: CommunityTool): string | null {
  for (const [category, matcher] of Object.entries(toolCategoryMatchers)) {
    if (matcher(tool)) {
      return category;
    }
  }
  return null; // Uncategorized
}

// Function to get all matching categories for a tool
export function getToolCategories(tool: CommunityTool): string[] {
  return Object.entries(toolCategoryMatchers)
    .filter(([_, matcher]) => matcher(tool))
    .map(([category]) => category);
} 