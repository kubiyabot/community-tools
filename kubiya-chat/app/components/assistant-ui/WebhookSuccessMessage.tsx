import { useState } from 'react';
import { 
  Webhook, 
  Code2, 
  Copy, 
  Check, 
  PlayCircle, 
  Terminal, 
  Trash2, 
  ExternalLink,
  ChevronDown,
  GitBranch,
  GitPullRequest,
  MessageSquare,
  AlertTriangle
} from 'lucide-react';
import { Button } from '../ui/button';
import { toast } from '../ui/use-toast';
import { MarkdownText } from './MarkdownText';
import { ContextVariable } from '../activity/ContextVariable';
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from '../ui/collapsible';
import { Textarea } from '../ui/textarea';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '../ui/alert-dialog';
import { cn } from '@/lib/utils';

interface WebhookProps {
  id: string;
  webhook_url: string;
  provider: string;
  event_type: string;
  prompt_template: string;
  created_at: string;
  teammate_id?: string;
}

export function WebhookSuccessMessage({ webhook }: { webhook: WebhookProps }) {
  const [isTestingWebhook, setIsTestingWebhook] = useState(false);
  const [isCustomPayload, setIsCustomPayload] = useState(false);
  const [testPayload, setTestPayload] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  const formatPromptWithContext = (text: string) => {
    // Replace context variables with formatted components
    const formattedText = text.replace(
      /{{([^}]+)}}/g,
      (match, variable) => `<var>${variable.trim()}</var>`
    );

    return (
      <div className="space-y-4">
        <MarkdownText content={formattedText} />
        <div className="flex flex-wrap gap-2 pt-2 border-t border-[#2A3347]">
          {Array.from(text.matchAll(/{{([^}]+)}}/g)).map(([_, variable], index) => (
            <ContextVariable key={index} variable={variable.trim()} />
          ))}
        </div>
      </div>
    );
  };

  const getProviderIcon = () => {
    switch (webhook.provider.toLowerCase()) {
      case 'github':
        return <GitBranch className="h-4 w-4 text-purple-400" />;
      case 'gitlab':
        return <GitPullRequest className="h-4 w-4 text-orange-400" />;
      case 'jira':
        return <MessageSquare className="h-4 w-4 text-blue-400" />;
      default:
        return <Webhook className="h-4 w-4 text-emerald-400" />;
    }
  };

  const handleCopyUrl = async () => {
    try {
      await navigator.clipboard.writeText(webhook.webhook_url);
      toast({
        description: "Webhook URL copied to clipboard",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to copy webhook URL",
        variant: "destructive",
      });
    }
  };

  const handleCopyCurl = async () => {
    const curlCommand = `curl -X POST \\
  ${webhook.webhook_url} \\
  -H 'Content-Type: application/json' \\
  -d '${testPayload || JSON.stringify({ test: true })}'`;

    try {
      await navigator.clipboard.writeText(curlCommand);
      toast({
        description: "cURL command copied to clipboard",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to copy cURL command",
        variant: "destructive",
      });
    }
  };

  const handleTestWebhook = async () => {
    setIsTestingWebhook(true);
    try {
      const response = await fetch(webhook.webhook_url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: testPayload || JSON.stringify({
          test: true,
          provider: webhook.provider,
          event: webhook.event_type
        })
      });

      if (!response.ok) {
        throw new Error('Failed to test webhook');
      }

      toast({
        title: "Test successful",
        description: "The webhook endpoint responded successfully."
      });
    } catch (error) {
      console.error('Error testing webhook:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : 'Failed to test webhook',
        variant: "destructive"
      });
    } finally {
      setIsTestingWebhook(false);
    }
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      const response = await fetch(`/api/webhooks/${webhook.id}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to delete webhook');
      }

      toast({
        title: "Webhook deleted",
        description: "Your webhook has been deleted successfully."
      });
    } catch (error) {
      console.error('Error deleting webhook:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : 'Failed to delete webhook',
        variant: "destructive"
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const getProviderSetupInstructions = () => {
    switch (webhook.provider.toLowerCase()) {
      case 'github':
        return (
          <ol className="list-decimal list-inside space-y-2 text-sm text-slate-300">
            <li>Go to your GitHub repository settings</li>
            <li>Click on "Webhooks" in the left sidebar</li>
            <li>Click "Add webhook"</li>
            <li>Enter the webhook URL in the "Payload URL" field</li>
            <li>Set content type to "application/json"</li>
            <li>Select the events you want to trigger the webhook</li>
            <li>Click "Add webhook" to save</li>
          </ol>
        );
      case 'gitlab':
        return (
          <ol className="list-decimal list-inside space-y-2 text-sm text-slate-300">
            <li>Go to your GitLab project settings</li>
            <li>Click on "Webhooks" in the left sidebar</li>
            <li>Enter the webhook URL</li>
            <li>Select the events you want to trigger the webhook</li>
            <li>Click "Add webhook" to save</li>
          </ol>
        );
      default:
        return (
          <p className="text-sm text-slate-300">
            Configure your webhook endpoint in your {webhook.provider} settings using the provided URL.
          </p>
        );
    }
  };

  return (
    <div className="flex items-start gap-3">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-emerald-500/10 flex items-center justify-center">
        {getProviderIcon()}
      </div>
      <div className="flex-1 space-y-4">
        <div className="flex items-center gap-2">
          <div className="text-sm font-medium text-white">Webhook Created</div>
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs bg-emerald-500/10 text-emerald-400">
            <Check className="h-3 w-3" />
            <span>Active</span>
          </div>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-red-400 hover:text-red-300 hover:bg-red-500/10"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete Webhook</AlertDialogTitle>
                <AlertDialogDescription>
                  Are you sure you want to delete this webhook? This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleDelete}
                  className="bg-red-500 hover:bg-red-600 text-white"
                  disabled={isDeleting}
                >
                  {isDeleting ? 'Deleting...' : 'Delete'}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>

        <div className="bg-[#1A1F2E]/50 rounded-lg p-4 space-y-4">
          {/* Provider & Event Type */}
          <div className="flex items-center gap-2 p-2 rounded-lg bg-[#2A3347]/50 border border-[#3D4B5E]">
            {getProviderIcon()}
            <div className="flex-1">
              <div className="text-xs text-slate-400">Event Source</div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-200 font-medium">
                  {webhook.provider} • {webhook.event_type}
                </span>
              </div>
            </div>
          </div>

          {/* Webhook URL */}
          <div className="space-y-2">
            <div className="text-xs font-medium text-slate-400">Webhook URL</div>
            <div className="flex items-center gap-2 p-2 rounded-lg bg-[#2A3347] group relative">
              <code className="text-sm text-slate-300 font-mono break-all flex-1">
                {webhook.webhook_url}
              </code>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCopyUrl}
                className="h-8 text-sm text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10"
              >
                <Copy className="h-4 w-4 mr-2" />
                Copy
              </Button>
            </div>
          </div>

          {/* Prompt Template */}
          <div className="space-y-2">
            <div className="text-xs font-medium text-slate-400">Prompt Template</div>
            <div className="bg-[#2A3347] rounded-lg p-3">
              {formatPromptWithContext(webhook.prompt_template)}
            </div>
          </div>

          {/* Test Webhook */}
          <div className="space-y-2">
            <div className="text-xs font-medium text-slate-400">Test Webhook</div>
            <div className="bg-[#2A3347] rounded-lg p-3 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-slate-200">Payload</h4>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsCustomPayload(!isCustomPayload)}
                  className="text-xs text-slate-400 hover:text-emerald-400"
                >
                  {isCustomPayload ? 'Use Default' : 'Custom Payload'}
                </Button>
              </div>

              {isCustomPayload ? (
                <Textarea
                  value={testPayload || JSON.stringify({ test: true }, null, 2)}
                  onChange={(e) => setTestPayload(e.target.value)}
                  className="min-h-[150px] font-mono text-sm bg-[#1A1F2E] border-[#3D4B5E] text-slate-300"
                  placeholder="Enter your custom JSON payload..."
                />
              ) : (
                <pre className="p-3 rounded-lg bg-[#1A1F2E] border border-[#3D4B5E] text-sm text-slate-400 font-mono overflow-auto max-h-[150px]">
                  {JSON.stringify({ test: true }, null, 2)}
                </pre>
              )}

              <div className="flex items-center gap-2">
                <Button
                  onClick={handleTestWebhook}
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

          {/* Setup Instructions */}
          <div className="space-y-2">
            <div className="text-xs font-medium text-slate-400">Setup Instructions</div>
            <div className="bg-[#2A3347] rounded-lg p-3">
              {getProviderSetupInstructions()}
            </div>
          </div>

          {/* Metadata */}
          <div className="pt-3 border-t border-[#2A3347] space-y-2">
            <div className="flex items-center justify-between">
              <div className="text-xs text-slate-400">
                Webhook ID: <span className="font-mono">{webhook.id}</span>
              </div>
              <div className="text-xs text-slate-400">
                Created: {new Date(webhook.created_at).toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 