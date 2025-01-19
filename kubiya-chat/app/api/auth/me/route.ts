import { getSession } from '@auth0/nextjs-auth0/edge';
import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const res = new NextResponse();
    const session = await getSession(req, res);

    if (!session?.user) {
      return NextResponse.json({ 
        error: 'Unauthorized',
        message: 'No session found'
      }, { 
        status: 401,
        headers: {
          'Cache-Control': 'no-store, must-revalidate',
          'Pragma': 'no-cache'
        }
      });
    }

    const headers = new Headers(res.headers);
    headers.set('Cache-Control', 'no-store, must-revalidate');
    headers.set('Pragma', 'no-cache');

    return NextResponse.json({
      user: session.user,
      accessToken: session.accessToken
    }, { headers });
  } catch (error) {
    console.error('Profile error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch profile' },
      { 
        status: 500,
        headers: {
          'Cache-Control': 'no-store, must-revalidate',
          'Pragma': 'no-cache'
        }
      }
    );
  }
} 