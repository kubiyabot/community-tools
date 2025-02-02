import type { TeammateDetails } from '@/app/types/teammate';

export interface InstallToolFormProps {
  isOpen: boolean;
  onClose: () => void;
  onInstall: (data: any) => void;
  teammate: TeammateDetails;
} 