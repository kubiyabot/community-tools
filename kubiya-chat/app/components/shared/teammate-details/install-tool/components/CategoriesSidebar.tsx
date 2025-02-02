import * as React from 'react';
import { CategoryInfo } from '../types';
import { CommunityTool } from '@/app/types/tools';

interface CategoriesSidebarProps {
  categories: Record<string, CategoryInfo>;
  tools: CommunityTool[];
  activeCategory: string | null;
  onCategorySelect: (category: string) => void;
}

export function CategoriesSidebar({
  categories,
  tools,
  activeCategory,
  onCategorySelect
}: CategoriesSidebarProps) {
  return (
    <div className="flex flex-col gap-2">
      {Object.entries(categories).map(([key, category]) => (
        <button
          key={key}
          onClick={() => onCategorySelect(key)}
          className={`flex items-center gap-2 p-2 rounded-lg ${
            activeCategory === key ? 'bg-primary/10' : 'hover:bg-primary/5'
          }`}
        >
          <category.Icon className="h-5 w-5" />
          <span>{category.name}</span>
        </button>
      ))}
    </div>
  );
} 