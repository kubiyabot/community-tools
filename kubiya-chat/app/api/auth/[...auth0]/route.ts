import { handleAuth, handleLogin, handleCallback, Session } from '@auth0/nextjs-auth0/edge';
import { NextRequest } from 'next/server';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

const baseUrl = process.env.AUTH0_BASE_URL || 'http://localhost:3000';

const auth0Handler = handleAuth({
  login: handleLogin({
    returnTo: '/chat',
    getLoginState: (req: NextRequest) => {
      const url = new URL(req.url);
      const org = url.searchParams.get('organization');
      return { 
        returnTo: '/chat',
        organization: org  // This will be passed to the authorization request
      };
    },
    authorizationParams: {
      response_type: 'code',
      scope: 'openid profile email',
      audience: 'https://api.kubiya.ai'
    }
  }),
  callback: handleCallback({
    authorizationParams: {
      scope: 'openid profile email',
      audience: 'https://api.kubiya.ai'
    },
    afterCallback: async (req: NextRequest, session: Session) => {
      // Get the callback URL parameters
      const url = new URL(req.url);
      const org = url.searchParams.get('organization') || session.user?.org_id;
      
      console.log('After callback - Full session details:', {
        hasAccessToken: !!session?.accessToken,
        hasUser: !!session?.user,
        userFields: session?.user ? Object.keys(session.user) : [],
        userEmail: session?.user?.email,
        userSub: session?.user?.sub,
        tokenPrefix: session?.accessToken ? session.accessToken.substring(0, 50) + '...' : null,
        organization: org
      });

      // Add organization to session if present
      if (org && session.user) {
        session.user.org_id = org;
        // Add the organization to the token claims
        session.accessTokenExtraParameters = {
          ...session.accessTokenExtraParameters,
          org_id: org
        };
      }

      // Validate required claims
      if (!session.user?.email) {
        console.error('Missing required email claim');
        throw new Error('Missing required email claim');
      }
      
      return session;
    }
  })
});

export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    console.log('Original URL:', url.pathname);
    console.log('Query params:', Object.fromEntries(url.searchParams));
    console.log('Environment:', {
      baseUrl
    });

    // Extract route parameters
    const path = url.pathname.split('/').filter(Boolean);
    const authIndex = path.indexOf('auth');
    const params = path.slice(authIndex + 1);
    console.log('Auth params:', params);

    // Create the context object with state
    const ctx = { 
      params: { auth0: params },
      state: { returnTo: '/chat' }
    };

    // If this is a login request with a connection, add it to the URL
    if (params.length === 2 && params[0] === 'auth0' && params[1] === 'login') {
      const connection = url.searchParams.get('connection');
      if (connection) {
        const loginUrl = new URL(`${baseUrl}/api/auth/login`);
        loginUrl.searchParams.set('connection', connection);
        return new Response(null, {
          status: 307,
          headers: { Location: loginUrl.toString() }
        });
      }
    }

    return auth0Handler(req, ctx);
  } catch (error) {
    console.error('Auth error:', error);
    return new Response(JSON.stringify({ error: 'Authentication failed', details: error instanceof Error ? error.message : 'Unknown error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
} 