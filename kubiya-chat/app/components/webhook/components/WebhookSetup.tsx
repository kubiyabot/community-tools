import { useState } from 'react';
import { Button } from '../../ui/button';
import { cn } from '../../../lib/utils';
import { WebhookProvider, WebhookEvent } from '../providers';
import { Copy, PlayCircle, Code2, Terminal, ExternalLink, ChevronDown, MessageSquare } from 'lucide-react';
import { toast } from '../../ui/use-toast';
import { Textarea } from '../../ui/textarea';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "../../../components/ui/collapsible";
import { InteractionDestination } from '../types';

interface WebhookSetupProps {
  selectedProvider: WebhookProvider | null;
  selectedEvent: string;
  promptTemplate: string;
  webhookUrl: string;
  webhookCreated: boolean;
  isCreatingWebhook: boolean;
  isTestingWebhook: boolean;
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
  onCreateWebhook: () => void;
  onTestWebhook: () => void;
}

export function WebhookSetup({
  selectedProvider,
  selectedEvent,
  promptTemplate,
  webhookUrl,
  webhookCreated,
  isCreatingWebhook,
  isTestingWebhook,
  teammate,
  interaction,
  onCreateWebhook,
  onTestWebhook
}: WebhookSetupProps) {
  const [testPayload, setTestPayload] = useState('');
  const [isCustomPayload, setIsCustomPayload] = useState(false);
  const [showInstructions, setShowInstructions] = useState(true);

  if (!selectedProvider) return null;
  const event = selectedProvider.events.find((e: WebhookEvent) => e.type === selectedEvent);
  if (!event) return null;

  const handleCopyUrl = () => {
    navigator.clipboard.writeText(webhookUrl);
    toast({
      title: "Copied to clipboard",
      description: "Webhook URL has been copied to your clipboard."
    });
  };

  const handleCopyCurl = () => {
    const curlCommand = `curl -X POST ${webhookUrl} \\
  -H "Content-Type: application/json" \\
  -d '${JSON.stringify(event.example, null, 2)}'`;
    
    navigator.clipboard.writeText(curlCommand);
    toast({
      title: "Copied to clipboard",
      description: "cURL command has been copied to your clipboard."
    });
  };

  const getProviderSetupInstructions = () => {
    const instructions = [];
    
    switch (selectedProvider.id) {
      case 'github':
        instructions.push(
          <div key="github" className="space-y-4">
            <ol className="list-decimal list-inside space-y-2 text-sm text-slate-400">
              <li>Go to your repository settings</li>
              <li>Click on "Webhooks" in the left sidebar</li>
              <li>Click "Add webhook"</li>
              <li>Set Payload URL to: <code className="text-emerald-400">{webhookUrl}</code></li>
              <li>Set Content type to: <code className="text-emerald-400">application/json</code></li>
              <li>Select events: <code className="text-emerald-400">{event.name}</code></li>
              <li>Click "Add webhook"</li>
            </ol>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open('https://github.com/settings/webhooks/new', '_blank')}
                className="text-xs"
              >
                <ExternalLink className="w-3 h-3 mr-1" />
                Open GitHub Settings
              </Button>
            </div>
          </div>
        );
        break;
      case 'gitlab':
        instructions.push(
          <div key="gitlab" className="space-y-4">
            <ol className="list-decimal list-inside space-y-2 text-sm text-slate-400">
              <li>Go to your project's Settings {'->'} Webhooks</li>
              <li>Enter URL: <code className="text-emerald-400">{webhookUrl}</code></li>
              <li>Select trigger: <code className="text-emerald-400">{event.name}</code></li>
              <li>Click "Add webhook"</li>
            </ol>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open('https://gitlab.com/-/profile/applications', '_blank')}
                className="text-xs"
              >
                <ExternalLink className="w-3 h-3 mr-1" />
                Open GitLab Settings
              </Button>
            </div>
          </div>
        );
        break;
      default:
        instructions.push(
          <div key="default" className="space-y-4">
            <ol className="list-decimal list-inside space-y-2 text-sm text-slate-400">
              <li>Configure your webhook endpoint: <code className="text-emerald-400">{webhookUrl}</code></li>
              <li>Set Content-Type header: <code className="text-emerald-400">application/json</code></li>
              <li>Send POST requests with JSON payload</li>
            </ol>
            <div className="mt-4 p-4 rounded-lg bg-slate-800/50 border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <h5 className="text-sm font-medium text-slate-200">Example cURL Command</h5>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCopyCurl}
                  className="h-8 text-xs text-slate-400 hover:text-emerald-400"
                >
                  <Copy className="w-3 h-3 mr-1" />
                  Copy
                </Button>
              </div>
              <pre className="text-xs text-slate-400 font-mono whitespace-pre-wrap break-all">
                {`curl -X POST ${webhookUrl} \\
  -H "Content-Type: application/json" \\
  -d '${JSON.stringify(event.example, null, 2)}'`}
              </pre>
            </div>
          </div>
        );
    }

    if (interaction) {
      instructions.push(
        <div key="interaction" className="mt-4 pt-4 border-t border-[#2D3B4E]">
          <h5 className="text-sm font-medium text-slate-300 mb-2">Updates will be sent to:</h5>
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <MessageSquare className="h-4 w-4 text-emerald-400" />
            {interaction.type === 'slack' ? (
              <span>Slack {interaction.channel}</span>
            ) : (
              <span>Microsoft Teams (Coming Soon)</span>
            )}
          </div>
        </div>
      );
    }

    return instructions;
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h3 className="text-lg font-medium text-slate-200">Webhook Setup</h3>
        <p className="text-sm text-slate-400">
          Create and configure your webhook endpoint to start receiving events from {selectedProvider.name}.
        </p>
      </div>

      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <Button
            onClick={onCreateWebhook}
            disabled={webhookCreated || isCreatingWebhook}
            className={cn(
              "text-white shadow-sm",
              !webhookCreated && !isCreatingWebhook
                ? "bg-emerald-500 hover:bg-emerald-600 shadow-emerald-500/20"
                : "bg-slate-600 cursor-not-allowed"
            )}
          >
            <PlayCircle className="h-4 w-4 mr-2" />
            {isCreatingWebhook ? 'Creating...' : webhookCreated ? 'Created' : 'Create Webhook'}
          </Button>
        </div>

        {webhookCreated && (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-4">
                <Collapsible defaultOpen>
                  <CollapsibleTrigger className="flex items-center justify-between w-full p-4 rounded-lg bg-[#1E293B] border border-[#2D3B4E] hover:bg-[#1E293B]/80 transition-colors">
                    <div className="flex items-center gap-2">
                      <Code2 className="h-4 w-4 text-emerald-400" />
                      <h4 className="text-sm font-medium text-slate-200">Webhook URL</h4>
                    </div>
                    <ChevronDown className="h-4 w-4 text-slate-400" />
                  </CollapsibleTrigger>
                  <CollapsibleContent className="pt-4">
                    <div className="p-4 rounded-lg bg-[#141B2B] border border-[#2D3B4E]">
                      <div className="flex items-center justify-between">
                        <code className="text-sm text-slate-300 font-mono break-all">{webhookUrl}</code>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleCopyUrl}
                          className="h-8 text-sm text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition-all shrink-0 ml-2"
                        >
                          <Copy className="h-4 w-4 mr-2" />
                          Copy
                        </Button>
                      </div>
                    </div>
                  </CollapsibleContent>
                </Collapsible>

                <Collapsible defaultOpen>
                  <CollapsibleTrigger className="flex items-center justify-between w-full p-4 rounded-lg bg-[#1E293B] border border-[#2D3B4E] hover:bg-[#1E293B]/80 transition-colors">
                    <div className="flex items-center gap-2">
                      <ExternalLink className="h-4 w-4 text-emerald-400" />
                      <h4 className="text-sm font-medium text-slate-200">Setup Instructions</h4>
                    </div>
                    <ChevronDown className="h-4 w-4 text-slate-400" />
                  </CollapsibleTrigger>
                  <CollapsibleContent className="pt-4">
                    <div className="p-4 rounded-lg bg-[#141B2B] border border-[#2D3B4E]">
                      {getProviderSetupInstructions()}
                    </div>
                  </CollapsibleContent>
                </Collapsible>
              </div>

              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-[#1E293B] border border-[#2D3B4E]">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-sm font-medium text-slate-200">Test Webhook</h4>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setIsCustomPayload(!isCustomPayload)}
                      className="text-xs text-slate-400 hover:text-emerald-400"
                    >
                      {isCustomPayload ? 'Use Example' : 'Custom Payload'}
                    </Button>
                  </div>

                  {isCustomPayload ? (
                    <div className="space-y-4">
                      <Textarea
                        value={testPayload || JSON.stringify(event.example, null, 2)}
                        onChange={(e) => setTestPayload(e.target.value)}
                        className="min-h-[300px] font-mono text-sm bg-[#141B2B] border-[#2D3B4E] text-slate-300"
                        placeholder="Enter your custom JSON payload..."
                      />
                    </div>
                  ) : (
                    <pre className="p-4 rounded-lg bg-[#141B2B] border border-[#2D3B4E] text-sm text-slate-400 font-mono overflow-auto max-h-[300px]">
                      {JSON.stringify(event.example, null, 2)}
                    </pre>
                  )}

                  <div className="mt-4 flex items-center gap-2">
                    <Button
                      onClick={onTestWebhook}
                      disabled={isTestingWebhook}
                      className="bg-emerald-500 hover:bg-emerald-600 text-white shadow-sm shadow-emerald-500/20"
                    >
                      <PlayCircle className="h-4 w-4 mr-2" />
                      {isTestingWebhook ? 'Testing...' : 'Test Webhook'}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleCopyCurl}
                      className="text-xs"
                    >
                      <Terminal className="w-3 h-3 mr-1" />
                      Copy as cURL
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
} 