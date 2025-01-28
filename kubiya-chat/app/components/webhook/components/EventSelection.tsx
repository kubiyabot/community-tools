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
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-medium text-slate-200">Select an Event Type</h3>
          <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/30">
            Step 2 of 3
          </Badge>
        </div>
        <p className="text-sm text-slate-400">
          Choose the type of event you want to receive from {selectedProvider.name}.
          Each event type provides different data that you can use in your prompt.
        </p>
      </div>

      <div className="space-y-6">
        {Object.entries(eventsByCategory).map(([category, events]) => (
          <div key={category} className="space-y-3">
            <h4 className="text-sm font-medium text-slate-300 flex items-center gap-2">
              {category}
              <Badge variant="outline" className="bg-slate-800/50 text-slate-400 border-slate-700">
                {events.length} event{events.length === 1 ? '' : 's'}
              </Badge>
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {(events as WebhookEvent[]).map((event) => (
                <Button
                  key={event.type}
                  variant="outline"
                  onClick={() => onEventSelect(event.type)}
                  className={cn(
                    "h-auto p-4 flex flex-col items-start gap-2 transition-all relative",
                    selectedEvent === event.type
                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400 ring-2 ring-emerald-500/20"
                      : "bg-[#1E293B] border-[#2D3B4E] text-slate-200 hover:border-emerald-500/30 hover:bg-emerald-500/10"
                  )}
                >
                  {selectedEvent === event.type && (
                    <div className="absolute top-2 right-2">
                      <Badge className="bg-emerald-500 text-white border-none">
                        Selected
                      </Badge>
                    </div>
                  )}
                  <div className="w-full flex items-start justify-between gap-2">
                    <div>
                      <h4 className="text-sm font-medium">{event.name}</h4>
                      <p className="text-xs text-slate-400 mt-1">{event.description}</p>
                    </div>
                    <Badge 
                      variant="outline" 
                      className={cn(
                        "shrink-0",
                        selectedEvent === event.type
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                          : "bg-slate-800/50 text-slate-400 border-slate-700"
                      )}
                    >
                      {event.type}
                    </Badge>
                  </div>
                  <div className="w-full mt-2 pt-2 border-t border-slate-700/50">
                    <p className="text-xs text-slate-400">
                      Available data: {event.variables.join(', ')}
                    </p>
                  </div>
                </Button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
} 