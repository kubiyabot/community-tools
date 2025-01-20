import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

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
  req: NextRequest,
  context: { params: { id: string } }
) {
  try {
    const res = new NextResponse();
    const session = await getSession(req, res);

    if (!session?.idToken) {
      return NextResponse.json({ 
        error: 'Unauthorized',
        message: 'No session found'
      }, { 
        status: 401,
        headers: {
          ...corsHeaders,
          'Cache-Control': 'no-store'
        }
      });
    }

    const teammateId = context.params.id;
    const baseUrl = process.env.NEXT_PUBLIC_KUBIYA_API_URL || 'https://api.kubiya.ai/api/v1';

    // Fetch teammate details
    const teammateResponse = await fetch(`${baseUrl}/agents/${teammateId}`, {
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      cache: 'no-store'
    });

    if (!teammateResponse.ok) {
      throw new Error(`Failed to fetch teammate: ${teammateResponse.statusText}`);
    }

    const teammate = await teammateResponse.json();

    // Extract and format capabilities
    const capabilities = {
      tools: teammate.tools || [],
      integrations: teammate.integrations || [],
      starters: teammate.starters || [],
      instruction_type: teammate.instruction_type,
      llm_model: teammate.llm_model,
      description: teammate.description
    };

    return NextResponse.json(capabilities, {
      headers: {
        ...corsHeaders,
        'Cache-Control': 'no-store'
      }
    });
  } catch (error) {
    console.error('Capabilities error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch capabilities' },
      { 
        status: 500,
        headers: {
          ...corsHeaders,
          'Cache-Control': 'no-store'
        }
      }
    );
  }
} 