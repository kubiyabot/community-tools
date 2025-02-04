import { NextRequest, NextResponse } from 'next/server';
import { getToolMetadata } from '@/app/api/sources/community/client';

const KUBIYA_API_URL = process.env.KUBIYA_API_URL || 'https://api.kubiya.ai';
const COMMUNITY_TOOLS_BASE = 'https://github.com/kubiyabot/community-tools/tree';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string } }
) {
  try {
    if (!params.path) {
      return NextResponse.json({ error: 'Path is required' }, { status: 400 });
    }

    const metadata = await getToolMetadata(params.path, request);
    return NextResponse.json(metadata);
  } catch (error) {
    console.error('Error getting tool metadata:', error);
    return NextResponse.json({ error: 'Failed to get tool metadata' }, { status: 500 });
  }
} 