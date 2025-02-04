import { getSession } from '@auth0/nextjs-auth0/edge';
import { NextRequest, NextResponse } from 'next/server';
import type { Integration } from '@/app/types/integration';
import { revalidateTag } from 'next/cache';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

// CORS headers for preflight requests
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

export async function OPTIONS() {
  return new Response(JSON.stringify({}), { 
    headers: {
      ...corsHeaders,
      'Content-Type': 'application/json'
    }
  });
}

// Add cache tag helpers
const getIntegrationsCacheTag = (teammateId: string) => `teammate-${teammateId}-integrations`;

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await getSession(request, NextResponse.next());
    
    if (!session?.idToken) {
      console.error('Authentication error: No ID token found');
      return NextResponse.json({ 
        error: 'Not authenticated',
        details: 'No ID token found in session'
      }, { status: 401 });
    }

    // Log the incoming request
    console.log('Integrations endpoint - Request details:', {
      teammateId: params.id,
      hasToken: !!session.idToken,
      orgId: session.user?.org_id
    });

    // Use internal teammate route to get teammate details with caching
    const teammateResponse = await fetch(`${request.nextUrl.origin}/api/teammates/${params.id}`, {
      headers: {
        'Cookie': request.headers.get('cookie') || '',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      next: {
        tags: [getIntegrationsCacheTag(params.id)],
        // Cache for 5 minutes
        revalidate: 300
      }
    });

    if (!teammateResponse.ok) {
      console.error('Failed to fetch teammate:', {
        id: params.id,
        status: teammateResponse.status,
        statusText: teammateResponse.statusText
      });
      return NextResponse.json({ 
        error: 'Failed to fetch teammate',
        details: `Teammate not found. Please ensure the teammate exists and you have the correct permissions.`
      }, { status: teammateResponse.status });
    }

    const teammate = await teammateResponse.json();
    const teammateIntegrationNames = (teammate.integrations || [])
      .map((int: any) => typeof int === 'string' ? int : int.name)
      .filter(Boolean);

    console.log('Teammate integrations:', {
      teammateId: params.id,
      integrationNames: teammateIntegrationNames
    });

    // Use internal integrations route to get all integrations with caching
    const integrationsResponse = await fetch(`${request.nextUrl.origin}/api/integrations`, {
      headers: {
        'Cookie': request.headers.get('cookie') || '',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      next: {
        tags: ['integrations'],
        // Cache for 5 minutes
        revalidate: 300
      }
    });

    if (!integrationsResponse.ok) {
      console.error('Failed to fetch integrations:', {
        status: integrationsResponse.status,
        statusText: integrationsResponse.statusText
      });
      return NextResponse.json({ 
        error: 'Failed to fetch integrations',
        details: integrationsResponse.statusText
      }, { status: integrationsResponse.status });
    }

    const allIntegrations = await integrationsResponse.json();
    
    // Filter integrations based on teammate's integration names
    const filteredIntegrations = teammateIntegrationNames.length > 0
      ? allIntegrations.filter((integration: Integration) => 
          teammateIntegrationNames.includes(integration.name))
      : [];

    console.log('Filtered integrations:', {
      total: allIntegrations.length,
      filtered: filteredIntegrations.length
    });

    return NextResponse.json(filteredIntegrations);

  } catch (error: any) {
    console.error('Teammate integrations endpoint error:', error);
    const statusCode = error.status || 500;
    return NextResponse.json(
      { 
        error: 'Failed to fetch teammate integrations',
        details: error.message || 'An unexpected error occurred',
        status: statusCode
      },
      { status: statusCode }
    );
  }
}

// Add method to invalidate integration cache
export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { action } = await request.json();
    
    if (action === 'revalidate') {
      revalidateTag(getIntegrationsCacheTag(params.id));
      return NextResponse.json({ revalidated: true, timestamp: Date.now() });
    }
    
    return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
  } catch (error) {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 });
  }
} 