import React from 'react';
import { useState, useEffect } from 'react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Badge } from '../../ui/badge';
import { cn } from '../../../lib/utils';
import { AlertCircle, Loader2 } from 'lucide-react';
import { toast } from '../../ui/use-toast';
import { InteractionDestination as InteractionDestinationType } from '../types';
import { useUser } from '@auth0/nextjs-auth0/client';
import type { UserProfile } from '@auth0/nextjs-auth0/client';

interface Platform {
  id: string;
  name: string;
  icon: React.ReactNode;
  description: string;
  available: boolean;
  comingSoon?: boolean;
  features: string[];
}

interface InteractionDestinationProps {
  selectedDestination?: InteractionDestinationType;
  onContinue: (destination: InteractionDestinationType) => void;
  teammate?: {
    uuid: string;
    org_id?: string;
    email?: string;
  };
  provider: string;
  eventType: string;
  promptTemplate: string;
}

const PLATFORMS: Platform[] = [
  {
    id: 'slack',
    name: 'Slack',
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="w-7 h-7">
        <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z"/>
      </svg>
    ),
    description: 'Send updates and interact through Slack channels or direct messages',
    available: true,
    features: ['Channel & DM support', 'Interactive responses', 'Rich message formatting']
  },
  {
    id: 'teams',
    name: 'Microsoft Teams',
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="w-7 h-7">
        <path d="M14.5 21.1c-2.8 0-5.1-2.3-5.1-5.1v-6c0-2.8 2.3-5.1 5.1-5.1h4.3c2.8 0 5.1 2.3 5.1 5.1v6c0 2.8-2.3 5.1-5.1 5.1h-4.3zm-1.7-11.1v6c0 .9.8 1.7 1.7 1.7h4.3c.9 0 1.7-.8 1.7-1.7v-6c0-.9-.8-1.7-1.7-1.7h-4.3c-.9 0-1.7.8-1.7 1.7z"/>
        <path d="M9.7 15.9c-.9 0-1.7-.8-1.7-1.7v-6c0-.9-.8-1.7-1.7-1.7H2c-.9 0-1.7.8-1.7 1.7v6c0 .9.8 1.7 1.7 1.7h4.3c.9 0 1.7-.8 1.7-1.7"/>
      </svg>
    ),
    description: 'Send updates and interact through Microsoft Teams channels',
    available: false,
    comingSoon: true,
    features: ['Channel support', 'Adaptive cards', 'Rich message formatting']
  }
];

type PlatformId = typeof PLATFORMS[number]['id'];

export function InteractionDestination({ 
  selectedDestination, 
  onContinue,
  teammate,
  provider,
  eventType,
  promptTemplate
}: InteractionDestinationProps) {
  const [selectedPlatform, setSelectedPlatform] = useState<PlatformId | null>(
    (selectedDestination?.type as PlatformId) || null
  );
  const [channel, setChannel] = useState(selectedDestination?.channel || '');
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const { user: auth0User, isLoading: isAuth0Loading } = useUser();
  const [profileData, setProfileData] = useState<UserProfile | null>(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState(true);

  useEffect(() => {
    const fetchProfileData = async () => {
      if (!auth0User) return;

      try {
        const response = await fetch('/api/auth/me', {
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        });

        if (!response.ok) {
          if (response.status === 401) {
            console.log('Session expired, redirecting to login');
            window.location.href = '/api/auth/login';
            return;
          }
          throw new Error(`Profile fetch failed: ${response.status}`);
        }

        const data = await response.json();
        if (data.user) {
          setProfileData({
            ...data.user,
            email: data.user.email || auth0User.email,
          });
        }
      } catch (error) {
        console.error('Failed to fetch profile:', error);
      } finally {
        setIsLoadingProfile(false);
      }
    };

    if (auth0User) {
      fetchProfileData();
    } else {
      setIsLoadingProfile(false);
    }
  }, [auth0User]);

  const validateChannel = (value: string) => {
    if (!value) {
      setError('Channel is required');
      return false;
    }
    if (value.startsWith('#') || value.startsWith('@')) {
      setError(null);
      return true;
    }
    setError('Channel must start with # (for channels) or @ (for users)');
    return false;
  };

  const createWebhookTrigger = async () => {
    if (selectedPlatform === 'teams') {
      toast({
        title: "Teams Integration",
        description: "Teams integration requires Kubiya to enable it for your organization. Please contact support for more information.",
        variant: "destructive"
      });
      return;
    }

    if (isAuth0Loading || isLoadingProfile) {
      toast({
        title: "Loading User Data",
        description: "Please wait while we load your user information.",
        variant: "default"
      });
      return;
    }

    const userEmail = profileData?.email || auth0User?.email;
    if (!userEmail) {
      console.error('Missing user email:', { profileData, auth0User });
      toast({
        title: "Missing Email",
        description: "Your email is required to create a webhook trigger. Please ensure you're properly logged in.",
        variant: "destructive"
      });
      return;
    }

    if (selectedPlatform === 'slack' && validateChannel(channel)) {
      try {
        setIsCreating(true);
        const response = await fetch('/api/webhooks/create', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            provider,
            eventType,
            agentId: teammate?.uuid,
            promptTemplate,
            platform: selectedPlatform,
            channel
          })
        });

        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.details || 'Failed to create webhook trigger');
        }
        
        toast({
          title: "Webhook Trigger Created!",
          description: "Your webhook has been created successfully. You can now proceed with the setup.",
          variant: "default"
        });

        onContinue({ 
          type: selectedPlatform, 
          channel,
          webhookUrl: data.webhookUrl,
          webhookId: data.id,
          name: data.name,
          source: data.source,
          communication: data.communication,
          createdAt: data.created_at,
          createdBy: data.created_by,
          org: data.org
        });
      } catch (err) {
        console.error('Error creating webhook:', err);
        toast({
          title: "Error Creating Webhook",
          description: err instanceof Error ? err.message : 'Failed to create webhook trigger',
          variant: "destructive"
        });
      } finally {
        setIsCreating(false);
      }
    }
  };

  return (
    <div className="space-y-8">
      <div className="space-y-3">
        <h3 className="text-xl font-semibold text-slate-200">Choose Your Interaction Platform</h3>
        <p className="text-sm text-slate-400">
          Select where you want to receive notifications and interact with the AI. Each platform offers different features and capabilities.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {PLATFORMS.map((platform) => (
          <button
            key={platform.id}
            onClick={() => {
              if (!platform.available) {
                toast({
                  title: `${platform.name} Integration`,
                  description: "This integration is coming soon. Please check back later or contact support for early access.",
                  variant: "destructive"
                });
                return;
              }
              setSelectedPlatform(platform.id);
            }}
            disabled={!platform.available}
            className={cn(
              "relative p-6 rounded-xl border transition-all text-left",
              selectedPlatform === platform.id
                ? "bg-emerald-500/10 border-emerald-500/30 ring-2 ring-emerald-500/20"
                : platform.available
                ? "bg-[#141B2B] border-[#2D3B4E] hover:border-emerald-500/30 hover:bg-emerald-500/5"
                : "bg-[#141B2B] border-[#2D3B4E] opacity-60 cursor-not-allowed"
            )}
          >
            <div className="flex items-start gap-4">
              <div className="relative w-12 h-12 flex items-center justify-center rounded-lg bg-[#1E293B]">
                <div className={cn(
                  "transition-opacity",
                  selectedPlatform === platform.id ? "text-emerald-400" : "text-slate-400",
                  !platform.available && "opacity-50"
                )}>
                  {platform.icon}
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-lg font-medium text-slate-200">{platform.name}</h4>
                  {platform.comingSoon ? (
                    <Badge variant="outline" className="bg-[#1E293B] text-slate-400 border-slate-700">Coming Soon</Badge>
                  ) : selectedPlatform === platform.id && (
                    <Badge variant="outline" className="bg-emerald-500/10 border-emerald-500/30 text-emerald-400">
                      Selected
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-slate-400 mb-4">{platform.description}</p>
                <div className="flex flex-wrap gap-2">
                  {platform.features.map((feature, index) => (
                    <span 
                      key={index}
                      className="text-xs px-2 py-1 rounded-full bg-[#1E293B] text-slate-400"
                    >
                      {feature}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </button>
        ))}
      </div>

      {selectedPlatform === 'slack' && (
        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">Channel or User</label>
            <div className="relative">
              <Input
                value={channel}
                onChange={(e) => {
                  setChannel(e.target.value);
                  if (error) validateChannel(e.target.value);
                }}
                placeholder="Enter #channel or @user"
                className={cn(
                  "bg-[#141B2B] border-[#2D3B4E] text-slate-200 pl-8",
                  error ? "border-red-400/50" : "focus:border-emerald-500/50"
                )}
              />
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                {channel.startsWith('@') ? '@' : '#'}
              </span>
            </div>
            {error && (
              <div className="flex items-center gap-2 text-red-400 text-sm">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            )}
            <p className="text-xs text-slate-400">
              Use # for channels (e.g., #alerts) or @ for users (e.g., @john)
            </p>
          </div>

          <Button
            onClick={createWebhookTrigger}
            disabled={!channel || !!error || isCreating}
            className={cn(
              "w-full h-11 text-white shadow-sm transition-all duration-200",
              !error && channel && !isCreating
                ? "bg-emerald-500 hover:bg-emerald-600 shadow-emerald-500/20"
                : "bg-slate-600 opacity-50 cursor-not-allowed"
            )}
          >
            {isCreating ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Creating Webhook...
              </>
            ) : (
              "Create Webhook"
            )}
          </Button>
        </div>
      )}
    </div>
  );
} 