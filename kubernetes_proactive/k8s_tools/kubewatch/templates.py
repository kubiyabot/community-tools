class KubeWatchTemplates:
    """KubeWatch notification templates"""
    
    @staticmethod
    def get_pod_prompt() -> str:
        return '''🚨 Critical Pod Issue Detected
═══════════════════════════
Pod: {{.Name}}
Namespace: {{.Namespace}}
Status: {{.Phase | podStatus}}
Issue: {{.Reason}}

Details:
{{- if .ContainerState }}
• State: {{ .ContainerState | formatContainer }}
{{- end }}
{{- if .RestartCount }}
• Restarts: {{ .RestartCount | formatRestarts }}
{{- end }}
{{- if .ExitCode }}
• Exit Code: {{ .ExitCode | formatExitCode }}
{{- end }}
{{- if .Message }}
• Message: {{ .Message | quote }}
{{- end }}

Context:
{{- if .Owner }}
• Owner: {{ .Owner.Kind }}/{{ .Owner.Name }}
{{- end }}
{{- if gt .EventCount 1 }}
• Related Events: {{ .EventCount }}
{{- range .GroupedEvents }}
- {{ .status | formatStatus }}: {{ .message }}
{{- end }}
{{- end }}'''

    @staticmethod
    def get_node_prompt() -> str:
        return '''🚨 Critical Node Issue Detected
════════════════════════════
Node: {{.Name}}
Status: {{.Status}}
Issue: {{.Reason}}

Resources:
• CPU: {{.Resources.cpu}}
• Memory: {{.Resources.memory}}
• Pods: {{.Resources.pods}}/{{.Resources.maxPods}}

{{- if gt .EventCount 1 }}
Recent Events:
{{- range .GroupedEvents }}
• {{ .status | formatStatus }}: {{ .message }}
{{- end }}
{{- end }}''' 