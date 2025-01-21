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
      const returnTo = url.searchParams.get('returnTo') || '/chat';
      return { 
        returnTo,
        organization: org
      };
    },
    authorizationParams: {
      response_type: 'code',
      scope: 'openid profile email read:organizations',
      audience: 'https://api.kubiya.ai'
    }
  }),
  callback: handleCallback({
    afterCallback: async (req: NextRequest, session: Session) => {
      const url = new URL(req.url);
      const org = url.searchParams.get('organization') || session.user?.org_id;
      const state = url.searchParams.get('state');
      let returnTo = '/chat';

      try {
        if (state) {
          const decodedState = JSON.parse(Buffer.from(state, 'base64').toString());
          returnTo = decodedState.returnTo || '/chat';
        }
      } catch (e) {
        console.warn('Failed to parse state:', e);
      }
      
      console.log('After callback:', {
        hasAccessToken: !!session?.accessToken,
        hasUser: !!session?.user,
        returnTo,
        organization: org
      });

      // Check if user has organization membership
      if (!org && !session.user?.org_id) {
        throw new Error('User does not belong to any organization');
      }

      if (org && session.user) {
        session.user.org_id = org;
        session.accessTokenExtraParameters = {
          ...session.accessTokenExtraParameters,
          org_id: org
        };
      }

      if (!session.user?.email) {
        console.error('Missing required email claim');
        throw new Error('Missing required email claim');
      }

      // Update the returnTo in the session
      session.returnTo = returnTo;
      
      return session;
    }
  })
});

export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    console.log('Auth request:', {
      pathname: url.pathname,
      params: Object.fromEntries(url.searchParams),
      baseUrl
    });

    // Extract route parameters
    const path = url.pathname.split('/').filter(Boolean);
    const authIndex = path.indexOf('auth');
    const params = path.slice(authIndex + 1);

    // Handle direct auth0 login redirects
    if (params.includes('auth0') && params.includes('login')) {
      const returnTo = url.searchParams.get('returnTo') || '/chat';
      const loginUrl = new URL(`${baseUrl}/api/auth/login`);
      loginUrl.searchParams.set('returnTo', returnTo);
      
      // Copy any additional parameters
      url.searchParams.forEach((value, key) => {
        if (key !== 'returnTo') {
          loginUrl.searchParams.set(key, value);
        }
      });

      return new Response(null, {
        status: 307,
        headers: { Location: loginUrl.toString() }
      });
    }

    // Prevent callback reuse
    if (params.includes('callback')) {
      const code = url.searchParams.get('code');
      if (!code) {
        return new Response('Missing authorization code', { status: 400 });
      }
    }

    const response = await auth0Handler(req, { 
      params: { auth0: params }
    });

    // Handle auth errors by redirecting to login
    if (response.status >= 400) {
      return new Response(null, {
        status: 307,
        headers: { Location: '/api/auth/login' }
      });
    }

    return response;
  } catch (error) {
    console.error('Auth error:', error);
    // Redirect to login on error
    return new Response(null, {
      status: 307,
      headers: { Location: '/api/auth/login' }
    });
  }
} 