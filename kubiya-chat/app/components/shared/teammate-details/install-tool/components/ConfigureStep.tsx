import * as React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/app/components/ui/card';
import { FormField, FormItem, FormLabel, FormControl, FormDescription } from '@/app/components/ui/form';
import { Textarea } from '@/app/components/ui/textarea';
import { useInstallToolContext } from '../context';
import { styles } from '../styles';
import { Input } from '@/app/components/ui/input';
import { Info } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/app/components/ui/tooltip";
import { cn } from '@/lib/utils';

export function ConfigureStep() {
  const { methods, teammate } = useInstallToolContext();
  const runnerName = teammate?.runners?.[0] || 'kubiya-hosted';

  // Force set the runner value when component mounts
  React.useEffect(() => {
    methods.setValue('runner', runnerName);
  }, [methods, runnerName]);

  return (
    <Card className={cn(
      "border-slate-800 bg-slate-900/50",
      "dark:border-slate-800 dark:bg-slate-900/50"
    )}>
      <CardHeader>
        <CardTitle className="text-slate-200">Advanced Configuration</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <FormField
          control={methods.control}
          name="runner"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-slate-200">Runner</FormLabel>
              <FormControl>
                <Input
                  {...field}
                  value={runnerName}
                  disabled
                  className={cn(
                    "bg-slate-800/50 text-slate-400 cursor-not-allowed",
                    "border-slate-700 focus-visible:ring-purple-400/20"
                  )}
                />
              </FormControl>
              <FormDescription className="text-slate-400">
                Tools will run on this teammate's assigned runner
              </FormDescription>
            </FormItem>
          )}
        />

        <FormField
          control={methods.control}
          name="dynamic_config"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-slate-200">Dynamic Configuration</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="{}"
                  className={cn(
                    "font-mono bg-slate-800/50 text-slate-200",
                    "border-slate-700 focus-visible:ring-purple-400/20",
                    "min-h-[100px]"
                  )}
                  {...field}
                />
              </FormControl>
              <FormDescription className="text-slate-400">
                Optional JSON configuration for the tools
              </FormDescription>
            </FormItem>
          )}
        />
      </CardContent>
    </Card>
  );
} 