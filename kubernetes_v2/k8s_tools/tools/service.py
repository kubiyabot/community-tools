from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

# Detailed service inspection tool
service_inspect_tool = KubernetesTool(
    name="service_inspect",
    description="Provides detailed information about a Kubernetes service including endpoints, pods, and events",
    content='''
    #!/bin/bash
    set -e

    # Ensure required parameters are provided
    if [ -z "${namespace}" ] || [ -z "${name}" ]; then
        echo "❌ Error: namespace and name are required."
        exit 1
    fi

    # Build base command
    base_cmd="kubectl --namespace ${namespace}"
    
    # Apply grep filter if provided
    filter_cmd=""
    if [ -n "${grep_filter}" ]; then
        filter_cmd="| grep -i '${grep_filter}'"
    fi

    # Show service details
    echo "📊 Service Details:"
    echo "=================="
    describe_cmd="${base_cmd} describe service ${name}"
    if [ -n "${grep_filter}" ]; then
        eval "$describe_cmd" | grep -i "${grep_filter}" | kubectl_with_truncation
    else
        eval "$describe_cmd" | kubectl_with_truncation
    fi

    # Show endpoints
    echo -e "\n🔌 Service Endpoints:"
    echo "=================="
    endpoints_cmd="${base_cmd} describe endpoints ${name}"
    if [ -n "${grep_filter}" ]; then
        eval "$endpoints_cmd" | grep -i "${grep_filter}" | kubectl_with_truncation
    else
        eval "$endpoints_cmd" | kubectl_with_truncation
    fi

    # Get service selector
    selector=$(kubectl get service ${name} -n ${namespace} -o jsonpath='{.spec.selector}' | jq -r 'to_entries | map("\(.key)=\(.value)") | join(",")')
    
    if [ -n "$selector" ]; then
        echo -e "\n📦 Backend Pods:"
        echo "=================="
        pods_cmd="${base_cmd} get pods -l ${selector} -o wide"
        if [ -n "${grep_filter}" ]; then
            eval "$pods_cmd" | grep -i "${grep_filter}" | kubectl_with_truncation
        else
            kubectl_with_truncation "$pods_cmd"
        fi

        # Show pod status summary
        echo -e "\n📈 Pod Status Summary:"
        echo "===================="
        eval "${base_cmd} get pods -l ${selector} --no-headers" | \
        awk '{status[$3]++} END {for (s in status) printf "%-20s: %d\\n", s, status[s]}' | \
        kubectl_with_truncation
    fi

    # Show recent events
    echo -e "\n📜 Recent Events:"
    echo "=================="
    format_events "$namespace" "$name" "Service"
    ''',
    args=[
        Arg(name="name", type="str", description="Name of the service", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=True),
        Arg(name="grep_filter", type="str", description="Optional grep filter to apply to the output", required=False),
    ],
)

# Service connectivity test tool
service_test_tool = KubernetesTool(
    name="service_test",
    description="Tests connectivity to a Kubernetes service using various methods",
    content='''
    #!/bin/bash
    set -e

    # Ensure required parameters are provided
    if [ -z "${namespace}" ] || [ -z "${name}" ]; then
        echo "❌ Error: namespace and name are required."
        exit 1
    fi

    # Get service details
    service_type=$(kubectl get service ${name} -n ${namespace} -o jsonpath='{.spec.type}')
    service_port=$(kubectl get service ${name} -n ${namespace} -o jsonpath='{.spec.ports[0].port}')
    
    echo "🔍 Testing Service: ${name}"
    echo "Type: ${service_type}"
    echo "Port: ${service_port}"
    echo "===================="

    case "${service_type}" in
        "LoadBalancer")
            external_ip=$(kubectl get service ${name} -n ${namespace} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
            if [ -n "${external_ip}" ]; then
                echo "📡 External IP: ${external_ip}"
                echo "Testing connection..."
                timeout 5 nc -zv ${external_ip} ${service_port} 2>&1 | kubectl_with_truncation || echo "❌ Connection failed"
            else
                echo "⚠️ External IP not yet assigned"
            fi
            ;;
        "NodePort")
            node_port=$(kubectl get service ${name} -n ${namespace} -o jsonpath='{.spec.ports[0].nodePort}')
            echo "🔌 NodePort: ${node_port}"
            node_ip=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
            echo "Testing connection to node ${node_ip}:${node_port}..."
            timeout 5 nc -zv ${node_ip} ${node_port} 2>&1 | kubectl_with_truncation || echo "❌ Connection failed"
            ;;
        "ClusterIP")
            cluster_ip=$(kubectl get service ${name} -n ${namespace} -o jsonpath='{.spec.clusterIP}')
            echo "🔄 ClusterIP: ${cluster_ip}"
            echo "Note: ClusterIP services are only accessible from within the cluster"
            ;;
    esac

    # Show endpoints status
    echo -e "\n📍 Endpoints Status:"
    echo "=================="
    endpoints_cmd="${base_cmd} get endpoints ${name}"
    kubectl_with_truncation "$endpoints_cmd"

    # Show service events
    echo -e "\n📜 Recent Events:"
    echo "=================="
    format_events "$namespace" "$name" "Service"
    ''',
    args=[
        Arg(name="name", type="str", description="Name of the service", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=True),
    ],
)

# Service metrics tool
service_metrics_tool = KubernetesTool(
    name="service_metrics",
    description="Shows metrics and statistics for a Kubernetes service",
    content='''
    #!/bin/bash
    set -e

    # Ensure required parameters are provided
    if [ -z "${namespace}" ] || [ -z "${name}" ]; then
        echo "❌ Error: namespace and name are required."
        exit 1
    fi

    # Get service selector
    selector=$(kubectl get service ${name} -n ${namespace} -o jsonpath='{.spec.selector}' | jq -r 'to_entries | map("\(.key)=\(.value)") | join(",")')
    
    if [ -n "$selector" ]; then
        echo "📊 Pod Metrics:"
        echo "=============="
        metrics_cmd="kubectl top pods -n ${namespace} -l ${selector} --sort-by=cpu"
        kubectl_with_truncation "$metrics_cmd"

        echo -e "\n🔄 Pod Status Distribution:"
        echo "======================="
        kubectl get pods -n ${namespace} -l ${selector} --no-headers | \
        awk '{status[$3]++} END {for (s in status) printf "%-20s: %d\\n", s, status[s]}' | \
        kubectl_with_truncation

        echo -e "\n⚖️ Resource Requests/Limits:"
        echo "========================"
        kubectl get pods -n ${namespace} -l ${selector} -o jsonpath='{range .items[*]}{.metadata.name}{": "}{.spec.containers[*].resources}{"\n"}{end}' | \
        kubectl_with_truncation
    else
        echo "❌ No selector found for service ${name}"
        exit 1
    fi
    ''',
    args=[
        Arg(name="name", type="str", description="Name of the service", required=True),
        Arg(name="namespace", type="str", description="Kubernetes namespace", required=True),
    ],
)

# Register all tools
for tool in [
    service_tool,
    service_inspect_tool,
    service_test_tool,
    service_metrics_tool,
]:
    tool_registry.register("kubernetes", tool)
