import { handleAuth, handleLogin, handleCallback } from '@auth0/nextjs-auth0/edge';
import { NextRequest, NextResponse } from 'next/server';
import type { Session } from '@auth0/nextjs-auth0';

export const runtime = 'edge';

const baseUrl = process.env.AUTH0_BASE_URL || 'http://localhost:3000';

const baseAuthParams = {
  returnTo: '/',
  audience: process.env.AUTH0_AUDIENCE,
  scope: 'openid profile email offline_access',
  redirect_uri: `${baseUrl}/api/auth/callback`
};

const auth = handleAuth({
  onError: async (req: NextRequest, error: Error) => {
    console.error('Auth0 error:', {
      message: error.message,
      stack: error.stack,
      url: req.url
    });
    return NextResponse.json({ error: error.message }, { status: 500 });
  },
  login: handleLogin({
    authorizationParams: baseAuthParams,
    returnTo: '/'
  }),
  'login-google': handleLogin({
    authorizationParams: {
      ...baseAuthParams,
      connection: 'google-oauth2'
    },
    returnTo: '/'
  }),
  callback: handleCallback({
    afterCallback: async (req: NextRequest, session: Session) => {
      const res = new NextResponse();
      
      // Set required cookies
      if (session) {
        res.cookies.set('appSession', session.user.sub, {
          httpOnly: true,
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'lax',
          path: '/'
        });
      }
      
      return session;
    }
  })
});

export async function GET(req: NextRequest, context: { params: Promise<{ auth0: string[] }> }) {
  try {
    const params = await context.params;
    const url = new URL(req.url);
    const connection = url.searchParams.get('connection');

    // If this is a login request with a connection parameter
    if (params.auth0[0] === 'auth0' && params.auth0[1] === 'login' && connection === 'google-oauth2') {
      const res = await auth(req, { params: { auth0: ['login-google'] } });
      return new Response(res.body, {
        status: res.status,
        statusText: res.statusText,
        headers: new Headers(res.headers)
      });
    }

    const res = await auth(req, { params });
    return new Response(res.body, {
      status: res.status,
      statusText: res.statusText,
      headers: new Headers(res.headers)
    });
  } catch (error) {
    console.error('Auth error:', error);
    return NextResponse.json({ error: 'Authentication failed' }, { status: 500 });
  }
}

export async function POST(req: NextRequest, context: { params: Promise<{ auth0: string[] }> }) {
  return GET(req, context);
} 