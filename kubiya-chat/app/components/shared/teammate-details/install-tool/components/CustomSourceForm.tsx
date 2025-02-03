import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card';
import { Input } from '@/app/components/ui/input';
import { Label } from '@/app/components/ui/label';
import { GitFork } from 'lucide-react';
import { UseFormReturn } from 'react-hook-form';

interface CustomSourceFormProps {
  methods: UseFormReturn<any>;
  onChange: (url: string) => void;
}

export function CustomSourceForm({ methods, onChange }: CustomSourceFormProps) {
  return (
    <Card className="bg-slate-900/50 border-slate-800">
      <CardHeader>
        <CardTitle className="text-lg font-medium text-slate-200 flex items-center gap-2">
          <GitFork className="h-5 w-5 text-purple-400" />
          Custom Source
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="url" className="text-sm text-slate-200">
            Repository URL
          </Label>
          <Input
            id="url"
            placeholder="https://github.com/username/repo"
            className="bg-slate-800 border-slate-700 text-slate-200"
            {...methods.register('url', {
              required: 'Repository URL is required',
              pattern: {
                value: /^https?:\/\/.+/,
                message: 'Must be a valid URL'
              },
              onChange: (e) => {
                methods.register('url').onChange(e);
                onChange(e.target.value);
              }
            })}
          />
          {methods.formState.errors.url && (
            <p className="text-sm text-red-400">
              {methods.formState.errors.url.message as string}
            </p>
          )}
          <p className="text-xs text-slate-400 mt-2">
            Enter the URL of a Git repository containing your tools
          </p>
        </div>
      </CardContent>
    </Card>
  );
} 