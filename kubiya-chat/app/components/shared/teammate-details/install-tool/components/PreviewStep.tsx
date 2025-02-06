import * as React from 'react';
import type { CommunityTool } from '@/app/types/tool';

interface CustomTool {
  name: string;
  description: string;
  tools: Array<{
    name: string;
    description?: string;
    type?: string;
  }>;
  type: 'custom';
}

interface PreviewStepProps {
  selectedTool: CommunityTool | CustomTool | null;
  isLoading?: boolean;
}

export function PreviewStep({ selectedTool, isLoading }: PreviewStepProps) {
  if (!selectedTool) return null;

  const tools = 'tools' in selectedTool ? selectedTool.tools : [];

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h3 className="text-lg font-medium text-white">{selectedTool.name}</h3>
        <p className="text-sm text-slate-400">{selectedTool.description}</p>
      </div>

      <div className="space-y-4">
        <h4 className="text-sm font-medium text-white">Tools to Install</h4>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {tools.map((tool, index) => (
            <div 
              key={`${tool.name}-${index}`}
              className="p-4 rounded-lg border border-slate-800 bg-slate-900/50"
            >
              <h5 className="text-sm font-medium text-white">{tool.name}</h5>
              {tool.description && (
                <p className="text-xs text-slate-400 mt-1">{tool.description}</p>
              )}
              {tool.type && (
                <div className="mt-2">
                  <span className="inline-flex items-center rounded-full px-2 py-1 text-xs font-medium bg-purple-500/10 text-purple-400 ring-1 ring-inset ring-purple-500/20">
                    {tool.type}
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 