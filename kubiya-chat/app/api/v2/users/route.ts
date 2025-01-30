import { NextRequest, NextResponse } from 'next/server';
import { getSessionAndToken, createApiHeaders, createResponseHeaders, handleApiError, createUnauthorizedResponse } from '@/app/lib/api-helpers';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const { session, idToken } = await getSessionAndToken(req);
    const { searchParams } = new URL(req.url);
    const limit = searchParams.get('limit') || '100';
    const page = searchParams.get('page') || '1';

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.kubiya.ai';
    const response = await fetch(`${apiUrl}/api/v2/users?limit=${limit}&page=${page}`, {
      headers: createApiHeaders(session)
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch users: ${response.statusText}`);
    }

    const data = await response.json();
    return NextResponse.json(data, { headers: createResponseHeaders() });
  } catch (error) {
    if (error instanceof Error && error.message === 'Unauthorized') {
      return createUnauthorizedResponse();
    }
    return handleApiError(error, 'Failed to fetch users');
  }
} 