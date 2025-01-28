import React, { useState, useCallback, useEffect } from 'react';
import { Button } from '../../ui/button';
import { toast } from '../../ui/use-toast';
import { WebhookProvider, WebhookEvent } from '../providers';
import { cn } from '../../../lib/utils';
import Editor from '@monaco-editor/react';
import { AlertCircle, Check, Copy, FileJson, Info, AlertTriangle } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../../ui/tooltip';

interface WebhookFlowProps {
  selectedProvider: WebhookProvider;
  selectedEvent: WebhookEvent;
  onEventDataChange: (data: string) => void;
  onValidationChange: (isValid: boolean) => void;
}

export function WebhookFlow({
  selectedProvider,
  selectedEvent,
  onEventDataChange,
  onValidationChange
}: WebhookFlowProps) {
  const [customJson, setCustomJson] = useState<string>(
    selectedEvent?.example ? JSON.stringify(selectedEvent.example, null, 2) : ''
  );
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [showHints, setShowHints] = useState(true);
  const [hasAttemptedContinue, setHasAttemptedContinue] = useState(false);

  useEffect(() => {
    // Reset the attempted continue flag when provider changes
    if (selectedProvider) {
      setHasAttemptedContinue(false);
    }
  }, [selectedProvider]);

  useEffect(() => {
    // Only validate and show errors after user has attempted to continue
    const isSelectionValid = Boolean(selectedProvider && selectedEvent);
    onValidationChange?.(isSelectionValid);
  }, [selectedProvider, selectedEvent, hasAttemptedContinue]);

  // Show event selection if provider is selected
  if (selectedProvider && !selectedEvent) {
    return (
      <div className="space-y-6">
        <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
          <div className="flex items-center gap-2 text-emerald-400">
            <Info className="h-4 w-4" />
            <p className="text-sm">Great! Now please select an event type for {selectedProvider.name}.</p>
          </div>
        </div>
        
        {/* Event selection will be rendered here by the parent component */}
      </div>
    );
  }

  // Show error only if user has attempted to continue without both selections
  if (hasAttemptedContinue && (!selectedProvider || !selectedEvent)) {
    return (
      <div className="space-y-4">
        <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
          <div className="flex items-center gap-2 text-yellow-300">
            <AlertTriangle className="h-4 w-4" />
            <p className="text-sm">Please select both a webhook provider and an event type to continue.</p>
          </div>
        </div>
      </div>
    );
  }

  const validateJson = useCallback((value: string) => {
    try {
      const parsed = JSON.parse(value);
      
      // Validate against schema if it exists
      if (selectedEvent.validation?.jsonSchema) {
        const { required, properties } = selectedEvent.validation.jsonSchema;
        
        // Check required fields
        for (const field of required) {
          if (!parsed[field]) {
            throw new Error(`Missing required field: ${field}`);
          }
        }

        // Validate field types
        for (const [key, value] of Object.entries(properties)) {
          if (parsed[key] && typeof parsed[key] !== value.type) {
            throw new Error(`Invalid type for ${key}: expected ${value.type}`);
          }
        }
      }

      setJsonError(null);
      onValidationChange(true);
      onEventDataChange(value);
      return true;
    } catch (error: unknown) {
      setJsonError(error instanceof Error ? error.message : 'Invalid JSON format');
      onValidationChange(false);
      return false;
    }
  }, [selectedEvent, onValidationChange, onEventDataChange]);

  const handleEditorChange = useCallback((value: string | undefined) => {
    if (!value) return;
    setCustomJson(value);
    validateJson(value);
  }, [validateJson]);

  const handleCopyExample = useCallback(() => {
    setCustomJson(JSON.stringify(selectedEvent.example, null, 2));
    validateJson(JSON.stringify(selectedEvent.example, null, 2));
    toast({
      title: "Example copied",
      description: "The example JSON has been loaded into the editor",
    });
  }, [selectedEvent, validateJson]);

  const handleFormatJson = useCallback(() => {
    try {
      const formatted = JSON.stringify(JSON.parse(customJson), null, 2);
      setCustomJson(formatted);
      validateJson(formatted);
      toast({
        title: "JSON formatted",
        description: "The JSON has been properly formatted",
      });
    } catch (error) {
      toast({
        title: "Format failed",
        description: "Please fix the JSON syntax errors first",
        variant: "destructive",
      });
    }
  }, [customJson, validateJson]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h3 className="text-lg font-medium text-slate-200">
            Custom Event Data
          </h3>
          <p className="text-sm text-slate-400">
            Define the structure of your webhook event
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleCopyExample}
            className="text-xs"
          >
            <Copy className="w-3 h-3 mr-1" />
            Load Example
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleFormatJson}
            className="text-xs"
          >
            <FileJson className="w-3 h-3 mr-1" />
            Format JSON
          </Button>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowHints(!showHints)}
                  className="text-xs"
                >
                  <Info className="w-3 h-3" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                Toggle validation hints
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-5">
        <div className="md:col-span-3">
          <div className="relative">
            <Editor
              height="400px"
              defaultLanguage="json"
              value={customJson}
              onChange={handleEditorChange}
              theme="vs-dark"
              options={{
                minimap: { enabled: false },
                fontSize: 12,
                lineNumbers: "on",
                scrollBeyondLastLine: false,
                wordWrap: "on",
                wrappingIndent: "indent",
                automaticLayout: true,
              }}
              className="border rounded-lg border-slate-700"
            />
            {jsonError && (
              <div className="absolute bottom-0 left-0 right-0 p-2 text-xs text-red-400 bg-red-950/50 border-t border-red-900">
                <AlertCircle className="inline-block w-3 h-3 mr-1" />
                {jsonError}
              </div>
            )}
          </div>
        </div>

        {showHints && selectedEvent.validation && (
          <div className="md:col-span-2 space-y-6">
            <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
              <h4 className="text-sm font-medium text-slate-200 mb-2">
                Required Fields
              </h4>
              <ul className="space-y-2">
                {selectedEvent.validation.required.map((field) => (
                  <li key={field} className="flex items-center text-xs text-slate-400">
                    <Check className="w-3 h-3 mr-1 text-emerald-500" />
                    {field}
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
              <h4 className="text-sm font-medium text-slate-200 mb-2">
                Best Practices
              </h4>
              <ul className="space-y-3">
                {selectedEvent.validation.bestPractices.map((practice) => (
                  <li key={practice.title} className="space-y-1">
                    <h5 className="text-xs font-medium text-slate-300">
                      {practice.title}
                    </h5>
                    <p className="text-xs text-slate-400">
                      {practice.description}
                    </p>
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
              <h4 className="text-sm font-medium text-slate-200 mb-2">
                Helpful Hints
              </h4>
              <ul className="space-y-2">
                {selectedEvent.validation.hints.map((hint, index) => (
                  <li key={index} className="flex items-start text-xs text-slate-400">
                    <Info className="w-3 h-3 mr-1 mt-0.5 text-blue-500" />
                    {hint}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 