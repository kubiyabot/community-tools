import { useState, useEffect } from 'react';
import { Loader2, Check, X, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '../ui/button';

interface Integration {
  name: string;
  type?: string;
  status: 'active' | 'inactive';
}

export interface Teammate {
  uuid: string;
  name?: string;
  team_id?: string;
  user_id?: string;
  org_id?: string;
  email?: string;
  context?: string;
  integrations?: Integration[];
}

interface TeammateWithLoadingState extends Teammate {
  isLoadingIntegrations?: boolean;
  hasLoadedIntegrations?: boolean;
}

interface TeammateSwitchProps {
  currentTeammate: Teammate;
  onSelect: (teammate: Teammate) => void;
  onClose: () => void;
  className?: string;
}

export function TeammateSwitch({ currentTeammate, onSelect, onClose, className }: TeammateSwitchProps) {
  const [teammates, setTeammates] = useState<TeammateWithLoadingState[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load teammates without integrations first
  useEffect(() => {
    const fetchTeammates = async () => {
      try {
        const response = await fetch('/api/teammates');
        const data = await response.json();
        setTeammates(data.map((teammate: Teammate) => ({
          ...teammate,
          isLoadingIntegrations: false,
          hasLoadedIntegrations: false
        })));
      } catch (error) {
        console.error('Failed to fetch teammates:', error);
        setError('Failed to load teammates. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchTeammates();
  }, []);

  // Function to load integrations for a specific teammate
  const loadIntegrationsForTeammate = async (teammateId: string) => {
    // Don't load if already loaded or loading
    const teammate = teammates.find(t => t.uuid === teammateId);
    if (teammate?.hasLoadedIntegrations || teammate?.isLoadingIntegrations) return;

    // Update loading state
    setTeammates(prev => prev.map(t => 
      t.uuid === teammateId ? { ...t, isLoadingIntegrations: true } : t
    ));

    try {
      const response = await fetch(`/api/teammates/${teammateId}/integrations`);
      const data = await response.json();
      
      setTeammates(prev => prev.map(t => 
        t.uuid === teammateId ? {
          ...t,
          integrations: data.integrations.map((integration: string | Integration) => ({
            name: typeof integration === 'string' ? integration : integration.name,
            status: 'active' as const
          })),
          isLoadingIntegrations: false,
          hasLoadedIntegrations: true
        } : t
      ));
    } catch (error) {
      console.error(`Failed to fetch integrations for teammate ${teammateId}:`, error);
      setTeammates(prev => prev.map(t => 
        t.uuid === teammateId ? { ...t, isLoadingIntegrations: false } : t
      ));
    }
  };

  // Load integrations for current teammate immediately
  useEffect(() => {
    if (currentTeammate?.uuid) {
      loadIntegrationsForTeammate(currentTeammate.uuid);
    }
  }, [currentTeammate.uuid]);

  const handleTeammateClick = async (teammate: TeammateWithLoadingState) => {
    onSelect(teammate);
    // Load integrations after selection
    loadIntegrationsForTeammate(teammate.uuid);
  };

  const getIntegrationIcon = (name: string) => {
    const icons: Record<string, string> = {
      'slack': 'https://cdn-icons-png.flaticon.com/512/2111/2111615.png',
      'jira': 'https://cdn.worldvectorlogo.com/logos/jira-1.svg',
      'github': 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png',
      'gitlab': 'https://about.gitlab.com/images/press/logo/png/gitlab-icon-rgb.png'
    };

    return icons[name.toLowerCase()] || null;
  };

  const handleOverlayClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  return (
    <div 
      className={cn(
        "fixed inset-0 z-50 bg-black/50 flex items-center justify-center",
        className
      )}
      onClick={handleOverlayClick}
    >
      <div 
        className="bg-[#0F172A] border border-[#1E293B] rounded-lg w-full max-w-2xl max-h-[85vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-4 border-b border-[#1E293B] flex items-center justify-between">
          <h2 className="text-lg font-medium text-slate-200">Switch Teammate</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="p-4 max-h-[calc(85vh-120px)] overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 text-purple-400 animate-spin" />
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-8 text-red-400 gap-2">
              <AlertCircle className="h-5 w-5" />
              {error}
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {teammates.map((teammate) => (
                <button
                  key={teammate.uuid}
                  onClick={() => handleTeammateClick(teammate)}
                  className={cn(
                    "w-full p-4 rounded-lg text-left transition-all",
                    "border hover:border-opacity-30",
                    teammate.uuid === currentTeammate.uuid
                      ? "bg-purple-500/10 border-purple-500/30"
                      : "bg-[#1E293B] border-[#2D3B4E] hover:bg-purple-500/5"
                  )}
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-base font-medium text-slate-200">
                          {teammate.name || teammate.email || 'Unnamed Teammate'}
                        </span>
                        {teammate.uuid === currentTeammate.uuid && (
                          <span className="px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-400 text-xs">
                            Current
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-slate-400 mt-1">
                        {teammate.email}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {teammate.isLoadingIntegrations ? (
                        <Loader2 className="h-4 w-4 text-slate-400 animate-spin" />
                      ) : teammate.integrations?.map((integration) => (
                        <div
                          key={integration.name}
                          className="relative group"
                        >
                          {getIntegrationIcon(integration.name) ? (
                            <img
                              src={getIntegrationIcon(integration.name)!}
                              alt={integration.name}
                              className="h-6 w-6 object-contain opacity-60 group-hover:opacity-100 transition-opacity"
                            />
                          ) : (
                            <div className="h-6 w-6 rounded-full bg-slate-700 flex items-center justify-center">
                              <span className="text-xs text-slate-400">
                                {integration.name.charAt(0).toUpperCase()}
                              </span>
                            </div>
                          )}
                          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 rounded bg-slate-800 text-xs text-slate-200 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
                            {integration.name}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 