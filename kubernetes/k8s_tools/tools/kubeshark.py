import inspect
from kubiya_sdk.tools import Arg, FileSpec
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry
from ..scripts import kubeshark_capture

# Common requirements for Kubeshark tools
REQUIREMENTS_FILE_CONTENT = """
websocket-client>=1.6.1
pyyaml>=6.0
slack_sdk>=3.19.0
"""

# Base command template for all Kubeshark tools
BASE_KUBESHARK_CMD = """
#!/bin/bash
set -euo pipefail

# Ensure Python output isn't buffered
export PYTHONUNBUFFERED=1

# Setup virtual environment
VENV_PATH="/tmp/venv"
python3 -m venv $VENV_PATH
. $VENV_PATH/bin/activate

# Install requirements
pip install -r /tmp/requirements.txt > /dev/null 2>&1

# Export Slack configuration
export SLACK_API_TOKEN="$(cat /tmp/secrets/SLACK_API_TOKEN 2>/dev/null || echo '')"
export SLACK_CHANNEL_ID="${SLACK_CHANNEL_ID:-}"
export SLACK_THREAD_TS="${SLACK_THREAD_TS:-}"

# Execute the capture script with parameters
python /tmp/scripts/kubeshark_capture.py \\
    --mode "$mode" \\
    --output-dir "/tmp/capture" \\
    $@

# Cleanup
deactivate
rm -rf $VENV_PATH
"""

# Network Traffic Analysis Tools
kubeshark_http_analyzer = KubernetesTool(
    name="analyze_http_traffic",
    description="""
    Analyzes HTTP/HTTPS traffic in the cluster with detailed insights.
    
    Required Configuration:
    - SLACK_API_TOKEN (secret): Slack API token for notifications
    - SLACK_CHANNEL_ID (env): Slack channel ID for updates
    - SLACK_THREAD_TS (env): Optional thread timestamp for replies
    """,
    content=f"{BASE_KUBESHARK_CMD} --filter \"protocol.name == 'http' or protocol.name == 'https'\" --duration \"$duration\"",
    args=[
        Arg(name="duration", type="str", description="Duration in seconds (1-3600)", required=True),
        Arg(name="namespace", type="str", description="Target namespace (optional)", required=False),
    ],
    file_specs=[
        FileSpec(destination="/tmp/scripts/kubeshark_capture.py", content=inspect.getsource(kubeshark_capture)),
        FileSpec(destination="/tmp/requirements.txt", content=REQUIREMENTS_FILE_CONTENT),
    ],
    mermaid="""
    flowchart TD
        A[Start HTTP Analysis] --> B{Check Dependencies}
        B -->|Missing| C[Install Tools]
        B -->|Present| D[Initialize Capture]
        C --> D
        D --> E[Filter HTTP Traffic]
        E --> F[Capture Packets]
        F --> G[Process Data]
        G --> H[Generate Metrics]
        H --> I[Create Report]
        
        subgraph Metrics
        H --> M1[Response Times]
        H --> M2[Status Codes]
        H --> M3[Endpoints]
        H --> M4[Error Rates]
        end
        
        style A fill:#f9f,stroke:#333,stroke-width:2px
        style I fill:#9f9,stroke:#333,stroke-width:2px
    """
)

# Service Mesh Analysis
kubeshark_service_mesh_analyzer = KubernetesTool(
    name="analyze_service_mesh",
    description="Analyzes service mesh traffic patterns and behavior.",
    content=f"{BASE_KUBESHARK_CMD} --mode service-mesh --duration \"$duration\" --namespace \"$namespace\"",
    args=[
        Arg(name="duration", type="str", description="Duration in seconds", required=True),
        Arg(name="namespace", type="str", description="Target namespace", required=True),
    ],
    file_specs=[
        FileSpec(destination="/tmp/scripts/kubeshark_capture.py", content=inspect.getsource(kubeshark_capture)),
        FileSpec(destination="/tmp/requirements.txt", content=REQUIREMENTS_FILE_CONTENT),
    ],
    mermaid="""
    graph TB
        subgraph Mesh Analysis
            A[Service Mesh Traffic] --> B{Traffic Type}
            B -->|Internal| C[Service-to-Service]
            B -->|Ingress| D[External Traffic]
            B -->|Egress| E[Outbound Traffic]
            
            C --> F[Analyze Patterns]
            D --> F
            E --> F
            
            F --> G[Generate Insights]
        end
        
        subgraph Metrics Collection
            G --> M1[Latency]
            G --> M2[Error Rates]
            G --> M3[Circuit Breakers]
            G --> M4[Retry Patterns]
        end
        
        style A fill:#f96,stroke:#333,stroke-width:2px
        style G fill:#96f,stroke:#333,stroke-width:2px
    """
)

# Security Analysis
kubeshark_security_analyzer = KubernetesTool(
    name="analyze_security",
    description="Analyzes traffic for security-related patterns and potential issues.",
    content=f"{BASE_KUBESHARK_CMD} --mode security --duration \"$duration\" --additional-args \"$security_level\"",
    args=[
        Arg(name="duration", type="str", description="Duration in seconds", required=True),
        Arg(name="security_level", type="str", description="Security analysis level (basic/advanced)", required=False, default="basic"),
    ],
    file_specs=[
        FileSpec(destination="/tmp/scripts/kubeshark_capture.py", content=inspect.getsource(kubeshark_capture)),
        FileSpec(destination="/tmp/requirements.txt", content=REQUIREMENTS_FILE_CONTENT),
    ],
    mermaid="""
    sequenceDiagram
        participant T as Traffic Capture
        participant F as Security Filters
        participant A as Analysis Engine
        participant R as Report Generator
        
        T->>F: Raw Traffic
        F->>F: Apply Security Rules
        F->>A: Filtered Traffic
        
        A->>A: Analyze Patterns
        
        loop Security Checks
            A->>A: Check Auth Failures
            A->>A: Detect Anomalies
            A->>A: Scan Headers
            A->>A: Verify TLS
        end
        
        A->>R: Security Findings
        R->>R: Generate Report
        
        Note over T,R: Continuous Monitoring
    """
)

# Performance Analysis
kubeshark_performance_analyzer = KubernetesTool(
    name="analyze_performance",
    description="Analyzes cluster performance metrics and patterns.",
    content=f"{BASE_KUBESHARK_CMD} --mode performance --duration \"$duration\" --threshold \"$threshold\"",
    args=[
        Arg(name="duration", type="str", description="Duration in seconds", required=True),
        Arg(name="threshold", type="str", description="Performance threshold in ms (default: 500)", required=False, default="500"),
    ],
    file_specs=[
        FileSpec(destination="/tmp/scripts/kubeshark_capture.py", content=inspect.getsource(kubeshark_capture)),
        FileSpec(destination="/tmp/requirements.txt", content=REQUIREMENTS_FILE_CONTENT),
    ],
    mermaid="""
    stateDiagram-v2
        [*] --> Capture
        
        state Capture {
            [*] --> CollectMetrics
            CollectMetrics --> ProcessData
            ProcessData --> AnalyzePerformance
        }
        
        state AnalyzePerformance {
            [*] --> ResponseTimes
            [*] --> Throughput
            [*] --> ErrorRates
            [*] --> Latency
        }
        
        Capture --> GenerateReport
        GenerateReport --> [*]
        
        note right of AnalyzePerformance
            Continuous performance
            monitoring and analysis
        end note
    """
)

# API Gateway Analysis
kubeshark_api_gateway_analyzer = KubernetesTool(
    name="analyze_api_gateway",
    description="Analyzes API Gateway traffic and behavior.",
    content=f"{BASE_KUBESHARK_CMD} --mode api-gateway --gateway \"$gateway_name\" --duration \"$duration\"",
    args=[
        Arg(name="gateway_name", type="str", description="API Gateway name", required=True),
        Arg(name="duration", type="str", description="Duration in seconds", required=True),
    ],
    file_specs=[
        FileSpec(destination="/tmp/scripts/kubeshark_capture.py", content=inspect.getsource(kubeshark_capture)),
        FileSpec(destination="/tmp/requirements.txt", content=REQUIREMENTS_FILE_CONTENT),
    ],
    mermaid="""
    graph LR
        A[API Gateway] --> B{Traffic Analysis}
        B --> C[Routes]
        B --> D[Auth]
        B --> E[Rate Limits]
        
        C --> F[Pattern Analysis]
        D --> F
        E --> F
        
        F --> G[Insights]
        G --> H[Reports]
        
        subgraph Metrics
        I[Response Times]
        J[Error Rates]
        K[Usage Patterns]
        end
        
        G --> Metrics
        
        style A fill:#f96,stroke:#333,stroke-width:2px
        style H fill:#96f,stroke:#333,stroke-width:2px
    """
)

# Add comprehensive troubleshooting tool
kubeshark_troubleshoot = KubernetesTool(
    name="troubleshoot_cluster",
    description="""
    Comprehensive cluster troubleshooting using Kubeshark.
    
    Examples:
    1. Basic health check:
       troubleshoot_cluster(mode="health", namespace="default")
    
    2. Performance investigation:
       troubleshoot_cluster(
           mode="performance",
           namespace="production",
           threshold=500,
           duration=600
       )
    
    3. Security audit:
       troubleshoot_cluster(
           mode="security",
           namespace="kube-system",
           security_level="advanced",
           include_tls=true
       )
    """,
    content=f"{BASE_KUBESHARK_CMD} --mode \"$mode\" --namespace \"$namespace\" $EXTRA_ARGS",
    args=[
        Arg(
            name="mode",
            type="str",
            description="""
            Troubleshooting mode:
            - health: Basic cluster health check
            - performance: Performance analysis
            - security: Security audit
            - network: Network connectivity
            - api: API behavior
            - database: Database interactions
            """,
            required=True
        ),
        Arg(
            name="namespace",
            type="str",
            description="Target namespace (use 'all' for all namespaces)",
            required=False,
            default="default"
        ),
        Arg(
            name="duration",
            type="str",
            description="Duration in seconds (default: 300)",
            required=False,
            default="300"
        ),
        Arg(
            name="threshold",
            type="str",
            description="Performance threshold in ms (default: 500)",
            required=False,
            default="500"
        ),
        Arg(
            name="security_level",
            type="str",
            description="""
            Security analysis depth:
            - basic: Common vulnerabilities
            - advanced: Deep security scan
            """,
            required=False,
            default="basic"
        ),
        Arg(
            name="include_tls",
            type="str",
            description="Include TLS/SSL analysis (true/false)",
            required=False,
            default="false"
        ),
        Arg(
            name="labels",
            type="str",
            description="""
            Label selectors for filtering (e.g., 'app=frontend,env=prod')
            Example: 'app=myapp,environment=production'
            """,
            required=False
        ),
        Arg(
            name="extra_filters",
            type="str",
            description="""
            Additional KFL filters.
            Example: 'response.status >= 500 and protocol.name == "http"'
            """,
            required=False
        )
    ],
    mermaid="""
    flowchart TD
        A[Start Troubleshooting] --> B{Select Mode}
        B -->|Health| C[Health Check]
        B -->|Performance| D[Performance Analysis]
        B -->|Security| E[Security Audit]
        B -->|Network| F[Network Analysis]
        B -->|API| G[API Analysis]
        B -->|Database| H[Database Analysis]
        
        subgraph Health Check
            C --> C1[Node Status]
            C --> C2[Pod Health]
            C --> C3[Service Status]
        end
        
        subgraph Performance
            D --> D1[Response Times]
            D --> D2[Resource Usage]
            D --> D3[Bottlenecks]
        end
        
        subgraph Security
            E --> E1[Auth Issues]
            E --> E2[TLS Analysis]
            E --> E3[Vulnerabilities]
        end
        
        style A fill:#f96,stroke:#333,stroke-width:2px
    """
)

# Add real-time monitoring tool
kubeshark_monitor = KubernetesTool(
    name="monitor_cluster",
    description="""
    Real-time cluster monitoring with alerts.
    
    Examples:
    1. Basic monitoring:
       monitor_cluster(duration=3600)
    
    2. Advanced monitoring:
       monitor_cluster(
           duration=7200,
           error_threshold=10,
           latency_threshold=1000,
           alert_interval=300
       )
    """,
    content=f"{BASE_KUBESHARK_CMD} --mode monitor --duration \"$duration\" $MONITOR_ARGS",
    args=[
        Arg(
            name="duration",
            type="str",
            description="Monitoring duration in seconds",
            required=True
        ),
        Arg(
            name="error_threshold",
            type="str",
            description="Error count threshold for alerts (default: 5)",
            required=False,
            default="5"
        ),
        Arg(
            name="latency_threshold",
            type="str",
            description="Latency threshold in ms (default: 1000)",
            required=False,
            default="1000"
        ),
        Arg(
            name="alert_interval",
            type="str",
            description="Alert check interval in seconds (default: 60)",
            required=False,
            default="60"
        ),
        Arg(
            name="namespaces",
            type="str",
            description="""
            Comma-separated list of namespaces to monitor
            Example: 'default,kube-system,production'
            """,
            required=False
        ),
        Arg(
            name="alert_conditions",
            type="str",
            description="""
            Custom alert conditions in KFL
            Example: 'response.status >= 500 or elapsedTime > 2000'
            """,
            required=False
        )
    ],
    mermaid="""
    stateDiagram-v2
        [*] --> Monitoring
        
        state Monitoring {
            [*] --> DataCollection
            DataCollection --> Analysis
            Analysis --> AlertCheck
            AlertCheck --> DataCollection
        }
        
        state AlertCheck {
            [*] --> CheckErrors
            [*] --> CheckLatency
            [*] --> CheckCustom
        }
        
        Monitoring --> [*]: Duration Exceeded
        
        note right of AlertCheck
            Continuous monitoring with
            configurable thresholds
        end note
    """
)

# Add service mesh analyzer
kubeshark_mesh_analyzer = KubernetesTool(
    name="analyze_service_mesh",
    description="""
    Analyze service mesh traffic and patterns.
    
    Examples:
    1. Basic mesh analysis:
       analyze_service_mesh(namespace="default")
    
    2. Detailed mesh analysis:
       analyze_service_mesh(
           namespace="production",
           include_metrics=true,
           trace_requests=true,
           latency_threshold=200
       )
    """,
    content=f"{BASE_KUBESHARK_CMD} --mode mesh --namespace \"$namespace\" $MESH_ARGS",
    args=[
        Arg(
            name="namespace",
            type="str",
            description="Target namespace",
            required=True
        ),
        Arg(
            name="duration",
            type="str",
            description="Analysis duration in seconds (default: 600)",
            required=False,
            default="600"
        ),
        Arg(
            name="include_metrics",
            type="str",
            description="Include detailed metrics collection (true/false)",
            required=False,
            default="true"
        ),
        Arg(
            name="trace_requests",
            type="str",
            description="Enable request tracing (true/false)",
            required=False,
            default="false"
        ),
        Arg(
            name="latency_threshold",
            type="str",
            description="Latency threshold for tracing in ms (default: 200)",
            required=False,
            default="200"
        ),
        Arg(
            name="service_patterns",
            type="str",
            description="""
            Service patterns to analyze
            Example: 'frontend-*,auth-service,api-*'
            """,
            required=False
        )
    ],
    mermaid="""
    graph TB
        subgraph Service Mesh Analysis
            A[Traffic Capture] --> B{Traffic Type}
            B -->|Service-to-Service| C[Internal Traffic]
            B -->|Ingress| D[External Traffic]
            B -->|Egress| E[External Services]
            
            C --> F[Pattern Analysis]
            D --> F
            E --> F
            
            F --> G[Generate Report]
        end
        
        subgraph Metrics
            G --> M1[Service Map]
            G --> M2[Latency Heatmap]
            G --> M3[Error Patterns]
        end
        
        style A fill:#f96,stroke:#333,stroke-width:2px
        style G fill:#96f,stroke:#333,stroke-width:2px
    """
)

# At the bottom of the file, just define the tools list
KUBESHARK_TOOLS = [
    kubeshark_troubleshoot,
    kubeshark_monitor,
    kubeshark_mesh_analyzer,
    kubeshark_http_analyzer,
    kubeshark_service_mesh_analyzer,
    kubeshark_security_analyzer,
    kubeshark_performance_analyzer,
    kubeshark_api_gateway_analyzer,
]