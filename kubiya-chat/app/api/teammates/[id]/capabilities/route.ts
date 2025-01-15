import { NextResponse } from 'next/server';
import { getKubiyaConfig } from '@/lib/config';

// CORS headers for preflight requests
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

export async function OPTIONS() {
  return NextResponse.json({}, { headers: corsHeaders });
}

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    // Await params.id before using it
    const teammateId = await params.id;
    const config = getKubiyaConfig();
    const authHeader = request.headers.get('Authorization');

    if (!authHeader) {
      return NextResponse.json(
        { error: 'Not authenticated' },
        { status: 401, headers: corsHeaders }
      );
    }

    // Use the awaited teammateId
    const teammateResponse = await fetch(`https://api.kubiya.ai/api/v1/agents/${teammateId}`, {
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    if (!teammateResponse.ok) {
      console.error('Failed to fetch teammate details:', {
        status: teammateResponse.status,
        statusText: teammateResponse.statusText,
      });
      const errorData = await teammateResponse.json().catch(() => ({ message: teammateResponse.statusText }));
      throw new Error(errorData.message || `Failed to fetch teammate details: ${teammateResponse.status}`);
    }

    const teammateData = await teammateResponse.json();
    const sourceIds = teammateData.sources || [];

    // Fetch capabilities from each source
    const capabilities = [];
    for (const sourceId of sourceIds) {
      // First get source metadata
      const metadataResponse = await fetch(`https://api.kubiya.ai/api/v1/sources/${sourceId}/metadata`, {
        headers: {
          'Authorization': authHeader,
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      });

      if (metadataResponse.ok) {
        const metadata = await metadataResponse.json();
        const tools = metadata.tools || [];
        
        // Transform tools into capabilities
        const sourceCapabilities = tools.map((tool: any) => ({
          name: tool.name,
          description: tool.description || 'No description available',
          source: sourceId,
          schema: tool.schema || {},
          parameters: tool.args || [],
          type: tool.type || 'unknown',
          icon_url: tool.icon_url,
          mermaid: tool.mermaid,
          content: tool.content,
          with_files: tool.with_files,
          with_volumes: tool.with_volumes,
          env: tool.env,
          metadata: tool.metadata || {}
        }));

        capabilities.push(...sourceCapabilities);
      }
    }

    return NextResponse.json(capabilities, { headers: corsHeaders });
  } catch (error) {
    console.error('Error fetching teammate capabilities:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to fetch teammate capabilities' },
      { status: 500, headers: corsHeaders }
    );
  }
} 