import React from 'react';
import { Button } from '../ui/button';
import { MessageSquare, Webhook, Trello } from 'lucide-react';
import { toast } from '../ui/use-toast';
import { cn } from '@/lib/utils';
import { type Integration, type IntegrationType } from '../../types/integration';
import { type TeammateInfo } from '../../types/teammate';

export type AssignmentMethod = 'chat' | 'jira' | 'webhook';

interface MethodSelectionProps {
  currentTeammate: TeammateInfo;
  hasJira: boolean;
  onMethodSelect: (method: AssignmentMethod) => void;
}

export function MethodSelection({ currentTeammate, hasJira, onMethodSelect }: MethodSelectionProps) {
  const handleMethodSelect = (method: AssignmentMethod) => {
    if (method === 'jira' && !hasJira) {
      toast({
        title: "JIRA Integration Required",
        description: "Please enable JIRA integration in your management console",
        variant: "destructive"
      });
      return;
    }
    onMethodSelect(method);
  };

  return (
    <div className="grid grid-cols-3 gap-4">
      <Button
        variant="outline"
        className={cn(
          "flex flex-col items-center gap-4 p-6 h-auto",
          "bg-[#1E293B] hover:bg-purple-500/10",
          "border-[#2D3B4E] hover:border-purple-500/30"
        )}
        onClick={() => handleMethodSelect('chat')}
      >
        <div className="w-12 h-12 rounded-lg bg-purple-500/10 border border-purple-500/20 
                     flex items-center justify-center">
          <MessageSquare className="h-6 w-6 text-purple-400" />
        </div>
        <div className="text-center">
          <h3 className="text-base font-medium text-slate-200 mb-1">Chat</h3>
          <p className="text-sm text-slate-400">
            Direct chat interaction with the teammate
          </p>
        </div>
      </Button>

      <Button
        variant="outline"
        className={cn(
          "flex flex-col items-center gap-4 p-6 h-auto",
          "bg-[#1E293B] hover:bg-emerald-500/10",
          "border-[#2D3B4E] hover:border-emerald-500/30"
        )}
        onClick={() => handleMethodSelect('webhook')}
      >
        <div className="w-12 h-12 rounded-lg bg-emerald-500/10 border border-emerald-500/20 
                     flex items-center justify-center">
          <Webhook className="h-6 w-6 text-emerald-400" />
        </div>
        <div className="text-center">
          <h3 className="text-base font-medium text-slate-200 mb-1">Webhook</h3>
          <p className="text-sm text-slate-400">
            Trigger on external events
          </p>
        </div>
      </Button>

      <Button
        variant="outline"
        className={cn(
          "flex flex-col items-center gap-4 p-6 h-auto",
          hasJira 
            ? "bg-[#1E293B] hover:bg-blue-500/10 border-[#2D3B4E] hover:border-blue-500/30"
            : "bg-slate-800/50 border-slate-700/50 cursor-not-allowed opacity-50"
        )}
        onClick={() => handleMethodSelect('jira')}
        disabled={!hasJira}
      >
        <div className={cn(
          "w-12 h-12 rounded-lg flex items-center justify-center",
          hasJira 
            ? "bg-blue-500/10 border border-blue-500/20" 
            : "bg-slate-700/50 border border-slate-600/50"
        )}>
          <Trello className={cn(
            "h-6 w-6",
            hasJira ? "text-blue-400" : "text-slate-500"
          )} />
        </div>
        <div className="text-center">
          <h3 className="text-base font-medium text-slate-200 mb-1">JIRA</h3>
          <p className="text-sm text-slate-400">
            {hasJira ? "Create and manage JIRA tasks" : "JIRA integration required"}
          </p>
        </div>
      </Button>
    </div>
  );
} 