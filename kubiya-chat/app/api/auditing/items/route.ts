import { NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';
import type { NextRequest } from 'next/server';

export const runtime = 'edge';

export async function GET(request: NextRequest) {
  try {
    const res = NextResponse.next();
    const session = await getSession(request, res);

    if (!session?.idToken) {
      return NextResponse.json({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const filter = searchParams.get('filter');
    const page = searchParams.get('page') || '1';
    const pageSize = searchParams.get('page_size') || '100';
    const sort = searchParams.get('sort');

    // Parse the filter parameter
    let filterObj = {};
    if (filter) {
      // Handle old timeframe format
      if (filter.startsWith('timeframe:')) {
        const timeframe = filter.split(':')[1];
        const now = new Date();
        let startDate = new Date();
        
        switch (timeframe) {
          case '1h':
            startDate = new Date(now.getTime() - (60 * 60 * 1000));
            break;
          case '24h':
            startDate = new Date(now.getTime() - (24 * 60 * 60 * 1000));
            break;
          case '7d':
            startDate = new Date(now.getTime() - (7 * 24 * 60 * 60 * 1000));
            break;
          case '30d':
            startDate = new Date(now.getTime() - (30 * 24 * 60 * 60 * 1000));
            break;
          default:
            startDate = new Date(0);
        }
        
        filterObj = {
          timestamp: {
            gte: startDate.toISOString(),
            lte: now.toISOString()
          }
        };
      } else {
        // Handle new JSON format
        try {
          filterObj = JSON.parse(filter);
        } catch (e) {
          console.error('Failed to parse filter:', e);
          return NextResponse.json({ error: 'Invalid filter parameter' }, { status: 400 });
        }
      }
    }

    // Construct the API URL with the correct query parameters
    const apiUrl = new URL('https://api.kubiya.ai/api/v1/auditing/items');
    
    apiUrl.searchParams.set('filter', JSON.stringify(filterObj));
    apiUrl.searchParams.set('page', page);
    apiUrl.searchParams.set('page_size', pageSize);
    if (sort) {
      apiUrl.searchParams.set('sort', sort);
    }

    console.log('Fetching from:', apiUrl.toString());

    const response = await fetch(apiUrl.toString(), {
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Content-Type': 'application/json',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('API Error:', {
        status: response.status,
        statusText: response.statusText,
        error: errorText
      });
      return NextResponse.json({ error: errorText }, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Error fetching audit data:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to fetch audit data' },
      { status: 500 }
    );
  }
} 