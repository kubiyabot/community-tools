import { WebhookEvent } from '../providers';
import { EventSelectionProps } from '../types';
import { Button } from '../../ui/button';
import { cn } from '../../../lib/utils';
import { Badge } from '../../ui/badge';

export function EventSelection({
  selectedProvider,
  selectedEvent,
  onEventSelect
}: EventSelectionProps) {
  if (!selectedProvider) return null;

  // Group events by category
  const eventsByCategory = selectedProvider.events.reduce<Record<string, WebhookEvent[]>>((acc: Record<string, WebhookEvent[]>, event: WebhookEvent) => {
    if (!acc[event.category]) {
      acc[event.category] = [];
    }
    acc[event.category].push(event);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h3 className="text-lg font-medium text-slate-200">Select an Event</h3>
        <p className="text-sm text-slate-400">
          Choose the type of event you want to receive from {selectedProvider.name}.
          Each event type provides different data that you can use in your prompt.
        </p>
      </div>

      <div className="space-y-6">
        {Object.entries(eventsByCategory).map(([category, events]) => (
          <div key={category} className="space-y-3">
            <h4 className="text-sm font-medium text-slate-300">{category}</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {(events as WebhookEvent[]).map((event) => (
                <Button
                  key={event.type}
                  variant="outline"
                  onClick={() => onEventSelect(event.type)}
                  className={cn(
                    "h-auto p-4 flex flex-col items-start gap-2 transition-all hover:border-emerald-500/30 hover:bg-emerald-500/10",
                    selectedEvent === event.type
                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                      : "bg-[#1E293B] border-[#2D3B4E] text-slate-200"
                  )}
                >
                  <div className="flex items-center gap-2 w-full">
                    <event.icon className={cn(
                      "h-5 w-5 transition-colors",
                      selectedEvent === event.type
                        ? "text-emerald-400"
                        : "text-slate-400"
                    )} />
                    <span className="font-medium">{event.name}</span>
                    <Badge 
                      variant="outline" 
                      className={cn(
                        "ml-auto text-xs",
                        selectedEvent === event.type
                          ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                          : "bg-slate-800/50 border-slate-700 text-slate-400"
                      )}
                    >
                      {event.variables.length} variable{event.variables.length === 1 ? '' : 's'}
                    </Badge>
                  </div>
                  <p className="text-sm text-slate-400 text-left">
                    {event.description}
                  </p>
                </Button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
} 