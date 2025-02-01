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

// Add interface for API request body
interface ScheduledTaskApiRequest {
  schedule_time: string;
  channel_id: string;
  task_description: string;
  selected_agent: string;
  cron_string: string;
}

interface TeammateInfo {
  uuid: string;
  name: string;
  description?: string;
  avatar?: string;
}

interface FormattedTaskResult {
  task_id: string;
  task_uuid: string;
  task_type: string;
  status: string;
  scheduled_time: string;
  channel_id: string;
  created_at: string;
  updated_at: string;
  parameters: {
    message_text: string;
    cron_string: string;
    selected_agent: string;
    selected_agent_name?: string;
    context: Record<string, any>;
    slack_info: {
      team_id: string;
      channel_id: string;
      channel_name: string;
      channel_link: string;
      tooltips: {
        channel_context: string;
        bi_directional: string;
        direct_commands: string;
      };
    };
  };
  teammate?: TeammateInfo;
}

export async function GET(req: NextRequest) {
  try {
    const res = NextResponse.next();
    const session = await getSession(req, res);
    
    if (!session?.idToken) {
      console.error('Scheduled Tasks endpoint - No ID token found');
      return createUnauthorizedResponse('No ID token found');
    }

    console.log('Fetching scheduled tasks...');
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

    console.log('Raw tasks from API:', {
      count: fetchedTasks.length,
      sample: fetchedTasks.slice(0, 2).map(t => ({
        taskId: t.task_id,
        rawData: {
          context: t.parameters?.context,
          parameters: t.parameters
        }
      }))
    });

    // Create a Set of unique teammate IDs from parameters.context
    const teammateIds = new Set<string>();
    fetchedTasks.forEach((task: any) => {
      // Extract teammate ID from parameters.context
      if (task.parameters?.context && typeof task.parameters.context === 'string') {
        teammateIds.add(task.parameters.context);
        console.log('Found teammate ID in parameters.context:', {
          taskId: task.task_id,
          context: task.parameters.context
        });
      }
    });

    console.log('Found teammate IDs:', {
      count: teammateIds.size,
      ids: Array.from(teammateIds)
    });

    // Fetch all unique teammates in parallel
    const teammateDetailsMap = new Map<string, any>();
    try {
      await Promise.all(
        Array.from(teammateIds).map(async (teammateId) => {
          if (!teammateId.trim()) {
            console.log('Skipping empty teammate ID');
            return;
          }
          const teammate = await fetchTeammateDetails(teammateId, session);
          teammateDetailsMap.set(teammateId, teammate);
          console.log('Fetched teammate details:', {
            teammateId,
            name: teammate.name,
            found: !!teammate
          });
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
      // Log raw task data before processing
      console.log('Processing task:', {
        taskId: task.task_id,
        rawData: {
          context: task.parameters?.context,
          parameters: task.parameters
        }
      });

      // Initialize the formatted task
      const formattedTask: FormattedTaskResult = {
        task_id: task.task_id,
        task_uuid: task.task_uuid,
        task_type: task.task_type || 'chat_activity',
        status: task.status || 'pending',
        scheduled_time: task.scheduled_time,
        channel_id: task.channel_id,
        created_at: task.created_at,
        updated_at: task.updated_at,
        parameters: {
          message_text: task.parameters?.message_text || '',
          cron_string: task.parameters?.cron_string || '',
          selected_agent: task.parameters?.context || '',
          selected_agent_name: '',
          context: task.parameters?.action_context_data || {},
          slack_info: {
            team_id: task.parameters?.body?.team?.id || '',
            channel_id: task.channel_id,
            channel_name: task.channel_name || task.channel_id,
            channel_link: task.parameters?.body?.team?.id ? 
              `slack://channel?team=${task.parameters.body.team.id}&id=${task.channel_id.replace('#', '')}` : '',
            tooltips: {
              channel_context: "This task will run in this Slack channel. You can interact with the teammate directly in the channel.",
              bi_directional: "Intelligent conversations are supported - the teammate understands context from previous messages in the channel.",
              direct_commands: "Use @mention to give direct commands to the teammate in this channel"
            }
          }
        }
      };

      // Try to find teammate details from context
      const teammateId = task.parameters?.context;
      if (teammateId?.trim()) {
        const teammate = teammateDetailsMap.get(teammateId);
        if (teammate) {
          formattedTask.teammate = {
            uuid: teammate.uuid,
            name: teammate.name,
            description: teammate.description,
            avatar: undefined // Avatar will be generated on client side
          };
          // Update selected_agent_name
          formattedTask.parameters.selected_agent_name = teammate.name;
          console.log('Added teammate to task:', {
            taskId: task.task_id,
            teammate: formattedTask.teammate
          });
        } else {
          console.log('No teammate found for task:', {
            taskId: task.task_id,
            teammateId
          });
        }
      } else {
        console.log('No valid teammate ID for task:', {
          taskId: task.task_id,
          context: task.parameters?.context
        });
      }

      return formattedTask;
    });

    console.log('Final enhanced tasks:', {
      count: enhancedTasks.length,
      withTeammates: enhancedTasks.filter(t => t.teammate).length,
      withoutTeammates: enhancedTasks.filter(t => !t.teammate).length,
      sample: enhancedTasks.slice(0, 2).map(t => ({
        taskId: t.task_id,
        teammate: t.teammate,
        parameters: {
          selected_agent: t.parameters.selected_agent,
          selected_agent_name: t.parameters.selected_agent_name
        }
      }))
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

    // Format the request body to match API requirements exactly
    const apiRequestBody: ScheduledTaskApiRequest = {
      schedule_time: body.scheduled_time || body.schedule_time, // Handle both formats
      channel_id: body.channel_id,
      task_description: body.parameters?.message_text || body.task_description, // Handle both formats
      selected_agent: body.parameters?.selected_agent || body.selected_agent, // Handle both formats
      cron_string: (body.parameters?.cron_string || body.cron_string || '').trim() // Always include cron_string, default to empty string
    };

    // Validate required fields
    if (!apiRequestBody.schedule_time || !apiRequestBody.channel_id || !apiRequestBody.task_description || !apiRequestBody.selected_agent) {
      return new Response(JSON.stringify({
        error: 'Missing required fields',
        details: 'schedule_time, channel_id, task_description, and selected_agent are required'
      }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    // Ensure schedule_time is in ISO format
    try {
      apiRequestBody.schedule_time = new Date(apiRequestBody.schedule_time).toISOString();
    } catch (e) {
      return new Response(JSON.stringify({
        error: 'Invalid date format',
        details: 'schedule_time must be a valid date'
      }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    // Ensure channel_id starts with # or @
    if (!apiRequestBody.channel_id.startsWith('#') && !apiRequestBody.channel_id.startsWith('@')) {
      apiRequestBody.channel_id = `#${apiRequestBody.channel_id}`;
    }

    console.log('Sending API request with body:', apiRequestBody);

    // Start creating task and fetching teammate details in parallel
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
      fetchTeammateDetails(apiRequestBody.selected_agent, session)
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

    // Format the response to match what the client expects
    const formattedResult: FormattedTaskResult = {
      task_id: result.task_id || body.task_id,
      task_uuid: result.task_uuid || body.task_uuid,
      task_type: result.task_type || 'message',
      status: result.status || 'pending',
      scheduled_time: result.schedule_time || apiRequestBody.schedule_time,
      channel_id: result.channel_id || apiRequestBody.channel_id,
      created_at: result.created_at || new Date().toISOString(),
      updated_at: result.updated_at || new Date().toISOString(),
      parameters: {
        message_text: result.task_description || apiRequestBody.task_description,
        cron_string: result.cron_string || apiRequestBody.cron_string || '',
        selected_agent: result.selected_agent || apiRequestBody.selected_agent,
        selected_agent_name: body.parameters?.selected_agent_name || teammate?.name,
        context: body.parameters?.context || {},
        slack_info: {
          team_id: result.parameters?.body?.team?.id || '',
          channel_id: result.channel_id,
          channel_name: result.channel_name || result.channel_id,
          channel_link: result.parameters?.body?.team?.id ? 
            `slack://channel?team=${result.parameters.body.team.id}&id=${result.channel_id.replace('#', '')}` : '',
          tooltips: {
            channel_context: "This task will run in this Slack channel. You can interact with the teammate directly in the channel.",
            bi_directional: "Intelligent conversations are supported - the teammate understands context from previous messages in the channel.",
            direct_commands: "Use @mention to give direct commands to the teammate in this channel"
          }
        }
      }
    };

    // Add teammate details if available
    if (teammate) {
      console.log('Adding teammate details to response:', teammate);
      formattedResult.teammate = {
        uuid: teammate.uuid,
        name: teammate.name,
        description: teammate.description,
        avatar: undefined // Avatar will be generated on client side
      };
    } else {
      console.log('No teammate details available for:', apiRequestBody.selected_agent);
    }

    console.log('Returning formatted result:', formattedResult);

    return new Response(JSON.stringify(formattedResult), {
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
      return createUnauthorizedResponse('No ID token found');
    }

    // Extract taskId from the URL
    const { searchParams } = new URL(req.url);
    const taskId = searchParams.get('taskId');

    if (!taskId) {
      console.error('Delete task - No taskId provided');
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

    console.log('Attempting to delete task:', { taskId });

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
      // Handle specific error cases
      if (response.status === 401) {
        return createUnauthorizedResponse('Session expired while deleting task');
      }

      if (response.status === 404) {
        console.error('Task not found:', { taskId });
        return new Response(JSON.stringify({
          error: 'Task not found',
          details: 'The specified task could not be found'
        }), { 
          status: 404,
          headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-store'
          }
        });
      }

      let errorData;
      try {
        errorData = await response.json();
        console.error('Delete task error:', {
          taskId,
          status: response.status,
          error: errorData
        });
      } catch (e) {
        errorData = {
          error: response.statusText,
          status: response.status,
          details: 'Could not parse error response'
        };
      }

      return new Response(JSON.stringify({
        error: 'Failed to delete task',
        status: response.status,
        details: errorData?.msg || response.statusText,
        taskId
      }), { 
        status: response.status,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store'
        }
      });
    }

    console.log('Task deleted successfully:', { taskId });

    // Return 204 No Content for successful deletion
    return new Response(null, { 
      status: 204,
      headers: {
        'Cache-Control': 'no-store'
      }
    });
  } catch (error) {
    console.error('Delete task error:', {
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined
    });

    if (error instanceof Error && error.message.includes('Unauthorized')) {
      return createUnauthorizedResponse(error.message);
    }

    return new Response(JSON.stringify({ 
      error: 'Failed to delete task',
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