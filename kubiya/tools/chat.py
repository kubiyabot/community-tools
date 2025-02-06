from kubiya_sdk.tools import Arg
from .base import KubiyaCliBase

# Send Message Tool
teammate_message = KubiyaCliBase(
    name="teammate_message",
    description="Send a message to a virtual teammate to request assistance or automation",
    cli_command='''
echo "💬 Sending message..."

# Create context file if provided
if [ -n "${context}" ]; then
    CONTEXT_FILE=$(create_content_file "${context}")
    CONTEXT_ARG="--context $CONTEXT_FILE"
fi

chat \\
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
    mermaid='''
graph TD
    A[Send Message] --> B{Teammate Identified?}
    B -->|Yes| C[Validate Teammate]
    B -->|No| D[Find Best Teammate]
    C --> E[Process Message]
    D --> E
    E --> F{Has Context?}
    F -->|Yes| G[Process Context]
    F -->|No| H[Use Default Context]
    G --> I[Send Request]
    H --> I
    I --> J{Stream Mode?}
    J -->|Yes| K[Stream Response]
    J -->|No| L[Wait for Response]
    K --> M[Return Result]
    L --> M
    '''
)

# Stream Chat Tool
teammate_stream = KubiyaCliBase(
    name="teammate_stream",
    description="Start a real-time conversation with a virtual teammate for complex tasks",
    cli_command='''
echo "🔄 Starting stream..."

# Create context file if provided
if [ -n "${context}" ]; then
    CONTEXT_FILE=$(create_content_file "${context}")
    CONTEXT_ARG="--context $CONTEXT_FILE"
fi

chat \\
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
    mermaid='''
graph TD
    A[Start Stream] --> B[Initialize Session]
    B --> C{Teammate Ready?}
    C -->|Yes| D[Open Stream]
    C -->|No| E[Error]
    D --> F[Send Initial Message]
    F --> G[Process Context]
    G --> H[Start Real-time Loop]
    H --> I{Message Type}
    I -->|Response| J[Show Response]
    I -->|Status| K[Update Status]
    I -->|Error| L[Handle Error]
    J --> H
    K --> H
    L --> M[Close Stream]
    '''
)

# Continue Chat Tool
teammate_continue = KubiyaCliBase(
    name="teammate_continue",
    description="Continue an existing conversation or task with a virtual teammate",
    cli_command='''
echo "🔄 Continuing session..."

# Create context file if provided
if [ -n "${context}" ]; then
    CONTEXT_FILE=$(create_content_file "${context}")
    CONTEXT_ARG="--context $CONTEXT_FILE"
fi

chat \\
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
    mermaid='''
graph TD
    A[Continue Chat] --> B[Load Session]
    B --> C{Session Valid?}
    C -->|Yes| D[Restore Context]
    C -->|No| E[Session Error]
    D --> F[Load History]
    F --> G[Process New Message]
    G --> H{Has New Context?}
    H -->|Yes| I[Merge Contexts]
    H -->|No| J[Use Existing Context]
    I --> K[Send Message]
    J --> K
    K --> L[Process Response]
    L --> M[Update Session]
    '''
)

# Register all tools
for tool in [teammate_message, teammate_stream, teammate_continue]:
    KubiyaCliBase.register(tool)

__all__ = [
    'teammate_message',
    'teammate_stream',
    'teammate_continue',
] 