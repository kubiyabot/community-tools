import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

export async function middleware(request: NextRequest) {
  // Skip auth check for auth-related routes and public assets
  if (
    request.nextUrl.pathname.startsWith('/api/auth') ||
    request.nextUrl.pathname.startsWith('/_next') ||
    request.nextUrl.pathname.startsWith('/images')
  ) {
    return NextResponse.next();
  }

  const res = NextResponse.next();
  const session = await getSession(request, res);

  // If no session and not on login page, redirect to login
  if (!session?.user && !request.nextUrl.pathname.startsWith('/login')) {
    const loginUrl = new URL('/api/auth/login', request.url);
    loginUrl.searchParams.set('returnTo', request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  return res;
}

export const config = {
  matcher: ['/((?!_next/static|favicon.ico).*)'],
}; 