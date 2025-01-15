import { handleAuth, handleCallback } from '@auth0/nextjs-auth0/edge';
import { NextRequest } from 'next/server';
import type { Session } from '@auth0/nextjs-auth0';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

const baseUrl = process.env.AUTH0_BASE_URL || 'http://localhost:3000';

const handler = handleAuth({
  callback: handleCallback({
    afterCallback: async (req: NextRequest, session: Session) => {
      console.log('Auth0 callback - Session created:', {
        hasSession: true,
        hasUser: !!session.user,
        hasAccessToken: !!session.accessToken,
        userEmail: session.user?.email,
        sub: session.user?.sub,
        provider: session.user?.sub?.split('|')[0],
        org: session.user?.org_id,
        orgName: session.user?.org_name
      });

      // Enhance the session with organization info if available
      if (session.user) {
        session.user.org_id = session.user.org_id || 'org_Tsc8lhUZFWGPCymz';
        session.user.org_name = session.user.org_name || 'kubiya';
      }

      return session;
    },
    redirectUri: `${baseUrl}/api/auth/callback`
  })
});

export async function GET(req: NextRequest) {
  try {
    console.log('Callback route - Processing request:', {
      url: req.url,
      method: req.method,
      cookies: {
        appSession: req.cookies.has('appSession') ? 'present' : 'missing',
        'auth0.is.authenticated': req.cookies.has('auth0.is.authenticated') ? 'present' : 'missing',
        state: req.cookies.get('auth0_state')?.value
      }
    });

    // Create a context object with the callback route params
    const ctx = { params: { auth0: ['callback'] } };

    const response = await handler(req, ctx);

    console.log('Callback route - Response:', {
      status: response.status,
      hasCookieHeader: response.headers.has('set-cookie'),
      location: response.headers.get('location'),
      headers: Object.fromEntries(response.headers.entries())
    });

    // Ensure cookies are set with the correct attributes
    if (response.headers.has('set-cookie')) {
      const cookies = response.headers.getAll('set-cookie');
      const newHeaders = new Headers(response.headers);
      newHeaders.delete('set-cookie');

      cookies.forEach((cookie: string) => {
        // Parse the cookie to get its name, value, and existing attributes
        const [nameValue, ...attributes] = cookie.split(';').map(part => part.trim());
        
        // Keep existing attributes that we want to preserve
        const preservedAttributes = attributes.filter(attr => 
          !attr.toLowerCase().startsWith('domain=') && 
          !attr.toLowerCase().startsWith('samesite=')
        );

        // Add our required attributes
        const requiredAttributes = [
          'Path=/',
          'HttpOnly',
          'Secure',
          'SameSite=Lax'
        ];

        // Combine everything
        const newCookie = [
          nameValue,
          ...preservedAttributes,
          ...requiredAttributes
        ].join('; ');

        newHeaders.append('Set-Cookie', newCookie);
      });
      
      // Ensure we redirect to the root path
      newHeaders.set('Location', '/');
      
      return new Response(null, {
        status: 302,
        headers: newHeaders
      });
    }

    return response;
  } catch (error) {
    console.error('Callback error:', {
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined,
      url: req.url,
      headers: Object.fromEntries(req.headers.entries()),
      cookies: Object.fromEntries(req.cookies),
      state: req.cookies.get('auth0_state')?.value
    });
    return Response.json(
      { error: 'Authentication failed', description: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
} 