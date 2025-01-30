import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

const DEFAULT_PAGE_SIZE = 10;

export async function GET(req: NextRequest) {
  try {
    // Parse pagination parameters from URL
    const url = new URL(req.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const pageSize = parseInt(url.searchParams.get('pageSize') || String(DEFAULT_PAGE_SIZE));

    const res = NextResponse.next();
    const session = await getSession(req, res);

    if (!session?.idToken) {
      return NextResponse.json({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }, { status: 401 });
    }

    // Add pagination parameters to the API request
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
      let errorData;
      try {
        errorData = await response.json();
        console.error('Sources endpoint - Full error response:', {
          status: response.status,
          headers: Object.fromEntries(response.headers.entries()),
          body: errorData
        });
      } catch (e) {
        errorData = {
          error: response.statusText,
          status: response.status,
          details: 'Could not parse error response'
        };
      }

      // Return detailed error information that can be displayed in the UI
      return NextResponse.json({
        error: 'API Error',
        status: response.status,
        details: errorData?.message || 'Failed to fetch sources',
        errorCode: errorData?.code || response.status,
        technicalDetails: errorData?.details || response.statusText,
        supportInfo: {
          message: 'Please contact the Kubiya support team for assistance.',
          email: 'support@kubiya.ai',
          subject: 'API Error - Sources',
          body: `Hi Kubiya Support,\n\nI'm experiencing issues fetching sources.\n\nError Details:\nStatus: ${response.status}\nCode: ${errorData?.code || 'N/A'}\nMessage: ${errorData?.message || response.statusText}`
        }
      }, { 
        status: response.status,
        headers: {
          'Cache-Control': 'no-store'
        }
      });
    }

    const data = await response.json();
    
    // Ensure data is always an array
    const items = Array.isArray(data) ? data : [];
    
    // Transform the response to include pagination metadata
    return NextResponse.json({
      items,
      pagination: {
        page,
        pageSize,
        totalItems: parseInt(response.headers.get('X-Total-Count') || '0'),
        hasMore: response.headers.get('X-Has-More') === 'true'
      }
    }, {
      headers: {
        'Cache-Control': 'no-store'
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