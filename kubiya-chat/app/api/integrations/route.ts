import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const res = NextResponse.next();
    const session = await getSession(req, res);

    if (!session?.idToken) {
      return NextResponse.json({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }, { 
        status: 401,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    // Fetch integrations from the Kubiya API
    const baseUrl = process.env.NEXT_PUBLIC_KUBIYA_API_URL || 'https://api.kubiya.ai/api/v1';
    const response = await fetch(`${baseUrl}/integrations`, {
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

    if (!response.ok) {
      throw new Error(`Failed to fetch integrations: ${response.statusText}`);
    }

    const data = await response.json();

    // Format the response to match the expected structure
    const formattedData = {
      tools: data.tools || {},
      integrations: data.integrations || [],
      metadata: data.metadata || {}
    };

    return NextResponse.json(formattedData, {
      headers: {
        'Cache-Control': 'no-store'
      }
    });
  } catch (error) {
    console.error('Integrations endpoint error:', error);
    return NextResponse.json(
      { 
        error: 'Failed to fetch integrations',
        details: error instanceof Error ? error.message : 'Unknown error'
      }, 
      { 
        status: 500,
        headers: {
          'Cache-Control': 'no-store'
        }
      }
    );
  }
} 