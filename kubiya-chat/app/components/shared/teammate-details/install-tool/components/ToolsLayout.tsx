import * as React from 'react';
import { Card } from '@/app/components/ui/card';
import { styles } from '../styles';
import type { CommunityTool, CategoryInfo } from '../types';
import { cn } from '@/lib/utils';
import { CommunityToolsHeader } from './CommunityToolsHeader';

interface ToolsLayoutProps {
  tools: CommunityTool[];
  categories: CategoryInfo[];
  selectedTool: CommunityTool | null;
  onToolSelect: (tool: Partial<CommunityTool>) => void;
  failedIcons: Set<string>;
  onIconError: (url: string) => void;
  expandedTools: Set<string>;
  setExpandedTools: React.Dispatch<React.SetStateAction<Set<string>>>;
  handleRefresh: () => Promise<void>;
}

export function ToolsLayout({
  tools,
  categories,
  selectedTool,
  onToolSelect,
  failedIcons,
  onIconError,
  expandedTools,
  setExpandedTools,
  handleRefresh
}: ToolsLayoutProps) {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [activeCategory, setActiveCategory] = React.useState<string | null>(null);

  const filteredTools = React.useMemo(() => {
    return tools.filter(tool => {
      const matchesSearch = searchQuery
        ? tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          tool.description.toLowerCase().includes(searchQuery.toLowerCase())
        : true;

      const matchesCategory = activeCategory
        ? categories.find(c => c.name === activeCategory)?.matcher(tool)
        : true;

      return matchesSearch && matchesCategory;
    });
  }, [tools, searchQuery, activeCategory, categories]);

  return (
    <div className="space-y-6">
      <CommunityToolsHeader onRefresh={handleRefresh} />
      <div className="grid grid-cols-2 gap-4">
        {filteredTools.map(tool => {
          const matchingCategory = categories.find(c => c.matcher(tool));
          const IconComponent = matchingCategory?.Icon;

          return (
            <Card
              key={tool.name}
              className={cn(
                styles.cards.base,
                "cursor-pointer transition-all duration-200",
                "hover:border-purple-500/30",
                selectedTool?.name === tool.name && "ring-2 ring-purple-500 border-purple-500"
              )}
              onClick={() => onToolSelect(tool)}
            >
              <div className="p-4">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-md bg-purple-500/10 border border-purple-500/20">
                    {tool.icon && !failedIcons.has(tool.icon) ? (
                      <img
                        src={tool.icon}
                        alt={tool.name}
                        className="h-8 w-8"
                        onError={() => onIconError(tool.icon!)}
                      />
                    ) : IconComponent ? (
                      <IconComponent className="h-8 w-8 text-purple-400" />
                    ) : null}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-medium text-slate-200">{tool.name}</h3>
                    <p className="text-sm text-slate-400 mt-1">{tool.description}</p>
                  </div>
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
} 