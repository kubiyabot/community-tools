terraform {
  required_providers {
    kubiya = {
      source = "kubiya-terraform/kubiya"
    }
  }
}

provider "kubiya" {
  // API key is set as an environment variable KUBIYA_API_KEY
}

resource "kubiya_source" "source" {
  url = "https://github.com/kubiyabot/terraform-modules/tree/main/resource-lifecycle/kubiya/tools"
}

resource "kubiya_agent" "agent" {
  name         = var.agent_name
  runner       = var.kubiya_runner
  description  = var.agent_description
  instructions = ""
  model        = "azure/gpt-4o"
  //image        = "kubiya/base-agent:tools-v7"
  secrets      = var.kubiya_secrets
  integrations = var.kubiya_integrations
  users        = var.kubiya_users
  groups       = var.kubiya_groups
  //tool_sources = var.agent_tool_sources
  sources = [kubiya_source.source.name]

  environment_variables = merge(
    {
      LOG_LEVEL              = var.log_level
      GRACE_PERIOD           = var.grace_period
      MAX_TTL                = var.max_ttl
      APPROVAL_SLACK_CHANNEL = var.approval_slack_channel
      ALLOWED_VENDORS        = var.allowed_vendors
      EXTENSION_PERIOD       = var.extension_period
      APPROVING_USERS        = join(",", var.kubiya_users_approving_users)
      KUBIYA_TOOL_TIMEOUT    = "5m"
    },
    var.store_tf_state_enabled ? { STORE_TF_STATE = "1" } : {},
    var.approval_workflow_enabled ? { APPROVAL_WORKFLOW = "1" } : {},
    var.debug ? { KUBIYA_DEBUG = "1" } : {},
    var.dry_run ? { DRY_RUN_ENABLED = "1" } : {}
  )
}

output "agent" {
  value = kubiya_agent.agent
}
