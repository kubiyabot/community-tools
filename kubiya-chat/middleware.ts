import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

// Define public paths that don't require authentication
const PUBLIC_PATHS = [
  '/api/auth',
  '/_next',
  '/images',
  '/favicon.ico',
  '/', // Landing page
  '/login',
  '/auth/session-expired'
];

export async function middleware(request: NextRequest) {
  // Skip auth check for public routes
  if (PUBLIC_PATHS.some(path => request.nextUrl.pathname.startsWith(path))) {
    return NextResponse.next();
  }

  const res = NextResponse.next();
  
  // Add security headers
  res.headers.set('X-Frame-Options', 'DENY');
  res.headers.set('X-Content-Type-Options', 'nosniff');
  res.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  res.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
  
  try {
    const session = await getSession(request, res);

    // If no session and not on public pages, redirect appropriately
    if (!session?.user) {
      // Check if session existed before but now expired
      const hadPreviousSession = request.cookies.get('appSession');
      if (hadPreviousSession) {
        return NextResponse.redirect(new URL('/auth/session-expired', request.url));
      }
      
      // No previous session, redirect to landing page
      return NextResponse.redirect(new URL('/', request.url));
    }

    // If user is authenticated and tries to access the landing page, redirect to chat
    if (session?.user && request.nextUrl.pathname === '/') {
      return NextResponse.redirect(new URL('/chat', request.url));
    }

    return res;
  } catch (error) {
    // On session validation error, redirect to session expired
    console.error('Session validation error:', error);
    return NextResponse.redirect(new URL('/auth/session-expired', request.url));
  }
}

export const config = {
  matcher: ['/((?!_next/static|favicon.ico).*)'],
}; 