import { NextRequest } from 'next/server';
import { CommunityToolsClient } from '../client';

export async function GET(req: NextRequest) {
  try {
    const client = CommunityToolsClient.getInstance(req);
    const tools = await client.listTools();
    return new Response(JSON.stringify(tools), {
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });
  } catch (error) {
    console.error('Error listing community tools:', error);
    return new Response(
      JSON.stringify({ 
        error: error instanceof Error ? error.message : 'Failed to list community tools' 
      }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      }
    );
  }
} 