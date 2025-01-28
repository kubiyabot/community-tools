import { getSession } from '@auth0/nextjs-auth0/edge';
import { NextRequest, NextResponse } from 'next/server';

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

export async function GET(request: NextRequest, context: { params: { id: string } }) {
  try {
    // Get the session using Auth0's Edge API with both request and response
    const response = NextResponse.next();
    const session = await getSession(request, response);
    
    if (!session?.idToken) {
      console.error('Capabilities endpoint - No ID token found');
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { 
          ...corsHeaders,
          'Content-Type': 'application/json' 
        },
      });
    }

    // Await the params to fix the NextJS dynamic route issue
    const { id: teammateId } = await context.params;
    const baseUrl = process.env.NEXT_PUBLIC_KUBIYA_API_URL || 'https://api.kubiya.ai/api/v1';

    // Fetch teammate details
    const teammateResponse = await fetch(`${baseUrl}/agents/${teammateId}`, {
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
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

    return new Response(JSON.stringify(capabilities), {
      status: 200,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });
  } catch (error) {
    console.error('Capabilities error:', error);
    return new Response(
      JSON.stringify({ error: 'Failed to fetch capabilities' }),
      { 
        status: 500,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      }
    );
  }
} 