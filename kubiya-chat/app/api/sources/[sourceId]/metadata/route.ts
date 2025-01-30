import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET(
  req: NextRequest,
  { params }: { params: { sourceId: string } }
) {
  try {
    const res = NextResponse.next();
    const session = await getSession(req, res);
    
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

    // Log request details
    console.log('Source metadata endpoint - Request details:', {
      sourceId: params.sourceId,
      hasToken: !!session.idToken,
      orgId: session.user?.org_id
    });

    // Fetch source metadata from the API
    const metadataResponse = await fetch(
      `https://api.kubiya.ai/api/v1/sources/${params.sourceId}/metadata`,
      {
        headers: {
          'Authorization': `Bearer ${session.idToken}`,
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache',
          'X-Organization-ID': session.user?.org_id || '',
          'X-Kubiya-Client': 'chat-ui'
        },
      }
    );

    if (!metadataResponse.ok) {
      console.error('Source metadata endpoint - Failed to fetch metadata:', {
        sourceId: params.sourceId,
        status: metadataResponse.status,
        statusText: metadataResponse.statusText
      });
      throw new Error(`Failed to fetch source metadata: ${await metadataResponse.text()}`);
    }

    const metadata = await metadataResponse.json();

    // Log success
    console.log('Source metadata endpoint - Successfully fetched metadata:', {
      sourceId: params.sourceId,
      toolsCount: metadata.tools?.length || 0
    });

    return new Response(JSON.stringify(metadata), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });
  } catch (error) {
    console.error('Source metadata endpoint error:', {
      sourceId: params.sourceId,
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined
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