import { WebhookEvent, WebhookProvider } from '../providers';
import { Button } from '../../ui/button';
import { cn } from '../../../lib/utils';
import { Badge } from '../../ui/badge';
import { Copy, PlayCircle } from 'lucide-react';
import { toast } from '../../ui/use-toast';
import { Textarea } from '../../ui/textarea';
import { useState } from 'react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../../ui/tooltip";

interface EventExampleProps {
  selectedProvider: WebhookProvider | null;
  selectedEvent: string;
  onContinue: () => void;
}

export function EventExample({
  selectedProvider,
  selectedEvent,
  onContinue
}: EventExampleProps) {
  const [customJson, setCustomJson] = useState('{\n  "example": "value"\n}');
  const [jsonError, setJsonError] = useState<string | null>(null);

  if (!selectedProvider) return null;

  const isCustomProvider = selectedProvider.id === 'custom';
  const event = !isCustomProvider ? selectedProvider.events.find((e: WebhookEvent) => e.type === selectedEvent) : null;

  const validateJson = (jsonString: string): boolean => {
    try {
      JSON.parse(jsonString);
      setJsonError(null);
      return true;
    } catch (e) {
      setJsonError((e as Error).message);
      return false;
    }
  };

  const handleCustomJsonChange = (value: string) => {
    setCustomJson(value);
    validateJson(value);
  };

  const handleCopyExample = () => {
    const textToCopy = isCustomProvider ? customJson : JSON.stringify(event?.example, null, 2);
    navigator.clipboard.writeText(textToCopy);
    toast({
      title: "Copied to clipboard",
      description: "Event example has been copied to your clipboard."
    });
  };

  const handleContinue = () => {
    if (isCustomProvider) {
      if (validateJson(customJson)) {
        onContinue();
      }
    } else {
      onContinue();
    }
  };

  if (isCustomProvider) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-3">
            <h5 className="text-sm font-medium text-slate-300">Example Payload</h5>
            <div className="space-y-2">
              <Textarea
                value={customJson}
                onChange={(e) => handleCustomJsonChange(e.target.value)}
                className="min-h-[400px] font-mono text-sm bg-[#141B2B] border-[#2D3B4E] text-slate-300"
                placeholder="Paste your JSON structure here..."
              />
              {jsonError && (
                <p className="text-sm text-red-400">
                  {jsonError}
                </p>
              )}
            </div>
          </div>
          <div className="space-y-3">
            <h5 className="text-sm font-medium text-slate-300">Instructions</h5>
            <div className="p-4 rounded-lg bg-[#141B2B] border border-[#2D3B4E] text-sm text-slate-400">
              <ol className="list-decimal list-inside space-y-2">
                <li>Paste your webhook's JSON payload structure</li>
                <li>Make sure it's valid JSON format</li>
                <li>This structure will be used to identify available variables for your prompt template</li>
              </ol>
            </div>
            <div className="flex items-center gap-2 mt-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCopyExample}
                className="h-8 text-sm text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition-all"
              >
                <Copy className="h-4 w-4 mr-2" />
                Copy JSON
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={handleContinue}
                disabled={!!jsonError}
                className={cn(
                  "h-8 text-white shadow-sm",
                  !jsonError 
                    ? "bg-emerald-500 hover:bg-emerald-600 shadow-emerald-500/20" 
                    : "bg-slate-600 cursor-not-allowed"
                )}
              >
                <PlayCircle className="h-4 w-4 mr-2" />
                Continue to Prompt
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!event) return null;

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h3 className="text-lg font-medium text-slate-200">Event Example</h3>
        <p className="text-sm text-slate-400">
          This is an example of the data that will be available when this event is triggered.
          You can use these variables in your prompt template.
        </p>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <event.icon className="h-5 w-5 text-emerald-400" />
            <h4 className="font-medium text-slate-200">{event.name}</h4>
            <Badge variant="outline" className="bg-emerald-500/10 border-emerald-500/30 text-emerald-400">
              {event.variables.length} variable{event.variables.length === 1 ? '' : 's'}
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopyExample}
              className="h-8 text-sm text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition-all"
            >
              <Copy className="h-4 w-4 mr-2" />
              Copy Example
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={handleContinue}
              className="h-8 bg-emerald-500 hover:bg-emerald-600 text-white shadow-sm shadow-emerald-500/20"
            >
              <PlayCircle className="h-4 w-4 mr-2" />
              Continue to Prompt
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-3">
            <h5 className="text-sm font-medium text-slate-300">Available Variables</h5>
            <div className="grid grid-cols-2 gap-2">
              {event.variables.map((variable: string) => (
                <TooltipProvider key={variable}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Badge 
                        variant="outline" 
                        className="bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 transition-colors cursor-help"
                      >
                        {variable}
                      </Badge>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="max-w-sm">
                      <p className="text-xs font-medium mb-1">Example value:</p>
                      <pre className="text-xs bg-slate-900 p-2 rounded overflow-auto max-h-32">
                        {typeof event.example[variable] === 'object' 
                          ? JSON.stringify(event.example[variable], null, 2) 
                          : String(event.example[variable])}
                      </pre>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <h5 className="text-sm font-medium text-slate-300">Example Payload</h5>
            <pre className="p-4 rounded-lg bg-[#141B2B] border border-[#2D3B4E] text-sm text-slate-400 overflow-auto max-h-[400px]">
              {JSON.stringify(event.example, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
} 