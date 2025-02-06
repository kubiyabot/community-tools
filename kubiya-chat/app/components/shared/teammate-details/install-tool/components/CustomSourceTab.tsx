import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card';
import { FormField, FormItem, FormLabel, FormControl, FormDescription, FormMessage } from '@/app/components/ui/form';
import { Input } from '@/app/components/ui/input';
import { styles } from '../styles';
import type { UseFormReturn } from 'react-hook-form';
import { Button } from '@/app/components/ui/button';
import { Loader2, AlertCircle, PackageSearch, Code, Settings, Database, Box, Terminal, ChevronDown, ChevronUp, Info } from 'lucide-react';
import { Alert, AlertTitle, AlertDescription } from '@/app/components/ui/alert';
import { Badge } from '@/app/components/ui/badge';
import { cn } from '@/lib/utils';
import { ScrollArea } from '@/app/components/ui/scroll-area';
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/app/components/ui/hover-card";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/app/components/ui/tooltip";
import { useEffect, useState } from 'react';
import type { TeammateDetails } from '@/app/types/teammate';
import { Switch } from '@/app/components/ui/switch';
import { Label } from '@/app/components/ui/label';
import { Textarea } from '@/app/components/ui/textarea';

interface CustomSourceTabProps {
  methods: UseFormReturn<any>;
  teammate: TeammateDetails;
}

interface PreviewTool {
  name: string;
  description?: string;
  type?: string;
  args?: Array<{
    name: string;
    type: string;
    description: string;
    required?: boolean;
  }>;
  secrets?: string[];
  env?: string[];
  image?: string;
  icon_url?: string;
}

interface PreviewData {
  tools: PreviewTool[];
  errors?: Array<{
    file: string;
    error: string;
    details?: string;
  }>;
}

export function CustomSourceTab({ methods, teammate }: CustomSourceTabProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [useDynamicConfig, setUseDynamicConfig] = useState(false);
  const [configFormat, setConfigFormat] = useState<'json' | 'keyvalue'>('json');
  const [keyValuePairs, setKeyValuePairs] = useState<Array<{ key: string; value: string }>>([{ key: '', value: '' }]);

  // Function to get the first runner from teammate
  const getTeammateRunner = () => {
    if (!teammate || !Array.isArray(teammate.runners) || teammate.runners.length === 0) {
      return null;
    }
    // According to TeammateDetails interface, runners is string[]
    return teammate.runners[0];
  };

  // Function to load preview data
  const loadPreview = async (url: string) => {
    if (!url) return;
    
    try {
      setIsLoading(true);
      setError(null);
      setPreviewData(null);

      const runner = getTeammateRunner();
      if (!runner) {
        throw new Error('No runner available for this teammate. Please configure a runner first.');
      }

      const response = await fetch(`/api/v1/sources/load?url=${encodeURIComponent(url)}&runner=${encodeURIComponent(runner)}`);
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || `Failed to load source preview`);
      }

      const data = await response.json();
      setPreviewData(data);
    } catch (err) {
      console.error('Error loading preview:', err);
      setError(err instanceof Error ? err.message : 'Failed to load source preview');
    } finally {
      setIsLoading(false);
    }
  };

  // Watch for URL changes
  useEffect(() => {
    const subscription = methods.watch((value, { name }) => {
      if (name === 'url' && value.url) {
        loadPreview(value.url);
      }
    });
    return () => subscription.unsubscribe();
  }, [methods]);

  // Function to validate JSON
  const isValidJSON = (str: string) => {
    try {
      JSON.parse(str);
      return true;
    } catch (e) {
      return false;
    }
  };

  // Convert key-value pairs to JSON
  const keyValueToJSON = () => {
    const json = keyValuePairs.reduce((acc, { key, value }) => {
      if (key.trim()) {
        try {
          // Try to parse the value as JSON if it looks like an object or array
          if ((value.startsWith('{') && value.endsWith('}')) || 
              (value.startsWith('[') && value.endsWith(']'))) {
            acc[key.trim()] = JSON.parse(value);
          } else {
            acc[key.trim()] = value;
          }
        } catch {
          acc[key.trim()] = value;
        }
      }
      return acc;
    }, {} as Record<string, any>);
    return JSON.stringify(json, null, 2);
  };

  // Handle dynamic config toggle
  const handleDynamicConfigToggle = (checked: boolean) => {
    setUseDynamicConfig(checked);
    if (!checked) {
      methods.setValue('dynamic_config', '');
      setKeyValuePairs([{ key: '', value: '' }]);
    }
  };

  // Handle format change
  const handleFormatChange = (newFormat: 'json' | 'keyvalue') => {
    setConfigFormat(newFormat);
    if (newFormat === 'keyvalue') {
      // Convert current JSON to key-value pairs if possible
      try {
        const currentValue = methods.getValues('dynamic_config');
        if (currentValue) {
          const parsed = JSON.parse(currentValue);
          const pairs = Object.entries(parsed).map(([key, value]) => ({
            key,
            value: typeof value === 'object' ? JSON.stringify(value) : String(value)
          }));
          setKeyValuePairs(pairs.length ? pairs : [{ key: '', value: '' }]);
        }
      } catch {
        setKeyValuePairs([{ key: '', value: '' }]);
      }
    } else {
      // Convert key-value pairs to JSON
      methods.setValue('dynamic_config', keyValueToJSON());
    }
  };

  // Handle key-value pair changes
  const handleKeyValueChange = (index: number, field: 'key' | 'value', value: string) => {
    const newPairs = [...keyValuePairs];
    newPairs[index][field] = value;
    setKeyValuePairs(newPairs);
    
    // Update the form value
    methods.setValue('dynamic_config', keyValueToJSON());
  };

  // Add new key-value pair
  const addKeyValuePair = () => {
    setKeyValuePairs([...keyValuePairs, { key: '', value: '' }]);
  };

  // Remove key-value pair
  const removeKeyValuePair = (index: number) => {
    const newPairs = keyValuePairs.filter((_, i) => i !== index);
    setKeyValuePairs(newPairs.length ? newPairs : [{ key: '', value: '' }]);
    methods.setValue('dynamic_config', keyValueToJSON());
  };

  function ToolCard({ tool }: { tool: PreviewTool }) {
    const paramCount = tool.args?.length || 0;
    const secretCount = tool.secrets?.length || 0;
    const envCount = tool.env?.length || 0;

    return (
      <div className="group relative bg-[#1E293B]/50 hover:bg-[#1E293B] rounded-lg border border-[#1E293B] hover:border-[#7C3AED]/50 transition-all duration-200">
        <div className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-md bg-[#2A3347] border border-[#2A3347]">
                {tool.icon_url ? (
                  <img src={tool.icon_url} alt={tool.name} className="h-5 w-5" />
                ) : (
                  <Code className="h-5 w-5 text-[#7C3AED]" />
                )}
              </div>
              <div>
                <h4 className="text-sm font-medium text-white tracking-wide flex items-center gap-2">
                  {tool.name}
                  {tool.type && (
                    <Badge 
                      variant="outline" 
                      className={cn(
                        "text-xs font-medium tracking-wide",
                        tool.type === 'docker' 
                          ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                          : "bg-purple-500/10 text-purple-400 border-purple-500/20"
                      )}
                    >
                      {tool.type}
                    </Badge>
                  )}
                </h4>
                <p className="text-xs text-[#94A3B8] mt-1 leading-relaxed">{tool.description}</p>
                
                {/* Tool Metadata */}
                <div className="flex items-center gap-3 mt-3">
                  <HoverCard>
                    <HoverCardTrigger asChild>
                      <div className="flex items-center gap-1.5 text-xs text-[#94A3B8] hover:text-[#7C3AED] cursor-help">
                        <Settings className="h-3.5 w-3.5" />
                        <span>{paramCount} params</span>
                      </div>
                    </HoverCardTrigger>
                    <HoverCardContent className="w-80 p-3">
                      <div className="space-y-2">
                        <h5 className="text-sm font-medium text-white">Parameters</h5>
                        <div className="space-y-1.5">
                          {tool.args?.map((param, idx) => (
                            <div key={idx} className="text-xs">
                              <div className="flex items-center gap-1.5">
                                <span className="font-medium text-[#7C3AED]">{param.name}</span>
                                <Badge variant="outline" className="text-[10px]">
                                  {param.type}
                                </Badge>
                                {param.required && (
                                  <Badge className="bg-red-500/10 text-red-400 border-red-500/20 text-[10px]">
                                    required
                                  </Badge>
                                )}
                              </div>
                              <p className="text-[#94A3B8] mt-0.5">{param.description}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </HoverCardContent>
                  </HoverCard>

                  {secretCount > 0 && (
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div className="flex items-center gap-1.5 text-xs text-[#94A3B8] hover:text-[#7C3AED] cursor-help">
                            <Database className="h-3.5 w-3.5" />
                            <span>{secretCount} secrets</span>
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>
                          <div className="space-y-1">
                            {tool.secrets?.map((secret, idx) => (
                              <div key={idx} className="text-xs text-[#94A3B8]">{secret}</div>
                            ))}
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  )}

                  {envCount > 0 && (
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div className="flex items-center gap-1.5 text-xs text-[#94A3B8] hover:text-[#7C3AED] cursor-help">
                            <Box className="h-3.5 w-3.5" />
                            <span>{envCount} env vars</span>
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>
                          <div className="space-y-1">
                            {tool.env?.map((env, idx) => (
                              <div key={idx} className="text-xs text-[#94A3B8]">{env}</div>
                            ))}
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card className={styles.cards.base}>
        <CardContent className="space-y-4 p-6">
          <FormField
            control={methods.control}
            name="url"
            render={({ field }) => (
              <FormItem>
                <FormLabel className={styles.text.primary}>Source URL</FormLabel>
                <FormControl>
                  <Input 
                    placeholder="https://github.com/org/repo" 
                    className="bg-[#1E293B] border-[#2D3B4E] text-slate-200"
                    {...field}
                  />
                </FormControl>
                <FormDescription className={styles.text.secondary}>
                  URL to the Git repository containing the tools
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* Advanced Options Section */}
          <div className="pt-2">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-2 text-sm text-[#94A3B8] hover:text-[#7C3AED] transition-colors"
            >
              {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              Advanced Options
            </button>

            {showAdvanced && (
              <div className="mt-4 space-y-4 pt-4 border-t border-[#2D3B4E]">
                <div className="flex items-start justify-between space-x-4">
                  <div className="space-y-1">
                    <Label className="text-sm text-white">Dynamic Configuration</Label>
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={useDynamicConfig}
                        onCheckedChange={handleDynamicConfigToggle}
                      />
                      <span className="text-sm text-[#94A3B8]">Provide dynamic configuration</span>
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger>
                            <Info className="h-4 w-4 text-[#94A3B8]" />
                          </TooltipTrigger>
                          <TooltipContent className="max-w-sm">
                            <p>Dynamic configuration allows you to provide additional settings that will be passed to the tool during installation.</p>
                            <p className="mt-2 text-xs text-[#94A3B8]">You can provide configuration in either JSON format or as key-value pairs.</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                  </div>
                </div>

                {useDynamicConfig && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-4">
                      <Button
                        type="button"
                        variant={configFormat === 'json' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => handleFormatChange('json')}
                        className={cn(
                          configFormat === 'json' 
                            ? "bg-[#7C3AED] hover:bg-[#6D28D9] text-white"
                            : "border-[#2D3B4E] text-[#94A3B8] hover:text-[#7C3AED]"
                        )}
                      >
                        JSON Format
                      </Button>
                      <Button
                        type="button"
                        variant={configFormat === 'keyvalue' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => handleFormatChange('keyvalue')}
                        className={cn(
                          configFormat === 'keyvalue'
                            ? "bg-[#7C3AED] hover:bg-[#6D28D9] text-white"
                            : "border-[#2D3B4E] text-[#94A3B8] hover:text-[#7C3AED]"
                        )}
                      >
                        Key-Value Pairs
                      </Button>
                    </div>

                    {configFormat === 'json' ? (
                      <FormField
                        control={methods.control}
                        name="dynamic_config"
                        render={({ field }) => (
                          <FormItem>
                            <FormControl>
                              <Textarea
                                placeholder="{}"
                                className="font-mono bg-[#1E293B] border-[#2D3B4E] text-slate-200 min-h-[120px]"
                                {...field}
                                onChange={(e) => {
                                  field.onChange(e);
                                  if (e.target.value && !isValidJSON(e.target.value)) {
                                    methods.setError('dynamic_config', {
                                      type: 'manual',
                                      message: 'Invalid JSON format'
                                    });
                                  } else {
                                    methods.clearErrors('dynamic_config');
                                  }
                                }}
                              />
                            </FormControl>
                            <FormDescription className="text-[#94A3B8]">
                              Enter a valid JSON object for dynamic configuration
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    ) : (
                      <div className="space-y-3">
                        {keyValuePairs.map((pair, index) => (
                          <div key={index} className="flex gap-3">
                            <Input
                              placeholder="Key"
                              value={pair.key}
                              onChange={(e) => handleKeyValueChange(index, 'key', e.target.value)}
                              className="flex-1 bg-[#1E293B] border-[#2D3B4E] text-slate-200"
                            />
                            <Input
                              placeholder="Value"
                              value={pair.value}
                              onChange={(e) => handleKeyValueChange(index, 'value', e.target.value)}
                              className="flex-1 bg-[#1E293B] border-[#2D3B4E] text-slate-200"
                            />
                            <Button
                              type="button"
                              variant="outline"
                              size="icon"
                              onClick={() => removeKeyValuePair(index)}
                              className="border-[#2D3B4E] text-[#94A3B8] hover:text-red-400"
                              disabled={keyValuePairs.length === 1}
                            >
                              <AlertCircle className="h-4 w-4" />
                            </Button>
                          </div>
                        ))}
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={addKeyValuePair}
                          className="mt-2 border-[#2D3B4E] text-[#94A3B8] hover:text-[#7C3AED]"
                        >
                          Add Key-Value Pair
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Preview Section */}
      <div className="space-y-4">
        {isLoading && (
          <div className="flex items-center justify-center p-12">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="h-8 w-8 animate-spin text-[#7C3AED]" />
              <p className="text-sm text-[#94A3B8]">Discovering tools...</p>
            </div>
          </div>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {previewData && (
          <Card className={styles.cards.base}>
            <CardHeader>
              <CardTitle className="text-lg font-medium flex items-center justify-between">
                <span>Discovered Tools</span>
                <Badge variant="outline" className="bg-[#1E293B] border-[#2D3B4E] text-[#94A3B8]">
                  {previewData.tools.length} tools found
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {previewData.tools.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <div className="p-3 rounded-full bg-amber-500/10 border border-amber-500/20">
                    <PackageSearch className="h-6 w-6 text-amber-400" />
                  </div>
                  <h3 className="text-lg font-medium text-white mt-4">No Tools Found</h3>
                  <p className="text-sm text-[#94A3B8] max-w-md mt-2">
                    No tools were discovered in this source. Please check the URL and try again.
                  </p>
                </div>
              ) : (
                <ScrollArea className="h-[400px]">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-1">
                    {previewData.tools.map((tool, index) => (
                      <ToolCard key={`${tool.name}-${index}`} tool={tool} />
                    ))}
                  </div>
                </ScrollArea>
              )}

              {/* Show Errors if any */}
              {previewData.errors && previewData.errors.length > 0 && (
                <div className="mt-6 space-y-3">
                  <h4 className="text-sm font-medium text-white">Issues Found</h4>
                  {previewData.errors.map((error, index) => (
                    <Alert key={index} variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertTitle>{error.file}</AlertTitle>
                      <AlertDescription>
                        {error.error}
                        {error.details && (
                          <p className="text-sm mt-1 text-red-300">{error.details}</p>
                        )}
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
} 