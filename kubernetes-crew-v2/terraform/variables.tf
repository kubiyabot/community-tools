# Core Configuration
variable "teammate_name" {
  description = "Name of the Kubernetes monitoring teammate (e.g., 'k8s-watcher')"
  type        = string
  default     = "k8s-watcher"
}

variable "kubiya_runner" {
  description = "The Kubiya Runner where your cluster is running"
  type        = string
}

variable "notification_channel" {
  description = "Slack channel where alerts will be sent (e.g., '#devops-alerts') - Note: Channel must be created in Slack and the Kubiya Slack App must be added to the channel"
  type        = string
  default     = "#devops-oncall"
}

variable "kubiya_groups_allowed_groups" {
  description = "List of groups allowed to interact with the teammate"
  type        = list(string)
  default     = ["Admin"]
}

# Watcher Configuration
variable "watch_namespaces" {
  description = "Comma-separated list of namespaces to monitor (e.g., 'default,kube-system') - use '*' to monitor all namespaces"
  type        = string
  default     = "default,kube-system"
}

variable "watch_pod" {
  description = "Enable monitoring of Pod-related events"
  type        = bool
  default     = true
}

variable "watch_node" {
  description = "Enable monitoring of Node-related events"
  type        = bool
  default     = true
}

variable "watch_event" {
  description = "Enable monitoring of general Kubernetes events"
  type        = bool
  default     = true
}

variable "enable_auto_pilot" {
  description = "Enable auto-pilot mode (BETA) - Attempts to automatically diagnose and fix issues without human intervention"
  type        = bool
  default     = false
}

variable "debug_mode" {
  description = "Enable debug mode for detailed logging and troubleshooting"
  type        = bool
  default     = false
}