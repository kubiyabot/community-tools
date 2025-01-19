"use client";

import { useAssistantToolUI, useInlineRender } from "@assistant-ui/react";
import { Terminal, Loader2, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

interface ToolExecutionProps {
  toolName: string;
}

interface ToolStatus {
  type: 'running' | 'complete' | 'incomplete' | 'requires-action';
  reason?: 'cancelled' | 'length' | 'content-filter' | 'other' | 'error' | 'tool-calls';
  error?: unknown;
}

export const ToolExecution = ({ toolName }: ToolExecutionProps) => {
  useAssistantToolUI({
    toolName,
    render: useInlineRender(({ args, status }) => {
      // Default to running state if status is undefined
      const toolStatus: ToolStatus = status || { type: 'running' };

      return (
        <div className="flex items-start space-x-2 p-2 rounded bg-[#1E293B] border border-[#334155]">
          <Terminal className="h-4 w-4 text-[#7C3AED] mt-1" />
          <div className="flex-1">
            <div className="text-sm font-medium text-[#E2E8F0] mb-1">
              Executing: {toolName}
            </div>
            <div className="text-xs text-[#94A3B8] font-mono">
              {args ? JSON.stringify(args, null, 2) : 'No arguments provided'}
            </div>
            {toolStatus.type === 'running' && (
              <div className="mt-2">
                <div className="animate-pulse flex space-x-2">
                  <div className="h-2 w-2 bg-[#7C3AED] rounded-full"></div>
                  <div className="h-2 w-2 bg-[#7C3AED] rounded-full"></div>
                  <div className="h-2 w-2 bg-[#7C3AED] rounded-full"></div>
                </div>
              </div>
            )}
            {toolStatus.type === 'complete' && (
              <div className="mt-2 flex items-center space-x-2 text-green-500">
                <CheckCircle2 className="h-4 w-4" />
                <span className="text-xs">Complete</span>
              </div>
            )}
            {toolStatus.type === 'incomplete' && (
              <div className="mt-2 flex items-center space-x-2 text-red-500">
                <XCircle className="h-4 w-4" />
                <span className="text-xs">Failed: {toolStatus.reason || 'Unknown error'}</span>
              </div>
            )}
            {toolStatus.type === 'requires-action' && (
              <div className="mt-2 flex items-center space-x-2 text-yellow-500">
                <AlertTriangle className="h-4 w-4" />
                <span className="text-xs">Waiting for action: {toolStatus.reason}</span>
              </div>
            )}
          </div>
        </div>
      );
    }),
  });

  return null;
}; 