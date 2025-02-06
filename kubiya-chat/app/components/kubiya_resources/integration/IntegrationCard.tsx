"use client";

import React, { useState, useMemo } from 'react';
import { format } from 'date-fns';
import { GitMerge, Globe, Key, Settings, Calendar, User, GitBranch, Database } from 'lucide-react';
import { Badge } from '@/app/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/app/components/ui/tooltip';
import type { 
  Integration, 
  AWSVendorSpecific, 
  GitHubVendorSpecific, 
  JiraVendorSpecific 
} from '@/app/types/integration';
import { IntegrationIcon } from '@/app/components/kubiya_resources/integration/IntegrationIcon';
import { IntegrationDetailsModal } from '@/app/components/kubiya_resources/integration/IntegrationDetailsModal';

interface IntegrationCardProps {
  integration: Integration;
  className?: string;
}

export function IntegrationCard({ integration, className }: IntegrationCardProps) {
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
        className={cn(
          "group relative bg-[#0F1629] rounded-xl border border-[#1E293B] overflow-hidden transition-all duration-200 hover:border-[#7C3AED]/50 hover:shadow-lg hover:shadow-[#7C3AED]/5 cursor-pointer",
          className
        )}
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
} 