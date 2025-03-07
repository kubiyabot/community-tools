from kubiya_sdk.tools import Arg
from .base import AzureTool, register_azure_tool

vm_list = AzureTool(
    name="vm_list",
    description="List Azure Virtual Machines",
    content="az vm list --output json",
    args=[],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List VMs| B[🤖 TeamMate]
        B --> C[Azure CLI: List VMs]
        C --> D[Azure API ☁️]
        D --> E[Retrieve VM list]
        E --> F[Format VM information]
        F --> G[User receives VM list 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style E fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style F fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

vm_start = AzureTool(
    name="vm_start",
    description="Start an Azure Virtual Machine",
    content="az vm start --name $vm_name --resource-group $resource_group",
    args=[
        Arg(name="vm_name", type="str", description="Name of the VM to start", required=True),
        Arg(name="resource_group", type="str", description="Resource group of the VM", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Start VM| B[🤖 TeamMate]
        B --> C{{"VM name and resource group?" 🖥️}}
        C --> D[User provides details ✍️]
        D --> E[Azure CLI: Start VM]
        E --> F[Azure API ☁️]
        F --> G[VM started 🚀]
        G --> H[User notified of successful start 📢]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style H fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

vm_stop = AzureTool(
    name="vm_stop",
    description="Stop an Azure Virtual Machine",
    content="az vm stop --name $vm_name --resource-group $resource_group",
    args=[
        Arg(name="vm_name", type="str", description="Name of the VM to stop", required=True),
        Arg(name="resource_group", type="str", description="Resource group of the VM", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Stop VM| B[🤖 TeamMate]
        B --> C{{"VM name and resource group?" 🖥️}}
        C --> D[User provides details ✍️]
        D --> E[Azure CLI: Stop VM]
        E --> F[Azure API ☁️]
        F --> G[VM stopped 🛑]
        G --> H[User notified of successful stop 📢]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style H fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

vm_create = AzureTool(
    name="vm_create",
    description="Create a new Azure Virtual Machine",
    content="az vm create --resource-group $resource_group --name $vm_name --image $image --admin-username $admin_username --generate-ssh-keys",
    args=[
        Arg(name="resource_group", type="str", description="Resource group for the new VM", required=True),
        Arg(name="vm_name", type="str", description="Name of the new VM", required=True),
        Arg(name="image", type="str", description="VM image to use", required=True),
        Arg(name="admin_username", type="str", description="Admin username for the VM", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Create VM| B[🤖 TeamMate]
        B --> C{{"VM details?" 🖥️}}
        C --> D[User provides details ✍️]
        D --> E[Azure CLI: Create VM]
        E --> F[Azure API ☁️]
        F --> G[VM created 🆕]
        G --> H[User notified of successful creation 📢]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style H fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

vm_delete = AzureTool(
    name="vm_delete",
    description="Delete an Azure Virtual Machine",
    content="az vm delete --name $vm_name --resource-group $resource_group --yes",
    args=[
        Arg(name="vm_name", type="str", description="Name of the VM to delete", required=True),
        Arg(name="resource_group", type="str", description="Resource group of the VM", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Delete VM| B[🤖 TeamMate]
        B --> C{{"VM name and resource group?" 🖥️}}
        C --> D[User provides details ✍️]
        D --> E[Azure CLI: Delete VM]
        E --> F[Azure API ☁️]
        F --> G[VM deleted 🗑️]
        G --> H[User notified of successful deletion 📢]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style H fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

vm_resize = AzureTool(
    name="vm_resize",
    description="Resize an Azure Virtual Machine",
    content="az vm resize --resource-group $resource_group --name $vm_name --size $new_size",
    args=[
        Arg(name="resource_group", type="str", description="Resource group of the VM", required=True),
        Arg(name="vm_name", type="str", description="Name of the VM to resize", required=True),
        Arg(name="new_size", type="str", description="New size for the VM (e.g., Standard_DS3_v2)", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Resize VM| B[🤖 TeamMate]
        B --> C{{"VM details and new size?" 🖥️}}
        C --> D[User provides details ✍️]
        D --> E[Azure CLI: Resize VM]
        E --> F[Azure API ☁️]
        F --> G[VM resized 🔄]
        G --> H[User notified of successful resize 📢]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style H fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

vm_restart = AzureTool(
    name="vm_restart",
    description="Restart an Azure Virtual Machine",
    content="az vm restart --resource-group $resource_group --name $vm_name",
    args=[
        Arg(name="resource_group", type="str", description="Resource group of the VM", required=True),
        Arg(name="vm_name", type="str", description="Name of the VM to restart", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Restart VM| B[🤖 TeamMate]
        B --> C{{"VM details?" 🖥️}}
        C --> D[User provides details ✍️]
        D --> E[Azure CLI: Restart VM]
        E --> F[Azure API ☁️]
        F --> G[VM restarted 🔄]
        G --> H[User notified of successful restart 📢]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style H fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

vm_show = AzureTool(
    name="vm_show",
    description="Show details of an Azure Virtual Machine",
    content="az vm show --resource-group $resource_group --name $vm_name",
    args=[
        Arg(name="resource_group", type="str", description="Resource group of the VM", required=True),
        Arg(name="vm_name", type="str", description="Name of the VM to show details", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Show VM details| B[🤖 TeamMate]
        B --> C{{"VM details?" 🖥️}}
        C --> D[User provides details ✍️]
        D --> E[Azure CLI: Show VM]
        E --> F[Azure API ☁️]
        F --> G[VM details retrieved 📋]
        G --> H[User receives VM information 📢]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style H fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

for tool in [vm_list, vm_start, vm_stop, vm_create, vm_delete, vm_resize, vm_restart, vm_show]:
    register_azure_tool(tool)