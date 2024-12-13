from kubiya_sdk.tools import Arg
from .base import create_tool

# Send Message Tool
teammate_message = create_tool(
    name="teammate_message",
    description="Send a message to a virtual teammate to request assistance or automation",
    cli_command='''
echo "💬 Sending message..."

# Create context file if provided
if [ -n "${context}" ]; then
    CONTEXT_FILE=$(create_content_file "${context}")
    CONTEXT_ARG="--context $CONTEXT_FILE"
fi

kubiya chat \\
    $([ -n "${id}" ] && echo "--id ${id}") \\
    $([ -n "${name}" ] && echo "--name ${name}") \\
    --message "${message}" \\
    $CONTEXT_ARG \\
    $([ "${stream}" = "true" ] && echo "--stream") \\
    $([ -n "${session}" ] && echo "--session-id ${session}") \\
    --output json
''',
    args=[
        Arg(name="message", type="str", description="Task or request for the teammate", required=True),
        Arg(name="id", type="str", description="Virtual teammate ID", required=False),
        Arg(name="name", type="str", description="Virtual teammate name", required=False),
        Arg(name="context", type="str", description="Additional context for the task", required=False),
        Arg(name="stream", type="bool", description="Get real-time responses", required=False, default="false"),
        Arg(name="session", type="str", description="Existing conversation ID", required=False),
    ],
)

# Stream Chat Tool
teammate_stream = create_tool(
    name="teammate_stream",
    description="Start a real-time conversation with a virtual teammate for complex tasks",
    cli_command='''
echo "🔄 Starting stream..."

# Create context file if provided
if [ -n "${context}" ]; then
    CONTEXT_FILE=$(create_content_file "${context}")
    CONTEXT_ARG="--context $CONTEXT_FILE"
fi

kubiya chat \\
    $([ -n "${id}" ] && echo "--id ${id}") \\
    $([ -n "${name}" ] && echo "--name ${name}") \\
    --message "${message}" \\
    $CONTEXT_ARG \\
    --stream \\
    $([ -n "${session}" ] && echo "--session-id ${session}") \\
    --output json
''',
    args=[
        Arg(name="message", type="str", description="Initial task or request", required=True),
        Arg(name="id", type="str", description="Virtual teammate ID", required=False),
        Arg(name="name", type="str", description="Virtual teammate name", required=False),
        Arg(name="context", type="str", description="Additional task context", required=False),
        Arg(name="session", type="str", description="Existing conversation ID", required=False),
    ],
)

# Continue Chat Tool
teammate_continue = create_tool(
    name="teammate_continue",
    description="Continue an existing conversation or task with a virtual teammate",
    cli_command='''
echo "🔄 Continuing session..."

# Create context file if provided
if [ -n "${context}" ]; then
    CONTEXT_FILE=$(create_content_file "${context}")
    CONTEXT_ARG="--context $CONTEXT_FILE"
fi

kubiya chat \\
    $([ -n "${id}" ] && echo "--id ${id}") \\
    $([ -n "${name}" ] && echo "--name ${name}") \\
    --message "${message}" \\
    $CONTEXT_ARG \\
    --session-id "${session}" \\
    $([ "${stream}" = "true" ] && echo "--stream") \\
    --output json
''',
    args=[
        Arg(name="message", type="str", description="Follow-up request or information", required=True),
        Arg(name="session", type="str", description="Previous conversation ID", required=True),
        Arg(name="id", type="str", description="Virtual teammate ID", required=False),
        Arg(name="name", type="str", description="Virtual teammate name", required=False),
        Arg(name="context", type="str", description="New context for the task", required=False),
        Arg(name="stream", type="bool", description="Get real-time responses", required=False, default="false"),
    ],
)

__all__ = [
    'teammate_message',
    'teammate_stream',
    'teammate_continue',
] 