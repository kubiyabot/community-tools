import { initAuth0 } from '@auth0/nextjs-auth0';

const baseUrl = process.env.AUTH0_BASE_URL || 'http://localhost:3000';

export const auth0 = initAuth0({
  baseURL: baseUrl,
  issuerBaseURL: process.env.AUTH0_ISSUER_BASE_URL!,
  clientID: process.env.AUTH0_CLIENT_ID!,
  clientSecret: process.env.AUTH0_CLIENT_SECRET!,
  secret: process.env.AUTH0_SECRET!,
  routes: {
    callback: '/api/auth/callback',
    login: '/api/auth/login',
    postLogoutRedirect: '/'
  },
  authorizationParams: {
    response_type: 'code',
    scope: 'openid profile email offline_access',
    audience: process.env.AUTH0_AUDIENCE || 'https://api.kubiya.ai',
    connection: 'slack',
    redirect_uri: `${baseUrl}/api/auth/callback`
  },
  session: {
    name: 'appSession',
    rolling: true,
    absoluteDuration: 24 * 60 * 60, // 24 hours
    cookie: {
      domain: undefined,
      path: '/',
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax' as const,
      httpOnly: true
    }
  },
  auth0Logout: true,
  clientAuthMethod: 'client_secret_post',
  transactionCookie: {
    name: 'auth_verification',
    domain: undefined,
    path: '/',
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax' as const
  },
  enableTelemetry: false,
  idTokenSigningAlg: 'RS256',
  clockTolerance: 60,
  httpTimeout: 5000
}); 