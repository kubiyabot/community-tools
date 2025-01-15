import { getSession } from '@auth0/nextjs-auth0/edge';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    // Log request details
    const requestHeaders = Object.fromEntries(req.headers.entries());
    console.log('/api/auth/me - Request details:', {
      url: req.url,
      method: req.method,
      headers: {
        ...requestHeaders,
        cookie: requestHeaders.cookie ? 'present' : 'missing' // Don't log actual cookies
      }
    });

    // Create a response object for Auth0's getSession
    const res = NextResponse.next();
    
    // Get Auth0 session with error handling
    let session;
    try {
      session = await getSession(req, res);
      console.log('/api/auth/me - Auth0 session details:', {
        hasSession: !!session,
        hasUser: !!session?.user,
        hasAccessToken: !!session?.accessToken,
        userEmail: session?.user?.email,
        sub: session?.user?.sub,
        provider: session?.user?.sub?.split('|')[0],
        sessionKeys: session ? Object.keys(session) : [],
        userKeys: session?.user ? Object.keys(session.user) : []
      });
    } catch (sessionError) {
      console.error('/api/auth/me - Failed to get Auth0 session:', {
        error: sessionError instanceof Error ? sessionError.message : 'Unknown error',
        stack: sessionError instanceof Error ? sessionError.stack : undefined
      });
      return NextResponse.json({ 
        isAuthenticated: false,
        error: 'Failed to get Auth0 session',
        details: sessionError instanceof Error ? sessionError.message : 'Unknown error'
      }, { 
        status: 401,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store, must-revalidate',
          'Pragma': 'no-cache'
        }
      });
    }

    if (!session?.user) {
      console.log('/api/auth/me - No valid session user');
      return NextResponse.json({ 
        isAuthenticated: false,
        error: 'Not authenticated',
        details: 'No user in session'
      }, { 
        status: 401,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store, must-revalidate',
          'Pragma': 'no-cache'
        }
      });
    }

    if (!session.accessToken) {
      console.log('/api/auth/me - No access token in session');
      return NextResponse.json({ 
        isAuthenticated: false,
        error: 'Not authenticated',
        details: 'No access token in session'
      }, { 
        status: 401,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store, must-revalidate',
          'Pragma': 'no-cache'
        }
      });
    }

    // Return user profile information and access token
    const response = NextResponse.json({
      isAuthenticated: true,
      user: session.user,
      accessToken: session.accessToken
    }, {
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store, must-revalidate',
        'Pragma': 'no-cache'
      }
    });

    // Copy any session headers from Auth0's response
    const authHeaders = Array.from(res.headers.entries());
    console.log('/api/auth/me - Auth0 response headers:', {
      headers: authHeaders.map(([key, value]) => ({
        key,
        value: key.toLowerCase().includes('cookie') ? 'present' : value
      }))
    });

    authHeaders.forEach(([key, value]) => {
      if (key.toLowerCase().startsWith('set-cookie')) {
        response.headers.append(key, value);
      }
    });

    console.log('/api/auth/me - Successfully authenticated user');
    return response;

  } catch (error) {
    console.error('/api/auth/me - Unexpected error:', {
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined
    });
    return NextResponse.json({ 
      isAuthenticated: false,
      error: 'Failed to get session',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { 
      status: 401,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store, must-revalidate',
        'Pragma': 'no-cache'
      }
    });
  }
} 