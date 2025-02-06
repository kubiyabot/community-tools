import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';
import { headers } from 'next/headers';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

interface SourceMeta {
  id: string;
  url: string;
  commit?: string;
  committer?: string;
  branch?: string;
}

interface KubiyaMetadata {
  created_at: string;
  last_updated: string;
  user_created: string;
  user_last_updated: string;
}

interface SourceResponse {
  url: string;
  uuid: string;
  name: string;
  task_id: string;
  managed_by: string;
  connected_agents_count: number;
  connected_tools_count: number;
  connected_workflows_count: number;
  kubiya_metadata: KubiyaMetadata;
  errors_count: number;
  source_meta: SourceMeta;
  dynamic_config: any;
  runner: string;
  errors?: Array<{
    file: string;
    error: string;
    traceback?: string;
  }>;
}

function formatSourceSummary(source: SourceResponse) {
  return {
    name: source.name,
    summary: {
      agents: source.connected_agents_count,
      tools: source.connected_tools_count,
      workflows: source.connected_workflows_count,
      errors: source.errors_count,
      lastUpdated: source.kubiya_metadata.last_updated,
      branch: source.source_meta.branch || 'main',
      commit: source.source_meta.commit ? source.source_meta.commit.slice(0, 7) : undefined,
    },
    details: {
      url: source.url,
      metadata: source.kubiya_metadata,
      sourceMeta: source.source_meta,
      errors: source.errors || [],
    }
  };
}

export async function POST(
  req: NextRequest,
  { params }: { params: { sourceId: string } }
) {
  try {
    const res = NextResponse.next();
    const session = await getSession(req, res);

    if (!session?.idToken) {
      console.error('Sources sync endpoint - No ID token found');
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const sourceId = params.sourceId;
    const orgId = req.headers.get('x-organization-id');

    // Get request body for dynamic configuration
    let dynamicConfig = null;
    try {
      const body = await req.json();
      dynamicConfig = body?.dynamic_config ?? null;
    } catch (error) {
      // If JSON parsing fails, we'll use null as default
      console.log('Sources sync endpoint - No valid JSON body provided, using null dynamic_config');
    }

    console.log('Sources sync endpoint - Request details:', {
      sourceId,
      hasToken: !!session.idToken,
      orgId,
      dynamicConfig
    });

    const response = await fetch(`https://api.kubiya.ai/api/v1/sources/${sourceId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Content-Type': 'application/json',
        'X-Organization-ID': orgId || '',
        'X-Kubiya-Client': 'chat-ui'
      },
      body: JSON.stringify({ dynamic_config: dynamicConfig })
    });

    const data = await response.json();

    if (!response.ok) {
      console.error('Sources sync endpoint - Failed to sync source:', {
        status: response.status,
        data
      });
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);

  } catch (error) {
    console.error('Sources sync endpoint - Error:', error);
    return NextResponse.json(
      { 
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

export async function PUT(
  req: NextRequest,
  { params }: { params: { sourceId: string } }
) {
  try {
    const res = NextResponse.next();
    const session = await getSession(req, res);
    
    if (!session?.idToken) {
      console.error('Sources update endpoint - No ID token found');
      return new Response(JSON.stringify({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }), { 
        status: 401,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    const { sourceId } = params;
    const body = await req.json();

    // get only the dynamic_config from the body
    const dynamicConfig = body?.dynamic_config || {};

    // Log request details
    console.log('Sources update endpoint - Request details:', {
      sourceId,
      hasConfig: !!dynamicConfig,
      hasToken: !!session.idToken,
      orgId: session.user?.org_id
    });

    const response = await fetch(
      `https://api.kubiya.ai/api/v1/sources/${sourceId}`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${session.idToken}`,
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache',
          'X-Organization-ID': session.user?.org_id || '',
          'X-Kubiya-Client': 'chat-ui'
        },
        body: JSON.stringify({ "dynamic_config": dynamicConfig })
      }
    );

    const data = await response.json();

    if (!response.ok) {
      console.error('Sources update endpoint - Failed to update source:', {
        status: response.status,
        data
      });
      return new Response(JSON.stringify(data), {
        status: response.status,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    // Log success
    console.log('Sources update endpoint - Successfully updated source:', {
      sourceId
    });

    return new Response(JSON.stringify(data), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });
  } catch (error) {
    console.error('Sources update endpoint error:', {
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined
    });
    return new Response(JSON.stringify({ 
      error: 'Failed to update source',
      details: error instanceof Error ? error.message : 'Unknown error'
    }), { 
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });
  }
} 