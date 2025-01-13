export async function POST(req: Request) {
  try {
    const authHeader = req.headers.get('Authorization');
    if (!authHeader) {
      return new Response('Unauthorized', { status: 401 });
    }

    // Forward the exact authorization header to maintain the auth type (Bearer or userkey)
    const response = await fetch('https://api.kubiya.ai/api/v1/converse', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(await req.json()),
    });

    if (!response.ok) {
      return new Response(`API error: ${response.status}`, { status: response.status });
    }

    // Stream the response back to the client
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error) {
    console.error('API error:', error);
    return new Response(
      JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }), 
      { status: 500 }
    );
  }
} 