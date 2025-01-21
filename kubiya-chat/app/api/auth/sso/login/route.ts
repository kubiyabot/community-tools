import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Redirect to the SSO provider's login page
    return NextResponse.redirect(process.env.SSO_LOGIN_URL || 'https://auth.kubiya.ai/login');
  } catch (error) {
    console.error('SSO login error:', error);
    return NextResponse.json({ error: 'Failed to initiate SSO login' }, { status: 500 });
  }
} 