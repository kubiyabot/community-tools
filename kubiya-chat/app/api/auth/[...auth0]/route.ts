import { handleAuth, handleLogin, handleCallback } from '@auth0/nextjs-auth0/edge';
import { NextRequest, NextResponse } from 'next/server';
import type { Session } from '@auth0/nextjs-auth0';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

const baseUrl = process.env.AUTH0_BASE_URL || 'http://localhost:3000';

// Create handlers for each provider
const baseAuthParams = {
  returnTo: '/',
  audience: process.env.AUTH0_AUDIENCE,
  scope: 'openid profile email offline_access',
  redirect_uri: `${baseUrl}/api/auth/callback`
};

// Create the base handler with all routes
const handler = handleAuth({
  onError: (req: NextRequest, error: Error) => {
    console.error('Auth0 error:', {
      message: error.message,
      stack: error.stack,
      url: req.url,
      searchParams: new URL(req.url).searchParams.toString(),
      cookies: req.cookies.getAll().map(c => ({ name: c.name, value: c.value }))
    });

    return NextResponse.json({ error: error.message }, { status: 500 });
  },
  callback: handleCallback({
    afterCallback: async (req: NextRequest, session: Session) => {
      console.log('Auth0 callback - Session created:', {
        hasSession: true,
        hasUser: !!session.user,
        hasAccessToken: !!session.accessToken,
        userEmail: session.user?.email,
        sub: session.user?.sub,
        provider: session.user?.sub?.split('|')[0]
      });

      return session;
    }
  }),
  login: handleLogin({
    authorizationParams: {
      ...baseAuthParams,
      connection: 'google-oauth2'
    },
    returnTo: '/',
    getLoginState: () => ({ returnTo: '/' })
  }),
  'login-google': handleLogin({
    authorizationParams: {
      ...baseAuthParams,
      connection: 'google-oauth2'
    },
    returnTo: '/',
    getLoginState: () => ({ returnTo: '/' })
  }),
  'login-slack': handleLogin({
    authorizationParams: {
      ...baseAuthParams,
      connection: 'slack'
    },
    returnTo: '/',
    getLoginState: () => ({ returnTo: '/' })
  })
});

export async function GET(req: NextRequest, context: { params: Promise<{ auth0: string[] }> }) {
  try {
    const params = await context.params;
    const url = new URL(req.url);
    const path = params.auth0.join('/');
    const connection = url.searchParams.get('connection');
    const isCallback = path === 'callback';
    const host = req.headers.get('host') || 'localhost:3000';

    console.log(`Auth route - Processing ${isCallback ? 'callback' : 'login'} request:`, {
      url: req.url,
      method: req.method,
      params,
      cookies: {
        appSession: req.cookies.has('appSession') ? 'present' : 'missing',
        'auth0.is.authenticated': req.cookies.has('auth0.is.authenticated') ? 'present' : 'missing',
        auth_verification: req.cookies.has('auth_verification') ? 'present' : 'missing',
        state: req.cookies.get('auth0_state')?.value
      }
    });

    // Create a new context object with non-promise params
    const ctx = { params: { auth0: params.auth0 } };

    // If this is a login request with a connection, use the appropriate handler
    if (path === 'auth0/login' && connection) {
      const response = connection === 'google-oauth2'
        ? await handler(req, { ...ctx, params: { auth0: ['login-google'] } })
        : await handler(req, { ...ctx, params: { auth0: ['login-slack'] } });

      // Ensure cookies are set with the correct attributes for development
      if (response.headers.has('set-cookie')) {
        const cookies = response.headers.getAll('set-cookie');
        const newHeaders = new Headers(response.headers);
        newHeaders.delete('set-cookie');

        cookies.forEach((cookie: string) => {
          // Parse the cookie to get its name and value
          const [nameValue, ...attributes] = cookie.split(';').map(part => part.trim());
          const [name] = nameValue.split('=');

          // Set required attributes for development
          const requiredAttributes = [
            'Path=/',
            'SameSite=Lax',
            process.env.NODE_ENV === 'production' ? 'Secure' : '',
            name === 'appSession' || name === 'auth_verification' ? 'HttpOnly' : ''
          ].filter(Boolean);

          // Combine everything
          const newCookie = [nameValue, ...requiredAttributes].join('; ');
          newHeaders.append('set-cookie', newCookie);
        });

        console.log('Auth0 login - Setting cookies:', {
          cookies: cookies.map((cookie: string) => {
            const [name] = cookie.split('=');
            return { name, attributes: cookie.split(';').slice(1).map((attr: string) => attr.trim()) };
          })
        });

        return new Response(response.body, {
          status: response.status,
          headers: newHeaders
        });
      }

      return response;
    }

    const response = await handler(req, ctx);

    // Also ensure cookies are set correctly for non-login routes
    if (response.headers.has('set-cookie')) {
      const cookies = response.headers.getAll('set-cookie');
      const newHeaders = new Headers(response.headers);
      newHeaders.delete('set-cookie');

      cookies.forEach((cookie: string) => {
        const [nameValue, ...attributes] = cookie.split(';').map(part => part.trim());
        const [name] = nameValue.split('=');

        const requiredAttributes = [
          'Path=/',
          'SameSite=Lax',
          process.env.NODE_ENV === 'production' ? 'Secure' : '',
          name === 'appSession' || name === 'auth_verification' ? 'HttpOnly' : ''
        ].filter(Boolean);

        const newCookie = [nameValue, ...requiredAttributes].join('; ');
        newHeaders.append('set-cookie', newCookie);
      });

      return new Response(response.body, {
        status: response.status,
        headers: newHeaders
      });
    }

    return response;
  } catch (error) {
    console.error('Auth error:', {
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined,
      url: req.url,
      headers: Object.fromEntries(req.headers.entries()),
      cookies: Object.fromEntries(req.cookies)
    });
    return NextResponse.json(
      { error: 'Authentication failed', description: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function POST(req: NextRequest, context: { params: Promise<{ auth0: string[] }> }) {
  return GET(req, context);
} 