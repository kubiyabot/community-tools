import { handleAuth, handleLogout } from '@auth0/nextjs-auth0/edge';
import { NextRequest } from 'next/server';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

const baseUrl = process.env.AUTH0_BASE_URL || 'http://localhost:3000';

const auth0Handler = handleAuth({
  logout: handleLogout({
    logoutParams: {
      returnTo: baseUrl
    }
  })
});

export async function GET(req: NextRequest) {
  try {
    console.log('Logout request received');
    
    // Extract route parameters for the handler
    const url = new URL(req.url);
    const path = url.pathname.split('/').filter(Boolean);
    const authIndex = path.indexOf('auth');
    const params = path.slice(authIndex + 1);

    // Clear cookies in the response
    const response = await auth0Handler(req, { 
      params: { auth0: params }
    });

    // Add cookie clearing headers
    const headers = new Headers(response.headers);
    headers.append('Set-Cookie', 'appSession=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT');
    headers.append('Set-Cookie', 'auth0.is.authenticated=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT');

    return new Response(response.body, {
      status: response.status,
      headers
    });
  } catch (error) {
    console.error('Logout error:', error);
    // Always redirect to home on error
    return new Response(null, {
      status: 307,
      headers: { 'Location': baseUrl }
    });
  }
} 