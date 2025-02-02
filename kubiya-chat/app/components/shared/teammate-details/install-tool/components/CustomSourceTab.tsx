import * as React from 'react';
import { Card, CardContent } from '@/app/components/ui/card';
import { FormField, FormItem, FormLabel, FormControl, FormDescription } from '@/app/components/ui/form';
import { Input } from '@/app/components/ui/input';
import { styles } from '../styles';
import type { UseFormReturn } from 'react-hook-form';

interface CustomSourceTabProps {
  methods: UseFormReturn<any>;
}

export function CustomSourceTab({ methods }: CustomSourceTabProps) {
  return (
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
            </FormItem>
          )}
        />
      </CardContent>
    </Card>
  );
} 