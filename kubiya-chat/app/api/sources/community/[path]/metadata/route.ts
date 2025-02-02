import { NextRequest, NextResponse } from 'next/server';
import { CommunityToolsClient } from '../../client';

const KUBIYA_API_URL = process.env.KUBIYA_API_URL || 'https://api.kubiya.ai';
const COMMUNITY_TOOLS_BASE = 'https://github.com/kubiyabot/community-tools/tree';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET(
  req: NextRequest,
  { params }: { params: { path: string } }
) {
  try {
    const client = CommunityToolsClient.getInstance();
    const data = await client.getToolMetadata(params.path);
    
    return NextResponse.json({
      tools: Array.isArray(data.tools) ? data.tools : 
             Array.isArray(data) ? data : 
             [],
      source: {
        url: `https://github.com/kubiyabot/community-tools/tree/main/${params.path}`,
        runner: 'kubiya-hosted'
      }
    });
  } catch (error) {
    console.error('Error fetching tool metadata:', error);
    return NextResponse.json({ 
      error: 'Failed to fetch tool metadata',
      details: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString()
    }, { status: 500 });
  }
} 