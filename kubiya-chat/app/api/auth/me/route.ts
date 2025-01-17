import { getSession } from '@auth0/nextjs-auth0';
import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const session = await getSession();
    
    if (!session?.user) {
      return NextResponse.json({ 
        isAuthenticated: false,
        error: 'Not authenticated'
      }, { status: 401 });
    }

    return NextResponse.json({
      isAuthenticated: true,
      user: session.user
    });

  } catch (error) {
    console.error('Auth error:', error);
    return NextResponse.json({ 
      isAuthenticated: false,
      error: 'Failed to get session'
    }, { status: 401 });
  }
} 