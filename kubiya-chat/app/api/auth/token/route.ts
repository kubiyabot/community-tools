import { getSession } from '@auth0/nextjs-auth0';
import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';

export async function GET(req: NextRequest) {
  try {
    const session = await getSession(req, new NextResponse());
    if (!session?.accessToken) {
      return NextResponse.json({ error: 'No access token found' }, { status: 401 });
    }
    return NextResponse.json({ 
      accessToken: session.accessToken,
      tokenType: 'Bearer'
    });
  } catch (error) {
    console.error('Token error:', error);
    return NextResponse.json({ error: 'Failed to get token' }, { status: 500 });
  }
} 