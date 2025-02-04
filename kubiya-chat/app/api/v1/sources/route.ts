import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';
import { unstable_cache, revalidateTag } from 'next/cache';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

const DEFAULT_PAGE_SIZE = 10;
const CACHE_TTL = 300; // 5 minutes in seconds
const REVALIDATE_AFTER = 60; // Start revalidating after 1 minute

// Cache key generation helper
const generateCacheKeys = (idToken: string, orgId: string, page: number, pageSize: number) => 
  ['sources', 'list', orgId, `page-${page}`, `size-${pageSize}`];

async function getSourcesFromApi(session: any, page: number, pageSize: number) {
  const apiUrl = new URL('https://api.kubiya.ai/api/v1/sources');
  apiUrl.searchParams.set('page', String(page));
  apiUrl.searchParams.set('page_size', String(pageSize));

  const response = await fetch(apiUrl.toString(), {
    headers: {
      'Authorization': `Bearer ${session.idToken}`,
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache',
      'X-Organization-ID': session.user?.org_id || '',
      'X-Kubiya-Client': 'chat-ui'
    }
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const data = await response.json();
  return {
    data,
    headers: {
      totalCount: response.headers.get('X-Total-Count'),
      hasMore: response.headers.get('X-Has-More')
    }
  };
}

// Cached fetch function using Next.js cache
const getCachedSources = unstable_cache(
  async (idToken: string, orgId: string, page: number, pageSize: number) => {
    const session = { idToken, user: { org_id: orgId } };
    const { data, headers } = await getSourcesFromApi(session, page, pageSize);
    
    return {
      items: Array.isArray(data) ? data : [],
      pagination: {
        page,
        pageSize,
        totalItems: parseInt(headers.totalCount || '0'),
        hasMore: headers.hasMore === 'true'
      }
    };
  },
  // Use a static array for the cache key
  ['sources', 'list'],
  {
    revalidate: REVALIDATE_AFTER,
    tags: ['sources']
  }
);

export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('pageSize') || String(DEFAULT_PAGE_SIZE));
    const skipCache = url.searchParams.get('skipCache') === 'true';

    const res = NextResponse.next();
    const session = await getSession(req, res);

    if (!session?.idToken) {
      return NextResponse.json({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }, { status: 401 });
    }

    // If skipCache is true, add a random query parameter to bypass cache
    const cacheKey = skipCache ? 
      `${Date.now()}-${Math.random()}` : 
      generateCacheKeys(session.idToken, session.user?.org_id || '', page, pageSize);

    const data = await getCachedSources(
      session.idToken,
      session.user?.org_id || '',
      page,
      pageSize
    );

    return NextResponse.json(data, {
      headers: {
        'Cache-Control': `public, max-age=${CACHE_TTL}, stale-while-revalidate=${REVALIDATE_AFTER}`,
        'X-Cache': skipCache ? 'BYPASS' : 'HIT'
      }
    });
  } catch (error) {
    console.error('Error in sources route:', error);
    return NextResponse.json({ 
      error: 'Internal Server Error',
      details: error instanceof Error ? error.message : 'Unknown error',
      errorCode: 'INTERNAL_ERROR',
      technicalDetails: error instanceof Error ? error.stack : undefined
    }, { 
      status: 500,
      headers: {
        'Cache-Control': 'no-store'
      }
    });
  }
}

// Cache invalidation endpoint
export async function DELETE(req: NextRequest) {
  try {
    const res = NextResponse.next();
    const session = await getSession(req, res);

    if (!session?.idToken) {
      return NextResponse.json({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }, { status: 401 });
    }

    // Revalidate the 'sources' tag to invalidate all sources cache
    await revalidateTag('sources');

    return NextResponse.json({ 
      success: true,
      message: 'Cache invalidated successfully'
    });
  } catch (error) {
    console.error('Error invalidating cache:', error);
    return NextResponse.json({ 
      error: 'Failed to invalidate cache',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
} 