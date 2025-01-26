import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const res = NextResponse.next();
    const session = await getSession(req, res);

    if (!session?.idToken) {
      return NextResponse.json({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }, { status: 401 });
    }

    const response = await fetch('https://api.kubiya.ai/api/v1/scheduled_tasks', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: response.statusText }));
      return NextResponse.json({
        error: 'Failed to fetch scheduled tasks',
        status: response.status,
        details: errorData.message || response.statusText
      }, { status: response.status });
    }

    const tasks = await response.json();
    return NextResponse.json(tasks);
  } catch (error) {
    console.error('Error fetching scheduled tasks:', error);
    return NextResponse.json(
      { error: 'Failed to fetch scheduled tasks' },
      { status: 500 }
    );
  }
}

export async function POST(req: NextRequest) {
  try {
    const res = NextResponse.next();
    const session = await getSession(req, res);

    if (!session?.idToken) {
      return NextResponse.json({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }, { status: 401 });
    }

    let data;
    try {
      const rawData = await req.text();
      data = JSON.parse(rawData);
    } catch (e) {
      return NextResponse.json({
        error: 'Invalid JSON format',
        details: 'Request body must be valid JSON'
      }, { status: 400 });
    }
    
    // Ensure all required fields are present
    if (!data.task_type || !data.scheduled_time || !data.channel_id || !data.parameters) {
      return NextResponse.json({
        error: 'Missing required fields',
        details: 'Required fields: task_type, scheduled_time, channel_id, parameters'
      }, { status: 400 });
    }

    // Ensure parameters have all required fields
    if (!data.parameters.message_text || !data.parameters.team_id || !data.parameters.user_email) {
      return NextResponse.json({
        error: 'Missing required parameter fields',
        details: 'Required parameter fields: message_text, team_id, user_email'
      }, { status: 400 });
    }

    // Log request details for debugging
    console.log('Schedule task endpoint - Request details:', {
      url: 'https://api.kubiya.ai/api/v1/scheduled_tasks',
      method: 'POST',
      token: {
        prefix: session.idToken.substring(0, 20) + '...',
        user: {
          email: session.user?.email,
          sub: session.user?.sub,
          org_id: session.user?.org_id
        }
      },
      data
    });
    
    const response = await fetch('https://api.kubiya.ai/api/v1/scheduled_tasks', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      },
      body: JSON.stringify({
        ...data,
        parameters: {
          ...data.parameters,
          organization_name: session.user?.org_id || '',
          team_id: data.parameters.team_id || session.user?.org_id,
          user_email: data.parameters.user_email || session.user?.email
        }
      })
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
        console.error('Schedule task endpoint - Full error response:', {
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

      return NextResponse.json({
        error: 'Failed to schedule task',
        status: response.status,
        details: errorData?.error || 'Unable to schedule task. This might be due to an expired session or misconfigured permissions.',
        supportInfo: {
          message: 'Please contact the Kubiya support team for assistance.',
          email: 'support@kubiya.ai',
          subject: 'Task Scheduling Issue - Chat UI',
          body: `Hi Kubiya Support,\n\nI'm experiencing issues scheduling tasks in the Chat UI.\n\nError Details:\nStatus: ${response.status}\nMessage: ${errorData?.error || response.statusText}`
        }
      }, { 
        status: response.status,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error('Error scheduling task:', error);
    return NextResponse.json(
      { error: 'Failed to schedule task', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function DELETE(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const taskId = searchParams.get('taskId');

    if (!taskId) {
      return NextResponse.json(
        { error: 'Task ID is required' },
        { status: 400 }
      );
    }

    const response = await fetch(`https://api.kubiya.ai/api/v1/scheduled_tasks/${taskId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(error, { status: response.status });
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error deleting task:', error);
    return NextResponse.json(
      { error: 'Failed to delete task' },
      { status: 500 }
    );
  }
} 