import { NextRequest, NextResponse } from 'next/server';
import { fetchCommunityTools } from '@/app/api/sources/community/client';

export async function GET() {
  try {
    const tools = await fetchCommunityTools();
    return NextResponse.json(tools);
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch community tools' },
      { status: 500 }
    );
  }
} 