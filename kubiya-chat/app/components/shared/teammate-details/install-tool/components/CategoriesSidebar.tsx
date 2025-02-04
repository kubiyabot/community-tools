import * as React from 'react';
import { CategoryInfo } from '../types';
import type { CommunityTool } from '../types';
import { cn } from '@/lib/utils';
import { getToolCategories } from '@/app/utils/tool-categorization';

interface CategoriesSidebarProps {
  categories: Record<string, CategoryInfo>;
  tools: CommunityTool[];
  activeCategory: string | null;
  onCategorySelect: (category: string | null) => void;
}

export function CategoriesSidebar({
  categories,
  tools,
  activeCategory,
  onCategorySelect
}: CategoriesSidebarProps) {
  // Get count of tools per category
  const categoryCounts = React.useMemo(() => {
    return tools.reduce((acc, tool) => {
      const toolCategories = getToolCategories(tool);
      toolCategories.forEach(category => {
        acc[category] = (acc[category] || 0) + 1;
      });
      return acc;
    }, {} as Record<string, number>);
  }, [tools]);

  return (
    <div className="flex flex-col gap-2">
      <button
        onClick={() => onCategorySelect(null)}
        className={cn(
          "flex items-center gap-2 w-full p-2 rounded-md",
          "transition-colors text-left",
          activeCategory === null
            ? "bg-purple-500/10 text-purple-400"
            : "text-slate-400 hover:text-slate-300 hover:bg-slate-800/50"
        )}
      >
        <span>All Tools</span>
        <span className="ml-auto text-xs text-slate-500">({tools.length})</span>
      </button>

      {Object.entries(categories).map(([id, category]) => (
        <button
          key={id}
          onClick={() => onCategorySelect(category.name)}
          className={cn(
            "flex items-center gap-2 w-full p-2 rounded-md",
            "transition-colors text-left",
            activeCategory === category.name
              ? "bg-purple-500/10 text-purple-400"
              : "text-slate-400 hover:text-slate-300 hover:bg-slate-800/50"
          )}
        >
          <category.Icon className="h-5 w-5" />
          <span>{category.name}</span>
          <span className="ml-auto text-xs text-slate-500">
            ({categoryCounts[id.toLowerCase()] || 0})
          </span>
        </button>
      ))}
    </div>
  );
} 