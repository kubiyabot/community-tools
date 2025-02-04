import React, { useEffect, useState } from 'react';
import { Loader2, Settings, AlertCircle, ExternalLink, Plus, Cloud, Key, Shield, User, Database, Globe, GitBranch, Terminal, Bot, Lock, FileKey, Webhook, Boxes, Clock, RefreshCw, Zap } from 'lucide-react';
import type { TeammateInfo } from '@/app/types/teammate';
import type { Integration, IntegrationConfigItem } from '@/app/types/integration';
import { Button } from '@/app/components/ui/button';
import { Separator } from '@/app/components/ui/separator';
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/app/components/ui/hover-card";
import { Badge } from '@/app/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/app/components/ui/tooltip";

// Reuse the IntegrationIcon component from SourcesTab
const IntegrationIcon = ({ type }: { type: string }) => {
  const normalizedType = type?.toLowerCase?.() || '';
  
  const getIconUrl = () => {
    switch (normalizedType) {
      case 'aws':
      case 'aws-serviceaccount':
        return 'https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg';
      case 'github':
        return 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png';
      case 'jira':
        return 'https://wac-cdn.atlassian.com/assets/img/favicons/atlassian/favicon-32x32.png';
      case 'slack':
        return 'https://a.slack-edge.com/80588/marketing/img/meta/slack_hash_256.png';
      case 'gitlab':
        return 'https://about.gitlab.com/images/press/logo/png/gitlab-icon-rgb.png';
      case 'kubernetes':
      case 'k8s':
        return 'https://kubernetes.io/images/favicon.png';
      default:
        return null;
    }
  };

  const iconUrl = getIconUrl();

  if (iconUrl) {
    return (
      <img 
        src={iconUrl} 
        alt={type} 
        className="h-6 w-6 object-contain"
      />
    );
  }

  // Fallback icons based on type
  switch (normalizedType) {
    case 'webhook':
      return <Webhook className="h-5 w-5 text-green-400" />;
    case 'database':
      return <Database className="h-5 w-5 text-blue-400" />;
    case 'api':
      return <Globe className="h-5 w-5 text-purple-400" />;
    case 'bot':
      return <Bot className="h-5 w-5 text-orange-400" />;
    default:
      return <Settings className="h-5 w-5 text-[#7C3AED]" />;
  }
};

const LoadingSpinner = () => (
  <div className="flex flex-col items-center justify-center h-[400px] p-6">
    <div className="p-3 rounded-full bg-[#1E293B] border border-[#1E293B]">
      <Loader2 className="h-6 w-6 text-[#7C3AED] animate-spin" />
    </div>
    <p className="text-sm font-medium text-[#94A3B8] mt-4">Loading integrations...</p>
  </div>
);

const EmptyState = () => (
  <div className="flex flex-col items-center justify-center h-[400px] p-6">
    <div className="p-3 rounded-full bg-[#1E293B] border border-[#1E293B]">
      <Settings className="h-6 w-6 text-[#7C3AED]" />
    </div>
    <p className="text-sm font-medium text-[#94A3B8] mt-4">No integrations configured</p>
  </div>
);

const ErrorState = ({ message }: { message: string }) => (
  <div className="flex flex-col items-center justify-center h-[400px] p-6">
    <div className="p-3 rounded-full bg-red-500/10 border border-red-500/20">
      <AlertCircle className="h-6 w-6 text-red-400" />
    </div>
    <p className="text-sm font-medium text-red-400 mt-4">{message}</p>
  </div>
);

const IntegrationCard = ({ integration }: { integration: Integration }) => {
  const getAuthTypeLabel = (authType: string) => {
    switch (authType) {
      case 'global':
        return 'Global Authentication';
      case 'per_user':
        return 'Per-User Authentication';
      default:
        return 'Custom Authentication';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const renderAWSDetails = (config: IntegrationConfigItem) => {
    const {
      arn,
      region,
      account_id,
      role_name,
      secret_name,
      capabilities = [],
      supported_fields = []
    } = config.vendor_specific || {};

    return (
      <div className="space-y-4">
        {/* Main AWS Info */}
        <div className="bg-gradient-to-r from-[#232f3e] to-[#1E293B] rounded-lg p-4 border border-[#2D3B4E] shadow-lg">
          <div className="flex items-center gap-3 mb-3">
            <Cloud className="h-5 w-5 text-[#FF9900]" />
            <span className="text-sm font-semibold text-white">AWS Configuration</span>
          </div>
          
          {/* ARN Section */}
          {arn && (
            <div className="mt-3">
              <div className="flex items-center gap-2 text-xs text-[#94A3B8] mb-2">
                <Key className="h-4 w-4 text-[#FF9900]" />
                <span className="font-medium">Role ARN</span>
              </div>
              <code className="block bg-[#1a1f36] rounded p-3 text-xs font-mono text-[#FF9900] overflow-x-auto border border-[#2D3B4E]">
                {arn}
              </code>
            </div>
          )}
        </div>

        {/* AWS Details Grid */}
        <div className="grid grid-cols-2 gap-4">
          {/* Account Details */}
          <div className="bg-gradient-to-br from-[#1E293B] to-[#161e2e] rounded-lg p-4 border border-[#2D3B4E] shadow-md">
            <div className="flex items-center gap-2 mb-3">
              <Shield className="h-4 w-4 text-green-400" />
              <span className="text-sm font-medium text-white">Account Details</span>
            </div>
            <div className="space-y-3">
              {account_id && (
                <div className="flex items-center justify-between text-xs bg-[#1a1f36] p-2 rounded border border-[#2D3B4E]">
                  <span className="text-[#94A3B8] font-medium">Account ID:</span>
                  <span className="font-mono text-green-400">{account_id}</span>
                </div>
              )}
              {region && (
                <div className="flex items-center justify-between text-xs bg-[#1a1f36] p-2 rounded border border-[#2D3B4E]">
                  <span className="text-[#94A3B8] font-medium">Region:</span>
                  <span className="font-mono text-green-400">{region}</span>
                </div>
              )}
            </div>
          </div>

          {/* Role Details */}
          <div className="bg-gradient-to-br from-[#1E293B] to-[#161e2e] rounded-lg p-4 border border-[#2D3B4E] shadow-md">
            <div className="flex items-center gap-2 mb-3">
              <User className="h-4 w-4 text-orange-400" />
              <span className="text-sm font-medium text-white">Role Details</span>
            </div>
            <div className="space-y-3">
              {role_name && (
                <div className="flex items-center justify-between text-xs bg-[#1a1f36] p-2 rounded border border-[#2D3B4E]">
                  <span className="text-[#94A3B8] font-medium">Role Name:</span>
                  <span className="font-mono text-orange-400">{role_name}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Capabilities and Supported Fields */}
        <div className="grid grid-cols-2 gap-4">
          {capabilities.length > 0 && (
            <div className="bg-gradient-to-br from-[#1E293B] to-[#161e2e] rounded-lg p-4 border border-[#2D3B4E] shadow-md">
              <div className="flex items-center gap-2 mb-3">
                <Lock className="h-4 w-4 text-blue-400" />
                <span className="text-sm font-medium text-white">Capabilities</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {capabilities.map((cap, idx) => (
                  <Badge 
                    key={idx}
                    variant="outline" 
                    className="bg-blue-500/10 text-blue-400 border-blue-500/20 text-xs hover:bg-blue-500/20 transition-colors"
                  >
                    {cap}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {supported_fields.length > 0 && (
            <div className="bg-gradient-to-br from-[#1E293B] to-[#161e2e] rounded-lg p-4 border border-[#2D3B4E] shadow-md">
              <div className="flex items-center gap-2 mb-3">
                <Database className="h-4 w-4 text-purple-400" />
                <span className="text-sm font-medium text-white">Supported Fields</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {supported_fields.map((field, idx) => (
                  <Badge 
                    key={idx}
                    variant="outline" 
                    className="bg-purple-500/10 text-purple-400 border-purple-500/20 text-xs hover:bg-purple-500/20 transition-colors"
                  >
                    {field}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Secrets Section */}
        {secret_name && (
          <div className="bg-gradient-to-br from-[#1E293B] to-[#161e2e] rounded-lg p-4 border border-[#2D3B4E] shadow-md">
            <div className="flex items-center gap-2 mb-3">
              <Lock className="h-4 w-4 text-red-400" />
              <span className="text-sm font-medium text-white">Secrets Configuration</span>
            </div>
            <div className="flex items-center justify-between text-xs bg-[#1a1f36] p-2 rounded border border-[#2D3B4E]">
              <span className="text-[#94A3B8] font-medium">Secret Name:</span>
              <span className="font-mono text-red-400">{secret_name}</span>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderGitHubDetails = (config: IntegrationConfigItem) => {
    const { capabilities = [] } = config.vendor_specific || {};
    return (
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-xs">
          <GitBranch className="h-3.5 w-3.5 text-[#7C3AED]" />
          <span>GitHub Integration</span>
        </div>
        {capabilities.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {capabilities.map((cap, idx) => (
              <Badge 
                key={idx}
                variant="outline" 
                className="bg-purple-500/10 text-purple-400 border-purple-500/20 text-xs"
              >
                {cap}
              </Badge>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderKubernetesDetails = (config: IntegrationConfigItem) => {
    const { vendor_specific } = config;
    if (!vendor_specific) return null;

    return (
      <div className="space-y-4">
        {/* Main K8s Info */}
        <div className="bg-[#1E293B] rounded-lg p-3 border border-[#2D3B4E]">
          <div className="flex items-center gap-2 mb-2">
            <Boxes className="h-4 w-4 text-blue-400" />
            <span className="text-sm font-medium text-white">Kubernetes Configuration</span>
          </div>
        </div>

        {/* K8s Details Grid */}
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(vendor_specific).map(([key, value]) => (
            value && (
              <div key={key} className="bg-[#1E293B] rounded-lg p-3 border border-[#2D3B4E]">
                <div className="flex items-center gap-2 mb-2">
                  {key === 'namespace' ? (
                    <Terminal className="h-3.5 w-3.5 text-green-400" />
                  ) : key === 'service_account' ? (
                    <FileKey className="h-3.5 w-3.5 text-purple-400" />
                  ) : (
                    <Settings className="h-3.5 w-3.5 text-blue-400" />
                  )}
                  <span className="text-xs font-medium text-white">
                    {key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                  </span>
                </div>
                <div className="text-xs font-mono text-[#94A3B8]">
                  {typeof value === 'string' ? value : JSON.stringify(value)}
                </div>
              </div>
            )
          ))}
        </div>

        {/* Capabilities */}
        {Array.isArray(vendor_specific?.capabilities) && vendor_specific.capabilities.length > 0 && (
          <div className="bg-[#1E293B] rounded-lg p-3 border border-[#2D3B4E]">
            <div className="flex items-center gap-2 mb-2">
              <Lock className="h-3.5 w-3.5 text-blue-400" />
              <span className="text-xs font-medium text-white">Capabilities</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {vendor_specific.capabilities.map((cap, idx) => (
                <Badge 
                  key={idx}
                  variant="outline" 
                  className="bg-blue-500/10 text-blue-400 border-blue-500/20 text-xs"
                >
                  {cap}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderConfigDetails = (config: IntegrationConfigItem) => {
    switch (integration.integration_type.toLowerCase()) {
      case 'aws':
      case 'aws-serviceaccount':
        return renderAWSDetails(config);
      case 'github':
        return renderGitHubDetails(config);
      case 'kubernetes':
      case 'k8s':
        return renderKubernetesDetails(config);
      default:
        return null;
    }
  };

  return (
    <div className="bg-gradient-to-br from-[#1E293B] to-[#161e2e] rounded-xl p-6 space-y-4 border border-[#2D3B4E] shadow-lg hover:shadow-xl transition-all duration-300">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-lg bg-gradient-to-br from-[#2A3347] to-[#1a1f36] border border-[#2D3B4E] shadow-md">
            <IntegrationIcon type={integration.integration_type} />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white tracking-wide flex items-center gap-2 mb-2">
              {integration.name}
              <Badge 
                variant="outline" 
                className="bg-[#7C3AED]/10 text-[#7C3AED] border-[#7C3AED]/20 hover:bg-[#7C3AED]/20 transition-colors"
              >
                {integration.integration_type}
              </Badge>
              <Badge 
                variant="outline" 
                className="bg-blue-500/10 text-blue-400 border-blue-500/20 hover:bg-blue-500/20 transition-colors"
              >
                {getAuthTypeLabel(integration.auth_type)}
              </Badge>
            </h3>
            
            {integration.description && (
              <p className="text-sm text-[#94A3B8] mb-3 font-medium">{integration.description}</p>
            )}

            <div className="flex flex-col gap-2 text-xs text-[#94A3B8]">
              <div className="flex items-center gap-2">
                <Clock className="h-3.5 w-3.5 text-[#7C3AED]" />
                <span className="font-medium">Created:</span>
                <span>{formatDate(integration.kubiya_metadata.created_at)}</span>
                {integration.kubiya_metadata.user_created && (
                  <span className="flex items-center gap-1">
                    <User className="h-3.5 w-3.5 text-[#7C3AED]" />
                    {integration.kubiya_metadata.user_created}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <RefreshCw className="h-3.5 w-3.5 text-[#7C3AED]" />
                <span className="font-medium">Updated:</span>
                <span>{formatDate(integration.kubiya_metadata.last_updated)}</span>
                {integration.kubiya_metadata.user_last_updated && (
                  <span className="flex items-center gap-1">
                    <User className="h-3.5 w-3.5 text-[#7C3AED]" />
                    {integration.kubiya_metadata.user_last_updated}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <Separator className="bg-[#2D3B4E]" />

      {/* Configuration Details */}
      <div className="space-y-4">
        <h4 className="text-sm font-medium text-white flex items-center gap-2">
          <Settings className="h-4 w-4 text-[#7C3AED]" />
          Configuration Details
        </h4>
        <div className="grid grid-cols-1 gap-4">
          {integration.configs.map((config: IntegrationConfigItem, index: number) => (
            <div key={index} className="bg-[#1a1f36] rounded-lg p-4 border border-[#2D3B4E]">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-2">
                  <h5 className="text-sm font-medium text-white">{config.name}</h5>
                  {config.is_default && (
                    <Badge className="bg-green-500/10 text-green-400 border-green-500/20">
                      Default
                    </Badge>
                  )}
                </div>
                {config.kubiya_metadata?.created_by && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className="text-xs text-[#94A3B8] flex items-center gap-1 hover:text-[#7C3AED] transition-colors">
                          <User className="h-3.5 w-3.5" />
                          {config.kubiya_metadata.created_by}
                        </div>
                      </TooltipTrigger>
                      <TooltipContent>
                        <div className="text-xs space-y-1">
                          <div className="flex items-center gap-2">
                            <Clock className="h-3.5 w-3.5" />
                            Created: {formatDate(config.kubiya_metadata.created_at || '')}
                          </div>
                          <div className="flex items-center gap-2">
                            <RefreshCw className="h-3.5 w-3.5" />
                            Updated: {formatDate(config.kubiya_metadata.last_updated || '')}
                          </div>
                        </div>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </div>
              {renderConfigDetails(config)}
            </div>
          ))}
        </div>
      </div>

      {/* Integration Capabilities */}
      {integration.kubiya_metadata.capabilities && integration.kubiya_metadata.capabilities.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-white flex items-center gap-2">
            <Zap className="h-4 w-4 text-[#7C3AED]" />
            Integration Capabilities
          </h4>
          <div className="flex flex-wrap gap-2">
            {integration.kubiya_metadata.capabilities.map((capability, index) => (
              <Badge 
                key={index}
                variant="outline" 
                className="bg-[#2A3347] text-[#94A3B8] border-[#2D3B4E] hover:bg-[#1a1f36] transition-colors"
              >
                {capability}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const IntegrationsTab: React.FC<{ teammate: TeammateInfo }> = ({ teammate }) => {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchIntegrationDetails = async () => {
      try {
        if (!teammate?.uuid) {
          setError('No teammate ID available');
          setIsLoading(false);
          return;
        }

        setIsLoading(true);
        const res = await fetch(`/api/teammates/${teammate.uuid}/integrations`);
        
        if (!res.ok) {
          throw new Error(`Failed to fetch integrations: ${res.statusText}`);
        }
        
        const data = await res.json();
        setIntegrations(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch integration details:', err);
        setError(err instanceof Error ? err.message : 'Failed to load integration details');
        setIntegrations([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchIntegrationDetails();
  }, [teammate?.uuid]);

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorState message={error} />;
  if (!integrations.length) return <EmptyState />;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-md bg-[#2A3347] border border-[#2A3347]">
                <Settings className="h-5 w-5 text-[#7C3AED]" />
              </div>
              <h2 className="text-xl font-semibold text-white">Integrations</h2>
              <Badge variant="outline" className="ml-2">
                {integrations.length} {integrations.length === 1 ? 'Integration' : 'Integrations'}
              </Badge>
            </div>
          </div>
        </div>

        <Button
          onClick={() => {/* TODO: Implement add integration */}}
          className="bg-[#7C3AED] hover:bg-[#6D28D9] text-white"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Integration
        </Button>
      </div>

      <Separator className="bg-[#2D3B4E]" />

      {/* Integrations List */}
      <div className="space-y-6">
        {integrations.map((integration) => (
          <IntegrationCard key={integration.uuid} integration={integration} />
        ))}
      </div>
    </div>
  );
};

export default IntegrationsTab; 