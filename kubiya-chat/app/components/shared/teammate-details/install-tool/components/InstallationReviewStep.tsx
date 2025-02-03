import * as React from 'react';
import { Card, CardContent } from '@/app/components/ui/card';
import { Badge } from '@/app/components/ui/badge';
import { Box as Cube, Info, Server } from 'lucide-react';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/app/components/ui/hover-card';
import { useInstallToolContext } from '../context';
import { styles } from '../styles';
import type { Tool } from '@/app/types/tool';
import type { TeammateDetails } from '@/app/types/teammate';

function isK8sTool(tool: Tool): boolean {
  console.log(tool);
  // for now, we'll just assume all tools are k8s tools
  return true;
}

export function InstallationReviewStep() {
  const { formState } = useInstallToolContext();
  const { data } = formState.preview;
  const runner = formState.runner;  // Get runner from formState

  if (!data) return null;

  const hasK8sPlugins = data.tools.some(isK8sTool);

  return (
    <div className="space-y-6">
      {/* Show runner info */}
      <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-800">
        <div className="flex items-center gap-2">
          <Server className="h-4 w-4 text-blue-400" />
          <span className="text-sm text-slate-200">Installing on runner: {runner}</span>
        </div>
      </div>

      {/* Installation Context */}
      <Card className={styles.cards.base}>
        <CardContent className="p-6">
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-slate-200">Installation Details</h3>
            
            {/* Runner Info */}
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20 flex items-center gap-1">
                <Cube className="h-3 w-3" />
                Running on: {runner}
              </Badge>
              
              {hasK8sPlugins && (
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20">
                    Includes K8s Plugins
                  </Badge>
                  <HoverCard>
                    <HoverCardTrigger>
                      <Info className="h-4 w-4 text-slate-400 cursor-help" />
                    </HoverCardTrigger>
                    <HoverCardContent className="w-80">
                      <p className="text-sm text-slate-400">
                        Some tools will install components on the Kubernetes cluster where the runner operates
                      </p>
                    </HoverCardContent>
                  </HoverCard>
                </div>
              )}
            </div>

            {/* Tools Summary */}
            <div className="mt-4">
              <p className="text-sm text-slate-400">
                Installing {data.tools.length} tool{data.tools.length !== 1 && 's'} from {data.source.name}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tools List */}
      <div className="space-y-4">
        {data.tools.map((tool: Tool) => (
          <Card key={tool.name} className={styles.cards.base}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="text-sm font-medium text-slate-200">{tool.name}</h4>
                  <p className="text-xs text-slate-400 mt-1">{tool.description}</p>
                </div>
                {isK8sTool(tool) && (
                  <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20">
                    K8s Plugin
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
} 