from .base import JiraTool, register_jira_tool
from kubiya_sdk.tools import Arg

issue_list = JiraTool(
    name="issue_list",
    description="List Jira issues with various filters and sorting options. Use 'grep' to further filter results.",
    content="""
    jira issue list --created "$created" \
                    --status "$status" \
                    --plain \
                    --order-by "$order_by" \
                    $([[ "$reverse" == "true" ]] && echo "--reverse") \
                    $([[ -n "$jql" ]] && echo "-q \"$jql\"") \
                    $([[ "$watching" == "true" ]] && echo "-w") \
                    --assignee "$assignee" \
                    --reporter "$reporter" \
                    --priority "$priority" \
                    --resolution "$resolution" \
                    --created-before "$created_before" \
                    --updated "$updated" \
                    $([[ -n "$labels" ]] && echo "--label $labels") \
                    $([[ "$history" == "true" ]] && echo "--history") \
    $([[ -n "$grep_filter" ]] && echo "grep \"$grep_filter\"" || echo "cat")
    """,
    args=[
        Arg(name="created", type="str", description="Filter by creation date (e.g., '-7d' for last 7 days)", required=False),
        Arg(name="status", type="str", description="Filter by status (e.g., 'To Do', 'In Progress')", required=False),
        Arg(name="order_by", type="str", description="Order results by field (e.g., 'created', 'updated')", required=False),
        Arg(name="reverse", type="bool", description="Reverse the order of results", required=False),
        Arg(name="jql", type="str", description="Custom JQL query", required=False),
        Arg(name="watching", type="bool", description="Show issues you're watching", required=False),
        Arg(name="assignee", type="str", description="Filter by assignee (use '$(jira me)' for self)", required=False),
        Arg(name="reporter", type="str", description="Filter by reporter", required=False),
        Arg(name="priority", type="str", description="Filter by priority (e.g., 'High', 'Low')", required=False),
        Arg(name="resolution", type="str", description="Filter by resolution (e.g., 'Fixed', 'Won't Do')", required=False),
        Arg(name="created_before", type="str", description="Filter by creation date before (e.g., '-30d' for before 30 days ago)", required=False),
        Arg(name="updated", type="str", description="Filter by last update date (e.g., '-24h' for last 24 hours)", required=False),
        Arg(name="labels", type="str", description="Filter by labels (comma-separated)", required=False),
        Arg(name="history", type="bool", description="Show issue history", required=False),
        Arg(name="grep_filter", type="str", description="Additional grep filter for results", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[User] -->|Request to list issues| B(TeamMate)
        B -->|Apply filters| C{Filters}
        C -->|Created| D[Date Range]
        C -->|Status| E[To Do/In Progress/Done]
        C -->|Order By| F[Created/Updated]
        C -->|Reverse| G[True/False]
        C -->|JQL Query| H[Custom Query]
        C -->|Watching| I[True/False]
        C -->|Assignee| J[User/Self]
        C -->|Reporter| K[User]
        C -->|Priority| L[High/Medium/Low]
        C -->|Resolution| M[Fixed/Won't Do]
        C -->|Created Before| N[Date]
        C -->|Updated| O[Date Range]
        C -->|Labels| P[Comma-separated]
        C -->|History| Q[True/False]
        C -->|Grep Filter| S[Regex]
        D & E & F & G & H & I & J & K & L & M & N & O & P & Q & R & S -->|List Issues| T[Jira API]
        T -->|Issue List| U[Results]
        U -->|Display| B
        B -->|Notify| A

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style T fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style U fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

issue_create = JiraTool(
    name="issue_create",
    description="Create a new Jira issue with specified details.",
    content="""
    jira issue create --type "$type" \
                      --summary "$summary" \
                      --priority "$priority" \
                      $([[ -n "$labels" ]] && echo "--labels $labels") \
                      $([[ -n "$components" ]] && echo "--components $components") \
                      --description "$description" \
                      $([[ -n "$fix_version" ]] && echo "--fix-version $fix_version") \
                      $([[ -n "$parent" ]] && echo "--parent $parent") \
                      $([[ -n "$custom" ]] && echo "--custom \"$custom\"") \
                      $([[ -n "$template" ]] && echo "--template $template")
    """,
    args=[
        Arg(name="type", type="str", description="Issue type (e.g., 'Bug', 'Task', 'Story')", required=True),
        Arg(name="summary", type="str", description="Issue summary", required=True),
        Arg(name="priority", type="str", description="Issue priority (e.g., 'High', 'Medium', 'Low')", required=True),
        Arg(name="labels", type="str", description="Issue labels (comma-separated)", required=False),
        Arg(name="components", type="str", description="Issue components (comma-separated)", required=False),
        Arg(name="description", type="str", description="Issue description", required=True),
        Arg(name="fix_version", type="str", description="Fix version", required=False),
        Arg(name="parent", type="str", description="Parent issue key for sub-tasks", required=False),
        Arg(name="custom", type="str", description="Custom fields in JSON format", required=False),
        Arg(name="template", type="str", description="Template file path for description", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[User] -->|Request to create issue| B(TeamMate)
        B -->|Prompt for details| C{Issue Details}
        C -->|Type| D[Bug/Task/Story]
        C -->|Summary| E[Issue Summary]
        C -->|Priority| F[High/Medium/Low]
        C -->|Description| G[Issue Description]
        D & E & F & G -->|Create Issue| H[Jira API]
        H -->|Issue Created| I[New Jira Issue]
        I -->|Confirm| B
        B -->|Notify| A

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style H fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style I fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

issue_edit = JiraTool(
    name="issue_edit",
    description="Edit an existing Jira issue, updating specified fields.",
    content="""
    jira issue edit $issue_key \
                    $([[ -n "$summary" ]] && echo "--summary \"$summary\"") \
                    $([[ -n "$priority" ]] && echo "--priority \"$priority\"") \
                    $([[ -n "$labels" ]] && echo "$labels") \
                    $([[ -n "$components" ]] && echo "$components") \
                    $([[ -n "$description" ]] && echo "--description \"$description\"") \
                    $([[ -n "$fix_version" ]] && echo "--fix-version $fix_version")
    """,
    args=[
        Arg(name="issue_key", type="str", description="Issue key (e.g., 'PROJ-123')", required=True),
        Arg(name="summary", type="str", description="New summary", required=False),
        Arg(name="priority", type="str", description="New priority", required=False),
        Arg(name="labels", type="str", description="Labels to add/remove (prefix with '-' to remove)", required=False),
        Arg(name="components", type="str", description="Components to add/remove (prefix with '-' to remove)", required=False),
        Arg(name="description", type="str", description="New description", required=False),
        Arg(name="fix_version", type="str", description="Fix version to add/remove", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[User] -->|Request to edit issue| B(TeamMate)
        B -->|Prompt for changes| C{Issue Changes}
        C -->|Summary| D[New Summary]
        C -->|Priority| E[New Priority]
        C -->|Labels| F[Add/Remove]
        C -->|Components| G[Add/Remove]
        C -->|Description| H[New Description]
        C -->|Fix Version| I[Add/Remove]
        D & E & F & G & H & I -->|Update Issue| J[Jira API]
        J -->|Issue Updated| K[Updated Jira Issue]
        K -->|Confirm| B
        B -->|Notify| A

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style J fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style K fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

issue_assign = JiraTool(
    name="issue_assign",
    description="Assign a Jira issue to a user or unassign it.",
    content="jira issue assign $issue_key \"$assignee\"",
    args=[
        Arg(name="issue_key", type="str", description="Issue key (e.g., 'PROJ-123')", required=True),
        Arg(name="assignee", type="str", description="Assignee name, 'x' to unassign, or '$(jira me)' for self", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[User] -->|Request to assign/unassign issue| B(TeamMate)
        B -->|Prompt for assignee| C[Assignee]
        C -->|Assign/Unassign| D[Jira API]
        D -->|Issue Updated| E[Updated Jira Issue]
        E -->|Confirm| B
        B -->|Notify| A

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style E fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

issue_move = JiraTool(
    name="issue_move",
    description="Move a Jira issue to a different status, optionally adding a comment or changing assignee.",
    content="""
    jira issue move $issue_key "$new_status" \
                    $([[ -n "$comment" ]] && echo "--comment \"$comment\"") \
                    $([[ -n "$resolution" ]] && echo "--resolution \"$resolution\"") \
                    $([[ -n "$assignee" ]] && echo "--assignee \"$assignee\"")
    """,
    args=[
        Arg(name="issue_key", type="str", description="Issue key (e.g., 'PROJ-123')", required=True),
        Arg(name="new_status", type="str", description="New status (e.g., 'In Progress', 'Done')", required=True),
        Arg(name="comment", type="str", description="Comment to add when moving the issue", required=False),
        Arg(name="resolution", type="str", description="Resolution when closing an issue", required=False),
        Arg(name="assignee", type="str", description="Assign to a user when moving", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[User] -->|Request to move issue| B(TeamMate)
        B -->|Prompt for new status| C[New Status]
        B -->|Prompt for comment| D[Comment]
        B -->|Prompt for resolution| E[Resolution]
        B -->|Prompt for assignee| F[Assignee]
        C & D & E & F -->|Move Issue| G[Jira API]
        G -->|Issue Moved| H[Updated Jira Issue]
        H -->|Confirm| B
        B -->|Notify| A

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style F fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style G fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style H fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

issue_view = JiraTool(
    name="issue_view",
    description="View details of a Jira issue, including recent comments if specified.",
    content="jira issue view $issue_key $([[ -n \"$comments\" ]] && echo \"--comments $comments\")",
    args=[
        Arg(name="issue_key", type="str", description="Issue key (e.g., 'PROJ-123')", required=True),
        Arg(name="comments", type="int", description="Number of recent comments to show", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[User] -->|Request to view issue| B(TeamMate)
        B -->|Prompt for issue key| C[Issue Key]
        B -->|Prompt for comments| D[Number of Comments]
        C & D -->|View Issue| E[Jira API]
        E -->|Issue Details| F[Jira Issue]
        F -->|Display| B
        B -->|Notify| A

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

issue_comment_add = JiraTool(
    name="issue_comment_add",
    description="Add a comment to a Jira issue, optionally using a template.",
    content="""
    jira issue comment add $issue_key "$comment" $([[ -n "$template" ]] && echo "--template $template")
    """,
    args=[
        Arg(name="issue_key", type="str", description="Issue key (e.g., 'PROJ-123')", required=True),
        Arg(name="comment", type="str", description="Comment body", required=True),
        Arg(name="template", type="str", description="Template file path for comment body", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[User] -->|Request to add comment| B(TeamMate)
        B -->|Prompt for issue key| C[Issue Key]
        B -->|Prompt for comment| D[Comment]
        B -->|Prompt for template| E[Template]
        C & D & E -->|Add Comment| F[Jira API]
        F -->|Comment Added| G[Updated Jira Issue]
        G -->|Confirm| B
        B -->|Notify| A

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style F fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

issue_link = JiraTool(
    name="issue_link",
    description="Create a link between two Jira issues with a specified relationship type.",
    content="jira issue link $inward_issue $outward_issue $link_type",
    args=[
        Arg(name="inward_issue", type="str", description="Inward issue key", required=True),
        Arg(name="outward_issue", type="str", description="Outward issue key", required=True),
        Arg(name="link_type", type="str", description="Type of link (e.g., 'Blocks', 'Relates to')", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[User] -->|Request to link issues| B(TeamMate)
        B -->|Prompt for inward issue| C[Inward Issue]
        B -->|Prompt for outward issue| D[Outward Issue]
        B -->|Prompt for link type| E[Link Type]
        C & D & E -->|Link Issues| F[Jira API]
        F -->|Issues Linked| G[Linked Jira Issues]
        G -->|Confirm| B
        B -->|Notify| A

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style F fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

issue_watch = JiraTool(
    name="issue_watch",
    description="Add or remove a watcher from a Jira issue.",
    content="jira issue watch $issue_key $action $user",
    args=[
        Arg(name="issue_key", type="str", description="Issue key (e.g., 'PROJ-123')", required=True),
        Arg(name="action", type="str", description="Action to perform ('add' or 'remove')", required=True),
        Arg(name="user", type="str", description="Username of the watcher", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[User] -->|Request to add/remove watcher| B(TeamMate)
        B -->|Prompt for issue key| C[Issue Key]
        B -->|Prompt for action| D[Add/Remove]
        B -->|Prompt for user| E[Username]
        C & D & E -->|Update Watchers| F[Jira API]
        F -->|Watchers Updated| G[Updated Jira Issue]
        G -->|Confirm| B
        B -->|Notify| A

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style F fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

issue_attachments = JiraTool(
    name="issue_attachments",
    description="List, add, or remove attachments from a Jira issue.",
    content="""
    if [ "$action" = "list" ]; then
        jira issue attachments $issue_key
    elif [ "$action" = "add" ]; then
        jira issue attachments add $issue_key "$file_path"
    elif [ "$action" = "remove" ]; then
        jira issue attachments remove $issue_key "$attachment_id"
    else
        echo "Invalid action. Use 'list', 'add', or 'remove'."
        exit 1
    fi
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform ('list', 'add', or 'remove')", required=True),
        Arg(name="issue_key", type="str", description="Issue key (e.g., 'PROJ-123')", required=True),
        Arg(name="file_path", type="str", description="Path to file to attach (for 'add' action)", required=False),
        Arg(name="attachment_id", type="str", description="ID of attachment to remove (for 'remove' action)", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[User] -->|Request to manage attachments| B(TeamMate)
        B -->|Prompt for action| C[List/Add/Remove]
        B -->|Prompt for issue key| D[Issue Key]
        B -->|Prompt for file path| E[File Path]
        B -->|Prompt for attachment ID| F[Attachment ID]
        C & D & E & F -->|Manage Attachments| G[Jira API]
        G -->|Attachments Updated| H[Updated Jira Issue]
        H -->|Confirm| B
        B -->|Notify| A

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style F fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style G fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style H fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

issue_transitions = JiraTool(
    name="issue_transitions",
    description="List available transitions for a Jira issue.",
    content="jira issue transitions $issue_key",
    args=[
        Arg(name="issue_key", type="str", description="Issue key (e.g., 'PROJ-123')", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[User] -->|Request to list transitions| B(TeamMate)
        B -->|Prompt for issue key| C[Issue Key]
        C -->|List Transitions| D[Jira API]
        D -->|Transitions List| E[Available Transitions]
        E -->|Display| B
        B -->|Notify| A

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style E fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

for tool in [issue_list, issue_create, issue_edit, issue_assign, issue_move, issue_view, 
             issue_comment_add, issue_link, issue_watch, issue_attachments, issue_transitions]:
    register_jira_tool(tool)