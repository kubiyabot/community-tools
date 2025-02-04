import * as React from 'react';
import type { TeammateDetails } from '@/app/types/teammate';
import type { Tool } from '@/app/types/tool';
import type { InstallToolFormState, InstallationStep, UseInstallToolReturn } from './types';
import { UseFormReturn } from 'react-hook-form';

interface InstallToolContextType extends UseInstallToolReturn {}

const InstallToolContext = React.createContext<InstallToolContextType | null>(null);

export function InstallToolProvider({ 
  children,
  teammate,
  value
}: { 
  children: React.ReactNode;
  teammate: TeammateDetails;
  value: UseInstallToolReturn;
}) {
  return (
    <InstallToolContext.Provider value={value}>
      {children}
    </InstallToolContext.Provider>
  );
}

export const useInstallToolContext = () => {
  const context = React.useContext(InstallToolContext);
  if (!context) {
    throw new Error('useInstallToolContext must be used within an InstallToolProvider');
  }
  
  // Ensure installationSteps is always an array
  return {
    ...context,
    installationSteps: context.installationSteps || []
  };
}; 