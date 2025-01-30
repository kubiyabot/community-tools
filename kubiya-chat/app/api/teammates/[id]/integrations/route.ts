import { getSession } from '@auth0/nextjs-auth0/edge';
import { NextRequest, NextResponse } from 'next/server';
import type { Integration } from '@/app/types/integration';

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

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await getSession(request, NextResponse.next());
    console.log('Session check:', {
      hasSession: !!session,
      hasIdToken: !!session?.idToken,
      hasUser: !!session?.user,
      orgId: session?.user?.org_id
    });

    if (!session?.idToken) {
      console.error('Authentication error: No ID token found');
      return NextResponse.json({ 
        error: 'Not authenticated',
        details: 'No ID token found in session'
      }, { status: 401 });
    }

    if (!params.id) {
      console.error('Invalid request: No teammate ID provided');
      return NextResponse.json({ 
        error: 'Invalid request',
        details: 'No teammate ID provided'
      }, { status: 400 });
    }

    console.log('Fetching integrations for teammate:', params.id);

    // First, fetch teammate details
    const teammateResponse = await fetch(`https://api.kubiya.ai/api/v1/agents/${params.id}`, {
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      }
    });

    if (!teammateResponse.ok) {
      const errorText = await teammateResponse.text().catch(() => 'Unknown error');
      console.error('Failed to fetch teammate details:', {
        status: teammateResponse.status,
        statusText: teammateResponse.statusText,
        teammateId: params.id,
        error: errorText
      });
      return NextResponse.json({ 
        error: 'Failed to fetch teammate details',
        details: errorText,
        status: teammateResponse.status
      }, { status: teammateResponse.status });
    }

    const teammateData = await teammateResponse.json();
    console.log('Teammate data received:', {
      id: params.id,
      hasIntegrations: !!teammateData.integrations,
      integrationsCount: teammateData.integrations?.length,
      hasCapabilities: !!teammateData.capabilities,
      capabilitiesIntegrations: teammateData.capabilities?.integrations?.length
    });

    // Get integrations from teammate data
    let teammateIntegrationNames: string[] = [];
    
    if (Array.isArray(teammateData.integrations)) {
      teammateIntegrationNames = teammateData.integrations;
    } else if (Array.isArray(teammateData.capabilities?.integrations)) {
      teammateIntegrationNames = teammateData.capabilities.integrations.map((i: any) => 
        typeof i === 'string' ? i : i.name || i.type
      );
    }

    // Clean up and normalize integration names
    teammateIntegrationNames = teammateIntegrationNames
      .filter(Boolean)
      .map(name => name.toLowerCase());

    console.log('Teammate integration names:', teammateIntegrationNames);

    if (teammateIntegrationNames.length === 0) {
      console.log('No integrations found for teammate');
      return NextResponse.json([]);
    }

    // Fetch all available integrations
    const integrationsResponse = await fetch('https://api.kubiya.ai/api/v2/integrations?full=true', {
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      }
    });

    if (!integrationsResponse.ok) {
      const errorText = await integrationsResponse.text().catch(() => 'Unknown error');
      console.error('Failed to fetch integrations:', {
        status: integrationsResponse.status,
        statusText: integrationsResponse.statusText,
        error: errorText
      });
      return NextResponse.json({ 
        error: 'Failed to fetch integrations',
        details: errorText,
        status: integrationsResponse.status
      }, { status: integrationsResponse.status });
    }

    const allIntegrations = await integrationsResponse.json();
    
    // Filter integrations based on teammate's integration names
    const filteredIntegrations = allIntegrations.filter((integration: Integration) => {
      const integrationName = integration.name?.toLowerCase() || '';
      const integrationType = integration.integration_type?.toLowerCase() || '';
      
      return teammateIntegrationNames.some(name => 
        integrationName.includes(name) || integrationType.includes(name)
      );
    });

    console.log('Filtered integrations:', {
      total: allIntegrations.length,
      filtered: filteredIntegrations.length,
      matches: filteredIntegrations.map((i: Integration) => ({
        name: i.name,
        type: i.integration_type
      }))
    });

    return NextResponse.json(filteredIntegrations);

  } catch (error: any) {
    console.error('Teammate integrations endpoint error:', error);
    return NextResponse.json(
      { 
        error: 'Failed to fetch teammate integrations',
        details: error.message,
        teammate_id: params.id
      },
      { status: 500 }
    );
  }
} 