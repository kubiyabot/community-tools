import React, { useState, useEffect } from 'react';
import { cn } from '../../lib/utils';
import { WEBHOOK_PROVIDERS, WebhookProvider, WebhookEvent } from './providers';
import { Button } from '../ui/button';
import { toast } from '../ui/use-toast';
import { Step, InteractionDestination as InteractionDestinationType } from './types';
import { StepIndicator } from './components/StepIndicator';
import { ProviderSelection } from './components/ProviderSelection';
import { EventSelection } from './components/EventSelection';
import { EventExample } from './components/EventExample';
import { PromptTemplate } from './components/PromptTemplate';
import { WebhookSetup } from './components/WebhookSetup';
import { useWebhookFlow } from './hooks/useWebhookFlow';
import { useWebhookCreation } from './hooks/useWebhookCreation';
import { useMermaidDiagram } from './hooks/useMermaidDiagram';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { InteractionDestination } from './components/InteractionDestination';
import { Code, Eye } from 'lucide-react';
import { Badge } from '../ui/badge';

export interface WebhookFlowProps {
  webhookProvider: WebhookProvider | null;
  eventType: string;
  promptTemplate: string;
  currentStep: Step;
  setWebhookProvider: (provider: WebhookProvider | null) => void;
  setEventType: (type: string) => void;
  setPromptTemplate: (template: string) => void;
  setCurrentStep: (step: Step) => void;
  session: {
    idToken: string;
    user: {
      email?: string;
      org_id?: string;
    };
  };
  teammate?: {
    uuid: string;
    name?: string;
    team_id?: string;
    user_id?: string;
    org_id?: string;
    email?: string;
    context?: string;
  };
  standalone?: boolean;
  interaction?: InteractionDestinationType;
  setInteraction?: (interaction: InteractionDestinationType) => void;
}

export function WebhookFlowSection({
  webhookProvider,
  eventType,
  promptTemplate,
  currentStep,
  setWebhookProvider,
  setEventType,
  setPromptTemplate,
  setCurrentStep,
  session,
  teammate,
  standalone,
  interaction,
  setInteraction
}: WebhookFlowProps) {
  const [webhookCreated, setWebhookCreated] = useState(false);
  const [previewMarkdown, setPreviewMarkdown] = useState(false);
  const [jmesFilter, setJmesFilter] = useState('');

  // Always call hooks at the top level
  const webhookFlow = useWebhookFlow({
    webhookProvider,
    eventType,
    promptTemplate,
    currentStep,
    setWebhookProvider,
    setEventType,
    setPromptTemplate,
    setCurrentStep,
    interaction,
    setInteraction,
    teammate
  });

  const webhookCreation = useWebhookCreation({
    selectedProvider: webhookProvider,
    selectedEvent: eventType,
    promptTemplate,
    teammate,
    session,
    webhookUrl: webhookFlow.webhookUrl,
    setWebhookCreated,
    interaction
  });

  const mermaidDiagram = useMermaidDiagram({
    selectedProvider: webhookProvider,
    selectedEvent: eventType,
    promptTemplate,
    webhookUrl: webhookFlow.webhookUrl,
    teammate,
    interaction
  });

  // Reset states when unmounting
  useEffect(() => {
    return () => {
      webhookFlow.resetState();
    };
  }, []);

  const renderStepIndicator = () => {
    const steps = [
      { id: 'provider', label: 'Provider' },
      { id: 'event', label: 'Event' },
      { id: 'event_example', label: 'Example' },
      { id: 'prompt', label: 'Prompt' },
      { id: 'interaction', label: 'Destination' },
      { id: 'webhook', label: 'Setup' }
    ];

    return (
      <div className="flex items-center space-x-2 mb-8">
        {steps.map((step, index) => {
          const isActive = currentStep === step.id;
          const isPast = webhookFlow.canNavigateToStep(step.id as Step);
          const showLine = index < steps.length - 1;

          return (
            <React.Fragment key={step.id}>
              <button
                onClick={() => {
                  if (webhookFlow.canNavigateToStep(step.id as Step)) {
                    setCurrentStep(step.id as Step);
                  }
                }}
                className={cn(
                  "relative flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium transition-all",
                  isActive
                    ? "bg-emerald-500 text-white"
                    : isPast
                    ? "bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30"
                    : "bg-slate-800 text-slate-400 cursor-not-allowed"
                )}
              >
                {index + 1}
                <div className="absolute -bottom-6 whitespace-nowrap text-xs font-medium text-slate-400">
                  {step.label}
                </div>
              </button>
              {showLine && (
                <div
                  className={cn(
                    "flex-1 h-0.5",
                    isPast
                      ? "bg-emerald-500/50"
                      : "bg-slate-800"
                  )}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    );
  };

  const renderContent = () => {
    const processTemplate = (template: string, eventData: Record<string, any>) => {
      return template.replace(/\{\{\.event\.([^}]+)\}\}/g, (_, variable) => {
        const value = eventData[variable];
        return typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value);
      });
    };

    switch (currentStep) {
      case 'provider':
        return (
          <ProviderSelection
            selectedProvider={webhookProvider}
            onProviderSelect={webhookFlow.handleProviderSelect}
          />
        );
      case 'event':
        return (
          <EventSelection
            selectedProvider={webhookProvider}
            selectedEvent={eventType}
            onEventSelect={webhookFlow.handleEventSelect}
          />
        );
      case 'event_example':
        return (
          <EventExample
            selectedProvider={webhookProvider}
            selectedEvent={eventType}
            onContinue={webhookFlow.handleContinue}
          />
        );
      case 'prompt':
        const selectedEvent = webhookProvider?.events.find((e: WebhookEvent) => e.type === eventType);
        
        return (
          <div className="space-y-6">
            <PromptTemplate
              selectedProvider={webhookProvider}
              selectedEvent={eventType}
              promptTemplate={promptTemplate}
              setPromptTemplate={setPromptTemplate}
              onContinue={webhookFlow.handleContinue}
              filter={jmesFilter}
              setFilter={setJmesFilter}
            />
            
            {promptTemplate && (
              <div className="p-6 rounded-lg bg-[#1E293B] border border-[#2D3B4E]">
                <div className="flex items-center justify-between mb-4">
                  <div className="space-y-1">
                    <h4 className="text-sm font-medium text-slate-200">Final Output Preview</h4>
                    <p className="text-xs text-slate-400">This is how your prompt will look with the actual event data</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setPreviewMarkdown(!previewMarkdown)}
                      className="text-xs text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 flex items-center gap-2"
                    >
                      {previewMarkdown ? (
                        <>
                          <Code className="h-3 w-3" />
                          Raw
                        </>
                      ) : (
                        <>
                          <Eye className="h-3 w-3" />
                          Preview
                        </>
                      )}
                    </Button>
                  </div>
                </div>

                <div className="space-y-4">
                  {!previewMarkdown ? (
                    <div className="prose prose-invert prose-sm max-w-none p-4 rounded-lg bg-[#141B2B] border border-[#2D3B4E] overflow-auto">
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                          p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
                          h1: ({ children }) => <h1 className="text-xl font-bold mb-4 text-slate-200">{children}</h1>,
                          h2: ({ children }) => <h2 className="text-lg font-bold mb-3 text-slate-200">{children}</h2>,
                          h3: ({ children }) => <h3 className="text-base font-bold mb-2 text-slate-200">{children}</h3>,
                          ul: ({ children }) => <ul className="list-disc pl-4 mb-3 space-y-1">{children}</ul>,
                          ol: ({ children }) => <ol className="list-decimal pl-4 mb-3 space-y-1">{children}</ol>,
                          li: ({ children }) => <li className="text-slate-300">{children}</li>,
                          code: ({ children }) => (
                            <code className="bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded text-sm">
                              {children}
                            </code>
                          ),
                          pre: ({ children }) => (
                            <pre className="bg-[#1A2234] p-3 rounded-md overflow-auto border border-[#2D3B4E] mb-3">
                              {children}
                            </pre>
                          ),
                          blockquote: ({ children }) => (
                            <blockquote className="border-l-2 border-emerald-500 pl-4 italic text-slate-400 mb-3">
                              {children}
                            </blockquote>
                          ),
                        }}
                      >
                        {selectedEvent?.example ? processTemplate(promptTemplate, selectedEvent.example) : promptTemplate}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <pre className="text-sm text-slate-300 font-mono whitespace-pre-wrap p-4 rounded-lg bg-[#141B2B] border border-[#2D3B4E] overflow-auto">
                      {selectedEvent?.example ? processTemplate(promptTemplate, selectedEvent.example) : promptTemplate}
                    </pre>
                  )}

                  {selectedEvent?.example && (
                    <div className="p-3 rounded-lg bg-[#141B2B] border border-[#2D3B4E]">
                      <div className="flex items-center gap-2 text-xs text-slate-400">
                        <Badge variant="outline" className="bg-emerald-500/10 border-emerald-500/30 text-emerald-400">
                          Event Data
                        </Badge>
                        Example values that will be replaced in your prompt
                      </div>
                      <div className="mt-3 grid grid-cols-2 gap-2">
                        {selectedEvent.variables.map((variable: string) => (
                          <div key={variable} className="p-2 rounded bg-[#1A2234] border border-[#2D3B4E]">
                            <code className="text-xs text-emerald-400">{"{{.event." + variable + "}}"}</code>
                            <div className="mt-1 text-xs text-slate-400 truncate">
                              {typeof selectedEvent.example[variable] === 'object' 
                                ? JSON.stringify(selectedEvent.example[variable])
                                : String(selectedEvent.example[variable])}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      case 'interaction':
        return (
          <InteractionDestination
            selectedDestination={interaction}
            onContinue={(destination) => {
              if (setInteraction) {
                setInteraction(destination);
                webhookFlow.handleContinue();
              }
            }}
            teammate={teammate ? {
              ...teammate,
              email: teammate.email || session.user.email || ''
            } : undefined}
            provider={webhookProvider?.id || ''}
            eventType={eventType}
            promptTemplate={promptTemplate}
          />
        );
      case 'webhook':
        return (
          <div className="space-y-6">
            <WebhookSetup
              selectedProvider={webhookProvider}
              selectedEvent={eventType}
              promptTemplate={promptTemplate}
              webhookUrl={webhookFlow.webhookUrl}
              webhookCreated={webhookCreated}
              isCreatingWebhook={webhookCreation.isCreatingWebhook}
              isTestingWebhook={webhookFlow.isTestingWebhook}
              teammate={teammate}
              interaction={interaction}
              onCreateWebhook={webhookCreation.createWebhook}
              onTestWebhook={webhookCreation.handleTestWebhook}
            />
            {mermaidDiagram && (
              <div className="p-6 rounded-lg bg-[#1E293B] border border-[#2D3B4E]">
                <h4 className="text-sm font-medium text-slate-200 mb-4">Workflow Diagram</h4>
                <div className="bg-[#141B2B] rounded-lg p-6 overflow-hidden border border-[#2D3B4E]">
                  <div className="mermaid text-xs">
                    {mermaidDiagram}
                  </div>
                </div>
              </div>
            )}
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="relative flex flex-col min-h-0 bg-[#0F1629] rounded-lg border border-[#2D3B4E] p-8">
      {renderStepIndicator()}

      <div className="flex-1 overflow-y-auto space-y-8">
        {renderContent()}
      </div>
      
      {standalone && (
        <div className="flex justify-between pt-6 mt-6 border-t border-[#2D3B4E]">
          {currentStep !== 'provider' && (
            <Button
              size="lg"
              variant="outline"
              onClick={webhookFlow.handleBack}
              className="bg-[#1E293B] border-[#2D3B4E] hover:bg-emerald-500/10 text-slate-200"
            >
              Back
            </Button>
          )}
          {currentStep !== 'webhook' && (
            <Button
              size="lg"
              className={cn(
                "ml-auto transition-all",
                webhookFlow.canContinue() 
                  ? "bg-emerald-500 hover:bg-emerald-600 text-white shadow-lg shadow-emerald-500/20" 
                  : "bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700"
              )}
              onClick={webhookFlow.handleContinue}
              disabled={!webhookFlow.canContinue()}
            >
              Continue
            </Button>
          )}
        </div>
      )}
    </div>
  );
} 