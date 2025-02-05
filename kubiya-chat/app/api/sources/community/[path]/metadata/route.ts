import { NextRequest, NextResponse } from 'next/server';
import { getToolMetadata } from '@/app/api/sources/community/client';

const KUBIYA_API_URL = process.env.KUBIYA_API_URL || 'https://api.kubiya.ai';
const COMMUNITY_TOOLS_BASE = 'https://github.com/kubiyabot/community-tools/tree';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET(
  request: Request,
  { params }: { params: { path: string } }
) {
  try {
    const metadata = await getToolMetadata(params.path);
    return NextResponse.json(metadata);
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch tool metadata' },
      { status: 500 }
    );
  }
} 