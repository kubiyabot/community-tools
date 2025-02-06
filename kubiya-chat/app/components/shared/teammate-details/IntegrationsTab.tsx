"use client";

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import type { TeammateWithIntegrations } from './types';
import type { Integration } from '@/app/types/integration';
import { GitMerge, Globe, Key, Settings, Calendar, User, Lock, ExternalLink, AlertCircle, Clock, Info, Database, ChevronRight, RefreshCw, Users, GitBranch } from 'lucide-react';
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../../ui/dialog';
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '../../ui/tabs';

interface IntegrationsTabProps {
  teammate: TeammateWithIntegrations;
}

// Add these type definitions at the top of the file, after the imports
interface AWSVendorSpecific {
  region?: string;
  account_id?: string;
  role_name?: string;
  arn?: string;
  external_id?: string;
  session_name?: string;
  capabilities?: string[];
  supported_fields?: string[];
}

interface GitHubVendorSpecific {
  repository?: string;
  owner?: string;
  branch?: string;
  installation_id?: string;
  capabilities?: string[];
  supported_fields?: string[];
}

interface JiraVendorSpecific {
  site?: string;
  cloud_id?: string;
  project_key?: string;
  capabilities?: string[];
  supported_fields?: string[];
}

type VendorSpecific = AWSVendorSpecific | GitHubVendorSpecific | JiraVendorSpecific;

const IntegrationIcon = ({ type, name }: { type: string; name?: string }) => {
  // Normalize both type and name to handle variations
  const normalizedType = type?.toLowerCase?.() || '';
  const normalizedName = name?.toLowerCase?.() || '';
  
  // Helper function to check if any of the terms are included in type or name
  const includesAny = (terms: string[]) => {
    return terms.some(term => 
      normalizedType.includes(term) || normalizedName.includes(term)
    );
  };
  
  // Map both full names and partial matches
  const getIconUrl = () => {
    // Cloud Providers
    if (includesAny(['aws', 'amazon', 'cloudformation', 'dynamodb', 'lambda', 's3', 'ec2', 'ecs', 'eks'])) {
      return 'https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg';
    }
    if (includesAny(['azure', 'microsoft', 'aks'])) {
      return 'https://upload.wikimedia.org/wikipedia/commons/f/fa/Microsoft_Azure.svg';
    }
    if (includesAny(['gcp', 'google cloud', 'gke', 'bigquery', 'cloud platform'])) {
      return 'https://upload.wikimedia.org/wikipedia/commons/5/51/Google_Cloud_logo.svg';
    }

    // Version Control & CI/CD
    if (includesAny(['github', 'gh'])) {
      return 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png';
    }
    if (includesAny(['gitlab', 'gl'])) {
      return 'https://about.gitlab.com/images/press/logo/svg/gitlab-icon-rgb.svg';
    }
    if (includesAny(['bitbucket', 'bb'])) {
      return 'https://wac-cdn.atlassian.com/assets/img/favicons/bitbucket/favicon-32x32.png';
    }
    if (includesAny(['jenkins', 'ci', 'build'])) {
      return 'https://www.jenkins.io/images/logos/jenkins/jenkins.png';
    }
    if (includesAny(['circleci', 'circle'])) {
      return 'https://cdn.worldvectorlogo.com/logos/circleci.svg';
    }
    if (includesAny(['travis', 'travisci'])) {
      return 'https://cdn.worldvectorlogo.com/logos/travis-ci.svg';
    }

    // Collaboration & Project Management
    if (includesAny(['jira', 'atlassian'])) {
      return 'https://wac-cdn.atlassian.com/assets/img/favicons/jira/favicon-32x32.png';
    }
    if (includesAny(['confluence'])) {
      return 'https://wac-cdn.atlassian.com/assets/img/favicons/confluence/favicon-32x32.png';
    }
    if (includesAny(['slack', 'chat'])) {
      return 'https://a.slack-edge.com/80588/marketing/img/meta/slack_hash_256.png';
    }
    if (includesAny(['teams', 'microsoft teams'])) {
      return 'https://cdn.worldvectorlogo.com/logos/microsoft-teams-1.svg';
    }
    if (includesAny(['discord'])) {
      return 'https://cdn.worldvectorlogo.com/logos/discord-6.svg';
    }

    // Container & Orchestration
    if (includesAny(['kubernetes', 'k8s', 'kube', 'kubectl', 'helm'])) {
      return 'https://kubernetes.io/images/favicon.png';
    }
    if (includesAny(['docker', 'container', 'dockerfile'])) {
      return 'https://www.docker.com/wp-content/uploads/2023/04/docker-logo-white.png';
    }
    if (includesAny(['openshift', 'ocp'])) {
      return 'https://cdn.worldvectorlogo.com/logos/openshift.svg';
    }
    if (includesAny(['rancher'])) {
      return 'https://cdn.worldvectorlogo.com/logos/rancher.svg';
    }

    // Databases
    if (includesAny(['postgresql', 'postgres', 'psql'])) {
      return 'https://www.postgresql.org/media/img/about/press/elephant.png';
    }
    if (includesAny(['mysql', 'mariadb'])) {
      return 'https://www.mysql.com/common/logos/logo-mysql-170x115.png';
    }
    if (includesAny(['mongodb', 'mongo', 'nosql'])) {
      return 'https://cdn.worldvectorlogo.com/logos/mongodb-icon-1.svg';
    }
    if (includesAny(['redis', 'cache'])) {
      return 'https://cdn.worldvectorlogo.com/logos/redis.svg';
    }
    if (includesAny(['elasticsearch', 'elastic', 'elk'])) {
      return 'https://cdn.worldvectorlogo.com/logos/elasticsearch.svg';
    }
    if (includesAny(['cassandra'])) {
      return 'https://cdn.worldvectorlogo.com/logos/cassandra.svg';
    }

    // Monitoring & Logging
    if (includesAny(['prometheus', 'prom'])) {
      return 'https://cdn.worldvectorlogo.com/logos/prometheus.svg';
    }
    if (includesAny(['grafana'])) {
      return 'https://cdn.worldvectorlogo.com/logos/grafana.svg';
    }
    if (includesAny(['datadog', 'dd'])) {
      return 'https://cdn.worldvectorlogo.com/logos/datadog.svg';
    }
    if (includesAny(['splunk'])) {
      return 'https://cdn.worldvectorlogo.com/logos/splunk.svg';
    }

    // Service Mesh & API
    if (includesAny(['istio'])) {
      return 'https://cdn.worldvectorlogo.com/logos/istio.svg';
    }
    if (includesAny(['consul', 'hashicorp'])) {
      return 'https://cdn.worldvectorlogo.com/logos/consul-3.svg';
    }
    if (includesAny(['backstage'])) {
      return 'https://backstage.io/img/backstage-logo-white.svg';
    }
    if (includesAny(['kong', 'api gateway'])) {
      return 'https://cdn.worldvectorlogo.com/logos/kong.svg';
    }

    // Security & Identity
    if (includesAny(['vault', 'secrets'])) {
      return 'https://cdn.worldvectorlogo.com/logos/vault-1.svg';
    }
    if (includesAny(['okta', 'auth', 'identity'])) {
      return 'https://cdn.worldvectorlogo.com/logos/okta-2.svg';
    }
    if (includesAny(['auth0'])) {
      return 'https://cdn.worldvectorlogo.com/logos/auth0.svg';
    }

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
  if (includesAny(['database', 'db', 'sql'])) return <Database className="h-5 w-5 text-blue-400" />;
  if (includesAny(['webhook', 'http', 'api'])) return <Globe className="h-5 w-5 text-green-400" />;
  if (includesAny(['custom', 'other'])) return <Settings className="h-5 w-5 text-purple-400" />;

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

  const vendorSpecific = config.vendor_specific;
  const awsDetails = isAWS ? vendorSpecific as AWSVendorSpecific : undefined;
  const githubDetails = isGitHub ? vendorSpecific as GitHubVendorSpecific : undefined;
  const jiraDetails = isJira ? vendorSpecific as JiraVendorSpecific : undefined;

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
          {isAWS && awsDetails && (
            <>
              <div className="flex items-center gap-2">
                <Globe className="h-3.5 w-3.5 text-[#7C3AED]" />
                <span className="text-xs text-[#94A3B8]">
                  Region: {awsDetails.region || 'N/A'}
                </span>
              </div>
              {awsDetails.arn && (
                <>
                  <div className="flex items-center gap-2">
                    <Key className="h-3.5 w-3.5 text-[#7C3AED]" />
                    <span className="text-xs text-[#94A3B8]">
                      Account: {awsDetails.arn.split(':')[4] || 'N/A'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <User className="h-3.5 w-3.5 text-[#7C3AED]" />
                    <span className="text-xs text-[#94A3B8]">
                      Role: {awsDetails.arn.split('/')[1] || 'N/A'}
                    </span>
                  </div>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className="flex items-center gap-2 cursor-help">
                          <Info className="h-3.5 w-3.5 text-[#7C3AED]" />
                          <code className="text-xs text-[#94A3B8] font-mono truncate max-w-[200px]">
                            {awsDetails.arn}
                          </code>
                        </div>
                      </TooltipTrigger>
                      <TooltipContent side="right" className="bg-[#1A1F2E] border-[#2A3347]">
                        <p className="text-xs font-mono text-white">{awsDetails.arn}</p>
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
          {config.kubiya_metadata?.user_created && (
            <div className="flex items-center gap-2">
              <User className="h-3.5 w-3.5 text-[#7C3AED]" />
              <span className="text-xs text-[#94A3B8]">
                Created by {config.kubiya_metadata.user_created}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const MIN_LOADING_TIME = 1500; // Minimum time to show loading animation (1.5 seconds)

const IntegrationCard = ({ integration }: { integration: Integration }) => {
  const [showDetails, setShowDetails] = useState(false);
  const hasConfigs = integration.configs && integration.configs.length > 0;
  const integrationType = integration.integration_type?.toLowerCase() || '';
  const isAWS = integrationType.includes('aws');
  const isGitHub = integrationType.includes('github');
  const isJira = integrationType.includes('jira');
  const isOAuth2 = integration.auth_type === 'per_user';

  // Get the first config for quick access to vendor details
  const primaryConfig = integration.configs?.[0];
  
  // Parse vendor-specific details more comprehensively
  const vendorDetails = useMemo(() => {
    if (!primaryConfig?.vendor_specific) return null;
    
    if (isAWS) {
      const vendorSpecific = primaryConfig.vendor_specific as AWSVendorSpecific;
      const {
        region,
        account_id,
        role_name,
        arn,
        external_id,
        session_name
      } = vendorSpecific;
      
      return {
        type: 'aws' as const,
        details: {
          region,
          accountId: account_id || (arn ? arn.split(':')[4] : null),
          roleName: role_name || (arn ? arn.split('/')[1] : null),
          arn,
          externalId: external_id,
          sessionName: session_name
        }
      };
    }
    
    if (isGitHub) {
      const vendorSpecific = primaryConfig.vendor_specific as GitHubVendorSpecific;
      const {
        repository,
        owner,
        branch,
        installation_id
      } = vendorSpecific;
      
      return {
        type: 'github' as const,
        details: {
          repository,
          owner,
          branch,
          installationId: installation_id
        }
      };
    }
    
    if (isJira) {
      const vendorSpecific = primaryConfig.vendor_specific as JiraVendorSpecific;
      const {
        site,
        cloud_id,
        project_key
      } = vendorSpecific;
      
      return {
        type: 'jira' as const,
        details: {
          site,
          cloudId: cloud_id,
          projectKey: project_key
        }
      };
    }
    
    return {
      type: 'generic' as const,
      details: primaryConfig.vendor_specific
    };
  }, [primaryConfig, isAWS, isGitHub, isJira]);

  return (
    <>
      <div 
        className="group relative bg-[#0F1629] rounded-xl border border-[#1E293B] overflow-hidden transition-all duration-200 hover:border-[#7C3AED]/50 hover:shadow-lg hover:shadow-[#7C3AED]/5 cursor-pointer"
        onClick={() => setShowDetails(true)}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-[#7C3AED]/0 to-[#4F46E5]/0 opacity-0 group-hover:from-[#7C3AED]/5 group-hover:to-[#4F46E5]/5 group-hover:opacity-100 transition-all duration-300" />
        
        <div className="relative p-5">
          <div className="flex items-start gap-4">
            {/* Icon with enhanced styling */}
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-[#7C3AED]/10 to-[#4F46E5]/10 rounded-lg blur-xl group-hover:from-[#7C3AED]/20 group-hover:to-[#4F46E5]/20 transition-all duration-300" />
              <div className="relative p-3 rounded-lg bg-[#1A1F2E] border border-[#2A3347] group-hover:border-[#7C3AED]/30 transition-all duration-200 shadow-xl">
                <IntegrationIcon type={integration.integration_type} name={integration.name} />
              </div>
            </div>
            
            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-medium text-white group-hover:text-[#7C3AED] transition-colors duration-200">
                      {integration.name}
                    </h4>
                    <Badge 
                      variant="secondary"
                      className={cn(
                        "bg-[#7C3AED]/10 text-[#7C3AED] border-[#7C3AED]/20",
                        isOAuth2 && "bg-blue-500/10 text-blue-400 border-blue-500/20"
                      )}
                    >
                      {integration.auth_type}
                    </Badge>
                    {isOAuth2 && (
                      <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20">
                        {integration.configs?.length || 0} users
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-[#94A3B8] leading-relaxed">
                    {integration.description}
                  </p>
                </div>
              </div>

              {/* Quick Details with Vendor Information */}
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  {/* Core Details */}
                  <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
                    <Calendar className="h-3.5 w-3.5" />
                    <span>Created {integration.kubiya_metadata?.created_at && 
                      format(new Date(integration.kubiya_metadata.created_at), 'MMM d, yyyy')}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
                    <User className="h-3.5 w-3.5" />
                    <span>By {integration.kubiya_metadata?.user_created || 'Unknown'}</span>
                  </div>
                  {integration.configs?.length > 0 && (
                    <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
                      <Settings className="h-3.5 w-3.5" />
                      <span>{integration.configs.length} configuration{integration.configs.length !== 1 ? 's' : ''}</span>
                    </div>
                  )}
                </div>

                {/* Vendor-specific Quick Info */}
                {vendorDetails && (
                  <div className="space-y-2">
                    {vendorDetails.type === 'aws' && (
                      <>
                        <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
                          <Globe className="h-3.5 w-3.5" />
                          <span>Region: {vendorDetails.details.region}</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
                          <Key className="h-3.5 w-3.5" />
                          <span>Account: {vendorDetails.details.accountId}</span>
                        </div>
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <div className="flex items-center gap-2 text-xs text-[#94A3B8] cursor-help">
                                <User className="h-3.5 w-3.5" />
                                <span className="truncate">Role: {vendorDetails.details.roleName}</span>
                              </div>
                            </TooltipTrigger>
                            <TooltipContent side="right">
                              <p className="text-xs font-mono">{vendorDetails.details.arn}</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      </>
                    )}
                    {vendorDetails.type === 'github' && (
                      <>
                        <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
                          <GitMerge className="h-3.5 w-3.5" />
                          <span>Repository: {vendorDetails.details.repository}</span>
                        </div>
                        {vendorDetails.details.branch && (
                          <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
                            <GitBranch className="h-3.5 w-3.5" />
                            <span>Branch: {vendorDetails.details.branch}</span>
                          </div>
                        )}
                      </>
                    )}
                    {vendorDetails.type === 'jira' && (
                      <>
                        <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
                          <Globe className="h-3.5 w-3.5" />
                          <span>Site: {vendorDetails.details.site}</span>
                        </div>
                        {vendorDetails.details.projectKey && (
                          <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
                            <Database className="h-3.5 w-3.5" />
                            <span>Project: {vendorDetails.details.projectKey}</span>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>

              {/* Capabilities Preview */}
              {integration.kubiya_metadata?.capabilities && (
                <div className="mt-4 flex flex-wrap gap-1.5">
                  {integration.kubiya_metadata.capabilities.slice(0, 3).map((capability, idx) => (
                    <Badge 
                      key={idx}
                      variant="outline" 
                      className="bg-[#1A1F2E] text-[#94A3B8] border-[#2A3347] text-[10px]"
                    >
                      {capability}
                    </Badge>
                  ))}
                  {integration.kubiya_metadata.capabilities.length > 3 && (
                    <Badge 
                      variant="outline" 
                      className="bg-[#1A1F2E] text-[#94A3B8] border-[#2A3347] text-[10px]"
                    >
                      +{integration.kubiya_metadata.capabilities.length - 3} more
                    </Badge>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <IntegrationDetailsModal
        integration={integration}
        isOpen={showDetails}
        onClose={() => setShowDetails(false)}
      />
    </>
  );
};

// Replace the IntegrationsLoader component with this new version
const IntegrationsLoader = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-6">
      <div className="relative w-64 h-64">
        {/* Central loading spinner */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative">
            <div className="absolute inset-0 bg-[#7C3AED]/10 rounded-full blur-lg animate-pulse" />
            <div className="relative p-4 rounded-full bg-[#1E293B] border border-[#7C3AED]/30">
              <GitMerge className="h-6 w-6 text-[#7C3AED] animate-spin" />
            </div>
          </div>
        </div>

        {/* Floating integration icons */}
        <div className="absolute inset-0">
          {[
            { icon: 'aws', color: '#FF9900', delay: 0 },
            { icon: 'github', color: '#2088FF', delay: 0.2 },
            { icon: 'jira', color: '#0052CC', delay: 0.4 },
            { icon: 'slack', color: '#E01E5A', delay: 0.6 },
            { icon: 'kubernetes', color: '#326CE5', delay: 0.8 }
          ].map((item, index) => (
            <div
              key={index}
              className="absolute w-10 h-10"
              style={{
                left: `${Math.random() * 80 + 10}%`,
                top: `${Math.random() * 80 + 10}%`,
                animation: `float 3s ease-in-out ${item.delay}s infinite`
              }}
            >
              <div 
                className="relative p-2 rounded-lg bg-[#1A1F2E] border border-[#2A3347] shadow-lg"
                style={{ 
                  animation: `pulse 2s ease-in-out ${item.delay}s infinite`,
                  backgroundColor: `${item.color}10`
                }}
              >
                <IntegrationIcon type={item.icon} />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-6 space-y-2 text-center">
        <h3 className="text-base font-medium text-white animate-pulse">
          Loading Integrations
        </h3>
        <div className="flex items-center justify-center gap-1">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-[#7C3AED]"
              style={{ animation: `bounce 1.4s ease-in-out ${i * 0.2}s infinite` }}
            />
          ))}
        </div>
      </div>

      <style jsx>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px) scale(1); }
          50% { transform: translateY(-10px) scale(1.05); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 1; }
        }
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-4px); }
        }
      `}</style>
    </div>
  );
};

// Add new IntegrationDetailsModal component
interface IntegrationDetailsModalProps {
  integration: Integration;
  isOpen: boolean;
  onClose: () => void;
}

const IntegrationDetailsModal = ({ integration, isOpen, onClose }: IntegrationDetailsModalProps) => {
  const integrationType = integration.integration_type?.toLowerCase() || '';
  const isAWS = integrationType === 'aws';
  const isGitHub = integrationType === 'github';
  const isJira = integrationType === 'jira';
  const isOAuth2 = integration.auth_type === 'per_user';

  const vendorSpecific = integration.configs?.[0]?.vendor_specific;
  const awsDetails = isAWS ? vendorSpecific as AWSVendorSpecific : undefined;
  const githubDetails = isGitHub ? vendorSpecific as GitHubVendorSpecific : undefined;
  const jiraDetails = isJira ? vendorSpecific as JiraVendorSpecific : undefined;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto bg-[#0F172A] border-[#2D3B4E]">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-[#1A1F2E] border border-[#2A3347]">
                <IntegrationIcon type={integration.integration_type} name={integration.name} />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">{integration.name}</h2>
                <p className="text-sm text-[#94A3B8]">{integration.description}</p>
              </div>
            </div>
            <Badge 
              variant="secondary"
              className={cn(
                "bg-[#7C3AED]/10 text-[#7C3AED] border-[#7C3AED]/20",
                isOAuth2 && "bg-blue-500/10 text-blue-400 border-blue-500/20"
              )}
            >
              {integration.auth_type}
            </Badge>
          </DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="details" className="mt-4">
          <TabsList className="bg-slate-800/50 border-b border-slate-700">
            <TabsTrigger value="details" className="data-[state=active]:bg-slate-700/50">
              Details
            </TabsTrigger>
            <TabsTrigger value="configs" className="data-[state=active]:bg-slate-700/50">
              Configurations
            </TabsTrigger>
            {isOAuth2 && (
              <TabsTrigger value="users" className="data-[state=active]:bg-slate-700/50">
                Authenticated Users
              </TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="details" className="space-y-6 pt-4">
            {/* Core Details */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-white flex items-center gap-2">
                  <Settings className="h-4 w-4 text-[#7C3AED]" />
                  Integration Details
                </h3>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
                    <Calendar className="h-4 w-4" />
                    <span>Created {integration.kubiya_metadata?.created_at && 
                      format(new Date(integration.kubiya_metadata.created_at), 'MMM d, yyyy h:mm a')}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
                    <User className="h-4 w-4" />
                    <span>Created by {integration.kubiya_metadata?.user_created || 'Unknown'}</span>
                  </div>
                </div>
              </div>

              {/* Vendor-specific details */}
              {vendorSpecific && (
                <div className="space-y-4">
                  <h3 className="text-sm font-medium text-white flex items-center gap-2">
                    <Database className="h-4 w-4 text-[#7C3AED]" />
                    Vendor Details
                  </h3>
                  <div className="space-y-2">
                    {isAWS && awsDetails && (
                      <>
                        <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
                          <Globe className="h-4 w-4" />
                          <span>Region: {awsDetails.region}</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
                          <Key className="h-4 w-4" />
                          <span>Account: {awsDetails.account_id}</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
                          <User className="h-4 w-4" />
                          <span>Role: {awsDetails.role_name}</span>
                        </div>
                        <div className="p-2 rounded-lg bg-[#1A1F2E] border border-[#2A3347] mt-3">
                          <code className="text-xs text-[#94A3B8] font-mono">
                            {awsDetails.arn}
                          </code>
                        </div>
                      </>
                    )}
                    {isGitHub && githubDetails && (
                      <>
                        <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
                          <Globe className="h-4 w-4" />
                          <span>Repository: {githubDetails.repository}</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
                          <User className="h-4 w-4" />
                          <span>Owner: {githubDetails.owner}</span>
                        </div>
                        {githubDetails.branch && (
                          <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
                            <Key className="h-4 w-4" />
                            <span>Branch: {githubDetails.branch}</span>
                          </div>
                        )}
                      </>
                    )}
                    {isJira && jiraDetails && (
                      <>
                        <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
                          <Globe className="h-4 w-4" />
                          <span>Site: {jiraDetails.site}</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
                          <Database className="h-4 w-4" />
                          <span>Cloud ID: {jiraDetails.cloud_id}</span>
                        </div>
                        {jiraDetails.project_key && (
                          <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
                            <Key className="h-4 w-4" />
                            <span>Project Key: {jiraDetails.project_key}</span>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Capabilities */}
            {integration.kubiya_metadata?.capabilities && (
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-white flex items-center gap-2">
                  <Settings className="h-4 w-4 text-[#7C3AED]" />
                  Capabilities
                </h3>
                <div className="flex flex-wrap gap-2">
                  {integration.kubiya_metadata.capabilities.map((capability, idx) => (
                    <Badge 
                      key={idx}
                      variant="outline" 
                      className="bg-[#1A1F2E] text-[#94A3B8] border-[#2A3347]"
                    >
                      {capability}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="configs" className="space-y-6 pt-4">
            <div className="space-y-4">
              {integration.configs?.map((config, idx) => (
                <div 
                  key={idx}
                  className="p-4 rounded-lg bg-[#1A1F2E] border border-[#2A3347]"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <User className="h-4 w-4 text-[#7C3AED]" />
                      <span className="text-sm font-medium text-white">{config.name}</span>
                      {config.is_default && (
                        <Badge variant="secondary" className="bg-[#7C3AED]/10 text-[#7C3AED] border-[#7C3AED]/20">
                          Default
                        </Badge>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
                        <Calendar className="h-4 w-4" />
                        <span>Created {config.kubiya_metadata?.created_at && 
                          format(new Date(config.kubiya_metadata.created_at), 'MMM d, yyyy h:mm a')}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
                        <User className="h-4 w-4" />
                        <span>Created by {config.kubiya_metadata?.created_by || 'Unknown'}</span>
                      </div>
                    </div>

                    {config.vendor_specific && (
                      <div className="space-y-2">
                        {Object.entries(config.vendor_specific).map(([key, value]) => (
                          <div key={key} className="flex items-center gap-2 text-sm text-[#94A3B8]">
                            <Settings className="h-4 w-4" />
                            <span>{key}: {value}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>

          {isOAuth2 && (
            <TabsContent value="users" className="space-y-6 pt-4">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-white flex items-center gap-2">
                    <Users className="h-4 w-4 text-[#7C3AED]" />
                    Authenticated Users
                  </h3>
                  <Badge variant="outline" className="bg-[#1A1F2E] text-[#94A3B8] border-[#2A3347]">
                    {integration.configs?.length || 0} users
                  </Badge>
                </div>

                <div className="grid gap-4">
                  {integration.configs?.map((config, idx) => (
                    <div 
                      key={idx}
                      className="p-4 rounded-lg bg-[#1A1F2E] border border-[#2A3347] flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-full bg-[#2A3347] flex items-center justify-center">
                          <User className="h-4 w-4 text-[#7C3AED]" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-white">{config.name}</p>
                          <p className="text-xs text-[#94A3B8]">
                            Authenticated {config.kubiya_metadata?.created_at && 
                              format(new Date(config.kubiya_metadata.created_at), 'MMM d, yyyy')}
                          </p>
                        </div>
                      </div>
                      {config.is_default && (
                        <Badge variant="secondary" className="bg-[#7C3AED]/10 text-[#7C3AED] border-[#7C3AED]/20">
                          Default User
                        </Badge>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </TabsContent>
          )}
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};

const IntegrationsTab: React.FC<IntegrationsTabProps> = ({ teammate }) => {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadingStartTime, setLoadingStartTime] = useState<number | null>(null);

  const fetchIntegrationDetails = useCallback(async () => {
    try {
      if (!teammate?.uuid) {
        console.error('No teammate UUID provided to IntegrationsTab');
        setError('No teammate ID available. Please ensure the teammate exists and try again.');
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setLoadingStartTime(Date.now());
      
      console.log('Fetching integrations for teammate:', {
        uuid: teammate.uuid,
        name: teammate.name || 'Unknown'
      });
      
      const res = await fetch(`/api/teammates/${teammate.uuid}/integrations`);
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ 
          error: 'Unknown error',
          details: res.statusText 
        }));
        
        throw new Error(
          errorData.details || 
          errorData.error || 
          `Failed to fetch integrations. Please ensure you have the correct permissions and try again.`
        );
      }
      
      const data = await res.json();
      
      // Ensure minimum loading time
      const loadingTime = Date.now() - (loadingStartTime || Date.now());
      if (loadingTime < MIN_LOADING_TIME) {
        await new Promise(resolve => setTimeout(resolve, MIN_LOADING_TIME - loadingTime));
      }

      setIntegrations(data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch integration details:', err);
      setError(err instanceof Error ? err.message : 'Failed to load integration details');
      setIntegrations([]);
    } finally {
      setIsLoading(false);
      setLoadingStartTime(null);
    }
  }, [teammate?.uuid, teammate?.name]);

  useEffect(() => {
    if (teammate?.uuid) {
      fetchIntegrationDetails();
    } else {
      setIsLoading(false);
    }
  }, [teammate?.uuid, fetchIntegrationDetails]);

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
    return <IntegrationsLoader />;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-6">
        <div className="p-3 rounded-full bg-red-500/10 mb-4">
          <AlertCircle className="h-6 w-6 text-red-400" />
        </div>
        <h3 className="text-lg font-medium text-red-400 mb-2">Error Loading Integrations</h3>
        <p className="text-sm text-[#94A3B8] max-w-sm mb-4">
          {error}
        </p>
        <Button 
          variant="outline" 
          onClick={() => {
            setError(null);
            setIsLoading(true);
            fetchIntegrationDetails();
          }}
          className="bg-red-500/10 text-red-400 border-red-500/20 hover:bg-red-500/20"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
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
};

export default IntegrationsTab; 