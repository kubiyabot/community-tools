import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET(
  req: NextRequest,
  context: { params: Promise<{ sourceId: string }> }
) {
  try {
    // Get session first
    const res = NextResponse.next();
    const session = await getSession(req, res);

    if (!session?.idToken) {
      return NextResponse.json({ 
        error: 'Not authenticated',
        details: 'No ID token found',
        errorCode: 'AUTH_REQUIRED',
        displayMessage: 'Authentication required to access source details'
      }, { status: 401 });
    }

    // Get sourceId from params - await it properly
    const { sourceId } = await context.params;
    if (!sourceId) {
      return NextResponse.json({ 
        error: 'Bad Request', 
        details: 'Source ID is required',
        errorCode: 'MISSING_SOURCE_ID',
        displayMessage: 'Source identifier is missing'
      }, { status: 400 });
    }

    // Fetch both the source data and the full sources list
    const [sourceData, allSourcesResponse] = await Promise.all([
      // Original source data fetch
      fetch(`https://api.kubiya.ai/api/v1/sources/${sourceId}`, {
        headers: {
          'Authorization': `Bearer ${session.idToken}`
        }
      }),
      // Additional sources metadata fetch
      fetch('https://api.kubiya.ai/api/v1/sources', {
        headers: {
          'Authorization': `Bearer ${session.idToken}`
        }
      })
    ]);

    if (!sourceData.ok) {
      return NextResponse.json({
        error: 'Source Data Fetch Failed',
        details: 'Unable to fetch source data',
        errorCode: 'SOURCE_DATA_ERROR',
        displayMessage: 'Unable to load source details',
      }, { status: sourceData.status });
    }

    if (!allSourcesResponse.ok) {
      console.error('Error fetching all sources:', await allSourcesResponse.text());
      return NextResponse.json({
        error: 'Internal Server Error',
        details: 'Failed to fetch additional source metadata',
        errorCode: 'METADATA_FETCH_ERROR',
        displayMessage: 'Unable to retrieve complete source information'
      }, { status: 500 });
    }

    const baseSourceData = await sourceData.json();
    const allSources = await allSourcesResponse.json();

    // Find matching source metadata
    const additionalMetadata = allSources.find((source: any) => source.uuid === sourceId);
    
    // Merge the data
    const enrichedSourceData = {
      ...baseSourceData,
      dynamic_config: additionalMetadata?.dynamic_config || null,
      runner: additionalMetadata?.runner || '',
      connected_agents_count: additionalMetadata?.connected_agents_count || 0,
      connected_tools_count: additionalMetadata?.connected_tools_count || 0,
      connected_workflows_count: additionalMetadata?.connected_workflows_count || 0,
      source_meta: additionalMetadata?.source_meta || {},
      errors_count: additionalMetadata?.errors_count || 0
    };

    // Return the enriched source data
    return NextResponse.json(enrichedSourceData, {
      headers: {
        'Cache-Control': 'no-store'
      }
    });

  } catch (error) {
    console.error('Error in source details route:', error);
    return NextResponse.json({ 
      error: 'Internal Server Error',
      details: error instanceof Error ? error.message : 'Unknown error',
      errorCode: 'INTERNAL_ERROR',
      displayMessage: 'An unexpected error occurred while fetching source details',
      technicalDetails: error instanceof Error ? {
        message: error.message,
        stack: error.stack
      } : undefined
    }, { 
      status: 500,
      headers: {
        'Cache-Control': 'no-store'
      }
    });
  }
} 