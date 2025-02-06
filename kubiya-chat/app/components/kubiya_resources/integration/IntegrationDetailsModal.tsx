"use client";

import { format } from 'date-fns';
import { Settings, Calendar, User, Globe, Key, Database, Users } from 'lucide-react';
import { Badge } from '@/app/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/app/components/ui/dialog';
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '@/app/components/ui/tabs';
import type { Integration, AWSVendorSpecific, GitHubVendorSpecific, JiraVendorSpecific } from '@/app/types/integration';
import { IntegrationIcon } from './IntegrationIcon';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/app/components/ui/tooltip';

interface IntegrationDetailsModalProps {
  integration: Integration;
  isOpen: boolean;
  onClose: () => void;
}

export function IntegrationDetailsModal({ integration, isOpen, onClose }: IntegrationDetailsModalProps) {
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
                        <span>Created by {config.kubiya_metadata?.user_created || 'Unknown'}</span>
                      </div>
                    </div>

                    {config.vendor_specific && (
                      <div className="space-y-2">
                        {Object.entries(config.vendor_specific).map(([key, value]) => (
                          <TooltipProvider key={key}>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <div className="flex items-center gap-2 text-sm text-[#94A3B8] cursor-help">
                                  <Settings className="h-4 w-4" />
                                  <span className="truncate">{key}: {value}</span>
                                </div>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p className="text-xs font-mono">{value}</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
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
} 