import { useEffect, useState } from 'react';
import { WebhookProvider, WebhookEvent } from '../providers';
import { InteractionDestination } from '../types';
import mermaid from 'mermaid';

export interface UseMermaidDiagramProps {
  selectedProvider: WebhookProvider | null;
  selectedEvent: string;
  promptTemplate: string;
  webhookUrl: string;
  teammate?: {
    uuid: string;
    name?: string;
    team_id?: string;
    user_id?: string;
    org_id?: string;
    email?: string;
    context?: string;
  };
  interaction?: InteractionDestination;
}

export function useMermaidDiagram({
  selectedProvider,
  selectedEvent,
  promptTemplate,
  webhookUrl,
  teammate,
  interaction
}: UseMermaidDiagramProps) {
  const [diagram, setDiagram] = useState<string | null>(null);

  useEffect(() => {
    mermaid.initialize({
      theme: 'dark',
      themeVariables: {
        primaryColor: '#059669',
        primaryTextColor: '#fff',
        primaryBorderColor: '#059669',
        lineColor: '#059669',
        secondaryColor: '#1E293B',
        tertiaryColor: '#0F172A',
        nodeBorder: '#2D3B4E',
        clusterBkg: '#1E293B',
        clusterBorder: '#2D3B4E',
        edgeLabelBackground: '#1E293B'
      }
    });
  }, []);

  useEffect(() => {
    if (!selectedProvider || !selectedEvent) {
      setDiagram(null);
      return;
    }

    const event = selectedProvider.events.find((e: WebhookEvent) => e.type === selectedEvent);
    if (!event) {
      setDiagram(null);
      return;
    }

    const mermaidDiagram = `
      flowchart LR
        subgraph Source["${selectedProvider.name} Source"]
          direction TB
          E["${event.name}"]
          ED["Event Data"]
          style E fill:#059669,stroke:#059669,color:#fff
          style ED fill:#1E293B,stroke:#2D3B4E,color:#94A3B8
          E --> ED
        end

        subgraph Kubiya["Kubiya Webhooks Processing"]
          direction TB
          W["Webhook Endpoint<br/>${webhookUrl.split('/').slice(-3).join('/')}"]
          P["Prompt Template<br/>${promptTemplate.split('\n')[0] || 'Processing...'}"]
          V["Variable Substitution<br/>${event.variables.slice(0, 3).join(', ')}..."]
          style W fill:#1E293B,stroke:#2D3B4E,color:#94A3B8
          style P fill:#1E293B,stroke:#2D3B4E,color:#94A3B8
          style V fill:#1E293B,stroke:#2D3B4E,color:#94A3B8
          W --> P --> V
        end

        subgraph Teammate["Teammate: ${teammate?.name || 'Assistant'}"]
          direction TB
          T["Task Execution"]
          subgraph Tools["Available Tools"]
            direction TB
            AWS["AWS Services"]
            K8S["Kubernetes"]
            GH["GitHub Actions"]
            DB["Databases"]
            API["REST APIs"]
          end
          style T fill:#059669,stroke:#059669,color:#fff
          style AWS,K8S,GH,DB,API fill:#0F172A,stroke:#2D3B4E,color:#94A3B8
          T --- Tools
        end

        ${interaction ? `
        subgraph Updates["Real-time Updates"]
          direction TB
          U["${interaction.type === 'slack' ? 'Slack' : 'Teams'}<br/>${interaction.channel || 'Channel'}"]
          style U fill:#1E293B,stroke:#2D3B4E,color:#94A3B8
        end
        ` : ''}

        ED -->|"POST Request"| W
        V -->|"Execute Task"| T
        ${interaction ? 'T -->|"Live Updates"| U' : ''}

        classDef default fill:#1E293B,stroke:#2D3B4E,color:#94A3B8
        classDef source fill:#059669,stroke:#059669,color:#fff
        classDef highlight fill:#059669,stroke:#059669,color:#fff
    `;

    setDiagram(mermaidDiagram);
  }, [selectedProvider, selectedEvent, promptTemplate, webhookUrl, teammate, interaction]);

  return diagram;
} 