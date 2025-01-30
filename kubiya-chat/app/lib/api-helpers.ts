import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

export async function getSessionAndToken(req: NextRequest) {
  const res = new NextResponse();
  const session = await getSession(req, res);
  const idToken = session?.idToken;

  if (!idToken) {
    throw new Error('Unauthorized');
  }

  return { session, idToken };
}

export function createApiHeaders(session: any) {
  return {
    'Accept': 'application/json',
    'Authorization': `Bearer ${session.idToken}`,
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'X-Organization-ID': session.user?.org_id || '',
    'X-Kubiya-Client': 'chat-ui'
  };
}

export function createResponseHeaders() {
  const headers = new Headers();
  headers.set('Cache-Control', 'no-store, must-revalidate');
  headers.set('Pragma', 'no-cache');
  return headers;
}

export function handleApiError(error: any, customMessage?: string) {
  console.error('API error:', error);
  return new NextResponse(
    JSON.stringify({ error: customMessage || 'Internal server error' }), 
    { 
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store, must-revalidate',
        'Pragma': 'no-cache'
      }
    }
  );
}

export function createUnauthorizedResponse(message = 'Unauthorized') {
  return new NextResponse(
    JSON.stringify({ error: message }), 
    { 
      status: 401,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store, must-revalidate',
        'Pragma': 'no-cache'
      }
    }
  );
} 