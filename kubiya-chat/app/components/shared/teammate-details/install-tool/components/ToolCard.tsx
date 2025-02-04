import * as React from 'react';
import { Code } from 'lucide-react';
import { Badge } from '@/app/components/ui/badge';
import { cn } from '@/lib/utils';

interface ToolCardProps {
  tool: {
    name: string;
    path: string;
    description?: string;
    category?: string;
    icon_url?: string;
    type?: string;
  };
  onSelect: () => void;
}

export function ToolCard({ tool, onSelect }: ToolCardProps) {
  return (
    <div 
      className="group relative bg-slate-800/50 hover:bg-slate-800 rounded-lg border border-slate-700 hover:border-purple-500/50 transition-all duration-200 cursor-pointer p-4 m-2"
      onClick={onSelect}
    >
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-md bg-slate-700 border border-slate-600">
          {tool.icon_url ? (
            <img src={tool.icon_url} alt={tool.name} className="h-5 w-5" />
          ) : (
            <Code className="h-5 w-5 text-purple-400" />
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
          {tool.description && (
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              {tool.description}
            </p>
          )}
          {tool.category && (
            <div className="mt-2">
              <Badge variant="outline" className="text-xs bg-slate-700/50 text-slate-300 border-slate-600">
                {tool.category}
              </Badge>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 