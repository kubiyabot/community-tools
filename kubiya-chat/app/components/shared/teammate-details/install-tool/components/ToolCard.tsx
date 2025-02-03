import { useState } from 'react';
import { Card } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { ChevronDown, ChevronUp, PackageOpen } from 'lucide-react';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/app/components/ui/hover-card';
import { cn } from '@/lib/utils';
import type { CommunityTool } from '../types';
import { MarkdownText } from '@/app/components/assistant-ui/MarkdownText';

interface ToolCardProps {
  tool: CommunityTool;
  isSelected: boolean;
  isExpanded: boolean;
  onSelect: (tool: CommunityTool) => void;
  onToggleExpand: () => void;
  Icon?: React.ComponentType<{ className?: string }>;
}

export function ToolCard({ 
  tool, 
  isSelected, 
  isExpanded,
  onSelect, 
  onToggleExpand,
  Icon 
}: ToolCardProps) {
  const [isReadmeLoading, setIsReadmeLoading] = useState(false);
  const [readme, setReadme] = useState<string | null>(null);

  const loadReadme = async () => {
    if (readme || isReadmeLoading) return;
    setIsReadmeLoading(true);
    try {
      const response = await fetch(`/api/sources/community/${tool.path}/readme`);
      const data = await response.json();
      setReadme(data.content);
    } catch (error) {
      console.error('Failed to load README:', error);
    } finally {
      setIsReadmeLoading(false);
    }
  };

  return (
    <Card
      className={cn(
        "transition-all duration-200 cursor-pointer",
        "hover:border-purple-500/30",
        isSelected && "ring-2 ring-purple-500 border-purple-500",
        isExpanded && "col-span-2",
        tool.loadingState === 'error' && "border-red-500/30"
      )}
      onClick={() => onSelect(tool)}
    >
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-md bg-purple-500/10 border border-purple-500/20">
            {Icon ? (
              <Icon className="h-8 w-8 text-purple-400" />
            ) : (
              <PackageOpen className="h-8 w-8 text-purple-400" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-slate-200">
                {tool.name}
                {tool.loadingState === 'loading' && (
                  <span className="ml-2 text-sm text-slate-400">(Loading...)</span>
                )}
              </h3>
              <Button
                variant="ghost"
                size="sm"
                className="ml-2"
                onClick={(e) => {
                  e.stopPropagation();
                  onToggleExpand();
                  if (!isExpanded) {
                    loadReadme();
                  }
                }}
                disabled={tool.loadingState === 'loading'}
              >
                {isExpanded ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </Button>
            </div>
            {tool.loadingState === 'error' && tool.error ? (
              <p className="text-sm text-red-400 mt-1">{tool.error}</p>
            ) : (
              <HoverCard>
                <HoverCardTrigger>
                  <p className="text-sm text-slate-400 mt-1 line-clamp-2">
                    {tool.description}
                  </p>
                </HoverCardTrigger>
                <HoverCardContent className="w-80">
                  <p className="text-sm">{tool.description}</p>
                </HoverCardContent>
              </HoverCard>
            )}
            {isExpanded && (
              <div className="mt-4 border-t border-slate-800 pt-4">
                {isReadmeLoading ? (
                  <div className="animate-pulse space-y-2">
                    <div className="h-4 bg-slate-800 rounded w-3/4" />
                    <div className="h-4 bg-slate-800 rounded w-1/2" />
                  </div>
                ) : readme ? (
                  <MarkdownText content={readme} />
                ) : (
                  <p className="text-sm text-slate-400">No README available</p>
                )}
              </div>
            )}
          </div>
        </div>
        {isExpanded && tool.tools_count > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-800">
            <h4 className="text-sm font-medium text-slate-200 mb-2">Available Tools</h4>
            <div className="grid grid-cols-2 gap-2">
              {tool.tools.map((subTool: any) => (
                <div
                  key={subTool.name}
                  className="p-2 rounded-md bg-slate-800/50 text-sm text-slate-400"
                >
                  {subTool.name}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
} 