from kubiya_sdk.tools import Arg
from .base import AzureTool, register_azure_tool

storage_account_list = AzureTool(
    name="storage_account_list",
    description="List Azure Storage Accounts",
    content="az storage account list --output json",
    args=[],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List Storage Accounts| B[🤖 TeamMate]
        B --> C[Azure CLI: List Storage Accounts]
        C --> D[Azure API ☁️]
        D --> E[Retrieve Storage Account list]
        E --> F[Format Storage Account information]
        F --> G[User receives Storage Account list 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style E fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style F fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

storage_account_create = AzureTool(
    name="storage_account_create",
    description="Create an Azure Storage Account",
    content="az storage account create --name $name --resource-group $resource_group --location $location --sku $sku",
    args=[
        Arg(name="name", type="str", description="Name of the new storage account", required=True),
        Arg(name="resource_group", type="str", description="Resource group for the new storage account", required=True),
        Arg(name="location", type="str", description="Location for the new storage account", required=True),
        Arg(name="sku", type="str", description="SKU for the new storage account", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Create Storage Account| B[🤖 TeamMate]
        B --> C{{"Storage Account details?" 🗄️}}
        C --> D[User provides details ✍️]
        D --> E[Azure CLI: Create Storage Account]
        E --> F[Azure API ☁️]
        F --> G[Storage Account created 🆕]
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

storage_account_delete = AzureTool(
    name="storage_account_delete",
    description="Delete an Azure Storage Account",
    content="az storage account delete --name $name --resource-group $resource_group --yes",
    args=[
        Arg(name="name", type="str", description="Name of the storage account to delete", required=True),
        Arg(name="resource_group", type="str", description="Resource group of the storage account", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Delete Storage Account| B[🤖 TeamMate]
        B --> C{{"Storage Account details?" 🗄️}}
        C --> D[User provides details ✍️]
        D --> E[Azure CLI: Delete Storage Account]
        E --> F[Azure API ☁️]
        F --> G[Storage Account deleted 🗑️]
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

blob_upload = AzureTool(
    name="blob_upload",
    description="Upload a file to Azure Blob Storage",
    content="az storage blob upload --account-name $account_name --container-name $container_name --name $blob_name --file $file_path",
    args=[
        Arg(name="account_name", type="str", description="Storage account name", required=True),
        Arg(name="container_name", type="str", description="Container name", required=True),
        Arg(name="blob_name", type="str", description="Name for the blob in storage", required=True),
        Arg(name="file_path", type="str", description="Path to the file to upload", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Upload Blob| B[🤖 TeamMate]
        B --> C{{"Blob details?" 📁}}
        C --> D[User provides details ✍️]
        D --> E[Azure CLI: Upload Blob]
        E --> F[Azure API ☁️]
        F --> G[File uploaded to Blob Storage 📤]
        G --> H[User notified of successful upload 📢]

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

for tool in [storage_account_list, storage_account_create, storage_account_delete, blob_upload]:
    register_azure_tool(tool)