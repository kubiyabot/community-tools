import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Input } from '../ui/input';
import { Activity, Search, X } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface TeammateInfo {
  uuid: string;
  name: string;
  team_id?: string;
  user_id?: string;
  org_id?: string;
  email?: string;
  context?: string;
  description?: string;
  avatar_url?: string;
  integrations?: Array<{ name: string; type?: string; }>;
}

interface Integration {
  name: string;
  type?: string;
}

interface TeammateSelectorProps {
  currentTeammate: TeammateInfo | undefined;
  onTeammateSelect: (teammate: TeammateInfo) => void;
  teammates: TeammateInfo[];
  isLoading?: boolean;
}

// Avatar generation
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

interface AvatarInput {
  uuid: string;
  name: string;
}

function generateAvatarUrl(input: AvatarInput) {
  const seed = (input.uuid + input.name).split('').reduce((acc: number, char: string, i: number) => 
    acc + (char.charCodeAt(0) * (i + 1)), 0);
  const randomIndex = Math.abs(Math.sin(seed) * AVATAR_IMAGES.length) | 0;
  return `/images/avatars/${AVATAR_IMAGES[randomIndex]}`;
}

export function TeammateSelector({
  currentTeammate,
  onTeammateSelect,
  teammates,
  isLoading
}: TeammateSelectorProps) {
  const [searchQuery, setSearchQuery] = React.useState('');

  const filteredTeammates = teammates.filter(t => 
    !searchQuery || 
    t.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.integrations?.some((integration: Integration | string) => 
      (typeof integration === 'string' ? integration : integration.name).toLowerCase().includes(searchQuery.toLowerCase())
    )
  );

  return (
    <div className="w-80">
      <Select
        value={currentTeammate?.uuid}
        onValueChange={(value) => {
          const selected = teammates.find(t => t.uuid === value);
          if (selected) {
            onTeammateSelect(selected);
          }
        }}
        disabled={isLoading}
      >
        <SelectTrigger className="w-full h-12 px-4 bg-[#1E293B] border-[#2D3B4E] hover:bg-[#1A2438] hover:border-purple-500/30">
          {isLoading ? (
            <div className="flex items-center gap-2 text-slate-400">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-purple-500 border-t-transparent" />
              <span>Loading teammates...</span>
            </div>
          ) : currentTeammate ? (
            <div className="flex items-center gap-3">
              <div className="relative flex-shrink-0">
                <img
                  src={generateAvatarUrl({ uuid: currentTeammate.uuid, name: currentTeammate.name || '' })}
                  alt={currentTeammate.name}
                  className="w-9 h-9 rounded-lg transform transition-all duration-300 
                           group-hover:scale-105 group-hover:shadow-md group-hover:shadow-purple-500/10
                           object-cover"
                />
                {currentTeammate.integrations && currentTeammate.integrations.length > 0 && (
                  <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-purple-500 
                               rounded-full ring-2 ring-[#1E293B] shadow-lg" />
                )}
              </div>
              <div className="flex flex-col items-start">
                <span className="text-sm font-medium text-slate-200">{currentTeammate.name}</span>
                {currentTeammate.integrations && currentTeammate.integrations.length > 0 && (
                  <span className="text-xs text-slate-400">
                    {currentTeammate.integrations.length} integration{currentTeammate.integrations.length !== 1 ? 's' : ''}
                  </span>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-slate-400">
              <div className="w-9 h-9 rounded-lg bg-[#1A2438] border border-[#2D3B4E] flex items-center justify-center">
                <Activity className="h-4 w-4 text-slate-500" />
              </div>
              <span>Select a teammate</span>
            </div>
          )}
        </SelectTrigger>
        <SelectContent className="max-h-[400px] p-2 bg-[#1E293B] border-[#2D3B4E]">
          <div className="sticky top-0 px-2 py-2 mb-2 bg-[#1E293B] border-b border-[#2D3B4E] z-10">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <Input
                placeholder="Search by name or integration..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 h-9 bg-[#1A2438] border-[#2D3B4E] text-sm
                         focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500/30"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-md
                           hover:bg-slate-700/50 text-slate-400 hover:text-slate-300"
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </div>
            {filteredTeammates && (
              <div className="mt-2 text-xs text-slate-400">
                {filteredTeammates.length} teammate{filteredTeammates.length !== 1 ? 's' : ''} found
              </div>
            )}
          </div>
          <div className="space-y-1">
            {filteredTeammates?.length === 0 ? (
              <div className="px-2 py-4 text-center">
                <div className="text-sm text-slate-400">No teammates found</div>
                <div className="text-xs text-slate-500 mt-1">Try adjusting your search terms</div>
              </div>
            ) : (
              filteredTeammates?.map((t) => (
                <SelectItem 
                  key={t.uuid} 
                  value={t.uuid}
                  className={cn(
                    "rounded-lg px-3 py-2 text-sm cursor-pointer",
                    "hover:bg-purple-500/10 focus:bg-purple-500/10",
                    "data-[state=checked]:bg-purple-500/20 data-[state=checked]:text-purple-400",
                    "transition-colors duration-150"
                  )}
                >
                  <div className="flex items-center gap-3 w-full">
                    <div className="relative flex-shrink-0">
                      <img
                        src={generateAvatarUrl({ uuid: t.uuid, name: t.name || '' })}
                        alt={t.name}
                        className="w-9 h-9 rounded-lg transform transition-all duration-300 
                                 group-hover:scale-105 group-hover:shadow-md group-hover:shadow-purple-500/10
                                 object-cover"
                      />
                      {t.integrations && t.integrations.length > 0 && (
                        <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-purple-500 
                                     rounded-full ring-2 ring-[#1E293B] shadow-lg" />
                      )}
                    </div>
                    <div className="flex flex-col min-w-0">
                      <span className="text-sm font-medium text-slate-200 truncate">{t.name}</span>
                      {t.integrations && t.integrations.length > 0 && (
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-slate-400">
                            {t.integrations.length} integration{t.integrations.length !== 1 ? 's' : ''}
                          </span>
                          <div className="flex -space-x-1.5">
                            {t.integrations.slice(0, 3).map((integration: Integration | string, idx: number) => {
                              const type = typeof integration === 'string' ? integration.toLowerCase() : integration.type?.toLowerCase() || integration.name.toLowerCase();
                              return (
                                <div 
                                  key={idx}
                                  className="w-4 h-4 rounded-full bg-[#1A2438] border border-[#2D3B4E] flex items-center justify-center overflow-hidden"
                                  title={type.charAt(0).toUpperCase() + type.slice(1)}
                                >
                                  {type === 'jira' && (
                                    <img src="https://wac-cdn.atlassian.com/assets/img/favicons/atlassian/favicon-32x32.png" alt="JIRA" className="w-3 h-3" />
                                  )}
                                  {type === 'slack' && (
                                    <img src="https://upload.wikimedia.org/wikipedia/commons/d/d5/Slack_icon_2019.svg" alt="Slack" className="w-3 h-3" />
                                  )}
                                  {type === 'github' && (
                                    <img src="https://github.githubassets.com/favicons/favicon.svg" alt="GitHub" className="w-3 h-3" />
                                  )}
                                  {type === 'gitlab' && (
                                    <img src="https://gitlab.com/uploads/-/system/group/avatar/6543/gitlab-logo-square.png" alt="GitLab" className="w-3 h-3" />
                                  )}
                                </div>
                              );
                            })}
                            {t.integrations.length > 3 && (
                              <div 
                                className="w-4 h-4 rounded-full bg-[#1A2438] border border-[#2D3B4E] flex items-center justify-center"
                                title={`${t.integrations.length - 3} more integration${t.integrations.length - 3 !== 1 ? 's' : ''}`}
                              >
                                <span className="text-[10px] text-slate-400">+{t.integrations.length - 3}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </SelectItem>
              ))
            )}
          </div>
        </SelectContent>
      </Select>
    </div>
  );
} 