"use client";

import { type ToolCallContentPartComponent } from "@assistant-ui/react";
import { Loader2, Terminal, CheckCircle2, XCircle } from 'lucide-react';

export const ToolExecution: ToolCallContentPartComponent<Record<string | number, unknown>, unknown> = ({ 
  toolName,
  argsText, 
  status
}) => {
  return (
    <div className="flex flex-col gap-2 bg-[#0A0F1E] rounded-xl p-4 my-2 mx-auto max-w-[90%] ring-1 ring-[#1E293B] shadow-sm">
      <div className="flex items-center gap-2 text-white">
        {status.type === 'running' ? (
          <Loader2 className="h-4 w-4 animate-spin text-[#7C3AED]" />
        ) : status.type === 'complete' ? (
          <CheckCircle2 className="h-4 w-4 text-[#7C3AED]" />
        ) : (
          <XCircle className="h-4 w-4 text-red-500" />
        )}
        <Terminal className="h-4 w-4 text-[#7C3AED]" />
        <span className="font-mono text-sm font-medium">{toolName || 'Tool Execution'}</span>
      </div>
      
      {argsText && (
        <div className="mt-2 rounded-lg bg-[#1E293B] p-3 ring-1 ring-[#1E293B]">
          <div className="text-xs text-white/70 font-mono mb-1">Arguments:</div>
          <div className="text-sm text-white font-mono whitespace-pre-wrap break-all">
            {argsText}
          </div>
        </div>
      )}
      
      {status.type === 'complete' && (
        <div className="mt-1 text-sm text-[#7C3AED] font-mono flex items-center gap-1.5">
          <CheckCircle2 className="h-3.5 w-3.5" />
          Completed
        </div>
      )}
      
      {status.type === 'incomplete' && (
        <div className="mt-1 text-sm text-red-500 font-mono flex items-center gap-1.5">
          <XCircle className="h-3.5 w-3.5" />
          Failed to complete
        </div>
      )}
    </div>
  );
}; 