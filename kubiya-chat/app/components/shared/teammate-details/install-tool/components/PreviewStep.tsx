import * as React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/app/components/ui/card';
import { Badge } from '@/app/components/ui/badge';
import { Code, Loader2 } from 'lucide-react';
import { useInstallToolContext } from '../context';
import { styles } from '../styles';

export function PreviewStep() {
  const { formState } = useInstallToolContext();
  const { isLoading, error, data } = formState.preview;

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 p-8">
        <div className="relative">
          <div className="absolute inset-0 animate-ping rounded-full bg-purple-400/20" />
          <Loader2 className="h-8 w-8 text-purple-400 animate-spin relative" />
        </div>
        <div className="text-center">
          <p className={styles.text.primary + " text-sm font-medium"}>Analyzing Tools</p>
          <p className={styles.text.secondary + " text-xs mt-1"}>
            Reading tool definitions and validating configuration...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-500/30 bg-red-500/10">
        <CardContent className="p-6">
          <div className="text-red-400 text-sm">{error}</div>
        </CardContent>
      </Card>
    );
  }

  if (!data?.tools?.length) {
    return (
      <div className="text-center p-8">
        <p className={styles.text.primary}>No tools found</p>
      </div>
    );
  }

  return (
    <Card className={styles.cards.base}>
      <CardHeader>
        <CardTitle className={styles.text.primary}>Available Tools</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {data.tools.map((tool: any) => (
          <div 
            key={tool.name}
            className="flex items-start gap-3 p-3 rounded-md bg-[#0F172A]/50 border border-[#2A3347]"
          >
            <div className="p-2 rounded-md bg-purple-500/10 border border-purple-500/20">
              <Code className="h-5 w-5 text-purple-400" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-slate-200">{tool.name}</p>
                {tool.type && (
                  <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/20">
                    {tool.type}
                  </Badge>
                )}
              </div>
              <p className="text-sm text-slate-400 mt-1">{tool.description}</p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
} 