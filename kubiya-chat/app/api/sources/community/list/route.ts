import { NextRequest, NextResponse } from 'next/server';
import { listTools } from '@/app/api/sources/community/client';

export async function GET(request: NextRequest) {
  try {
    const tools = await listTools(request);
    return NextResponse.json(tools);
  } catch (error) {
    console.error('Error listing tools:', error);
    return NextResponse.json({ error: 'Failed to list tools' }, { status: 500 });
  }
} 