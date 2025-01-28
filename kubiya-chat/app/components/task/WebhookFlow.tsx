import React from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Webhook, Code, Copy, MessageSquare } from 'lucide-react';
import { toast } from '../ui/use-toast';
import { cn } from '@/lib/utils';

interface WebhookProvider {
  id: string;
  name: string;
  description: string;
  icon: string;
  events: WebhookEvent[];
}

interface WebhookEvent {
  type: string;
  name: string;
  description: string;
  variables: ContextVariable[];
  example: Record<string, any>;
  category?: string;
}

interface ContextVariable {
  path: string;
  description: string;
  example: any;
}

interface WebhookFlowProps {
  provider: WebhookProvider | null;
  onProviderSelect: (provider: WebhookProvider) => void;
  eventType: string;
  onEventTypeSelect: (eventType: string) => void;
  promptTemplate: string;
  onPromptTemplateChange: (template: string) => void;
  providers: WebhookProvider[];
  isLoadingProviders?: boolean;
}

export function WebhookFlow({
  provider,
  onProviderSelect,
  eventType,
  onEventTypeSelect,
  promptTemplate,
  onPromptTemplateChange,
  providers,
  isLoadingProviders
}: WebhookFlowProps) {
  const selectedEvent = provider?.events.find(e => e.type === eventType);

  return (
    <div className="space-y-8">
      {/* Provider Selection */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Webhook className="h-5 w-5 text-emerald-400" />
          <h3 className="text-base font-medium text-slate-200">Select Provider</h3>
        </div>
        <div className="grid grid-cols-3 gap-4">
          {providers.map((p) => (
            <Button
              key={p.id}
              variant="outline"
              className={cn(
                "flex flex-col items-center gap-4 p-6 h-auto",
                "bg-[#1E293B] hover:bg-emerald-500/10",
                "border-[#2D3B4E] hover:border-emerald-500/30",
                provider?.id === p.id && "bg-emerald-500/10 border-emerald-500/30"
              )}
              onClick={() => onProviderSelect(p)}
            >
              <div className="w-12 h-12 rounded-lg bg-emerald-500/10 border border-emerald-500/20 
                           flex items-center justify-center">
                <img src={p.icon} alt={p.name} className="h-6 w-6" />
              </div>
              <div className="text-center">
                <h3 className="text-base font-medium text-slate-200 mb-1">{p.name}</h3>
                <p className="text-sm text-slate-400">{p.description}</p>
              </div>
            </Button>
          ))}
        </div>
      </div>

      {/* Event Selection */}
      {provider && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Code className="h-5 w-5 text-emerald-400" />
            <h3 className="text-base font-medium text-slate-200">Select Event</h3>
          </div>
          <div className="grid grid-cols-2 gap-4">
            {provider.events.map((event) => (
              <div
                key={event.type}
                onClick={() => onEventTypeSelect(event.type)}
                className={cn(
                  "p-4 rounded-lg border cursor-pointer transition-all",
                  "hover:bg-emerald-500/5 hover:border-emerald-500/30",
                  eventType === event.type
                    ? "bg-emerald-500/10 border-emerald-500/30"
                    : "bg-[#1E293B] border-[#2D3B4E]"
                )}
              >
                <h4 className="text-sm font-medium text-slate-200 mb-1">{event.name}</h4>
                <p className="text-xs text-slate-400">{event.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Prompt Template */}
      {selectedEvent && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-emerald-400" />
              <h3 className="text-base font-medium text-slate-200">Prompt Template</h3>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-slate-400 hover:text-emerald-400"
              onClick={() => {
                const example = `Please review the ${selectedEvent.name.toLowerCase()} and provide feedback.`;
                onPromptTemplateChange(example);
              }}
            >
              <MessageSquare className="h-4 w-4 mr-2" />
              Use Example
            </Button>
          </div>
          <div className="space-y-4">
            <textarea
              value={promptTemplate}
              onChange={(e) => onPromptTemplateChange(e.target.value)}
              placeholder={`Enter your prompt template. Use variables like {{.variable_name}} to make it dynamic.`}
              className={cn(
                "w-full h-32 bg-[#1E293B] border border-[#2D3B4E] rounded-lg p-3",
                "text-sm text-slate-200 resize-none",
                "focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/30"
              )}
            />
            <div className="p-4 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-emerald-400">Available Variables</h4>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs text-slate-400 hover:text-emerald-400"
                  onClick={() => {
                    const example = JSON.stringify(selectedEvent.example, null, 2);
                    navigator.clipboard.writeText(example);
                    toast({
                      title: "Copied to clipboard",
                      description: "Example payload has been copied to your clipboard.",
                    });
                  }}
                >
                  <Copy className="h-3 w-3 mr-1" />
                  Copy Example
                </Button>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {selectedEvent.variables.map((variable) => (
                  <div
                    key={variable.path}
                    className="p-2 rounded bg-[#1E293B] border border-[#2D3B4E]"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <code className="text-xs font-mono text-emerald-400">
                        {`{{.${variable.path}}}`}
                      </code>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 text-xs text-slate-400 hover:text-emerald-400"
                        onClick={() => {
                          const cursorPos = document.activeElement instanceof HTMLTextAreaElement
                            ? document.activeElement.selectionStart
                            : promptTemplate.length;
                          const newTemplate = promptTemplate.slice(0, cursorPos) +
                            `{{.${variable.path}}}` +
                            promptTemplate.slice(cursorPos);
                          onPromptTemplateChange(newTemplate);
                        }}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                    <p className="text-xs text-slate-400">{variable.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 