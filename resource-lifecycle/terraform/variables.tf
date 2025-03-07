variable "agent_name" {
  description = "Name of the agent"
  type        = string
}

variable "kubiya_runner" {
  description = "Runner for the agent"
  type        = string
}

variable "store_tf_state_enabled" {
  description = "Decide whether to store Terraform state or not when creating resources or requesting changes to resources"
  type        = bool
  default     = false
}

variable "approval_workflow_enabled" {
  description = "Decide whether to enable approval workflow or not"
  type        = bool
  default     = false
}

variable "agent_description" {
  description = "Description of the agent"
  type        = string
}

variable "kubiya_secrets" {
  description = "Secrets for the agent"
  type        = list(string)
}

variable "kubiya_integrations" {
  description = "Integrations for the agent"
  type        = list(string)
}

variable "kubiya_users" {
  description = "Users for the agent"
  type        = list(string)
}

variable "kubiya_groups" {
  description = "Groups for the agent"
  type        = list(string)
}

variable "log_level" {
  description = "Log level"
  type        = string
  default     = "INFO"
}

variable "grace_period" {
  description = "Grace period for nagging reminders"
  type        = string
  default     = "5h"
}

variable "max_ttl" {
  description = "Maximum TTL for a request"
  type        = string
  default     = "30d"
}

variable "approval_slack_channel" {
  description = "Slack channel for approval notifications"
  type        = string
}

variable "allowed_vendors" {
  description = "Allowed cloud vendors"
  type        = string
  default     = "aws"
}

variable "extension_period" {
  description = "Extension period for resource TTL"
  type        = string
  default     = "1w"
}

variable "kubiya_users_approving_users" {
  description = "List of users who can approve"
  type        = list(string)
}

variable "debug" {
  description = "Enable debug mode"
  type        = bool
  default     = false
}

variable "dry_run" {
  description = "Enable dry run mode (no changes will be made to infrastructure from the agent)"
  type        = bool
  default     = false
}
