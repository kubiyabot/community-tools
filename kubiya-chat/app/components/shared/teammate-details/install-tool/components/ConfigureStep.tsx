import * as React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/app/components/ui/card';
import { FormField, FormItem, FormLabel, FormControl, FormDescription } from '@/app/components/ui/form';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/app/components/ui/select';
import { Textarea } from '@/app/components/ui/textarea';
import { useInstallToolContext } from '../context';
import { styles } from '../styles';

export function ConfigureStep() {
  const { methods } = useInstallToolContext();

  return (
    <Card className={styles.cards.base}>
      <CardHeader>
        <CardTitle className={styles.text.primary}>Advanced Configuration</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <FormField
          control={methods.control}
          name="runner"
          render={({ field }) => (
            <FormItem>
              <FormLabel className={styles.text.primary}>Runner</FormLabel>
              <Select 
                onValueChange={field.onChange} 
                defaultValue={field.value}
              >
                <FormControl>
                  <SelectTrigger className="bg-[#1E293B] border-[#2D3B4E] text-slate-200">
                    <SelectValue placeholder="Select a runner" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="kubiya-hosted">Kubiya Hosted</SelectItem>
                  <SelectItem value="self-hosted">Self Hosted</SelectItem>
                </SelectContent>
              </Select>
              <FormDescription className={styles.text.secondary}>
                Select the environment where the tools will run
              </FormDescription>
            </FormItem>
          )}
        />

        <FormField
          control={methods.control}
          name="dynamic_config"
          render={({ field }) => (
            <FormItem>
              <FormLabel className={styles.text.primary}>Dynamic Configuration</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="{}"
                  className="font-mono bg-[#1E293B] border-[#2D3B4E] text-slate-200"
                  {...field}
                />
              </FormControl>
              <FormDescription className={styles.text.secondary}>
                Optional JSON configuration for the tools
              </FormDescription>
            </FormItem>
          )}
        />
      </CardContent>
    </Card>
  );
} 