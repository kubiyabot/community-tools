import { getSession } from '@auth0/nextjs-auth0/edge';
import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    // Create a new response to pass to getSession
    const res = new NextResponse();
    
    // Get the session with both request and response
    const session = await getSession(req, res);
    
    if (!session?.user) {
      // Create a new response with the error
      const errorResponse = NextResponse.json({ 
        isAuthenticated: false,
        error: 'Not authenticated'
      }, { status: 401 });

      // Copy all headers from the session response
      res.headers.forEach((value, key) => {
        errorResponse.headers.set(key, value);
      });

      return errorResponse;
    }

    // Create a new response with the session data
    const successResponse = NextResponse.json({
      isAuthenticated: true,
      user: session.user
    });

    // Copy all headers from the session response
    res.headers.forEach((value, key) => {
      successResponse.headers.set(key, value);
    });

    return successResponse;

  } catch (error) {
    console.error('Auth error:', error);
    return NextResponse.json({ 
      isAuthenticated: false,
      error: 'Failed to get session'
    }, { status: 401 });
  }
} 