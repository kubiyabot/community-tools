from kubiya_workflow_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_workflow_sdk.tools.registry import tool_registry

manifest_apply_tool = KubernetesTool(
    name="manifest_apply",
    description="Apply Kubernetes manifests from various sources (URL, file, directory) with validation and dry-run support",
    content='''
    #!/bin/bash
    set -e

    # Function to validate YAML
    validate_yaml() {
        local file="$1"
        if ! kubectl apply --dry-run=client -f "$file" > /dev/null 2>&1; then
            echo "❌ YAML validation failed for $file"
            return 1
        fi
        return 0
    }

    # Function to download from URL
    download_manifest() {
        local url="$1"
        local tmp_file=$(mktemp)
        if curl -sSL "$url" -o "$tmp_file"; then
            echo "$tmp_file"
        else
            echo ""
            return 1
        fi
    }

    # Main execution
    {
        # Handle different source types
        if [ -n "${url:-}" ]; then
            echo "🌐 Downloading manifest from URL: $url"
            manifest_file=$(download_manifest "$url")
            if [ -z "$manifest_file" ]; then
                echo "❌ Failed to download manifest from URL"
                exit 1
            fi
            source_type="url"
        elif [ -n "${file:-}" ]; then
            manifest_file="$file"
            source_type="file"
        elif [ -n "${directory:-}" ]; then
            manifest_file="$directory"
            source_type="directory"
        else
            echo "❌ No source specified. Provide either url, file, or directory."
            exit 1
        fi

        # Validate manifests
        echo "🔍 Validating manifests..."
        if [ "$source_type" = "directory" ]; then
            find "$manifest_file" -type f -name "*.y*ml" | while read -r file; do
                echo "  Validating $file..."
                validate_yaml "$file" || exit 1
            done
        else
            validate_yaml "$manifest_file" || exit 1
        fi

        # Perform dry-run if requested
        if [ "${dry_run:-false}" = "true" ]; then
            echo "🔬 Performing dry-run..."
            kubectl apply --dry-run=server -f "$manifest_file"
            exit 0
        fi

        # Apply manifests
        echo "🚀 Applying manifests..."
        if ! kubectl apply -f "$manifest_file" ${prune:+--prune=true} ${prune_whitelist:+--prune-whitelist=$prune_whitelist}; then
            echo "❌ Failed to apply manifests"
            exit 1
        fi

        echo "✅ Successfully applied manifests"
        
        # Show applied resources if requested
        if [ "${show_resources:-false}" = "true" ]; then
            echo -e "\n📦 Applied Resources:"
            kubectl get -f "$manifest_file"
        fi
    }
    ''',
    args=[
        Arg(name="url", type="str", description="URL to manifest file", required=False),
        Arg(name="file", type="str", description="Path to manifest file", required=False),
        Arg(name="directory", type="str", description="Path to directory containing manifests", required=False),
        Arg(name="dry_run", type="bool", description="Perform dry-run only", required=False),
        Arg(name="prune", type="bool", description="Prune resources not in manifest", required=False),
        Arg(name="prune_whitelist", type="str", description="Comma-separated list of resources to prune", required=False),
        Arg(name="show_resources", type="bool", description="Show applied resources", required=False),
    ],
)

cluster_housekeeping_tool = KubernetesTool(
    name="cluster_housekeeping",
    description="Perform cluster housekeeping tasks like cleaning up resources, fixing common issues, and optimizing cluster state",
    content='''
    #!/bin/bash
    set -e

    # Function to clean up resources
    cleanup_resources() {
        local namespace="$1"
        local resource_type="$2"
        local min_age="$3"
        local ns_flag=""
        [ -n "$namespace" ] && ns_flag="-n $namespace" || ns_flag="--all-namespaces"

        echo "🧹 Cleaning up $resource_type resources older than $min_age..."
        kubectl get "$resource_type" $ns_flag -o json | \
        jq -r --arg age "$min_age" '.items[] | 
            select(.metadata.creationTimestamp | fromdateiso8601 < (now - ($age | split("")[:-1] | join("") | tonumber * 
                if ($age | split(""))[-1] == "h" then 3600
                elif ($age | split(""))[-1] == "d" then 86400
                elif ($age | split(""))[-1] == "w" then 604800
                else 0 end))) |
            [.metadata.namespace, .metadata.name] | @tsv' | \
        while read -r ns name; do
            echo "  Deleting $resource_type/$name in namespace $ns..."
            kubectl delete "$resource_type" "$name" -n "$ns" --ignore-not-found
        done
    }

    # Function to fix common issues
    fix_common_issues() {
        local namespace="$1"
        local ns_flag=""
        [ -n "$namespace" ] && ns_flag="-n $namespace" || ns_flag="--all-namespaces"

        echo "🔧 Fixing common issues..."

        # Fix stuck terminating namespaces
        echo "  Checking for stuck terminating namespaces..."
        kubectl get namespaces --field-selector status.phase=Terminating -o json | \
        jq -r '.items[] | .metadata.name' | while read -r ns; do
            echo "    Fixing stuck namespace: $ns"
            kubectl get namespace "$ns" -o json | \
            jq 'del(.spec.finalizers)' | \
            kubectl replace --raw "/api/v1/namespaces/$ns/finalize" -f -
        done

        # Fix stuck terminating pods
        echo "  Checking for stuck terminating pods..."
        kubectl get pods $ns_flag --field-selector status.phase=Terminating -o json | \
        jq -r '.items[] | [.metadata.namespace, .metadata.name] | @tsv' | \
        while read -r ns name; do
            echo "    Force deleting pod: $name in namespace $ns"
            kubectl delete pod "$name" -n "$ns" --force --grace-period=0
        done

        # Fix crashlooping pods
        echo "  Checking for crashlooping pods..."
        kubectl get pods $ns_flag -o json | \
        jq -r '.items[] | select(.status.containerStatuses[]?.restartCount > 5) | [.metadata.namespace, .metadata.name] | @tsv' | \
        while read -r ns name; do
            echo "    Restarting pod: $name in namespace $ns"
            kubectl delete pod "$name" -n "$ns"
        done
    }

    # Function to optimize resources
    optimize_resources() {
        local namespace="$1"
        local ns_flag=""
        [ -n "$namespace" ] && ns_flag="-n $namespace" || ns_flag="--all-namespaces"

        echo "⚡ Optimizing cluster resources..."

        # Check for pods without resource limits
        echo "  Checking for pods without resource limits..."
        kubectl get pods $ns_flag -o json | \
        jq -r '.items[] | select(.spec.containers[] | select(.resources.limits == null)) | [.metadata.namespace, .metadata.name] | @tsv' | \
        while read -r ns name; do
            echo "    ⚠️  Pod $name in namespace $ns has no resource limits"
        done

        # Check for pods without readiness/liveness probes
        echo "  Checking for pods without health probes..."
        kubectl get pods $ns_flag -o json | \
        jq -r '.items[] | select(.spec.containers[] | select(.livenessProbe == null or .readinessProbe == null)) | [.metadata.namespace, .metadata.name] | @tsv' | \
        while read -r ns name; do
            echo "    ⚠️  Pod $name in namespace $ns is missing health probes"
        done
    }

    # Main execution
    {
        namespace="${namespace:-}"
        tasks="${tasks:-all}"
        min_age="${min_age:-7d}"

        echo "🧰 Starting cluster housekeeping tasks..."
        [ -n "$namespace" ] && echo "📁 Target namespace: $namespace"

        # Execute requested tasks
        case "$tasks" in
            "cleanup")
                cleanup_resources "$namespace" "pods" "$min_age"
                cleanup_resources "$namespace" "jobs" "$min_age"
                cleanup_resources "$namespace" "replicasets" "$min_age"
                ;;
            "fix")
                fix_common_issues "$namespace"
                ;;
            "optimize")
                optimize_resources "$namespace"
                ;;
            "all")
                cleanup_resources "$namespace" "pods" "$min_age"
                cleanup_resources "$namespace" "jobs" "$min_age"
                cleanup_resources "$namespace" "replicasets" "$min_age"
                fix_common_issues "$namespace"
                optimize_resources "$namespace"
                ;;
            *)
                echo "❌ Invalid task specified. Use cleanup, fix, optimize, or all."
                exit 1
                ;;
        esac

        echo "✅ Housekeeping tasks completed"
    }
    ''',
    args=[
        Arg(name="namespace", type="str", description="Target namespace (optional)", required=False),
        Arg(name="tasks", type="str", description="Tasks to perform (cleanup, fix, optimize, all)", required=False),
        Arg(name="min_age", type="str", description="Minimum age for cleanup (e.g., 7d, 24h)", required=False),
    ],
)


# Register tools
for tool in [manifest_apply_tool, cluster_housekeeping_tool]:
    tool_registry.register("kubernetes", tool) 