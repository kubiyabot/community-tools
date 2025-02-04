import { getSession } from '@auth0/nextjs-auth0/edge';
import { NextRequest, NextResponse } from 'next/server';
import { revalidatePath, revalidateTag } from 'next/cache';

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

interface TeammateResponse {
  sources?: string[];
}

export async function GET(request: NextRequest, context: { params: { id: string } }) {
  try {
    // Get the session using Auth0's Edge API with both request and response
    const response = NextResponse.next();
    const session = await getSession(request, response);
    
    // Await the params to fix the NextJS dynamic route issue
    const teammateId = await context.params.id;
    
    // Add the tag for this specific teammate's sources
    const tag = `teammate-${teammateId}-sources`;
    
    if (!session?.idToken) {
      console.error('Sources endpoint - No ID token found');
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { 
          ...corsHeaders,
          'Content-Type': 'application/json' 
        },
      });
    }

    // Log request details
    console.log('Sources endpoint - Request details:', {
      teammateId,
      hasToken: !!session.idToken,
      orgId: session.user?.org_id
    });

    // Try both teammate ID formats
    const attempts = [teammateId];

    console.log('Attempting teammate lookup with ID:', teammateId);

    let teammate = null;
    let lastError = null;

    try {
      const teammateResponse = await fetch(`https://api.kubiya.ai/api/v1/agents/${teammateId}`, {
        headers: {
          'Authorization': `Bearer ${session.idToken}`,
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache',
          'X-Organization-ID': session.user?.org_id || '',
          'X-Kubiya-Client': 'chat-ui'
        }
      });

      const responseText = await teammateResponse.text();
      let responseData;
      try {
        responseData = JSON.parse(responseText);
      } catch {
        responseData = { error: responseText };
      }

      if (teammateResponse.ok) {
        teammate = responseData;
        // Log the teammate data to help with debugging
        console.log('Teammate found:', {
          id: teammate.id,
          uuid: teammate.uuid,
          name: teammate.name
        });
      } else {
        lastError = {
          status: teammateResponse.status,
          error: responseData.error || responseData.message || 'Unknown error',
          id: teammateId,
          response: responseText
        };
        console.error(`Teammate lookup failed for ID ${teammateId}:`, {
          status: teammateResponse.status,
          error: responseData,
          response: responseText
        });
      }
    } catch (error) {
      console.error(`Failed attempt with ID ${teammateId}:`, error);
      lastError = {
        error: error instanceof Error ? error.message : 'Unknown error',
        id: teammateId
      };
    }

    if (!teammate) {
      console.error('Teammate lookup failed:', {
        id: teammateId,
        lastError
      });
      return new Response(JSON.stringify({
        error: 'Not Found',
        details: 'Teammate not found',
        id: teammateId,
        last_error: lastError
      }), { status: 404 });
    }

    const sourceIds = teammate.sources || [];

    if (sourceIds.length === 0) {
      console.log('Sources endpoint - No sources found for teammate:', teammateId);
      const emptyResponse = new Response(JSON.stringify([]), {
        status: 200,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });

      // Copy any session cookies
      response.headers.forEach((value, key) => {
        if (key.toLowerCase() === 'set-cookie') {
          emptyResponse.headers.append(key, value);
        }
      });

      return emptyResponse;
    }

    // Log success with source IDs
    console.log('Sources endpoint - Successfully fetched sources:', {
      count: sourceIds.length,
      sourceIds
    });

    // Fetch metadata for each source
    const sourcesWithMetadata = await Promise.all(sourceIds.map(async (sourceId: string) => {
      try {
        const metadataResponse = await fetch(`https://api.kubiya.ai/api/v1/sources/${sourceId}/metadata`, {
          headers: {
            'Authorization': `Bearer ${session.idToken}`,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'X-Organization-ID': session.user?.org_id || '',
            'X-Kubiya-Client': 'chat-ui'
          }
        });

        if (!metadataResponse.ok) {
          console.error(`Failed to fetch metadata for source ${sourceId}:`, await metadataResponse.text());
          return null;
        }

        const metadata = await metadataResponse.json();
        return {
          uuid: sourceId,
          name: metadata.name || `Source ${sourceId.slice(0, 8)}`,
          url: metadata.url || '',
          connected_agents_count: metadata.connected_agents_count || 0,
          connected_tools_count: metadata.tools?.length || 0,
          connected_workflows_count: metadata.connected_workflows_count || 0,
          errors_count: metadata.errors?.length || 0,
          kubiya_metadata: {
            created_at: metadata.kubiya_metadata?.created_at || new Date().toISOString(),
            last_updated: metadata.kubiya_metadata?.last_updated || new Date().toISOString()
          },
          source_meta: {
            id: metadata.source_meta?.id || sourceId,
            url: metadata.source_meta?.url || '',
            branch: metadata.source_meta?.branch || 'main',
            commit: metadata.source_meta?.commit || '',
            committer: metadata.source_meta?.committer || ''
          },
          tools: metadata.tools?.map((tool: any) => ({
            name: tool.name,
            description: tool.description,
            type: tool.type || 'unknown',
            icon_url: tool.icon_url,
            args: tool.args?.map((arg: any) => ({
              name: arg.name,
              type: arg.type,
              description: arg.description,
              required: arg.required
            })),
            env: tool.env,
            image: tool.image,
            source: tool.source,
            metadata: tool.metadata
          })) || []
        };
      } catch (error) {
        console.error(`Error fetching metadata for source ${sourceId}:`, error);
        return null;
      }
    }));

    // Filter out any failed fetches
    const validSources = sourcesWithMetadata.filter(Boolean);

    // Log the final formatted response
    console.log('Sources endpoint - Returning formatted sources:', {
      count: validSources.length,
      firstSource: validSources[0]
    });

    // Create response with session cookies
    const responseWithSources = new Response(JSON.stringify(validSources), {
      status: 200,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });

    // Copy any session cookies
    response.headers.forEach((value, key) => {
      if (key.toLowerCase() === 'set-cookie') {
        responseWithSources.headers.append(key, value);
      }
    });

    return responseWithSources;
  } catch (error) {
    console.error('Sources endpoint error:', {
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined,
      params: await context.params
    });

    return new Response(JSON.stringify({ 
      error: 'Failed to fetch sources',
      details: error instanceof Error ? error.message : 'Unknown error'
    }), { 
      status: 500,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });
  }
}

export async function PUT(request: NextRequest, context: { params: { id: string } }) {
  try {
    // Get the session using Auth0's Edge API
    const response = NextResponse.next();
    const session = await getSession(request, response);
    
    if (!session?.idToken) {
      console.error('Sources update endpoint - No ID token found');
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { 
          ...corsHeaders,
          'Content-Type': 'application/json' 
        },
      });
    }

    const teammateId = await context.params.id;
    const { sources } = await request.json();

    // First, get the current teammate data
    const teammateResponse = await fetch(`https://api.kubiya.ai/api/v1/agents/${teammateId}`, {
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      }
    });

    if (!teammateResponse.ok) {
      console.error('Sources update endpoint - Failed to fetch teammate:', teammateResponse.statusText);
      return new Response(JSON.stringify({ 
        error: 'Failed to fetch teammate',
        details: await teammateResponse.text()
      }), { 
        status: teammateResponse.status,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }

    const teammate = await teammateResponse.json();

    // Update only the sources field while preserving all other fields
    // Omit the id field from the update payload
    const { id, ...teammateWithoutId } = teammate;
    const updatedTeammate = {
      ...teammateWithoutId,
      sources: sources
    };

    // Update the teammate with the new sources
    const updateResponse = await fetch(`https://api.kubiya.ai/api/v1/agents/${teammateId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      },
      body: JSON.stringify(updatedTeammate)
    });

    if (!updateResponse.ok) {
      const errorText = await updateResponse.text();
      console.error('Sources update endpoint - Failed to update teammate:', {
        status: updateResponse.status,
        error: errorText
      });
      return new Response(JSON.stringify({ 
        error: 'Failed to update teammate sources',
        details: errorText
      }), { 
        status: updateResponse.status,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json'
        }
      });
    }

    // Revalidate the cache for this teammate's sources
    revalidateTag(`teammate-${teammateId}-sources`);
    revalidatePath(`/api/teammates/${teammateId}/sources`);

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('Sources update endpoint error:', error);
    return new Response(JSON.stringify({ 
      error: 'Internal server error',
      details: error instanceof Error ? error.message : 'Unknown error'
    }), { 
      status: 500,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json'
      }
    });
  }
} 