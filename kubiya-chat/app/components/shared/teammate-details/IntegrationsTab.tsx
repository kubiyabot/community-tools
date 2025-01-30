"use client";

import React, { useEffect, useState } from 'react';
import type { TeammateDetails } from './types';
import type { Integration } from '@/app/types/integration';
import { GitMerge, Globe, Key, Settings, Calendar, User, Lock, ExternalLink, AlertCircle, Clock, Info, Database, ChevronRight } from 'lucide-react';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../../ui/tooltip';

interface IntegrationsTabProps {
  teammate: (TeammateDetails & { integrations: Integration[] }) | null;
}

const IntegrationIcon = ({ type }: { type: string }) => {
  // Normalize the type to handle variations
  const normalizedType = type?.toLowerCase?.() || '';
  
  // Map both full names and partial matches
  const getIconUrl = () => {
    if (normalizedType.includes('aws')) return 'https://uxwing.com/wp-content/themes/uxwing/download/brands-and-social-media/aws-icon.png';
    if (normalizedType.includes('github')) return 'https://cdn-icons-png.flaticon.com/512/25/25231.png';
    if (normalizedType.includes('jira')) return 'https://cdn-icons-png.flaticon.com/512/5968/5968875.png';
    if (normalizedType.includes('slack')) return 'https://cdn4.iconfinder.com/data/icons/logos-and-brands/512/306_Slack_logo-512.png';
    if (normalizedType.includes('gitlab')) return 'https://about.gitlab.com/images/press/logo/png/gitlab-icon-rgb.png';
    if (normalizedType.includes('kubernetes') || normalizedType.includes('k8s')) return 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Kubernetes_logo_without_workmark.svg/2109px-Kubernetes_logo_without_workmark.svg.png';
    return null;
  };

  const iconUrl = getIconUrl();

  if (iconUrl) {
    return (
      <img 
        src={iconUrl} 
        alt={type || 'Integration'} 
        className="h-5 w-5 object-contain"
      />
    );
  }

  // Default icons for types without specific images
  if (normalizedType.includes('database')) return <Database className="h-5 w-5 text-blue-400" />;
  if (normalizedType.includes('webhook')) return <Globe className="h-5 w-5 text-green-400" />;
  if (normalizedType.includes('custom')) return <Settings className="h-5 w-5 text-purple-400" />;

  return <GitMerge className="h-5 w-5 text-[#7C3AED]" />;
};

const IntegrationConfig = ({ 
  config, 
  isAWS,
  integrationType
}: { 
  config: Integration['configs'][0];
  isAWS: boolean;
  integrationType: string | undefined;
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const type = integrationType?.toLowerCase() || '';
  const isGitHub = type.includes('github');
  const isJira = type.includes('jira');
  const isSlack = type.includes('slack');

  const getPlatformName = () => {
    if (isGitHub) return 'GitHub';
    if (isJira) return 'Jira';
    if (isSlack) return 'Slack';
    return integrationType;
  };

  return (
    <div 
      className={cn(
        "bg-[#0F1629] rounded-lg p-3 border transition-all duration-200",
        isExpanded ? "border-[#7C3AED]" : "border-[#1E293B] hover:border-[#7C3AED]/30",
        "group cursor-pointer"
      )}
      onClick={() => setIsExpanded(!isExpanded)}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {config.is_default && (
            <Badge variant="secondary" className="bg-[#7C3AED]/10 text-[#7C3AED] border-[#7C3AED]/20">
              Default
            </Badge>
          )}
          <div className="flex items-center gap-2">
            <User className="h-4 w-4 text-[#7C3AED]" />
            <span className="text-xs text-white">{config.name}</span>
          </div>
        </div>
        <ChevronRight 
          className={cn(
            "h-4 w-4 text-[#94A3B8] transition-transform duration-200",
            isExpanded && "rotate-90"
          )} 
        />
      </div>

      {/* OAuth2 User Info */}
      {(isGitHub || isJira || isSlack) && (
        <div className="mt-2 flex items-center gap-2">
          <div className="flex-1 p-2 rounded-md bg-[#1A1F2E] border border-[#2A3347]">
            <div className="flex items-center gap-2">
              <Lock className="h-3.5 w-3.5 text-green-400" />
              <span className="text-xs text-green-400">Authenticated User</span>
            </div>
            <p className="text-xs text-[#94A3B8] mt-1">
              This user has authenticated to Kubiya using {getPlatformName()}. The teammate can interact with {getPlatformName()} on their behalf using OAuth2 token refresh managed by Kubiya.
            </p>
          </div>
        </div>
      )}

      {/* Expanded Details */}
      {isExpanded && (
        <div className="mt-3 space-y-2 border-t border-[#1E293B] pt-3">
          {/* AWS Specific Info */}
          {isAWS && config.vendor_specific && (
            <>
              <div className="flex items-center gap-2">
                <Globe className="h-3.5 w-3.5 text-[#7C3AED]" />
                <span className="text-xs text-[#94A3B8]">
                  Region: {config.vendor_specific.region || 'N/A'}
                </span>
              </div>
              {config.vendor_specific.arn && (
                <>
                  <div className="flex items-center gap-2">
                    <Key className="h-3.5 w-3.5 text-[#7C3AED]" />
                    <span className="text-xs text-[#94A3B8]">
                      Account: {config.vendor_specific.arn.split(':')[4] || 'N/A'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <User className="h-3.5 w-3.5 text-[#7C3AED]" />
                    <span className="text-xs text-[#94A3B8]">
                      Role: {config.vendor_specific.arn.split('/')[1] || 'N/A'}
                    </span>
                  </div>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className="flex items-center gap-2 cursor-help">
                          <Info className="h-3.5 w-3.5 text-[#7C3AED]" />
                          <code className="text-xs text-[#94A3B8] font-mono truncate max-w-[200px]">
                            {config.vendor_specific.arn}
                          </code>
                        </div>
                      </TooltipTrigger>
                      <TooltipContent side="right" className="bg-[#1A1F2E] border-[#2A3347]">
                        <p className="text-xs font-mono text-white">{config.vendor_specific.arn}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </>
              )}
            </>
          )}

          {/* Metadata */}
          {config.kubiya_metadata?.created_at && (
            <div className="flex items-center gap-2">
              <Clock className="h-3.5 w-3.5 text-[#7C3AED]" />
              <span className="text-xs text-[#94A3B8]">
                Created {format(new Date(config.kubiya_metadata.created_at), 'MMM d, h:mm a')}
              </span>
            </div>
          )}
          {config.kubiya_metadata?.created_by && (
            <div className="flex items-center gap-2">
              <User className="h-3.5 w-3.5 text-[#7C3AED]" />
              <span className="text-xs text-[#94A3B8]">
                Created by {config.kubiya_metadata.created_by}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const IntegrationCard = ({ integration }: { integration: Integration }) => {
  const hasConfigs = integration.configs && integration.configs.length > 0;
  const integrationType = integration.integration_type?.toLowerCase() || '';
  const isAWS = integrationType.includes('aws');
  const isGitHub = integrationType.includes('github');
  const isJira = integrationType.includes('jira');
  const isOAuth2 = integration.auth_type === 'per_user';  // OAuth2 integrations use per_user auth type

  return (
    <div className="group relative bg-[#0F1629] rounded-lg border border-[#1E293B] overflow-hidden transition-all duration-200 hover:border-[#7C3AED]/50">
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-md bg-[#1A1F2E] border border-[#2A3347] group-hover:border-[#7C3AED]/30">
              <IntegrationIcon type={integration.integration_type} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-medium text-white">{integration.name}</h4>
                <Badge 
                  variant="secondary"
                  className={cn(
                    "bg-[#7C3AED]/10 text-[#7C3AED] border-[#7C3AED]/20",
                    integration.auth_type === 'per_user' && "bg-blue-500/10 text-blue-400 border-blue-500/20"
                  )}
                >
                  {integration.auth_type}
                </Badge>
                {!hasConfigs && (
                  <Badge variant="outline" className="bg-yellow-500/10 text-yellow-400 border-yellow-500/20">
                    No Config
                  </Badge>
                )}
                {integration.uuid && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Badge variant="outline" className="bg-[#1A1F2E] text-[#94A3B8] border-[#2A3347] cursor-help">
                          ID
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent side="right" className="bg-[#1A1F2E] border-[#2A3347]">
                        <p className="text-xs font-mono text-white">{integration.uuid}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </div>
              <p className="text-xs text-[#94A3B8] mt-1">{integration.description}</p>
              
              {/* OAuth2 Info */}
              {isOAuth2 && (
                <div className="mt-2 p-2 rounded-md bg-[#1A1F2E] border border-[#2A3347]">
                  <div className="flex items-center gap-2">
                    <Lock className="h-3.5 w-3.5 text-blue-400" />
                    <span className="text-xs text-blue-400">OAuth2 Integration</span>
                  </div>
                  <p className="text-xs text-[#94A3B8] mt-1">
                    This integration requires individual user authentication. The configurations shown are from users who have authenticated with {integration.name}.
                  </p>
                </div>
              )}

              {/* Capabilities */}
              {integration.kubiya_metadata?.capabilities && integration.kubiya_metadata.capabilities.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {integration.kubiya_metadata.capabilities.map((capability, idx) => (
                    <Badge 
                      key={idx}
                      variant="outline" 
                      className="bg-[#1A1F2E] text-[#94A3B8] border-[#2A3347] text-[10px]"
                    >
                      {capability}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Configurations */}
        {hasConfigs && (
          <div className="mt-4">
            <div className="flex items-center gap-2 mb-2">
              <Settings className="h-4 w-4 text-[#94A3B8]" />
              <span className="text-xs text-[#94A3B8]">
                {integration.auth_type === 'per_user' ? 'User Configurations' : 'Configurations'}
              </span>
            </div>
            <div className="space-y-2">
              {integration.configs.map((config, configIdx) => (
                <IntegrationConfig 
                  key={`${config.name}-${configIdx}`}
                  config={config}
                  isAWS={isAWS}
                  integrationType={integration.integration_type}
                />
              ))}
            </div>
          </div>
        )}

        {/* Metadata */}
        <div className="mt-4 flex items-center gap-4 text-xs text-[#94A3B8]">
          {integration.kubiya_metadata?.created_at && (
            <div className="flex items-center gap-2">
              <Clock className="h-3.5 w-3.5 text-[#7C3AED]" />
              <span>
                Created {format(new Date(integration.kubiya_metadata.created_at), 'MMM d, h:mm a')}
              </span>
            </div>
          )}
          {integration.kubiya_metadata?.user_created && (
            <>
              <div className="text-[#2A3347]">•</div>
              <div className="flex items-center gap-2">
                <User className="h-3.5 w-3.5 text-[#7C3AED]" />
                <span>By {integration.kubiya_metadata.user_created}</span>
              </div>
            </>
          )}
          {integration.managed_by && (
            <>
              <div className="text-[#2A3347]">•</div>
              <div className="flex items-center gap-2">
                <Settings className="h-3.5 w-3.5 text-[#7C3AED]" />
                <span>Managed by {integration.managed_by}</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export function IntegrationsTab({ teammate }: IntegrationsTabProps) {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchIntegrationDetails = async () => {
      try {
        if (!teammate?.uuid) {
          console.error('No teammate UUID provided to IntegrationsTab');
          setError('No teammate ID available');
          setIsLoading(false);
          return;
        }

        setIsLoading(true);
        console.log('Fetching integrations for teammate:', {
          uuid: teammate.uuid,
          name: teammate.name
        });
        
        const res = await fetch(`/api/teammates/${teammate.uuid}/integrations`);
        if (!res.ok) {
          const errorData = await res.json().catch(() => null);
          console.error('Failed to fetch integrations:', {
            status: res.status,
            statusText: res.statusText,
            errorData
          });
          throw new Error(errorData?.details || `Failed to fetch integrations: ${res.statusText}`);
        }
        
        const data = await res.json();
        console.log('Received integrations data:', {
          count: data.length,
          integrations: data.map((i: Integration) => ({
            uuid: i.uuid,
            name: i.name,
            type: i.integration_type
          }))
        });
        
        setIntegrations(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch integration details:', err);
        setError(err instanceof Error ? err.message : 'Failed to load integration details');
      } finally {
        setIsLoading(false);
      }
    };

    if (teammate?.uuid) {
      fetchIntegrationDetails();
    } else {
      setIsLoading(false);
    }
  }, [teammate?.uuid]);

  if (!teammate) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-6">
        <div className="p-3 rounded-full bg-red-500/10 mb-4">
          <AlertCircle className="h-6 w-6 text-red-400" />
        </div>
        <h3 className="text-lg font-medium text-red-400 mb-2">Error Loading Teammate</h3>
        <p className="text-sm text-[#94A3B8] max-w-sm">
          Unable to load teammate details. Please try refreshing the page.
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-6">
        <div className="p-3 rounded-full bg-[#1E293B] animate-pulse">
          <GitMerge className="h-6 w-6 text-[#7C3AED]" />
        </div>
        <h3 className="text-lg font-medium text-white mt-4">Loading Integrations</h3>
        <p className="text-sm text-[#94A3B8] max-w-sm mt-2">
          Fetching integration details...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-6">
        <div className="p-3 rounded-full bg-red-500/10 mb-4">
          <AlertCircle className="h-6 w-6 text-red-400" />
        </div>
        <h3 className="text-lg font-medium text-red-400 mb-2">Error Loading Integrations</h3>
        <p className="text-sm text-[#94A3B8] max-w-sm">
          {error}. Please try refreshing the page.
        </p>
      </div>
    );
  }

  if (!integrations.length) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-6">
        <div className="p-3 rounded-full bg-[#7C3AED]/10 mb-4">
          <GitMerge className="h-6 w-6 text-[#7C3AED]" />
        </div>
        <h3 className="text-lg font-medium text-white mb-2">No Integrations</h3>
        <p className="text-sm text-[#94A3B8] max-w-sm">
          This teammate doesn't have any integrations configured yet.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {integrations.map((integration) => (
        <IntegrationCard key={integration.uuid || integration.name} integration={integration} />
      ))}
    </div>
  );
} 