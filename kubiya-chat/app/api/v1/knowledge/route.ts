import { NextRequest, NextResponse } from 'next/server';
import { getSessionAndToken, createApiHeaders, createResponseHeaders, handleApiError, createUnauthorizedResponse } from '@/app/lib/api-helpers';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const { session } = await getSessionAndToken(req);
    const url = new URL(req.url);
    const teammateId = url.searchParams.get('teammateId');

    if (!teammateId) {
      return NextResponse.json({ 
        error: 'Bad Request',
        details: 'Teammate ID is required'
      }, { 
        status: 400,
        headers: createResponseHeaders()
      });
    }

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.kubiya.ai';
    const response = await fetch(`${apiUrl}/api/v1/knowledge?owner=${teammateId}`, {
      headers: createApiHeaders(session)
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch knowledge entries: ${response.statusText}`);
    }

    const data = await response.json();
    return NextResponse.json(data, { headers: createResponseHeaders() });
  } catch (error) {
    if (error instanceof Error && error.message === 'Unauthorized') {
      return createUnauthorizedResponse();
    }
    return handleApiError(error, 'Failed to fetch knowledge entries');
  }
} 