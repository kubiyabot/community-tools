import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

// Helper function to create an unauthorized response
function createUnauthorizedResponse(message = 'Unauthorized') {
  return new Response(JSON.stringify({ 
    error: 'Unauthorized',
    details: message,
    shouldLogout: true
  }), { 
    status: 401,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-store'
    }
  });
}

// Helper function to fetch teammate details
async function fetchTeammateDetails(teammateId: string, session: any) {
  try {
    const teammateResponse = await fetch(`https://api.kubiya.ai/api/v1/agents/${teammateId}`, {
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      },
    });

    if (!teammateResponse.ok) {
      if (teammateResponse.status === 401) {
        throw new Error('Unauthorized');
      }
      console.error(`Failed to fetch teammate ${teammateId}:`, teammateResponse.statusText);
      // Return a default teammate object if fetch fails
      return {
        uuid: teammateId,
        name: teammateId.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
        description: 'Teammate details unavailable'
      };
    }

    const teammate = await teammateResponse.json();
    return teammate;
  } catch (error) {
    if (error instanceof Error && error.message === 'Unauthorized') {
      throw error;
    }
    console.error(`Error fetching teammate ${teammateId}:`, error);
    // Return a default teammate object on error
    return {
      uuid: teammateId,
      name: teammateId.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
      description: 'Teammate details unavailable'
    };
  }
}

export async function GET(req: NextRequest) {
  try {
    const res = NextResponse.next();
    const session = await getSession(req, res);
    
    if (!session?.idToken) {
      console.error('Scheduled Tasks endpoint - No ID token found');
      return createUnauthorizedResponse('No ID token found');
    }

    const response = await fetch('https://api.kubiya.ai/api/v1/scheduled_tasks', {
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        return createUnauthorizedResponse('Session expired or invalid');
      }
      throw new Error(`Failed to fetch tasks: ${response.statusText}`);
    }

    const fetchedTasks: any[] = await response.json();

    // Create a Set of unique teammate IDs
    const teammateIds = new Set<string>(
      fetchedTasks
        .filter((task: any) => task.parameters?.selected_agent && typeof task.parameters.selected_agent === 'string')
        .map((task: any) => task.parameters.selected_agent as string)
    );

    // Fetch all unique teammates in parallel
    const teammateDetailsMap = new Map<string, any>();
    try {
      await Promise.all(
        Array.from(teammateIds).map(async (teammateId) => {
          const teammate = await fetchTeammateDetails(teammateId, session);
          teammateDetailsMap.set(teammateId, teammate);
        })
      );
    } catch (error) {
      if (error instanceof Error && error.message === 'Unauthorized') {
        return createUnauthorizedResponse('Session expired while fetching teammate details');
      }
      console.error('Error fetching teammate details:', error);
    }

    // Map tasks with teammate details
    const enhancedTasks = fetchedTasks.map((task: any) => {
      // First try to get teammate details from the map
      if (task.parameters?.selected_agent) {
        const teammate = teammateDetailsMap.get(task.parameters.selected_agent);
        if (teammate) {
          return {
            ...task,
            teammate: {
              uuid: teammate.uuid,
              name: task.parameters.selected_agent_name || teammate.name,
              description: teammate.description,
              avatar: undefined // Avatar will be generated on the client side
            }
          };
        }
      }

      // If no teammate details but we have selected_agent_name, use that
      if (task.parameters?.selected_agent_name) {
        return {
          ...task,
          teammate: {
            uuid: task.parameters.selected_agent || 'unknown',
            name: task.parameters.selected_agent_name,
            description: 'Teammate details loading...'
          }
        };
      }

      // If we have selected_agent but no name, format the agent ID
      if (task.parameters?.selected_agent) {
        const formattedName = task.parameters.selected_agent
          .split('_')
          .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ');
        return {
          ...task,
          teammate: {
            uuid: task.parameters.selected_agent,
            name: formattedName,
            description: 'Teammate details loading...'
          }
        };
      }

      return task;
    });

    return new Response(JSON.stringify(enhancedTasks), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });
  } catch (error) {
    console.error('Scheduled Tasks endpoint error:', {
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined
    });

    // Check if it's an unauthorized error
    if (error instanceof Error && error.message.includes('Unauthorized')) {
      return createUnauthorizedResponse(error.message);
    }

    return new Response(JSON.stringify({ 
      error: 'Failed to fetch scheduled tasks',
      details: error instanceof Error ? error.message : 'Unknown error'
    }), { 
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });
  }
}

export async function POST(req: NextRequest) {
  try {
    const res = NextResponse.next();
    const session = await getSession(req, res);
    
    if (!session?.idToken) {
      console.error('Scheduled Tasks endpoint - No ID token found');
      return new Response(JSON.stringify({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }), { 
        status: 401,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    const body = await req.json();
    console.log('Creating scheduled task with body:', body);

    // Format the request body to match API requirements
    const apiRequestBody = {
      task_type: body.task_type || 'message',
      scheduled_time: body.scheduled_time,
      channel_id: body.channel_id,
      parameters: {
        message_text: body.parameters.message_text,
        selected_agent: body.parameters.selected_agent,
        selected_agent_name: body.parameters.selected_agent_name || 
          (body.teammate?.name ? body.teammate.name : undefined),
        cron_string: body.parameters.cron_string,
        context: body.parameters.context || {}
      }
    };

    // Start creating task and fetching teammate details in parallel if a teammate is selected
    const [response, teammate] = await Promise.all([
      fetch('https://api.kubiya.ai/api/v1/scheduled_tasks', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.idToken}`,
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache',
          'X-Organization-ID': session.user?.org_id || '',
          'X-Kubiya-Client': 'chat-ui'
        },
        body: JSON.stringify(apiRequestBody),
      }),
      body.parameters?.selected_agent ? 
        fetchTeammateDetails(body.parameters.selected_agent, session) : 
        Promise.resolve(null)
    ]);

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
        console.error('Scheduled Tasks endpoint - Create task error:', {
          status: response.status,
          headers: Object.fromEntries(response.headers.entries()),
          body: errorData,
          sentBody: apiRequestBody
        });
      } catch (e) {
        errorData = {
          error: response.statusText,
          status: response.status,
          details: 'Could not parse error response'
        };
      }

      return new Response(JSON.stringify({
        error: 'Failed to create scheduled task',
        status: response.status,
        details: errorData?.msg || response.statusText,
        requestBody: apiRequestBody
      }), { 
        status: response.status,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    const result = await response.json();

    // Add teammate details if available
    const taskWithTeammate = teammate ? {
      ...result,
      teammate: {
        uuid: teammate.uuid,
        name: body.parameters.selected_agent_name || teammate.name,
        description: teammate.description
      }
    } : result;

    return new Response(JSON.stringify(taskWithTeammate), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });
  } catch (error) {
    console.error('Scheduled Tasks endpoint error:', {
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined
    });
    return new Response(JSON.stringify({ 
      error: 'Failed to create scheduled task',
      details: error instanceof Error ? error.message : 'Unknown error'
    }), { 
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });
  }
}

export async function DELETE(req: NextRequest) {
  try {
    const res = NextResponse.next();
    const session = await getSession(req, res);
    
    if (!session?.idToken) {
      console.error('Scheduled Tasks endpoint - No ID token found');
      return new Response(JSON.stringify({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }), { 
        status: 401,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    const { searchParams } = new URL(req.url);
    const taskId = searchParams.get('taskId');

    if (!taskId) {
      return new Response(JSON.stringify({ 
        error: 'Bad Request',
        details: 'Task ID is required'
      }), { 
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    const response = await fetch(`https://api.kubiya.ai/api/v1/scheduled_tasks/${taskId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${session.idToken}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'X-Organization-ID': session.user?.org_id || '',
        'X-Kubiya-Client': 'chat-ui'
      },
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
        console.error('Scheduled Tasks endpoint - Delete task error:', {
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

      return new Response(JSON.stringify({
        error: 'Failed to delete scheduled task',
        status: response.status,
        details: errorData?.msg || response.statusText
      }), { 
        status: response.status,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    return new Response(null, { 
      status: 204,
      headers: {
        'Cache-Control': 'no-store'
      }
    });
  } catch (error) {
    console.error('Scheduled Tasks endpoint - Delete error:', {
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined
    });
    return new Response(JSON.stringify({ 
      error: 'Failed to delete scheduled task',
      details: error instanceof Error ? error.message : 'Unknown error'
    }), { 
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store'
      }
    });
  }
} 