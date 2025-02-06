import * as React from 'react';
import type { UseFormReturn } from 'react-hook-form';
import type { TeammateDetails } from '@/app/types/teammate';
import type { UseInstallToolReturn } from './types';

interface InstallToolContextValue extends UseInstallToolReturn {
  teammate: TeammateDetails;
}

const InstallToolContext = React.createContext<InstallToolContextValue | null>(null);

interface InstallToolProviderProps {
  children: React.ReactNode;
  teammate: TeammateDetails;
  value: UseInstallToolReturn;
}

export function InstallToolProvider({ 
  children, 
  teammate,
  value 
}: InstallToolProviderProps) {
  const contextValue = React.useMemo(() => ({
    ...value,
    teammate
  }), [value, teammate]);

  return (
    <InstallToolContext.Provider value={contextValue}>
      {children}
    </InstallToolContext.Provider>
  );
}

export function useInstallToolContext() {
  const context = React.useContext(InstallToolContext);
  if (!context) {
    throw new Error('useInstallToolContext must be used within an InstallToolProvider');
  }
  return context;
} 