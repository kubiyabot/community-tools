import * as React from 'react';
import { Loader2, AlertCircle, Box, RefreshCw } from 'lucide-react';
import { Button } from '@/app/components/ui/button';
import { styles } from '../styles';
import { CommunityToolCard } from './CommunityToolCard';
import type { FormState } from '../types';
import type { CommunityTool } from '@/app/types/tool';

interface CommunityToolsTabProps {
  formState: FormState;
  onRefresh: () => void;
  onToolSelect: (tool: CommunityTool) => void;
  selectedTool: CommunityTool | null;
  failedIcons: Set<string>;
  onIconError: (url: string) => void;
  expandedTools: Set<string>;
  setExpandedTools: React.Dispatch<React.SetStateAction<Set<string>>>;
}

export function CommunityToolsTab({
  formState,
  onRefresh,
  onToolSelect,
  selectedTool,
  failedIcons,
  onIconError,
  expandedTools,
  setExpandedTools
}: CommunityToolsTabProps) {
  const { isLoading, error, data } = formState.communityTools;
  const hasData = data && data.length > 0;

  // Show error banner if there's an error but we have data to display
  const showErrorBanner = error && hasData;

  // Show loading overlay if loading and no data
  const showLoadingOverlay = isLoading && !hasData;

  // Show error state if error and no data
  const showErrorState = error && !hasData;

  return (
    <div className="relative">
      {/* Loading Overlay */}
      {showLoadingOverlay && (
        <div className="flex flex-col items-center justify-center gap-4 p-8">
          <div className="relative flex flex-col items-center">
            <div className="relative">
              <div className="absolute inset-0 animate-ping rounded-full bg-purple-400/20" />
              <Loader2 className="h-8 w-8 text-purple-400 animate-spin relative" />
            </div>
            <div className="mt-4 text-center">
              <p className={styles.text.primary + " text-sm font-medium"}>Loading Community Tools</p>
              <p className={styles.text.secondary + " text-xs mt-1"}>
                Fetching available tools from the official community repository...
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Error Banner - shows at top when we have data but encountered an error */}
      {showErrorBanner && (
        <div className="mb-4 p-4 rounded-lg bg-red-50 border border-red-200 flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
          <div className="flex-grow">
            <p className="text-sm text-red-800 font-medium">Failed to refresh tools</p>
            <p className="text-sm text-red-600 mt-0.5">{error}</p>
          </div>
          <Button 
            variant="outline" 
            size="sm"
            onClick={onRefresh}
            className="flex-shrink-0"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      )}

      {/* Error State - shows when we have no data and encountered an error */}
      {showErrorState && (
        <div className="flex flex-col items-center justify-center gap-4 p-8 text-center">
          <AlertCircle className="h-8 w-8 text-red-400" />
          <div>
            <p className={styles.text.primary + " text-sm font-medium"}>Failed to Load Tools</p>
            <p className={styles.text.secondary + " text-sm mt-1"}>{error}</p>
          </div>
          <Button 
            variant="outline" 
            size="sm"
            onClick={onRefresh}
            className="mt-2"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && (!data || data.length === 0) && (
        <div className="flex flex-col items-center justify-center gap-4 p-8 text-center">
          <Box className="h-8 w-8 text-slate-400" />
          <div>
            <p className={styles.text.primary + " text-sm font-medium"}>No Community Tools Available</p>
            <p className={styles.text.secondary + " text-sm mt-1"}>Please try again later or use a custom source.</p>
          </div>
          <Button 
            variant="outline" 
            size="sm"
            onClick={onRefresh}
            className="mt-2"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      )}

      {/* Tools Grid - shows whenever we have data */}
      {hasData && (
        <div className="grid grid-cols-2 gap-4 relative">
          {data.map((tool: CommunityTool) => (
            <div key={tool.name} className="relative">
              {tool.isDiscovering && (
                <div className="absolute inset-0 z-10 bg-[#0F172A]/90 backdrop-blur-sm rounded-lg flex items-center justify-center">
                  <div className="flex flex-col items-center gap-3 p-4 text-center">
                    <div className="relative">
                      <div className="absolute inset-0 animate-ping rounded-full bg-purple-400/20" />
                      <Loader2 className="h-8 w-8 text-purple-400 animate-spin relative" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-purple-400">Reading Code</p>
                      <p className="text-xs text-purple-400/70 mt-1">Analyzing tool definitions...</p>
                    </div>
                  </div>
                </div>
              )}
              <CommunityToolCard 
                tool={tool}
                isSelected={selectedTool?.name === tool.name}
                onSelect={() => onToolSelect(tool)}
                failedIcons={failedIcons}
                onIconError={onIconError}
                expandedTools={expandedTools}
                setExpandedTools={setExpandedTools}
              />
            </div>
          ))}
        </div>
      )}

      {/* Loading Indicator for Refresh - shows when loading with existing data */}
      {isLoading && hasData && (
        <div className="absolute top-0 right-0 m-4">
          <Loader2 className="h-5 w-5 text-purple-400 animate-spin" />
        </div>
      )}
    </div>
  );
} 