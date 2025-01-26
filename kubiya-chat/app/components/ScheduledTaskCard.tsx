import { format } from 'date-fns';
import { Clock, Trash2, Slack, MessageSquare } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from './ui/use-toast';

interface ScheduledTaskCardProps {
  task: {
    id: string;
    schedule_time: string;
    channel_id: string;
    task_description: string;
    selected_agent: string;
    cron_string?: string;
  };
  onDelete: () => void;
  onScheduleSimilar: (task: any) => void;
}

export function ScheduledTaskCard({ task, onDelete, onScheduleSimilar }: ScheduledTaskCardProps) {
  const handleDelete = async () => {
    try {
      const response = await fetch(`/api/scheduled_tasks?taskId=${task.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete task');
      }

      onDelete();
      toast({
        title: "Task Deleted",
        description: "The scheduled task has been cancelled.",
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to delete task. Please try again.",
      });
    }
  };

  const getDestinationIcon = () => {
    if (task.channel_id.startsWith('#')) {
      return <Slack className="h-4 w-4" />;
    }
    return <MessageSquare className="h-4 w-4" />;
  };

  return (
    <div className="bg-[#1E293B] border border-[#2D3B4E] rounded-lg p-4 hover:border-purple-500/30 transition-colors">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Clock className="h-4 w-4" />
            <span>
              {task.cron_string ? (
                <>Recurring: {task.cron_string}</>
              ) : (
                <>Scheduled for {format(new Date(task.schedule_time), 'PPp')}</>
              )}
            </span>
          </div>
          <p className="text-white">{task.task_description}</p>
          <div className="flex items-center gap-2 text-sm text-slate-400">
            {getDestinationIcon()}
            <span>{task.channel_id}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onScheduleSimilar(task)}
            className="text-slate-400 hover:text-purple-400 hover:bg-purple-400/10"
          >
            <Clock className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDelete}
            className="text-slate-400 hover:text-red-400 hover:bg-red-400/10"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
} 