import { NextResponse } from 'next/server';

export const runtime = 'edge';

// Keep track of all connected clients
const clients = new Set<ReadableStreamController<Uint8Array>>();

// Broadcast function to send updates to all connected clients
export function broadcastActivity(activity: unknown) {
  const message = JSON.stringify({
    type: 'activity_update',
    data: activity
  });

  clients.forEach(controller => {
    controller.enqueue(new TextEncoder().encode(`data: ${message}\n\n`));
  });
}

export async function GET() {
  const encoder = new TextEncoder();

  try {
    const stream = new ReadableStream({
      start: async (controller) => {
        let isConnectionClosed = false;

        // Keep connection alive with comment
        const keepAlive = setInterval(() => {
          if (!isConnectionClosed) {
            try {
              controller.enqueue(encoder.encode(': keepalive\n\n'));
            } catch (error) {
              // If controller is closed, clear interval
              clearInterval(keepAlive);
            }
          }
        }, 30000);

        // Clean up on close
        const cleanup = () => {
          isConnectionClosed = true;
          clearInterval(keepAlive);
          try {
            controller.close();
          } catch (error) {
            // Ignore if controller is already closed
          }
        };

        // Handle connection close
        try {
          // Your existing stream logic here
          // When you need to send data:
          // controller.enqueue(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));
        } catch (error) {
          cleanup();
          throw error;
        }
      }
    });

    return new NextResponse(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    console.error('Stream error:', error);
    return new NextResponse('Internal Server Error', { status: 500 });
  }
} 