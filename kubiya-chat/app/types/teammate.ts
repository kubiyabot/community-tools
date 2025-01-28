import { Integration } from './integration';

export interface TeammateInfo {
  uuid: string;
  name: string;
  team_id?: string;
  user_id?: string;
  org_id?: string;
  email?: string;
  context?: string;
  integrations?: (Integration | string)[];
  avatar?: string;
  role?: string;
  status?: 'active' | 'inactive' | 'busy';
  lastActive?: string;
  preferences?: {
    notifications?: boolean;
    theme?: 'light' | 'dark' | 'system';
    language?: string;
  };
}

export interface TeammateContextType {
  teammates: TeammateInfo[];
  selectedTeammate?: TeammateInfo;
  setSelectedTeammate: (teammate: TeammateInfo | string) => void;
  isLoading?: boolean;
  error?: Error;
} 