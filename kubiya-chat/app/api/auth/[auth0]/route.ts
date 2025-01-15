import { NextRequest } from 'next/server';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET(
  req: NextRequest,
  context: { params: Promise<{ auth0: string }> }
) {
  try {
    const params = await context.params;
    const { auth0 } = params;
    
    if (!auth0) {
      return new Response('Missing auth0 parameter', { status: 400 });
    }

    const url = new URL(req.url);
    const returnTo = url.searchParams.get('returnTo') || '/';
    const baseUrl = process.env.AUTH0_BASE_URL || url.origin;
    const connection = url.searchParams.get('connection');

    if (auth0 === 'login') {
      // If no connection parameter, show the login page instead of redirecting
      if (!connection) {
        return new Response(null, {
          status: 200,
          headers: {
            'Content-Type': 'text/html',
            'Cache-Control': 'no-store, must-revalidate',
            'Pragma': 'no-cache'
          }
        });
      }

      const auth0Domain = process.env.AUTH0_ISSUER_BASE_URL;
      const clientId = process.env.AUTH0_CLIENT_ID;
      const redirectUri = `${baseUrl}/api/auth/callback`;
      const scope = 'openid profile email offline_access';
      
      const params = new URLSearchParams({
        response_type: 'code',
        client_id: clientId!,
        redirect_uri: redirectUri,
        connection,
        scope,
        state: Buffer.from(JSON.stringify({ returnTo })).toString('base64'),
      });

      const authUrl = `${auth0Domain}/authorize?${params.toString()}`;
      console.log('Auth URL:', authUrl);

      return new Response(null, {
        status: 302,
        headers: {
          Location: authUrl,
          'Cache-Control': 'no-store, must-revalidate',
          'Pragma': 'no-cache'
        }
      });
    }

    if (auth0 === 'logout') {
      const auth0Domain = process.env.AUTH0_ISSUER_BASE_URL;
      const returnToUrl = `${baseUrl}${returnTo}`;
      const logoutUrl = `${auth0Domain}/v2/logout?returnTo=${encodeURIComponent(returnToUrl)}`;

      return new Response(null, {
        status: 302,
        headers: {
          Location: logoutUrl,
          'Set-Cookie': 'appSession=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0',
          'Cache-Control': 'no-store, must-revalidate',
          'Pragma': 'no-cache'
        }
      });
    }

    return new Response('Invalid auth endpoint', { status: 400 });
  } catch (error) {
    console.error('Auth error:', error);
    return new Response(JSON.stringify({ 
      error: 'Authentication failed', 
      description: error instanceof Error ? error.message : 'Unknown error' 
    }), { 
      status: 500,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }
}

export async function POST() {
  return new Response('Method not allowed', { status: 405 });
} 