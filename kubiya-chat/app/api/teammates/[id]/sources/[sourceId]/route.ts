import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string; sourceId: string } }
) {
  try {
    const res = NextResponse.next();
    const session = await getSession(req, res);
    
    // Await the params to fix the NextJS dynamic route issue
    const sourceId = await params.sourceId;
    
    if (!session?.idToken) {
      console.error('Source metadata endpoint - No ID token found');
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

    if (!sourceId) {
      console.error('Source metadata endpoint - No source ID provided');
      return new Response(JSON.stringify({ 
        error: 'Bad Request',
        details: 'Source ID is required'
      }), { 
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    // Log request details
    console.log('Source metadata endpoint - Request details:', {
      sourceId,
      hasToken: !!session.idToken,
      orgId: session.user?.org_id
    });

    // Fetch metadata directly from the sources API
    const metadataResponse = await fetch(`https://api.kubiya.ai/api/v1/sources/${sourceId}/metadata`, {
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      },
    });

    if (!metadataResponse.ok) {
      console.error('Source metadata endpoint - Failed to fetch metadata:', {
        status: metadataResponse.status,
        statusText: metadataResponse.statusText,
        url: metadataResponse.url
      });
      throw new Error(`Failed to fetch source metadata: ${await metadataResponse.text()}`);
    }

    const metadata = await metadataResponse.json();

    // Log success
    console.log('Source metadata endpoint - Successfully fetched metadata:', {
      sourceId,
      toolsCount: metadata.tools?.length || 0
    });

    // Ensure we have a valid tools array and metadata object
    const response = {
      sourceId,
      metadata: {
        tools: Array.isArray(metadata.tools) ? metadata.tools : [],
        ...(metadata.metadata || {})
      }
    };

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });
  } catch (error) {
    console.error('Source metadata endpoint error:', {
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined,
      params: await params
    });
    return new Response(JSON.stringify({ 
      error: 'Failed to fetch source metadata',
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