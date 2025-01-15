import { handleAuth, handleLogin, handleCallback } from '@auth0/nextjs-auth0/edge';
import { NextRequest, NextResponse } from 'next/server';
import { Session } from '@auth0/nextjs-auth0';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

// Create handlers for each provider
const baseAuthParams = {
  returnTo: process.env.AUTH0_BASE_URL,
  audience: process.env.AUTH0_AUDIENCE,
  scope: 'openid profile email offline_access',
};

// Create the base handler with all routes
const handler = handleAuth({
  login: handleLogin({
    authorizationParams: baseAuthParams,
  }),
  'login-google': handleLogin({
    authorizationParams: {
      ...baseAuthParams,
      connection: 'google-oauth2',
    },
  }),
  'login-github': handleLogin({
    authorizationParams: {
      ...baseAuthParams,
      connection: 'con_c8y49WGUJKZaC3Cl',
    },
  }),
  'login-slack': handleLogin({
    authorizationParams: {
      ...baseAuthParams,
      connection: 'con_Jjk4VpMPaZUo9hpO',
    },
  }),
  callback: handleCallback({
    afterCallback: async (req: NextRequest, session: Session) => {
      console.log('Auth0 callback - Session created:', {
        hasSession: true,
        hasUser: !!session.user,
        hasAccessToken: !!session.accessToken,
        userEmail: session.user?.email,
        sub: session.user?.sub
      });
      return session;
    },
    redirectUri: process.env.AUTH0_BASE_URL + '/api/auth/callback'
  })
});

export async function GET(req: NextRequest, context: { params: { auth0: string[] } }) {
  try {
    console.log('Auth route - Processing request:', {
      url: req.url,
      method: req.method,
      params: context.params,
      cookies: {
        appSession: req.cookies.has('appSession') ? 'present' : 'missing',
        'auth0.is.authenticated': req.cookies.has('auth0.is.authenticated') ? 'present' : 'missing'
      }
    });

    const response = await handler(req, context);

    console.log('Auth route - Response:', {
      status: response.status,
      hasCookieHeader: response.headers.has('set-cookie'),
      location: response.headers.get('location')
    });

    return response;
  } catch (error) {
    console.error('Auth error:', {
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined
    });
    return NextResponse.json(
      { error: 'Authentication failed', description: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function POST(req: NextRequest, context: { params: { auth0: string[] } }) {
  return GET(req, context);
} 