import { getSession } from '@auth0/nextjs-auth0/edge';
import { NextRequest, NextResponse } from 'next/server';
import { revalidateTag } from 'next/cache';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

// Add cache tag helper
const getTeammateCacheTag = (id: string) => `teammate-${id}`;

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await getSession(request, NextResponse.next());
    
    if (!session?.idToken) {
      console.error('Teammate endpoint - No ID token found');
      return NextResponse.json({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }, { status: 401 });
    }

    // Fetch teammate details from Kubiya API with caching
    const response = await fetch(`https://api.kubiya.ai/api/v1/agents/${params.id}`, {
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      },
      next: {
        tags: [getTeammateCacheTag(params.id)],
        // Cache for 5 minutes
        revalidate: 300
      }
    });

    if (!response.ok) {
      console.error('Teammate endpoint - Failed to fetch teammate:', {
        id: params.id,
        status: response.status,
        statusText: response.statusText
      });

      let errorMessage = 'Failed to fetch teammate';
      try {
        const errorData = await response.json();
        errorMessage = errorData.response?.message || errorData.error || response.statusText;
      } catch (e) {
        // If we can't parse the error response, use the status text
        errorMessage = response.statusText;
      }

      return NextResponse.json({ 
        error: 'Teammate not found',
        details: errorMessage
      }, { status: response.status });
    }

    const teammate = await response.json();
    
    // Log successful fetch
    console.log('Teammate endpoint - Successfully fetched teammate:', {
      id: params.id,
      name: teammate.name,
      hasIntegrations: Array.isArray(teammate.integrations),
      integrationsCount: teammate.integrations?.length || 0
    });

    return NextResponse.json(teammate);

  } catch (error: any) {
    console.error('Teammate endpoint error:', error);
    return NextResponse.json(
      { 
        error: 'Failed to fetch teammate',
        details: error.message || 'An unexpected error occurred'
      },
      { status: 500 }
    );
  }
}

// Add PATCH method for updating teammate and invalidating cache
export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await getSession(request, NextResponse.next());
    if (!session?.idToken) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    
    const response = await fetch(`https://api.kubiya.ai/api/v1/agents/${params.id}`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to update teammate' },
        { status: response.status }
      );
    }

    // Invalidate both teammate-specific and global teammates cache
    revalidateTag(getTeammateCacheTag(params.id));
    revalidateTag('teammates');

    return NextResponse.json(await response.json());
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to update teammate' },
      { status: 500 }
    );
  }
} 