from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from databricks_tools.tools.api.base import DatabricksApiTool

# Unity Catalog Operations
list_catalogs_tool = DatabricksApiTool(
    name="list-unity-catalogs",
    description="List all Unity Catalogs in the workspace with detailed metadata",
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

# Cluster Operations
create_cluster_tool = DatabricksApiTool(
    name="create-cluster",
    description="Create a new Databricks cluster with specified configuration",
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

# Job Operations
submit_job_tool = DatabricksApiTool(
    name="submit-notebook-job",
    description="Submit a notebook job to Databricks workspace",
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

# Workspace Operations
list_notebooks_tool = DatabricksApiTool(
    name="list-workspace-notebooks",
    description="List all notebooks in a specified workspace path",
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

# MLflow Operations
list_mlflow_experiments_tool = DatabricksApiTool(
    name="list-mlflow-experiments",
    description="List MLflow experiments and their recent runs",
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

# Secrets Management
create_secret_scope_tool = DatabricksApiTool(
    name="create-secret-scope",
    description="Create a new secret scope",
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

# Delta Lake Operations
optimize_table_tool = DatabricksApiTool(
    name="optimize-delta-table",
    description="Optimize a Delta table and manage its history",
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

for tool in databricks_tools:
    tool_registry.register("databricks", tool)
