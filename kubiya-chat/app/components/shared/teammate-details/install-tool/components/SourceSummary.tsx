import React from 'react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/app/components/ui/tooltip';
import { FileIcon, GitBranchIcon, GitCommitIcon, AlertCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface SourceSummaryProps {
  source: {
    name: string;
    summary: {
      agents: number;
      tools: number;
      workflows: number;
      errors: number;
      lastUpdated: string;
      branch: string;
      commit?: string;
    };
    details: {
      url: string;
      metadata: {
        created_at: string;
        last_updated: string;
        user_created: string;
        user_last_updated: string;
      };
      sourceMeta: {
        id: string;
        url: string;
        commit?: string;
        committer?: string;
        branch?: string;
      };
      errors: Array<{
        file: string;
        error: string;
        traceback?: string;
      }>;
    };
  };
}

function getFileExtensionIcon(filename: string) {
  const ext = filename.split('.').pop()?.toLowerCase();
  
  switch(ext) {
    case 'py':
      return '🐍';
    case 'js':
    case 'ts':
      return '📜';
    case 'yaml':
    case 'yml':
      return '📋';
    case 'json':
      return '📝';
    default:
      return '📄';
  }
}

export function SourceSummary({ source }: SourceSummaryProps) {
  const lastUpdated = formatDistanceToNow(new Date(source.summary.lastUpdated), { addSuffix: true });
  
  return (
    <div className="rounded-lg border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">{source.name}</h3>
        {source.summary.errors > 0 && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <div className="flex items-center text-red-500">
                  <AlertCircle className="w-4 h-4 mr-1" />
                  <span>{source.summary.errors} error{source.summary.errors !== 1 ? 's' : ''}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent className="w-96 p-4">
                <div className="space-y-3">
                  <h4 className="font-semibold">Source Errors</h4>
                  {source.details.errors.map((error, index) => (
                    <div key={index} className="space-y-1">
                      <div className="flex items-center text-sm">
                        <span className="mr-2">{getFileExtensionIcon(error.file)}</span>
                        <span className="font-mono">{error.file}</span>
                      </div>
                      <p className="text-sm text-red-500">{error.error}</p>
                      {error.traceback && (
                        <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                          {error.traceback}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>

      <div className="grid grid-cols-3 gap-4 text-sm">
        <div>
          <span className="text-gray-500">Agents</span>
          <p className="font-medium">{source.summary.agents}</p>
        </div>
        <div>
          <span className="text-gray-500">Tools</span>
          <p className="font-medium">{source.summary.tools}</p>
        </div>
        <div>
          <span className="text-gray-500">Workflows</span>
          <p className="font-medium">{source.summary.workflows}</p>
        </div>
      </div>

      <div className="flex items-center space-x-4 text-sm text-gray-500">
        <div className="flex items-center">
          <GitBranchIcon className="w-4 h-4 mr-1" />
          <span>{source.summary.branch}</span>
        </div>
        {source.summary.commit && (
          <div className="flex items-center">
            <GitCommitIcon className="w-4 h-4 mr-1" />
            <span>{source.summary.commit}</span>
          </div>
        )}
        <div className="flex items-center">
          <span>Updated {lastUpdated}</span>
        </div>
      </div>
    </div>
  );
} 