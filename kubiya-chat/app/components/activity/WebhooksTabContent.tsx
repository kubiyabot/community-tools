import * as React from 'react';
import { useState } from 'react';
import { ScrollArea } from "../ui/scroll-area";
import { Loader2, Filter as FilterIcon, Bot, Users } from 'lucide-react';
import { WebhookCard } from './WebhookCard';
import { WebhooksTabContentProps } from './types';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { cn } from '@/lib/utils';
import { useTeammateContext } from '../../MyRuntimeProvider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { Avatar, AvatarImage, AvatarFallback } from '../ui/avatar';

// Import avatar generation function
const AVATAR_IMAGES = [
  'Accountant.png',
  'Chemist-scientist.png',
  'Postman.png',
  'Security-guard.png',
  'builder-1.png',
  'builder-2.png',
  'builder-3.png',
  'capitan-1.png',
  'capitan-2.png',
  'capitan-3.png'
];

function generateAvatarUrl(teammate: { uuid: string; name: string }) {
  const seed = (teammate.uuid + teammate.name).split('').reduce((acc, char, i) => 
    acc + (char.charCodeAt(0) * (i + 1)), 0);
  const randomIndex = Math.abs(Math.sin(seed) * AVATAR_IMAGES.length) | 0;
  return `/images/avatars/${AVATAR_IMAGES[randomIndex]}`;
}

export const WebhooksTabContent: React.FC<WebhooksTabContentProps> = ({
  webhooks,
  isLoading,
  teammates = [],
  onTestWebhook = async () => {},
  onDeleteWebhook = async () => {},
}) => {
  const [selectedTeammate, setSelectedTeammate] = useState<string>('all');
  const [selectedSource, setSelectedSource] = useState<string>('all');

  // Get unique sources
  const sources = Array.from(new Set(webhooks.map(webhook => webhook.source)));

  // Get webhook stats
  const stats = {
    total: webhooks.length,
    bySource: sources.reduce((acc, source) => ({
      ...acc,
      [source]: webhooks.filter(w => w.source === source).length
    }), {} as Record<string, number>),
    byTeammate: teammates.reduce((acc, teammate) => ({
      ...acc,
      [teammate.uuid]: webhooks.filter(w => w.teammate?.uuid === teammate.uuid).length
    }), {} as Record<string, number>)
  };

  // Filter webhooks
  const filteredWebhooks = webhooks.filter(webhook => {
    if (selectedTeammate !== 'all' && webhook.teammate?.uuid !== selectedTeammate) return false;
    if (selectedSource !== 'all' && webhook.source !== selectedSource) return false;
    return true;
  });

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex-shrink-0 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-white">Webhooks</h2>
            <p className="text-sm text-slate-400">
              View and manage your active webhooks
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="bg-blue-500/10 text-blue-300 border-blue-500/30">
              {filteredWebhooks.length} webhook{filteredWebhooks.length !== 1 ? 's' : ''}
            </Badge>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4 pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-slate-400" />
            <Select
              value={selectedTeammate}
              onValueChange={setSelectedTeammate}
            >
              <SelectTrigger className="w-[200px] bg-slate-900/50 border-slate-800">
                <SelectValue placeholder="Filter by teammate" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Teammates</SelectItem>
                {teammates.map(teammate => (
                  <SelectItem key={teammate.uuid} value={teammate.uuid}>
                    <div className="flex items-center gap-2">
                      <Avatar className="h-5 w-5">
                        <AvatarImage src={generateAvatarUrl(teammate)} alt={teammate.name} />
                        <AvatarFallback className="bg-blue-500/10 text-blue-300 text-xs">
                          {teammate.name.charAt(0).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <span>{teammate.name}</span>
                      {stats.byTeammate[teammate.uuid] > 0 && (
                        <Badge variant="outline" className="ml-2 bg-blue-500/10 text-blue-300 border-blue-500/30">
                          {stats.byTeammate[teammate.uuid]}
                        </Badge>
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <Bot className="h-4 w-4 text-slate-400" />
            <Select
              value={selectedSource}
              onValueChange={setSelectedSource}
            >
              <SelectTrigger className="w-[200px] bg-slate-900/50 border-slate-800">
                <SelectValue placeholder="Filter by source" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sources</SelectItem>
                {sources.map(source => (
                  <SelectItem key={source} value={source}>
                    <div className="flex items-center justify-between w-full">
                      <span>{source}</span>
                      <Badge variant="outline" className="bg-blue-500/10 text-blue-300 border-blue-500/30">
                        {stats.bySource[source]}
                      </Badge>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 text-slate-400 animate-spin" />
        </div>
      ) : filteredWebhooks.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="p-3 bg-blue-500/10 text-blue-300 rounded-full mb-4">
            <FilterIcon className="h-6 w-6" />
          </div>
          <h3 className="text-lg font-medium text-white mb-2">No webhooks found</h3>
          <p className="text-sm text-slate-400 max-w-sm">
            {webhooks.length > 0 
              ? 'Try adjusting your filters to see more webhooks'
              : 'Configure webhooks to automate responses to external events and integrate with other services'}
          </p>
          {webhooks.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSelectedTeammate('all');
                setSelectedSource('all');
              }}
              className="mt-4"
            >
              Clear Filters
            </Button>
          )}
        </div>
      ) : (
        <div className="relative flex-1 min-h-0">
          <ScrollArea className="h-full absolute inset-0">
            <div className="space-y-4 pr-4 pb-4">
              {filteredWebhooks.map((webhook) => {
                // Find the teammate based on agent_id
                const teammate = teammates.find(t => t.uuid === webhook.agent_id);
                
                const webhookWithAvatar = {
                  ...webhook,
                  event_type: webhook.source, // Use source as event_type if not provided
                  selected_agent: teammate ? {
                    uuid: teammate.uuid,
                    name: teammate.name,
                    avatar: generateAvatarUrl(teammate),
                    description: teammate.description
                  } : undefined
                };

                return (
                  <WebhookCard
                    key={webhook.id}
                    webhook={webhookWithAvatar}
                    onTest={onTestWebhook}
                    onDelete={onDeleteWebhook}
                  />
                );
              })}
            </div>
          </ScrollArea>
        </div>
      )}
    </div>
  );
}; 