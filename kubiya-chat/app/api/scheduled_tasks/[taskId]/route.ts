import { NextResponse } from 'next/server';

export async function DELETE(
  request: Request,
  { params }: { params: { taskId: string } }
) {
  try {
    const taskId = params.taskId;
    
    const response = await fetch(`https://api.kubiya.ai/api/v1/scheduled_tasks/${taskId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        // Forward any auth headers from the original request
        ...request.headers
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to delete task: ${response.statusText}`);
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error('Error deleting scheduled task:', error);
    return new NextResponse(
      JSON.stringify({ error: 'Failed to delete scheduled task' }), 
      { status: 500 }
    );
  }
} 