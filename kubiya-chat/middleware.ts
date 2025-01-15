import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - api/auth/callback (auth callback)
     */
    '/((?!_next/static|_next/image|favicon.ico|api/auth/callback).*)',
  ],
};

export async function middleware(req: NextRequest) {
  try {
    console.log('Middleware - Request details:', {
      path: req.nextUrl.pathname,
      hasAuthHeader: req.headers.has('authorization'),
      cookies: {
        appSession: req.cookies.has('appSession') ? 'present' : 'missing',
        'auth0.is.authenticated': req.cookies.has('auth0.is.authenticated') ? 'present' : 'missing'
      },
      method: req.method
    });

    // Clone the request headers and add the client IP
    const requestHeaders = new Headers(req.headers);
    const forwardedFor = req.headers.get('x-forwarded-for');
    requestHeaders.set('x-forwarded-for', forwardedFor || '127.0.0.1');

    // Create a new response with the modified headers
    const response = NextResponse.next({
      request: {
        headers: requestHeaders,
      },
    });

    return response;
  } catch (error) {
    console.error('Middleware error:', error);
    return NextResponse.next();
  }
} 