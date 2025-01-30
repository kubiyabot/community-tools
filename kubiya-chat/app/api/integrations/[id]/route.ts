import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';
import type { Integration } from '@/app/types/integration';

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
  'aws-serviceaccount': {
    name: 'AWS Service Account',
    description: 'AWS Service Account integration for in-cluster access',
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

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const res = NextResponse.next();
    const session = await getSession(request, res);

    if (!session?.idToken) {
      return NextResponse.json({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }, { status: 401 });
    }

    // Fetch all integrations - we already get the full data from this endpoint
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

    const integrations = await response.json();
    
    // Find the specific integration by ID
    const integration = integrations.find((i: Integration) => i.uuid === params.id);
    
    if (!integration) {
      return NextResponse.json(
        { error: 'Integration not found' },
        { status: 404 }
      );
    }

    // Return the integration directly - it already has all the metadata we need
    return NextResponse.json(integration);

  } catch (error) {
    console.error('Integration endpoint error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch integration details' },
      { status: 500 }
    );
  }
} 