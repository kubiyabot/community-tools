import * as React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/app/components/ui/card';
import { FormField, FormItem, FormLabel, FormControl, FormDescription, FormMessage } from '@/app/components/ui/form';
import { Textarea } from '@/app/components/ui/textarea';
import { useInstallToolContext } from '../context';
import { Input } from '@/app/components/ui/input';
import { Info, AlertCircle, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/app/components/ui/tooltip";
import { cn } from '@/lib/utils';
import type { InstallationStep } from '../types';
import { InstallationProgress } from './InstallationProgress';
import { Button } from '@/app/components/ui/button';
import { Alert, AlertTitle, AlertDescription } from '@/app/components/ui/alert';
import type { FormValues as SchemaFormValues } from '../schema';
import { useFormContext } from 'react-hook-form';
import { useState, useEffect } from 'react';

interface ExtendedInstallationStatus {
  isLoading: boolean;
  error: string | null;
  data: {
    uuid?: string;
    errors?: Array<{
      file: string;
      error: string;
      details?: string;
    }>;
  };
  isComplete: boolean;
  steps: InstallationStep[];
}

type FormValues = SchemaFormValues;

interface ConfigureStepProps {
  isInstallationComplete: boolean;
}

const GITHUB_BASE_URL = 'https://github.com/kubiyabot/community-tools/tree/main';
const COMMUNITY_TOOLS_BASE = 'https://github.com/kubiyabot/community-tools';
const DEFAULT_BRANCH = 'main';

const getFullToolUrl = (path: string): string => {
  if (!path) return '';
  if (path.startsWith('http')) return path;
  return `${GITHUB_BASE_URL}/${path}`;
};

export function ConfigureStep({ isInstallationComplete }: ConfigureStepProps) {
  const { teammate, selectedTool, formState, installationSteps } = useInstallToolContext();
  const { control, setValue, watch } = useFormContext();
  const [customBranch, setCustomBranch] = useState(false);
  
  // Watch the name field to construct the URL
  const name = watch('name');
  const branch = watch('branch') || DEFAULT_BRANCH;

  // Set initial URL when name changes
  useEffect(() => {
    if (name && selectedTool?.type === 'community') {
      const toolPath = `${COMMUNITY_TOOLS_BASE}/tree/${branch}/${name}`;
      setValue('url', toolPath);
    }
  }, [name, branch, selectedTool, setValue]);

  // Add null check for installationSteps
  const showProgress = formState.installation?.isLoading || 
    (Array.isArray(installationSteps) && installationSteps.some((step: InstallationStep) => step.status !== 'pending'));

  // Handle source errors display
  const getSourceErrors = React.useCallback(() => {
    if (!formState.installation?.data?.errors?.length) return null;

    return (
      <Alert className="mt-4 bg-amber-500/10 border-amber-500/20">
        <AlertCircle className="h-5 w-5 text-amber-400" />
        <AlertTitle className="text-amber-400">Installation Warnings</AlertTitle>
        <AlertDescription className="space-y-4 mt-4">
          {formState.installation.data.errors.map((error: { file: string; error: string; details?: string }, index: number) => (
            <div key={index} className="p-3 rounded-md bg-amber-500/5 border border-amber-500/10">
              <p className="text-sm font-medium text-amber-400">{error.file}</p>
              <p className="text-sm text-amber-400/80 mt-1">{error.error}</p>
              {error.details && (
                <p className="text-sm text-amber-400/60 mt-1">{error.details}</p>
              )}
            </div>
          ))}
        </AlertDescription>
      </Alert>
    );
  }, [formState.installation?.data?.errors]);

  // Format dynamic_config for display
  const formatDynamicConfig = (config: any): string => {
    try {
      // If it's already an object
      if (typeof config === 'object' && config !== null) {
        return Object.keys(config).length ? JSON.stringify(config, null, 2) : '{}';
      }
      
      // If it's a string, try to parse it
      if (typeof config === 'string') {
        const trimmed = config.trim();
        if (!trimmed || trimmed === '[object Object]') return '{}';
        const parsed = JSON.parse(trimmed);
        return JSON.stringify(parsed, null, 2);
      }
      
      return '{}';
    } catch (e) {
      return '{}';
    }
  };

  // Only show success message when both conditions are met
  const isFullyComplete = isInstallationComplete && 
    installationSteps?.every((step) => step.status === 'success');

  return (
    <div className="space-y-6">
      {/* Installation Progress */}
      {showProgress && (
        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg font-medium">Installation Progress</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <InstallationProgress steps={installationSteps || []} />
          </CardContent>
        </Card>
      )}

      {/* Error Message */}
      {formState.installation?.error && (
        <Alert className="bg-red-500/10 border-red-500/20">
          <XCircle className="h-5 w-5 text-red-400" />
          <AlertTitle className="text-red-400">Installation Failed</AlertTitle>
          <AlertDescription>{formState.installation.error}</AlertDescription>
        </Alert>
      )}

      {/* Success Message - Updated condition */}
      {isFullyComplete && (
        <Alert className="bg-green-500/10 border-green-500/20">
          <CheckCircle2 className="h-5 w-5 text-green-400" />
          <AlertTitle className="text-green-400">Installation Complete</AlertTitle>
          <AlertDescription>
            The tool has been successfully installed and configured!
            <p className="text-sm mt-2 text-green-400/70">
              This dialog will close automatically in a few seconds...
            </p>
          </AlertDescription>
        </Alert>
      )}

      {/* Source Errors/Warnings */}
      {getSourceErrors()}

      {/* Configuration Form */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg font-medium">Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <FormField
            control={control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Name</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* Branch selection for community tools */}
          {selectedTool?.type === 'community' && (
            <FormField
              control={control}
              name="branch"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="flex items-center gap-2">
                    <span>Branch</span>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger>
                          <Info className="h-4 w-4 text-slate-400" />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Select branch for the community tools repository</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </FormLabel>
                  <div className="flex gap-2">
                    <FormControl>
                      <Input 
                        {...field}
                        placeholder={DEFAULT_BRANCH}
                        className="bg-slate-800/50 font-mono"
                        disabled={!customBranch || formState.installation?.isLoading}
                      />
                    </FormControl>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        setCustomBranch(!customBranch);
                        if (!customBranch) {
                          setValue('branch', '');
                        } else {
                          setValue('branch', DEFAULT_BRANCH);
                        }
                      }}
                      className="whitespace-nowrap"
                    >
                      {customBranch ? 'Use Default' : 'Custom Branch'}
                    </Button>
                  </div>
                  <FormDescription className="text-slate-400">
                    {customBranch ? 'Enter custom branch name' : `Using default branch (${DEFAULT_BRANCH})`}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          )}

          {/* URL field - read-only for community tools */}
          <FormField
            control={control}
            name="url"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="flex items-center gap-2">
                  <span>Source URL</span>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger>
                        <Info className="h-4 w-4 text-slate-400" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>The URL to the Git repository containing the tools</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </FormLabel>
                <FormControl>
                  <Input 
                    {...field}
                    readOnly={selectedTool?.type === 'community'}
                    className="bg-slate-800/50 font-mono"
                    disabled={formState.installation?.isLoading}
                  />
                </FormControl>
                <FormDescription className="text-slate-400">
                  {selectedTool?.type === 'community' 
                    ? 'URL is automatically generated for community tools'
                    : 'Enter the full URL to the Git repository'}
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={control}
            name="dynamic_config"
            render={({ field: { onChange, value, ...field } }) => (
              <FormItem>
                <FormLabel className="flex items-center gap-2">
                  <span>Dynamic Configuration</span>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Info className="h-4 w-4 text-slate-400" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Optional configuration in JSON format</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </FormLabel>
                <FormControl>
                  <Textarea 
                    {...field}
                    value={(() => {
                      try {
                        // Always ensure we have an object
                        const config = value || {};
                        // Convert to formatted JSON string
                        return JSON.stringify(config, null, 2);
                      } catch (err) {
                        console.error('Error stringifying value:', err);
                        return '{}';
                      }
                    })()}
                    onChange={(e) => {
                      const inputValue = e.target.value.trim();
                      try {
                        // Parse input to object
                        const config = inputValue ? JSON.parse(inputValue) : {};
                        onChange(config);
                      } catch (err) {
                        // Keep current value on error
                        console.error('Invalid JSON:', err);
                      }
                    }}
                    placeholder="Enter JSON configuration..."
                    className="min-h-[150px] bg-slate-800/50 font-mono"
                    disabled={formState.installation?.isLoading}
                  />
                </FormControl>
                <FormDescription className="text-slate-400">
                  Enter valid JSON configuration or leave empty for default settings
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </CardContent>
      </Card>
    </div>
  );
} 