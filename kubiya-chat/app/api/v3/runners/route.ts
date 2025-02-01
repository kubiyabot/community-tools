import { NextRequest, NextResponse } from 'next/server';
import { getSessionAndToken, createApiHeaders, createResponseHeaders, handleApiError, createUnauthorizedResponse } from '@/app/lib/api-helpers';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const { session, idToken } = await getSessionAndToken(req);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.kubiya.ai';
    
    const response = await fetch(`${apiUrl}/api/v3/runners`, {
      headers: createApiHeaders(session)
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch runners: ${response.statusText}`);
    }

    const data = await response.json();
    return NextResponse.json(data, { headers: createResponseHeaders() });
  } catch (error) {
    if (error instanceof Error && error.message === 'Unauthorized') {
      return createUnauthorizedResponse();
    }
    return handleApiError(error, 'Failed to fetch runners');
  }
} 