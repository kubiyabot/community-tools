import React from 'react';
import { Input } from '../ui/input';
import { Slack } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatFlowProps {
  slackTarget: string;
  onSlackTargetChange: (value: string) => void;
  description: string;
  onDescriptionChange: (value: string) => void;
}

export function ChatFlow({
  slackTarget,
  onSlackTargetChange,
  description,
  onDescriptionChange
}: ChatFlowProps) {
  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Slack className="h-5 w-5 text-purple-400" />
          <h3 className="text-base font-medium text-slate-200">Slack Channel</h3>
        </div>
        <Input
          placeholder="Enter channel name (e.g. #general)"
          value={slackTarget}
          onChange={(e) => onSlackTargetChange(e.target.value)}
          className={cn(
            "bg-[#1E293B] border-[#2D3B4E] h-12",
            "focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500/30"
          )}
        />
        <p className="text-sm text-slate-400">
          The teammate will respond in this Slack channel
        </p>
      </div>

      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <h3 className="text-base font-medium text-slate-200">Task Description</h3>
        </div>
        <textarea
          placeholder="What would you like the teammate to do?"
          value={description}
          onChange={(e) => onDescriptionChange(e.target.value)}
          className={cn(
            "w-full h-32 bg-[#1E293B] border border-[#2D3B4E] rounded-lg p-3",
            "text-sm text-slate-200 resize-none",
            "focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500/30"
          )}
        />
        <p className="text-sm text-slate-400">
          Describe the task in detail to ensure clear understanding
        </p>
      </div>
    </div>
  );
} 