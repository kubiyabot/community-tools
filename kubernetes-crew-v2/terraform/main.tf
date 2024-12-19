terraform {
  required_providers {
    http = {
      source = "hashicorp/http"
    }
    kubiya = {
      source = "kubiya-terraform/kubiya"
    }
  }
}

provider "kubiya" {
  // API key is set as an environment variable KUBIYA_API_KEY
}

#knowledge
data "http" "kubernetes_security" {
  url = "https://raw.githubusercontent.com/kubiyabot/terraform-modules/refs/heads/main/kubernetes-crew/terraform/knowledge/kubernetes_security.md"
}

data "http" "kubernetes_troubleshooting" {
  url = "https://raw.githubusercontent.com/kubiyabot/terraform-modules/refs/heads/main/kubernetes-crew/terraform/knowledge/kubernetes_troubleshooting.md"
}

data "http" "kubernetes_ops" {
  url = "https://raw.githubusercontent.com/kubiyabot/terraform-modules/refs/heads/main/kubernetes-crew/terraform/knowledge/kubernetes_ops.md"
}

resource "kubiya_source" "diagramming_capabilities" {
  url = "https://github.com/kubiyabot/community-tools/tree/main/mermaid"
}
resource "kubiya_source" "slack_capabilities" {
  url = "https://github.com/kubiyabot/community-tools/tree/slack-tools/slack"
}

resource "kubiya_agent" "kubernetes_crew" {
  name         = var.teammate_name
  runner       = var.kubiya_runner
  description  = "AI-powered Kubernetes operations assistant"
  model        = "azure/gpt-4o"
  instructions = ""
  sources      = []
  integrations = ["kubernetes", "slack"]
  users        = []
  groups       = var.kubiya_groups_allowed_groups
   is_debug_mode = var.debug_mode
}

# Unified webhook configuration
resource "kubiya_webhook" "source_control_webhook" {
  filter = ""
  
  name        = "${var.teammate_name}-k8s-webhook"
  source      = "K8S"
  prompt      = <<-EOT
    🚨 *Kubernetes Event Alert* 🚨
    
    📋 Event Details:
    {{.event.summary}}

    ${var.enable_auto_pilot ? "🤖 ***AUTO-PILOT MODE ENABLED***\n->> Automated diagnosis and resolution should be attempted without user interaction" : ""}
    
    Action Plan:
    1. Root Cause Analysis
       ->> Identify and investigate the underlying cause of this event
    
    2. Diagnostic Process  
       ->> Run comprehensive system diagnostics using available tooling
       ->> Collect relevant logs and metrics
    
    3. Impact Assessment
       ->> Evaluate effects on connected systems and services
       ->> Identify any potential cascading failures
    
    4. Resolution Steps
       ->> Implement immediate mitigation measures and diagram the solution where applicable
    
    ${var.enable_auto_pilot ? "Auto-Pilot Actions:\n->> Executing automated investigation and remediation\n->> Documenting all findings and actions in detail" : ""}
    EOT
  agent       = kubiya_agent.kubernetes_crew.name
  destination = var.notification_channel
  depends_on = [
    kubiya_agent.kubernetes_crew
  ]
}


resource "kubiya_knowledge" "kubernetes_ops" {
  name             = "Kubernetes Operations and Housekeeping Guide"
  groups           = var.kubiya_groups_allowed_groups
  description      = "Knowledge base for Kubernetes housekeeping operations"
  labels           = ["kubernetes", "operations", "housekeeping"]
  supported_agents = [kubiya_agent.kubernetes_crew.name]
  content          = data.http.kubernetes_ops.response_body
}

resource "kubiya_knowledge" "kubernetes_security" {
  name             = "Kubernetes Security Best Practices"
  groups           = var.kubiya_groups_allowed_groups
  description      = "Knowledge base for Kubernetes security practices"
  labels           = ["kubernetes", "security", "best-practices"]
  supported_agents = [kubiya_agent.kubernetes_crew.name]
  content          = data.http.kubernetes_security.response_body
}

resource "kubiya_knowledge" "kubernetes_troubleshooting" {
  name             = "Kubernetes Troubleshooting Guide"
  groups           = var.kubiya_groups_allowed_groups
  description      = "Knowledge base for Kubernetes troubleshooting techniques"
  labels           = ["kubernetes", "troubleshooting", "debugging"]
  supported_agents = [kubiya_agent.kubernetes_crew.name]
  content          = data.http.kubernetes_troubleshooting.response_body
}

resource "kubiya_source" "k8s_capabilities" {
  url = "https://github.com/kubiyabot/community-tools/tree/main/kubernetes_v2"

  dynamic_config = {
    namespaces   = var.watch_namespaces
    watch_pod    = tostring(var.watch_pod)
    watch_node   = tostring(var.watch_node)
    watch_event  = tostring(var.watch_event)
    namespaces   = var.watch_namespaces
    webhook_url  = kubiya_webhook.source_control_webhook.url
  }

  depends_on = [kubiya_webhook.source_control_webhook]
}

resource "null_resource" "runner_env_setup" {
  triggers = {
    runner = var.kubiya_runner
    webhook_id = kubiya_source.k8s_capabilities.id
  }

  provisioner "local-exec" {
    command = <<-EOT
      curl -X PUT \
      -H "Authorization: UserKey $KUBIYA_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "uuid": "${kubiya_agent.kubernetes_crew.id}",
        "environment_variables": {
          "NOTIFICATION_CHANNEL": "${var.notification_channel}",
          "KUBIYA_TOOL_TIMEOUT": "500"
        },
        "sources": [
          "${kubiya_source.diagramming_capabilities.id}",
          "${kubiya_source.slack_capabilities.id}",
          "${kubiya_source.k8s_capabilities.id}"
        ]
      }' \
      "https://api.kubiya.ai/api/v1/agents/${kubiya_agent.kubernetes_crew.id}"
    EOT
  }
  depends_on = [
    kubiya_source.k8s_capabilities
  ]
}


# Output the teammate details
output "kubernetes_crew" {
  value = {
    name                 = kubiya_agent.kubernetes_crew.name
    notification_channel = var.notification_channel
  }
}
