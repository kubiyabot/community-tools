from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

# Constants for output limiting
MAX_OUTPUT_LINES = 100
MAX_EVENTS = 25
MAX_LOG_LINES = 1000

# Common function to handle output limiting and filtering
COMMON_FUNCTIONS = '''
# Function to handle output with limits and filtering
show_output() {
    local content="$1"
    local description="$2"
    local max_lines="$3"
    local temp_file=$(mktemp)
    
    echo "$content" > "$temp_file"
    
    # Apply grep filter if provided
    if [ ! -z "$grep_filter" ]; then
        echo "🔍 Filtering $description with: $grep_filter"
        filtered_output=$(cat "$temp_file" | grep -i "$grep_filter" || true)
        if [ -z "$filtered_output" ]; then
            echo "⚠️ No matches found for filter: $grep_filter"
            rm "$temp_file"
            return
        fi
        echo "$filtered_output" > "$temp_file"
        filtered_lines=$(wc -l < "$temp_file")
        echo "Found $filtered_lines matching entries"
    fi
    
    # Show header if present
    if head -n 1 "$temp_file" | grep -q "NAME\\|NAMESPACE\\|STATUS\\|AGE"; then
        head -n 1 "$temp_file"
        tail -n +2 "$temp_file" | head -n "$max_lines"
    else
        head -n "$max_lines" "$temp_file"
    fi
    
    # Show truncation message if needed
    total_lines=$(wc -l < "$temp_file")
    if [ $total_lines -gt "$max_lines" ]; then
        echo ""
        echo "⚠️ Output truncated (showing $max_lines of $total_lines lines)"
        echo "💡 Use grep_filter to narrow down results"
    fi
    
    rm "$temp_file"
}
'''

change_replicas_tool = KubernetesTool(
    name="change_replicas",
    description="Modifies the number of replicas for a specific Kubernetes resource like deployments or statefulsets. Use this to scale up or down a resource.",
    content=f'''
    #!/bin/bash
    set -e

    {COMMON_FUNCTIONS}

    # Check if namespace is provided, exit if not
    if [ -z "$namespace" ]; then
        echo "❌ Namespace must be provided. Please specify a namespace to scale the resource."
        exit 1
    fi

    # Set namespace flag
    namespace_flag="-n $namespace"

    # Attempt to scale the resource
    if kubectl scale "$resource_type/$resource_name" --replicas="$replicas" $namespace_flag; then
        echo "✅ Successfully changed replicas for $resource_type/$resource_name to $replicas in namespace $namespace"
        
        # Show current status
        echo -e "\\n📊 Current Resource Status:"
        status_output=$(kubectl get "$resource_type/$resource_name" $namespace_flag -o wide)
        show_output "$status_output" "resource status" $MAX_OUTPUT_LINES
        
        # Show recent events
        echo -e "\\n📅 Recent Events:"
        events_output=$(kubectl get events $namespace_flag --field-selector "involvedObject.name=$resource_name,involvedObject.kind=$resource_type" --sort-by='.lastTimestamp')
        show_output "$events_output" "events" $MAX_EVENTS
    else
        echo "❌ Failed to change replicas for $resource_type/$resource_name in namespace $namespace"
        exit 1
    fi
    ''',
    args=[
        Arg(name="resource_type", type="str", description="Type of resource (e.g., deployment, statefulset)", required=True),
        Arg(name="resource_name", type="str", description="Name of the resource", required=True),
        Arg(name="replicas", type="int", description="Number of replicas", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=True),
        Arg(name="grep_filter", type="str", description="Optional case-insensitive grep pattern to filter results", required=False),
    ],
)

get_resource_events_tool = KubernetesTool(
    name="get_resource_events",
    description="Fetches the last events for a Kubernetes resource in a specific namespace",
    content=f'''
    #!/bin/bash
    set -e

    {COMMON_FUNCTIONS}

    # Check if namespace is provided, exit if not
    if [ -z "$namespace" ]; then
        echo "❌ Namespace must be provided. Please specify a namespace to fetch resource events."
        exit 1
    fi

    # Set namespace flag
    namespace_flag="-n $namespace"

    # Check if resource exists and fetch events
    if kubectl get "$resource_type" "$resource_name" $namespace_flag > /dev/null 2>&1; then
        echo "📅 Events for $resource_type/$resource_name in namespace $namespace:"
        
        # Get events with sorting and formatting
        events_output=$(kubectl get events $namespace_flag \\
            --field-selector "involvedObject.name=$resource_name,involvedObject.kind=$resource_type" \\
            --sort-by='.lastTimestamp' | \\
            awk '{{
                if (NR==1) print $0;
                else {{
                    type=$7;
                    emoji="ℹ️";
                    if (type == "Warning") emoji="⚠️";
                    else if (type == "Normal") emoji="✅";
                    print "  " emoji " " $0;
                }}
            }}')
        
        show_output "$events_output" "events" $MAX_EVENTS
        
        # Show resource status
        echo -e "\\n📊 Current Resource Status:"
        status_output=$(kubectl get "$resource_type" "$resource_name" $namespace_flag -o wide)
        show_output "$status_output" "resource status" $MAX_OUTPUT_LINES
    else
        echo "❗Error: $resource_type/$resource_name not found in namespace $namespace"
        exit 1
    fi
    ''',
    args=[
        Arg(name="resource_type", type="str", description="Type of resource (e.g., pod, deployment)", required=True),
        Arg(name="resource_name", type="str", description="Name of the resource", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=True),
        Arg(name="grep_filter", type="str", description="Optional case-insensitive grep pattern to filter results", required=False),
    ],
)

get_pod_logs_tool = KubernetesTool(
    name="get_pod_logs",
    description="Fetches logs for a Kubernetes pod with automatic fallback to previous logs if pod not found",
    content=f'''
    #!/bin/bash
    set -e

    {COMMON_FUNCTIONS}

    # Validate required inputs
    if [ -z "$namespace" ] || [ -z "$pod_name" ]; then
        echo "❌ Both namespace and pod_name are required"
        exit 1
    fi

    # Function to get and format logs
    get_logs() {{
        local cmd="$1"
        local log_type="$2"
        local temp_file=$(mktemp)
        
        if eval "$cmd" > "$temp_file" 2>/dev/null; then
            echo "📜 $log_type logs for $pod_name in $namespace:"
            show_output "$(cat "$temp_file")" "$log_type logs" $MAX_LOG_LINES
        else
            echo "❗Error getting $log_type logs: $(cat "$temp_file")"
        fi
        
        rm "$temp_file"
    }}

    # First attempt: Get current logs
    if kubectl get pod -n "$namespace" "$pod_name" >/dev/null 2>&1; then
        # Show pod status first
        echo "📊 Pod Status:"
        status_output=$(kubectl get pod -n "$namespace" "$pod_name" -o wide)
        show_output "$status_output" "pod status" $MAX_OUTPUT_LINES
        
        echo -e "\\n📜 Pod Logs:"
        get_logs "kubectl logs -n '$namespace' '$pod_name'" "current"
    else
        echo "⚠️ Pod '$pod_name' not found, attempting to fetch previous logs..."
        get_logs "kubectl logs -n '$namespace' '$pod_name' --previous" "previous"
    fi
    ''',
    args=[
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=True),
        Arg(name="pod_name", type="str", description="Name of the pod", required=True),
        Arg(name="grep_filter", type="str", description="Optional case-insensitive grep pattern to filter results", required=False),
    ],
)

node_status_tool = KubernetesTool(
    name="node_status",
    description="Lists Kubernetes nodes with their status and emojis",
    content=f'''
    #!/bin/bash
    set -e

    {COMMON_FUNCTIONS}

    echo "🖥️  Node Status:"
    echo "==============="
    
    # Get node status with detailed information
    status_output=$(kubectl get nodes -o custom-columns=NAME:.metadata.name,STATUS:.status.conditions[-1].type,REASON:.status.conditions[-1].reason,CPU:.status.capacity.cpu,MEMORY:.status.capacity.memory | \\
        awk '{{
            if (NR==1) print $0;
            else {{
                status = $2;
                emoji = "❓";
                if (status == "Ready") emoji = "✅";
                else if (status == "NotReady") emoji = "❌";
                else if (status == "SchedulingDisabled") emoji = "🚫";
                print "  " emoji " " $0;
            }}
        }}')
    
    show_output "$status_output" "node status" $MAX_OUTPUT_LINES
    
    # Show node conditions if any node is not ready
    if echo "$status_output" | grep -q "NotReady\\|SchedulingDisabled"; then
        echo -e "\\n⚠️  Node Conditions for Unhealthy Nodes:"
        conditions_output=$(kubectl describe nodes | grep -A5 "Conditions:" | grep -B5 "NotReady=True")
        show_output "$conditions_output" "node conditions" $MAX_OUTPUT_LINES
    fi
    ''',
    args=[
        Arg(name="grep_filter", type="str", description="Optional case-insensitive grep pattern to filter results", required=False),
    ],
)

find_suspicious_errors_tool = KubernetesTool(
    name="find_suspicious_errors",
    description="Finds suspicious errors in a specific Kubernetes namespace or across all namespaces if 'all' is provided.",
    content=f'''
    #!/bin/bash
    set -e

    {COMMON_FUNCTIONS}

    # Namespace is required and either a specific namespace or 'all' for all namespaces
    if [ "$namespace" = "all" ]; then
        echo "🔍 Searching for suspicious errors in all namespaces"
        namespace_flag="--all-namespaces"
    else
        echo "🔍 Searching for suspicious errors in namespace: $namespace"
        namespace_flag="-n $namespace"
    fi

    echo "========================================================="
    
    # Get and format error events
    echo "⚠️  Recent Error Events:"
    error_output=$(kubectl get events $namespace_flag --sort-by=.metadata.creationTimestamp | \\
        grep -E "Error|Failed|CrashLoopBackOff|Evicted|OOMKilled" | \\
        awk '{{
            if ($7 ~ /Error/) emoji = "❌";
            else if ($7 ~ /Failed/) emoji = "💔";
            else if ($7 ~ /CrashLoopBackOff/) emoji = "🔁";
            else if ($7 ~ /Evicted/) emoji = "👉";
            else if ($7 ~ /OOMKilled/) emoji = "💥";
            else emoji = "⚠️";
            print "  " emoji " " $0;
        }}')
    
    show_output "$error_output" "error events" $MAX_EVENTS

    # Get and format problematic pods
    echo -e "\\n⚠️  Pods with non-Running status:"
    pod_output=$(kubectl get pods $namespace_flag --field-selector status.phase!=Running | \\
        awk '{{
            if (NR==1) print $0;
            else {{
                status = $3;
                emoji = "❓";
                if (status == "Pending") emoji = "⏳";
                else if (status == "Succeeded") emoji = "🎉";
                else if (status == "Failed") emoji = "❌";
                else if (status == "Unknown") emoji = "❔";
                print "  " emoji " " $0;
            }}
        }}')
    
    show_output "$pod_output" "problematic pods" $MAX_OUTPUT_LINES
    ''',
    args=[
        Arg(name="namespace", type="str", description="Kubernetes namespace to search for errors. Use 'all' to search in all namespaces.", required=True),
        Arg(name="grep_filter", type="str", description="Optional case-insensitive grep pattern to filter results", required=False),
    ],
)

network_policy_analyzer_tool = KubernetesTool(
    name="network_policy_analyzer",
    description="Advanced network policy analyzer with pagination, output limiting and deep inspection capabilities",
    content="""
    #!/bin/bash
    set -e

    # Constants for output limiting
    MAX_POLICIES_PER_PAGE=10
    MAX_PODS_PER_PAGE=20
    MAX_RULES_PER_POLICY=5
    MAX_TOTAL_OUTPUT=5000
    MAX_OUTPUT_WIDTH=120

    # Function to handle cleanup
    cleanup() {
        rm -f "${temp_files[@]}" 2>/dev/null
        exit "${1:-0}"
    }
    trap 'cleanup $?' EXIT INT TERM

    # Array to track temporary files
    declare -a temp_files
    temp_dir=$(mktemp -d)
    temp_files+=("$temp_dir")

    # Function to create temp file
    create_temp_file() {
        local tmp="${temp_dir}/$(uuidgen || date +%s.%N)"
        temp_files+=("$tmp")
        echo "$tmp"
    }

    # Function to paginate output
    paginate_output() {
        local input_file=$1
        local page=${2:-1}
        local page_size=${3:-$MAX_POLICIES_PER_PAGE}
        local total_lines=$(wc -l < "$input_file")
        local total_pages=$(( (total_lines + page_size - 1) / page_size ))

        # Validate page number
        if [ "$page" -lt 1 ]; then
            page=1
        elif [ "$page" -gt "$total_pages" ]; then
            page=$total_pages
        fi

        # Calculate start and end lines
        local start_line=$(( (page - 1) * page_size + 1 ))
        local end_line=$(( page * page_size ))

        # Show pagination info
        echo "📄 Page $page of $total_pages (Items $start_line-$end_line of $total_lines)"
        echo "------------------------------------------------"

        # Extract and show the page
        sed -n "${start_line},${end_line}p" "$input_file"

        # Show navigation help if more than one page
        if [ "$total_pages" -gt 1 ]; then
            echo -e "\n📌 Use --page N to view different pages"
        fi
    }

    # Function to format network policy
    format_network_policy() {
        local policy_file=$1
        local temp_file=$(create_temp_file)

        jq -r --arg max_rules "$MAX_RULES_PER_POLICY" '
        . | 
        "Policy: \(.metadata.name)\n" +
        "Namespace: \(.metadata.namespace)\n" +
        "Pod Selector: \(.spec.podSelector | tostring)\n" +
        if .spec.policyTypes then "Types: \(.spec.policyTypes | join(", "))\n" else "" end +
        "\nIngress Rules:" + 
        if .spec.ingress then
            (.spec.ingress[0:($max_rules|tonumber)] | map(
                "\n  • From: " + 
                (if .[].from then
                    (.[].from | map(
                        if .namespaceSelector then "\n    - Namespace: \(.namespaceSelector)"
                        elif .podSelector then "\n    - Pod: \(.podSelector)"
                        elif .ipBlock then "\n    - IP Block: \(.ipBlock)"
                        else "\n    - Any"
                        end
                    ) | join(""))
                else "\n    - Any"
                end) +
                if .[].ports then
                    "\n    Ports: " + (.[].ports | map("\(.port)/\(.protocol)") | join(", "))
                else ""
                end
            ) | join("\n")) +
            if (.spec.ingress|length) > ($max_rules|tonumber) then
                "\n  ... \((.spec.ingress|length) - ($max_rules|tonumber)) more rules truncated ..."
            else ""
            end
        else "\n  None"
        end +
        "\n\nEgress Rules:" +
        if .spec.egress then
            (.spec.egress[0:($max_rules|tonumber)] | map(
                "\n  • To: " +
                (if .[].to then
                    (.[].to | map(
                        if .namespaceSelector then "\n    - Namespace: \(.namespaceSelector)"
                        elif .podSelector then "\n    - Pod: \(.podSelector)"
                        elif .ipBlock then "\n    - IP Block: \(.ipBlock)"
                        else "\n    - Any"
                        end
                    ) | join(""))
                else "\n    - Any"
                end) +
                if .[].ports then
                    "\n    Ports: " + (.[].ports | map("\(.port)/\(.protocol)") | join(", "))
                else ""
                end
            ) | join("\n")) +
            if (.spec.egress|length) > ($max_rules|tonumber) then
                "\n  ... \((.spec.egress|length) - ($max_rules|tonumber)) more rules truncated ..."
            else ""
            end
        else "\n  None"
        end' "$policy_file" > "$temp_file"

        # Add emojis and indentation
        sed 's/^Policy: /🔒 Policy: /;
             s/^Namespace: /📁 Namespace: /;
             s/^Pod Selector: /🎯 Pod Selector: /;
             s/^Types: /📋 Types: /;
             s/^Ingress Rules:/📥 Ingress Rules:/;
             s/^Egress Rules:/📤 Egress Rules:/;
             s/^/  /' "$temp_file"
    }

    # Function to analyze pods without policies
    analyze_pods_without_policies() {
        local namespace=${1:-}
        local page=${2:-1}
        local temp_file=$(create_temp_file)
        local ns_flag=""
        [ -n "$namespace" ] && ns_flag="-n $namespace"

        # Get all pods and their labels
        kubectl get pods $ns_flag -o json | jq -r --arg ns "$namespace" '
        .items[] | 
        select(.metadata.namespace as $pod_ns | 
            if $ns then $pod_ns == $ns else true end
        ) |
        {
            name: .metadata.name,
            namespace: .metadata.namespace,
            labels: (.metadata.labels // {}),
            status: .status.phase
        }' > "$temp_file"

        # Get network policies
        local policies_file=$(create_temp_file)
        kubectl get networkpolicies $ns_flag -o json | jq -r '.items[]' > "$policies_file"

        # Process pods and check if they're covered by any policy
        local output_file=$(create_temp_file)
        jq -r --slurpfile policies "$policies_file" '
        . | 
        select(.labels != null) |
        . as $pod |
        if ($policies | map(
            select(.spec.podSelector.matchLabels as $policy_labels |
                ($pod.labels | to_entries | all(
                    . as $label |
                    $policy_labels[$label.key] == $label.value
                ))
            )
        ) | length) == 0 then
            "🔓 Pod: \(.name)\n" +
            "  📁 Namespace: \(.namespace)\n" +
            "  🏷️  Labels: \(.labels | to_entries | map("\(.key)=\(.value)") | join(", "))\n" +
            "  📊 Status: \(.status)\n"
        else empty end
        ' "$temp_file" > "$output_file"

        # Show statistics
        local total_pods=$(jq -r '. | length' "$temp_file")
        local unprotected_pods=$(grep -c "🔓 Pod:" "$output_file" || echo 0)
        local protected_pods=$(( total_pods - unprotected_pods ))
        
        echo "📊 Network Policy Coverage:"
        echo "========================="
        echo "  ✅ Protected Pods: $protected_pods"
        echo "  ⚠️  Unprotected Pods: $unprotected_pods"
        echo "  📈 Coverage: $(( (protected_pods * 100) / total_pods ))%"
        echo

        if [ "$unprotected_pods" -gt 0 ]; then
            echo "🔍 Pods Without Network Policies:"
            echo "=============================="
            paginate_output "$output_file" "$page" "$MAX_PODS_PER_PAGE"
        else
            echo "✅ All pods are covered by network policies"
        fi
    }

    # Set namespace flag if provided
    namespace_flag=""
    [ -n "${namespace:-}" ] && namespace_flag="-n $namespace"

    # Get network policies
    echo "🔍 Analyzing Network Policies"
    echo "=========================="
    
    # Create temporary files for policies
    policies_file=$(create_temp_file)
    formatted_policies=$(create_temp_file)

    # Get and process policies
    if [ -n "$namespace" ]; then
        kubectl get networkpolicies -n "$namespace" -o json > "$policies_file"
    else
        kubectl get networkpolicies --all-namespaces -o json > "$policies_file"
    fi

    # Format each policy
    jq -r '.items[]' "$policies_file" | while read -r policy; do
        echo "$policy" | format_network_policy "$(create_temp_file)"
        echo
    done > "$formatted_policies"

    # Show policies with pagination
    if [ -s "$formatted_policies" ]; then
        paginate_output "$formatted_policies" "${page:-1}" "$MAX_POLICIES_PER_PAGE"
    else
        echo "⚠️  No network policies found"
    fi

    echo -e "\n🔍 Analyzing Pods Without Network Policies"
    echo "======================================="
    analyze_pods_without_policies "${namespace:-}" "${page:-1}"
    """,
    args=[
        Arg(
            name="namespace",
            type="str",
            description="Kubernetes namespace to analyze. If omitted, analyzes all namespaces.",
            required=False
        ),
        Arg(
            name="page",
            type="int",
            description="Page number for paginated output",
            required=False
        )
    ]
)

persistent_volume_usage_tool = KubernetesTool(
    name="persistent_volume_usage",
    description="Shows usage of persistent volumes in the cluster",
    content="""
    #!/bin/bash
    set -e
    echo "Persistent Volume Usage:"
    echo "========================"
    kubectl get pv -o custom-columns=NAME:.metadata.name,CAPACITY:.spec.capacity.storage,USED:.status.capacity.storage,STATUS:.status.phase,CLAIM:.spec.claimRef.name,NAMESPACE:.spec.claimRef.namespace
    """,
    args=[],
)

ingress_analyzer_tool = KubernetesTool(
    name="ingress_analyzer",
    description="Analyzes ingress resources in the cluster",
    content="""
    #!/bin/bash
    set -e
    echo "Ingress Analysis:"
    echo "================="
    kubectl get ingress --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,HOSTS:.spec.rules[*].host,PATHS:.spec.rules[*].http.paths[*].path,SERVICES:.spec.rules[*].http.paths[*].backend.service.name
    """,
    args=[],
)

resource_quota_usage_tool = KubernetesTool(
    name="resource_quota_usage",
    description="Shows resource quota usage across namespaces",
    content="""
    #!/bin/bash
    set -e
    echo "Resource Quota Usage:"
    echo "====================="
    kubectl get resourcequota --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,RESOURCE:.spec.hard,USED:.status.used
    """,
    args=[],
)

cluster_autoscaler_status_tool = KubernetesTool(
    name="cluster_autoscaler_status",
    description="Checks the status of the cluster autoscaler",
    content="""
    #!/bin/bash
    set -e
    echo "Cluster Autoscaler Status:"
    echo "=========================="
    kubectl get deployments -n kube-system | grep cluster-autoscaler
    echo "\nCluster Autoscaler Logs:"
    kubectl logs -n kube-system -l app=cluster-autoscaler --tail=50
    """,
    args=[],
)

pod_disruption_budget_checker_tool = KubernetesTool(
    name="pod_disruption_budget_checker",
    description="Checks Pod Disruption Budgets (PDBs) in the cluster, across all namespaces or filtered by a specific namespace.",
    content="""
    #!/bin/bash
    set -e

    # Set namespace flag if provided, or default to all namespaces
    namespace_flag=${namespace:---all-namespaces}

    echo "Pod Disruption Budgets:"
    echo "======================="
    
    if ! kubectl get pdb $namespace_flag -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,MIN-AVAILABLE:.spec.minAvailable,MAX-UNAVAILABLE:.spec.maxUnavailable,ALLOWED-DISRUPTIONS:.status.disruptionsAllowed; then
        echo "❌ Error: Failed to retrieve Pod Disruption Budgets. Please check permissions and kubectl availability."
        exit 1
    fi
    """,
    args=[
        Arg(
            name="namespace",
            type="str",
            description="Kubernetes namespace to filter results. If omitted, checks all namespaces.",
            required=False,
        ),
    ],
)

check_replicas_tool = KubernetesTool(
    name="check_replicas",
    description="Retrieves the current number of replicas for a specific Kubernetes deployment or statefulset. Requires specifying a namespace.",
    content="""
    #!/bin/bash
    set -e

    # Check if namespace is provided
    if [ -z "$namespace" ]; then
        echo "❌ Error: Namespace is required for checking replicas of $resource_type/$resource_name."
        exit 1
    fi

    # Set namespace flag
    namespace_flag="-n $namespace"

    # Get the number of replicas
    replicas=$(kubectl get $resource_type $resource_name $namespace_flag -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "NotFound")

    if [ "$replicas" = "NotFound" ]; then
        echo "❗Error: $resource_type/$resource_name not found in namespace $namespace."
    else
        echo "Current number of replicas for $resource_type/$resource_name: $replicas"
    fi
    """,
    args=[
        Arg(
            name="resource_type",
            type="str",
            description="Type of resource (e.g., deployment, statefulset)",
            required=True,
        ),
        Arg(
            name="resource_name",
            type="str",
            description="Name of the resource",
            required=True,
        ),
        Arg(
            name="namespace",
            type="str",
            description="Kubernetes namespace",
            required=True,
        ),
    ],
)

# Register all tools
for tool in [
    change_replicas_tool,
    get_resource_events_tool,
    get_pod_logs_tool,
    node_status_tool,
    find_suspicious_errors_tool,
    network_policy_analyzer_tool,
    persistent_volume_usage_tool,
    ingress_analyzer_tool,
    resource_quota_usage_tool,
    cluster_autoscaler_status_tool,
    pod_disruption_budget_checker_tool,
    check_replicas_tool,
]:
    tool_registry.register("kubernetes", tool)
