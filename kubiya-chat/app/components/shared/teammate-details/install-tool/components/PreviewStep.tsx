import * as React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/app/components/ui/card';
import { Badge } from '@/app/components/ui/badge';
import { Code, Loader2, Ship, Settings } from 'lucide-react';
import { useInstallToolContext } from '../context';
import { styles } from '../styles';
import { Button } from '@/app/components/ui/button';
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/app/components/ui/hover-card";
import { ToolDetailsModal } from '../../../tool-details/ToolDetailsModal';
import { cn } from '@/lib/utils';

export function PreviewStep() {
  const { formState, selectedTool } = useInstallToolContext();
  const { isLoading, error, data } = formState.preview;
  const [selectedToolDetails, setSelectedToolDetails] = React.useState<any>(null);

  const toolsToShow = data?.tools || selectedTool?.tools || [];

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

  if (!toolsToShow.length) {
    return (
      <div className="text-center p-8">
        <p className={styles.text.primary}>No tools found</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card className={cn(
        "border-slate-800 bg-slate-900/50",
        "dark:border-slate-800 dark:bg-slate-900/50"
      )}>
        <CardHeader>
          <CardTitle className="text-slate-200">Available Tools</CardTitle>
          <p className="text-sm text-slate-400">Review the tools that will be installed</p>
        </CardHeader>
        <CardContent className="space-y-4">
          {toolsToShow.map((tool: any) => (
            <HoverCard key={tool.name} openDelay={200}>
              <HoverCardTrigger asChild>
                <div className={cn(
                  "flex items-start gap-3 p-4 rounded-md transition-all group",
                  "bg-slate-800/50 border border-slate-700",
                  "hover:border-purple-500/30"
                )}>
                  <div className="p-2 rounded-md bg-purple-500/10 border border-purple-500/20">
                    {tool.icon_url ? (
                      <img src={tool.icon_url} alt={tool.name} className="h-5 w-5" />
                    ) : (
                      <Code className="h-5 w-5 text-purple-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-slate-200 group-hover:text-purple-400 transition-colors">
                          {tool.name}
                        </p>
                        {tool.type && (
                          <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/20">
                            {tool.type}
                          </Badge>
                        )}
                      </div>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={() => setSelectedToolDetails(tool)}
                      >
                        View Details
                      </Button>
                    </div>
                    <p className="text-sm text-slate-400 mt-1">{tool.description}</p>
                    
                    <div className="flex items-center gap-4 mt-3">
                      {tool.args && (
                        <div className="flex items-center gap-1.5 text-xs text-slate-400">
                          <Settings className="h-3.5 w-3.5" />
                          <span>{tool.args.length} parameters</span>
                        </div>
                      )}
                      {tool.image && (
                        <div className="flex items-center gap-1.5 text-xs text-slate-400">
                          <Ship className="h-3.5 w-3.5" />
                          <span>Docker Image</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </HoverCardTrigger>
              <HoverCardContent className="w-80 bg-slate-900 border-slate-800">
                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-slate-200">{tool.name}</h4>
                  {tool.args && tool.args.length > 0 && (
                    <div className="space-y-2">
                      <h5 className="text-xs font-medium text-slate-300">Parameters:</h5>
                      <div className="grid gap-1.5">
                        {tool.args.map((arg: any, idx: number) => (
                          <div key={idx} className="text-xs">
                            <code className="px-1.5 py-0.5 bg-slate-800 rounded text-slate-300">
                              {arg.name}
                            </code>
                            {arg.required && (
                              <Badge variant="outline" className="ml-2 text-[10px] bg-red-500/10 text-red-400 border-red-500/20">
                                Required
                              </Badge>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </HoverCardContent>
            </HoverCard>
          ))}
        </CardContent>
      </Card>

      {selectedToolDetails && (
        <ToolDetailsModal
          isOpen={!!selectedToolDetails}
          onCloseAction={() => setSelectedToolDetails(null)}
          tool={selectedToolDetails}
          source={data?.source}
        />
      )}
    </div>
  );
} 