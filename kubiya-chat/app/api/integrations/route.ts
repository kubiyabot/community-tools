import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';
import type { Integration, IntegrationType } from '@/app/types/integration';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

// Integration metadata for rich UI display
const INTEGRATION_METADATA = {
  aws: {
    name: 'AWS',
    description: 'Amazon Web Services integration for cloud resource management',
    icon: 'https://uxwing.com/wp-content/themes/uxwing/download/brands-and-social-media/aws-icon.png',
    capabilities: ['IAM', 'EC2', 'S3', 'Lambda', 'CloudFormation'],
    configFields: ['region', 'arn', 'account_id', 'role_name']
  },
  github: {
    name: 'GitHub',
    description: 'GitHub integration for repository and workflow management',
    icon: 'https://cdn-icons-png.flaticon.com/512/25/25231.png',
    capabilities: ['Repositories', 'Pull Requests', 'Actions', 'Issues'],
    configFields: ['repository', 'branch', 'webhook_url', 'secret_name']
  },
  gitlab: {
    name: 'GitLab',
    description: 'GitLab integration for repository and CI/CD management',
    icon: 'https://about.gitlab.com/images/press/logo/png/gitlab-icon-rgb.png',
    capabilities: ['Repositories', 'Merge Requests', 'CI/CD', 'Issues'],
    configFields: ['project_id', 'branch', 'webhook_url']
  },
  kubernetes: {
    name: 'Kubernetes',
    description: 'Kubernetes integration for container orchestration',
    icon: 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Kubernetes_logo_without_workmark.svg/2109px-Kubernetes_logo_without_workmark.svg.png',
    capabilities: ['Deployments', 'Services', 'Pods', 'ConfigMaps'],
    configFields: ['cluster', 'namespace', 'service_account']
  },
  slack: {
    name: 'Slack',
    description: 'Slack integration for team communication',
    icon: 'https://cdn4.iconfinder.com/data/icons/logos-and-brands/512/306_Slack_logo-512.png',
    capabilities: ['Messages', 'Channels', 'Users', 'Files'],
    configFields: ['workspace', 'channel', 'bot_token']
  },
  jira: {
    name: 'Jira',
    description: 'Jira integration for project and issue tracking',
    icon: 'https://cdn-icons-png.flaticon.com/512/5968/5968875.png',
    capabilities: ['Issues', 'Projects', 'Sprints', 'Boards'],
    configFields: ['site', 'project_key', 'board_id']
  }
};

function enrichIntegrationData(integration: any): Integration {
  const type = integration.type?.toLowerCase() as IntegrationType || 'custom';
  const metadata = INTEGRATION_METADATA[type as keyof typeof INTEGRATION_METADATA] || {
    name: integration.name || 'Custom Integration',
    description: 'Custom integration',
    icon: null,
    capabilities: [],
    configFields: []
  };

  return {
    name: integration.name || metadata.name,
    integration_type: type,
    auth_type: integration.auth_type || 'global',
    description: integration.description || metadata.description,
    managed_by: integration.managed_by || 'system',
    configs: (integration.configs || []).map((config: any) => ({
      name: config.name || 'Default Config',
      is_default: config.is_default || false,
      vendor_specific: {
        ...config.vendor_specific,
        capabilities: metadata.capabilities,
        supported_fields: metadata.configFields
      }
    })),
    kubiya_metadata: {
      created_at: integration.created_at || new Date().toISOString(),
      last_updated: integration.updated_at || new Date().toISOString(),
      user_created: integration.user_created,
      user_last_updated: integration.user_last_updated,
      icon_url: metadata.icon,
      capabilities: metadata.capabilities,
      config_fields: metadata.configFields
    }
  };
}

export async function GET(req: NextRequest) {
  try {
    const res = NextResponse.next();
    const session = await getSession(req, res);

    if (!session?.idToken) {
      return NextResponse.json({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }, { status: 401 });
    }

    // Use v2 endpoint with full details
    const response = await fetch('https://api.kubiya.ai/api/v2/integrations?full=true', {
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch integrations: ${response.statusText}`);
    }

    const data = await response.json();
    
    // Enrich the integration data with metadata
    const enrichedData = Array.isArray(data) 
      ? data.map(enrichIntegrationData)
      : [];

    return NextResponse.json(enrichedData);
  } catch (error) {
    console.error('Integrations endpoint error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch integrations' },
      { status: 500 }
    );
  }
}

export async function GET_v2() {
  try {
    const response = await fetch('https://api.kubiya.ai/api/v2/integrations?full=true', {
      headers: {
        'Authorization': `Bearer ${process.env.KUBIYA_API_KEY}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch integrations: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching integrations:', error);
    return NextResponse.json(
      { error: 'Failed to fetch integrations' },
      { status: 500 }
    );
  }
} 