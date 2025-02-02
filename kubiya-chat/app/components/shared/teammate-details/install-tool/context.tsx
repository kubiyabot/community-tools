import { createContext, useContext } from 'react';
import type { UseInstallToolReturn } from './types';

const InstallToolContext = createContext<UseInstallToolReturn | null>(null);

export function useInstallToolContext(): UseInstallToolReturn {
  const context = useContext(InstallToolContext);
  if (!context) {
    throw new Error('useInstallToolContext must be used within InstallToolProvider');
  }
  return context;
}

export const InstallToolProvider = InstallToolContext.Provider; 