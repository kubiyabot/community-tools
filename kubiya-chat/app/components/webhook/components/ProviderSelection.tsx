import { WEBHOOK_PROVIDERS, WebhookProvider, WebhookProviderType } from '../providers';
import { ProviderSelectionProps } from '../types';
import { Button } from '../../ui/button';
import { cn } from '../../../lib/utils';

export function ProviderSelection({
  selectedProvider,
  onProviderSelect
}: ProviderSelectionProps) {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-medium text-slate-200">Select a Provider</h3>
          <span className="text-xs text-red-400">*Required</span>
        </div>
        <p className="text-sm text-slate-400">
          Choose a provider to receive events from. Each provider has different types of events you can listen to.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(WEBHOOK_PROVIDERS).map(([type, provider]) => (
          <Button
            key={type}
            variant="outline"
            onClick={() => onProviderSelect({ 
              id: type as WebhookProviderType,
              name: provider.name,
              description: provider.description,
              icon: provider.icon,
              events: provider.events
            })}
            className={cn(
              "h-auto p-4 flex flex-col items-center gap-3 transition-all",
              selectedProvider?.id === type
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400 ring-2 ring-emerald-500/20"
                : "bg-[#1E293B] border-[#2D3B4E] text-slate-200 hover:border-emerald-500/30 hover:bg-emerald-500/10"
            )}
          >
            <provider.icon className={cn(
              "h-8 w-8 transition-colors",
              selectedProvider?.id === type
                ? "text-emerald-400"
                : "text-slate-400"
            )} />
            <div className="text-center">
              <h4 className="font-medium">{provider.name}</h4>
              <p className="text-xs mt-1 text-slate-400">
                {provider.events.length} event{provider.events.length === 1 ? '' : 's'} available
              </p>
            </div>
          </Button>
        ))}
      </div>
    </div>
  );
} 