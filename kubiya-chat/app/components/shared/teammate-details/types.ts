import type { Integration as BaseIntegration, IntegrationConfigItem } from '@/app/types/integration';
import type { Tool } from '@/app/types/tool';
import type { TeammateDetails } from '@/app/types/teammate';
import type { SourceInfo } from '@/app/types/source';

// Re-export the base types
export type { BaseIntegration };

// Extended types
export interface ExtendedIntegration extends BaseIntegration {
  uuid?: string;
  id?: string;
  icon_url?: string;
  type?: string;
}

// Composite types
export type TeammateWithIntegrations = TeammateDetails & {
  integrations: BaseIntegration[];
};

// Props interfaces
export interface TeammateHeaderProps {
  teammate: TeammateDetails | null;
  integrations?: BaseIntegration[];
}

export interface TeammateDetailsModalProps {
  isOpen: boolean;
  onCloseAction: () => void;
  teammate: TeammateDetails | null;
  integrations?: BaseIntegration[];
}

export interface SourcesTabProps {
  teammate: TeammateDetails | null;
  sources?: SourceInfo[];
  isLoading?: boolean;
}

// Re-export TeammateDetails
export { TeammateDetails };

