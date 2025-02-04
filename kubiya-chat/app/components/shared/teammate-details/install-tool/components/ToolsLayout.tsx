import * as React from 'react';
import { Card } from '@/app/components/ui/card';
import { styles } from '../styles';
import type { CommunityTool, CategoryInfo, Tool } from '../types';
import { cn } from '@/lib/utils';
import { CommunityToolsHeader } from './CommunityToolsHeader';
import { Code, Package, Star, Clock, ChevronRight, Users, Search } from 'lucide-react';
import { Badge } from '@/app/components/ui/badge';
import { Button } from '@/app/components/ui/button';
import { formatDistanceToNow, format } from 'date-fns';
import { determineToolCategory, getToolCategories } from '@/app/utils/tool-categorization';

interface ToolsLayoutProps {
  tools: CommunityTool[];
  categories: CategoryInfo[];
  selectedTool: CommunityTool | null;
  onToolSelect: (tool: CommunityTool) => void;
  failedIcons: Set<string>;
  onIconError: (url: string) => void;
  expandedTools: Set<string>;
  setExpandedTools: React.Dispatch<React.SetStateAction<Set<string>>>;
  handleRefresh: () => void;
  runners: string[];
  activeCategory: string | null;
  onCategorySelect: (category: string | null) => void;
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
  handleRefresh,
  runners,
  activeCategory,
  onCategorySelect
}: ToolsLayoutProps) {
  const [searchQuery, setSearchQuery] = React.useState('');

  const filteredTools = React.useMemo(() => {
    return tools.filter(tool => {
      const matchesSearch = searchQuery
        ? tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          tool.description?.toLowerCase().includes(searchQuery.toLowerCase())
        : true;

      const matchesCategory = activeCategory
        ? getToolCategories(tool).includes(activeCategory.toLowerCase())
        : true;

      return matchesSearch && matchesCategory;
    });
  }, [tools, searchQuery, activeCategory]);

  const categorizedTools = React.useMemo(() => {
    return filteredTools.reduce((acc, tool) => {
      const category = determineToolCategory(tool) || 'uncategorized';
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(tool);
      return acc;
    }, {} as Record<string, CommunityTool[]>);
  }, [filteredTools]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-medium text-slate-200">
          {activeCategory || 'All Tools'} 
          <span className="text-sm text-slate-400 ml-2">
            ({filteredTools.length} {filteredTools.length === 1 ? 'tool' : 'tools'})
          </span>
        </h2>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input 
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search tools..."
            className={cn(
              "h-9 w-[300px] pl-9 pr-4 rounded-md",
              "bg-slate-800/50 border border-slate-700",
              "text-sm text-slate-200 placeholder:text-slate-400",
              "focus:outline-none focus:ring-2 focus:ring-purple-400/20"
            )}
          />
        </div>
      </div>
      <CommunityToolsHeader onRefresh={handleRefresh} />
      <div className="grid grid-cols-2 gap-4">
        {Object.entries(categorizedTools).map(([category, toolsInCategory]) => (
          <div key={category}>
            <h3 className="text-lg font-medium text-slate-200 mb-2">{category.charAt(0).toUpperCase() + category.slice(1)}</h3>
            {toolsInCategory.map(tool => {
              const matchingCategory = categories.find(c => c.matcher(tool));
              const firstTool = tool.tools?.[0];
              const toolIcon = firstTool?.icon_url || tool.icon_url;

              return (
                <Card
                  key={tool.name}
                  className={cn(
                    "relative border border-slate-800 bg-slate-900",
                    "transition-all duration-200",
                    "hover:bg-slate-800/50",
                    (!tool.runner || runners.includes(tool.runner)) ? [
                      "cursor-pointer",
                      "hover:border-purple-500/30",
                      "focus:outline-none focus:ring-2 focus:ring-purple-500/50",
                      selectedTool?.name === tool.name && "ring-2 ring-purple-500 border-purple-500"
                    ] : [
                      "cursor-not-allowed opacity-50"
                    ]
                  )}
                  onClick={() => (!tool.runner || runners.includes(tool.runner)) && onToolSelect(tool as CommunityTool)}
                  tabIndex={!tool.runner || runners.includes(tool.runner) ? 0 : -1}
                  role="button"
                  aria-disabled={(tool.runner && !runners.includes(tool.runner)) ? true : false}
                >
                  <div className="p-4 space-y-4">
                    {/* Header with Icon and Title */}
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-md bg-purple-500/10 border border-purple-500/20">
                        {toolIcon && !failedIcons.has(toolIcon) ? (
                          <img
                            src={toolIcon}
                            alt={tool.name}
                            className="h-8 w-8 object-contain"
                            onError={() => onIconError(toolIcon!)}
                          />
                        ) : matchingCategory?.Icon ? (
                          <matchingCategory.Icon className="h-8 w-8 text-purple-400" />
                        ) : (
                          <Package className="h-8 w-8 text-purple-400" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <h3 className="text-lg font-medium text-slate-200">{tool.name}</h3>
                            {tool.tools_count > 0 && (
                              <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/20">
                                {tool.tools_count} tools
                              </Badge>
                            )}
                            {tool.runner && (
                              <Badge 
                                variant="outline" 
                                className={cn(
                                  runners.includes(tool.runner)
                                    ? "bg-green-500/10 text-green-400 border-green-500/20"
                                    : "bg-red-500/10 text-red-400 border-red-500/20"
                                )}
                              >
                                {tool.runner}
                              </Badge>
                            )}
                          </div>
                        </div>
                        <p className="text-sm text-slate-400 mt-1">{tool.description}</p>
                      </div>
                    </div>

                    {/* Metadata Row */}
                    <div className="flex items-center gap-4 text-xs text-slate-400">
                      {tool.stars !== undefined && (
                        <div className="flex items-center gap-1">
                          <Star className="h-3.5 w-3.5" />
                          <span>{tool.stars}</span>
                        </div>
                      )}
                      {tool.lastCommit && (
                        <div className="flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5" />
                          <span>Updated {formatDistanceToNow(new Date(tool.lastCommit.date))} ago</span>
                          {tool.lastCommit.author.avatar && (
                            <img 
                              src={tool.lastCommit.author.avatar} 
                              alt={tool.lastCommit.author.name}
                              className="h-4 w-4 rounded-full ml-1"
                            />
                          )}
                        </div>
                      )}
                      {tool.contributors_count !== undefined && tool.contributors_count > 0 && (
                        <div className="flex items-center gap-1">
                          <Users className="h-3.5 w-3.5" />
                          <span>{tool.contributors_count} contributors</span>
                        </div>
                      )}
                    </div>

                    {/* README Summary */}
                    {tool.readme_summary && (
                      <div className="mt-3">
                        <div className="text-xs font-medium text-slate-300 mb-2">About</div>
                        <div className="text-xs text-slate-400 line-clamp-3">
                          {tool.readme_summary}
                        </div>
                      </div>
                    )}

                    {/* Last Commit Info */}
                    {tool.lastCommit && (
                      <div className="mt-3 p-2 rounded-md bg-slate-800/50">
                        <div className="flex items-start gap-2">
                          <div className="flex-1 min-w-0">
                            <div className="text-xs font-medium text-slate-300">Latest Update</div>
                            <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                              {tool.lastCommit.message}
                            </p>
                          </div>
                          <div className="text-xs text-slate-500">
                            {format(new Date(tool.lastCommit.date), 'MMM d, yyyy')}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* README Preview */}
                    {tool.readme && (
                      <div className="mt-3">
                        <div className="text-xs font-medium text-slate-300 mb-2">README</div>
                        <div className="text-xs text-slate-400 line-clamp-3">
                          {tool.readme}
                        </div>
                      </div>
                    )}

                    {/* Tool Preview */}
                    {tool.tools && tool.tools.length > 0 && (
                      <div className="border-t border-slate-800 pt-3 mt-3">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-xs font-medium text-slate-300">Available Tools</div>
                          <Button variant="ghost" size="sm" className="h-6 px-2 text-xs">
                            View All <ChevronRight className="h-3 w-3 ml-1" />
                          </Button>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="flex -space-x-2">
                            {(tool.tools as Tool[]).slice(0, 3).map((subTool, idx) => (
                              <div
                                key={idx}
                                className={cn(
                                  "w-6 h-6 rounded-md border-2 border-slate-800 bg-slate-900",
                                  "flex items-center justify-center overflow-hidden"
                                )}
                              >
                                {subTool.icon_url && !failedIcons.has(subTool.icon_url) ? (
                                  <img
                                    src={subTool.icon_url}
                                    alt={subTool.name}
                                    className="h-4 w-4 object-contain"
                                    onError={() => onIconError(subTool.icon_url!)}
                                  />
                                ) : (
                                  <Code className="h-3 w-3 text-slate-400" />
                                )}
                              </div>
                            ))}
                          </div>
                          {tool.tools.length > 3 && (
                            <span className="text-xs text-slate-400">
                              +{tool.tools.length - 3} more
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
} 