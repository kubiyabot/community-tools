from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from databricks_tools.tools.api.base import DatabricksApiTool

# Unity Catalog Operations
list_catalogs_tool = DatabricksApiTool(
    name="list-unity-catalogs",
    description="List all Unity Catalogs in the workspace with detailed metadata",
    mermaid="""
    flowchart TD
        W[Workspace 🏢] --> C1[production_catalog 📚]
        W --> C2[analytics_catalog 📊]
        W --> C3[ml_features_catalog 🤖]
        
        C1 --> |Owner|O1[data_platform_admin 👤]
        C1 --> |Contains|T1[156 Tables 📑]
        
        C2 --> |Owner|O2[analytics_team 👥]
        C2 --> |Contains|T2[89 Tables 📑]
        
        C3 --> |Owner|O3[ml_platform_team 👥]
        C3 --> |Contains|T3[45 Tables 📑]

        style W fill:#f9f,stroke:#333,stroke-width:4px
        style C1 fill:#bbf,stroke:#333,stroke-width:2px
        style C2 fill:#bbf,stroke:#333,stroke-width:2px
        style C3 fill:#bbf,stroke:#333,stroke-width:2px
    """,
    content="""
        echo "🔍 Fetching Unity Catalogs..."
        sleep 2
        echo "📚 Found catalogs:"
        echo "├─ production_catalog"
        echo "│  └─ Owner: data_platform_admin"
        echo "│  └─ Tables: 156"
        echo "│  └─ Last Modified: 2024-03-15"
        echo "├─ analytics_catalog"
        echo "│  └─ Owner: analytics_team"
        echo "│  └─ Tables: 89"
        echo "│  └─ Last Modified: 2024-03-14"
        echo "└─ ml_features_catalog"
        echo "   └─ Owner: ml_platform_team"
        echo "   └─ Tables: 45"
        echo "   └─ Last Modified: 2024-03-13"
        echo "✨ Total catalogs found: 3"
    """,
    args=[],
    env=[],
    secrets=[]
)

create_schema_tool = DatabricksApiTool(
    name="create-schema",
    description="Create a new schema in Unity Catalog",
    mermaid="""
    sequenceDiagram
        participant U as User 👤
        participant C as Catalog 📚
        participant S as Schema 📁
        participant P as Permissions 🔐

        U->>+C: Request Schema Creation
        C->>+S: Initialize Schema
        S->>+P: Set Default Permissions
        P-->>-S: Permissions Set ✅
        S-->>-C: Schema Created
        C-->>-U: Success Response 🎉

        Note over U,P: Schema created with<br/>default permissions
    """,
    content="""
        echo "📁 Creating new schema '$schema_name' in catalog '$catalog_name'..."
        sleep 1
        echo "✅ Schema created successfully!"
        echo "📊 Schema Details:"
        echo "   • Full path: $catalog_name.$schema_name"
        echo "   • Owner: Shaked Askayo"
        echo "   • Created: $(date '+%Y-%m-%d %H:%M:%S')"
    """,
    args=[
        Arg(name="catalog_name", description="Name of the catalog", required=True),
        Arg(name="schema_name", description="Name of the schema to create", required=True),
    ],
    env=[],
    secrets=[]
)

create_cluster_tool = DatabricksApiTool(
    name="create-cluster",
    description="Create a new Databricks cluster with specified configuration",
    mermaid="""
    sequenceDiagram
        participant U as User 👤
        participant API as Databricks API 🔌
        participant C as Cluster Manager 🎛️
        participant R as Resources 💻

        U->>+API: Create Cluster Request 🚀
        Note over U,API: Specify name, workers, runtime
        
        API->>+C: Initialize Cluster 🔄
        C->>+R: Allocate Resources
        
        R-->>-C: Resources Ready ✅
        
        C->>C: Configure Runtime 📦
        Note over C: Install Dependencies
        
        C-->>-API: Cluster ID Generated
        API-->>-U: Success Response 🎉
        
        Note over U,R: Cluster starts in PENDING state
    """,
    content="""
        echo "🚀 Creating new Databricks cluster..."
        echo "⚙️ Configuring cluster with:"
        echo "   • Name: $cluster_name"
        echo "   • Workers: $num_workers"
        echo "   • Runtime: $runtime_version"
        sleep 2
        echo "📡 Initializing cluster resources..."
        sleep 1
        CLUSTER_ID="0314-$(printf '%04x%04x' $RANDOM $RANDOM)-test"
        echo "✅ Cluster created successfully!"
        echo "🔑 Cluster ID: $CLUSTER_ID"
        echo "🌐 Status: PENDING"
        echo "⏳ The cluster will be ready in approximately 5-7 minutes"
    """,
    args=[
        Arg(name="cluster_name", description="Name of the cluster", required=True),
        Arg(name="num_workers", description="Number of worker nodes", required=True),
        Arg(name="runtime_version", description="DBR version (e.g., 13.3.x-scala2.12)", required=True),
    ],
    env=[],
    secrets=[]
)

terminate_cluster_tool = DatabricksApiTool(
    name="terminate-cluster",
    description="Terminate a running Databricks cluster",
    mermaid="""
    sequenceDiagram
        participant U as User 👤
        participant API as API 🔌
        participant C as Cluster 💻
        participant R as Resources ♻️

        U->>+API: Terminate Request 🛑
        API->>+C: Stop All Jobs
        C->>C: Save State 💾
        C->>+R: Release Resources
        R-->>-C: Resources Released
        C-->>-API: Cleanup Complete
        API-->>-U: Cluster Terminated ✅

        Note over U,R: Resources are released<br/>back to the pool
    """,
    content="""
        echo "🛑 Terminating cluster '$cluster_id'..."
        sleep 2
        echo "✅ Cluster termination initiated"
        echo "⏳ Cleanup in progress:"
        echo "   • Stopping running jobs"
        sleep 1
        echo "   • Saving notebook states"
        sleep 1
        echo "   • Releasing compute resources"
        sleep 1
        echo "🏁 Cluster terminated successfully"
    """,
    args=[
        Arg(name="cluster_id", description="ID of the cluster to terminate", required=True)
    ],
    env=[],
    secrets=[]
)

submit_job_tool = DatabricksApiTool(
    name="submit-notebook-job",
    description="Submit a notebook job to Databricks workspace",
    mermaid="""
    stateDiagram-v2
        [*] --> SUBMITTED: Submit Job 📝
        SUBMITTED --> QUEUED: Process Request
        QUEUED --> RUNNING: Start Execution 🚀
        
        RUNNING --> SUCCEEDED: Complete Successfully ✅
        RUNNING --> FAILED: Error Occurs ❌
        RUNNING --> CANCELED: User Cancels 🛑
        
        SUCCEEDED --> [*]
        FAILED --> [*]
        CANCELED --> [*]

        note right of RUNNING
            Job execution on
            specified cluster
        end note
    """,
    content="""
        echo "📝 Preparing to submit notebook job..."
        echo "📋 Job configuration:"
        echo "   • Notebook: $notebook_path"
        echo "   • Cluster: $cluster_name"
        sleep 1
        JOB_ID=$((RANDOM % 90000 + 10000))
        RUN_ID=$((RANDOM % 900000 + 100000))
        echo "🚀 Submitting job..."
        sleep 2
        echo "✅ Job submitted successfully!"
        echo "📊 Job Details:"
        echo "   • Job ID: $JOB_ID"
        echo "   • Run ID: $RUN_ID"
        echo "   • Status: RUNNING"
        echo "   • Web URL: https://kubiya-awesome-workspace.cloud.databricks.com/?o=12345#job/$JOB_ID/run/$RUN_ID"
    """,
    args=[
        Arg(name="notebook_path", description="Path to the notebook in workspace", required=True),
        Arg(name="cluster_name", description="Name of the cluster to run on", required=True),
    ],
    env=[],
    secrets=[]
)

cancel_job_run_tool = DatabricksApiTool(
    name="cancel-job-run",
    description="Cancel a running job",
    mermaid="""
    sequenceDiagram
        participant U as User 👤
        participant J as Job Manager 📋
        participant C as Cluster 🖥️
        participant S as Storage 💾

        U->>+J: Cancel Job Request ⛔
        J->>+C: Stop Execution
        C->>S: Save Current State
        S-->>C: State Saved
        C-->>-J: Execution Stopped
        J-->>-U: Job Canceled ✅

        Note over U,S: Job state is preserved<br/>for debugging
    """,
    content="""
        echo "🛑 Canceling job run '$run_id'..."
        sleep 1
        echo "✅ Job run canceled"
        echo "📊 Final Status:"
        echo "   • State: CANCELED"
        echo "   • End Time: $(date '+%Y-%m-%d %H:%M:%S')"
    """,
    args=[
        Arg(name="run_id", description="ID of the job run to cancel", required=True)
    ],
    env=[],
    secrets=[]
)

list_notebooks_tool = DatabricksApiTool(
    name="list-workspace-notebooks",
    description="List all notebooks in a specified workspace path",
    mermaid="""
    flowchart TD
        W[Workspace Root 📂] --> D1[Data Pipeline]
        W --> D2[ML Models]
        W --> D3[Analytics]
        
        D1 --> N1[data_ingestion.py]
        D1 --> N2[feature_engineering.py]
        
        D2 --> N3[model_training.ipynb]
        D2 --> N4[evaluation.py]
        
        D3 --> N5[dashboards.py]
        
        style W fill:#f96,stroke:#333,stroke-width:4px
        style D1 fill:#bbf,stroke:#333
        style D2 fill:#bbf,stroke:#333
        style D3 fill:#bbf,stroke:#333
    """,
    content="""
        echo "🔍 Scanning workspace path: $workspace_path"
        sleep 1
        echo "📚 Found notebooks:"
        echo "├─ 📓 data_ingestion.py"
        echo "│  └─ Last modified: $(date -d "@$(($(date +%s) - RANDOM % 864000))" "+%Y-%m-%d %H:%M")"
        echo "├─ 📓 feature_engineering.py"
        echo "│  └─ Last modified: $(date -d "@$(($(date +%s) - RANDOM % 864000))" "+%Y-%m-%d %H:%M")"
        echo "├─ 📓 model_training.ipynb"
        echo "│  └─ Last modified: $(date -d "@$(($(date +%s) - RANDOM % 864000))" "+%Y-%m-%d %H:%M")"
        echo "└─ 📓 deployment_pipeline.py"
        echo "   └─ Last modified: $(date -d "@$(($(date +%s) - RANDOM % 864000))" "+%Y-%m-%d %H:%M")"
        echo "✨ Total notebooks: 4"
    """,
    args=[
        Arg(name="workspace_path", description="Path in the workspace to list notebooks from", required=True),
    ],
    env=[],
    secrets=[]
)

import_notebook_tool = DatabricksApiTool(
    name="import-notebook",
    description="Import a notebook into the workspace",
    mermaid="""
    sequenceDiagram
        participant U as User 👤
        participant W as Workspace 📂
        participant C as Converter 🔄
        participant S as Storage 💾

        U->>+W: Import Request 📤
        W->>+C: Convert Format
        C-->>-W: Format Converted
        W->>+S: Save Notebook
        S-->>-W: Save Complete
        W-->>-U: Import Success ✅

        Note over U,S: Supports Jupyter, HTML,<br/>and Source formats
    """,
    content="""
        echo "📥 Importing notebook..."
        echo "📋 Details:"
        echo "   • Source: $source_path"
        echo "   • Destination: $workspace_path"
        echo "   • Format: $format"
        sleep 2
        echo "✅ Notebook imported successfully!"
        echo "🔗 Access at: https://kubiya-awesome-workspace.cloud.databricks.com/?o=12345#notebook/$workspace_path"
    """,
    args=[
        Arg(name="source_path", description="Path to source notebook file", required=True),
        Arg(name="workspace_path", description="Destination path in workspace", required=True),
        Arg(name="format", description="Notebook format (JUPYTER, SOURCE, HTML)", required=True)
    ],
    env=[],
    secrets=[]
)

list_mlflow_experiments_tool = DatabricksApiTool(
    name="list-mlflow-experiments",
    description="List MLflow experiments and their recent runs",
    mermaid="""
    flowchart LR
        MLF[MLflow Tracking 📊] --> E1[Customer Churn]
        MLF --> E2[Fraud Detection]
        MLF --> E3[Recommendation Engine]
        
        E1 --> M1[Accuracy: 0.89]
        E1 --> R1[15 Runs]
        
        E2 --> M2[F1-Score: 0.95]
        E2 --> R2[23 Runs]
        
        E3 --> M3[NDCG: 0.76]
        E3 --> R3[8 Runs]
        
        style MLF fill:#f96,stroke:#333,stroke-width:4px
        style E1 fill:#bbf,stroke:#333
        style E2 fill:#bbf,stroke:#333
        style E3 fill:#bbf,stroke:#333
    """,
    content="""
        echo "🔬 Fetching MLflow experiments..."
        sleep 1
        echo "📊 Active experiments:"
echo "├─ 🧪 /Users/data_science/customer_churn"
        echo "│  ├─ Recent runs: 15"
        echo "│  ├─ Best metric (accuracy): 0.89"
        echo "│  └─ Last run: $(date -d "@$(($(date +%s) - RANDOM % 86400))" "+%Y-%m-%d %H:%M")"
        echo "├─ 🧪 /Users/data_science/fraud_detection"
        echo "│  ├─ Recent runs: 23"
        echo "│  ├─ Best metric (f1-score): 0.95"
        echo "│  └─ Last run: $(date -d "@$(($(date +%s) - RANDOM % 86400))" "+%Y-%m-%d %H:%M")"
        echo "└─ 🧪 /Users/data_science/recommendation_engine"
        echo "   ├─ Recent runs: 8"
        echo "   ├─ Best metric (ndcg): 0.76"
        echo "   └─ Last run: $(date -d "@$(($(date +%s) - RANDOM % 86400))" "+%Y-%m-%d %H:%M")"
        echo "✨ Total experiments: 3"
    """,
    args=[],
    env=[],
    secrets=[]
)

register_model_tool = DatabricksApiTool(
    name="register-mlflow-model",
    description="Register an MLflow model in the Model Registry",
    mermaid="""
    sequenceDiagram
        participant U as User 👤
        participant R as Registry 📦
        participant V as Version Control 🔄
        participant S as Storage 💾

        U->>+R: Register Model Request
        R->>+V: Create New Version
        V->>+S: Store Model Artifacts
        S-->>-V: Storage Complete
        V-->>-R: Version Created
        R-->>-U: Model Registered ✅

        Note over U,S: Model versioning and<br/>artifact storage handled
    """,
    content="""
        echo "📦 Registering model '$model_name'..."
        echo "📋 Model details:"
        echo "   • Run ID: $run_id"
        echo "   • Model path: $model_path"
        sleep 2
        echo "✅ Model registered successfully!"
        echo "📊 Registration details:"
        echo "   • Name: $model_name"
        echo "   • Version: 1"
        echo "   • Status: PENDING_REGISTRATION"
        echo "   • Registered by: $CURRENT_USER"
    """,
    args=[
        Arg(name="model_name", description="Name for the registered model", required=True),
        Arg(name="run_id", description="MLflow run ID containing the model", required=True),
        Arg(name="model_path", description="Path to the model in the run", required=True)
    ],
    env=[],
    secrets=[]
)

create_secret_scope_tool = DatabricksApiTool(
    name="create-secret-scope",
    description="Create a new secret scope",
    mermaid="""
    flowchart TD
        U[User 👤] --> S[Secret Scope Creation]
        S --> P[Permission Setup]
        S --> E[Encryption Setup]
        
        P --> A[Access Control]
        E --> K[Key Vault]
        
        A --> G[Group Permissions]
        A --> I[Individual Permissions]
        
        style U fill:#f96,stroke:#333,stroke-width:4px
        style S fill:#bbf,stroke:#333,stroke-width:2px
        style K fill:#ada,stroke:#333
    """,
    content="""
        echo "🔒 Creating new secret scope '$scope_name'..."
        sleep 1
        echo "✅ Secret scope created successfully!"
        echo "📋 Scope details:"
        echo "   • Name: $scope_name"
        echo "   • Backend type: DATABRICKS"
        echo "   • Created: $(date '+%Y-%m-%d %H:%M:%S')"
    """,
    args=[
        Arg(name="scope_name", description="Name of the secret scope", required=True)
    ],
    env=[],
    secrets=[]
)

optimize_table_tool = DatabricksApiTool(
    name="optimize-delta-table",
    description="Optimize a Delta table and manage its history",
    mermaid="""
    sequenceDiagram
        participant U as User 👤
        participant D as Delta Table 📊
        participant O as Optimizer 🔄
        participant C as Cleaner 🧹

        U->>+D: Optimize Request
        D->>+O: Begin Optimization
        O->>O: Compact Files
        O->>O: Z-Order Data
        O-->>-D: Optimization Complete
        D->>+C: Clean History
        C-->>-D: History Cleaned
        D-->>-U: Process Complete ✅

        Note over U,C: Optimizes storage and<br/>query performance
    """,
    content="""
        echo "🔄 Optimizing Delta table '$table_name'..."
        echo "📋 Operation details:"
        echo "   • Z-ORDER columns: $zorder_columns"
        echo "   • Retention hours: $retention_hours"
        sleep 2
        echo "✅ Table optimization complete!"
        echo "📊 Results:"
        echo "   • Files compacted: 245"
        echo "   • Space reclaimed: 1.2GB"
        echo "   • History cleaned up: $(date -d "@$(($(date +%s) - retention_hours*3600))" "+%Y-%m-%d %H:%M") and older"
    """,
    args=[
        Arg(name="table_name", description="Full name of the Delta table", required=True),
        Arg(name="zorder_columns", description="Columns to Z-ORDER by (comma-separated)", required=True),
        Arg(name="retention_hours", description="History retention in hours", required=True)
    ],
    env=[],
    secrets=[]
)

# Register all tools in a list for easy access
databricks_tools = [
    list_catalogs_tool,
    create_schema_tool,
    create_cluster_tool,
    terminate_cluster_tool,
    submit_job_tool,
    cancel_job_run_tool,
    list_notebooks_tool,
    import_notebook_tool,
    list_mlflow_experiments_tool,
    register_model_tool,
    create_secret_scope_tool,
    optimize_table_tool,
]

# Register all tools with the registry
for tool in databricks_tools:
    tool_registry.register("databricks", tool)
