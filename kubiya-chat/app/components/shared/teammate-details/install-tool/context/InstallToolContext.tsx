import * as React from 'react';
import type { UseInstallToolReturn } from '../types';

const InstallToolContext = React.createContext<UseInstallToolReturn | undefined>(undefined);

export function useInstallToolContext() {
  const context = React.useContext(InstallToolContext);
  if (!context) {
    throw new Error('useInstallToolContext must be used within an InstallToolProvider');
  }
  return context;
}

export function InstallToolProvider({ children, value }: { children: React.ReactNode; value: UseInstallToolReturn }) {
  return (
    <InstallToolContext.Provider value={value}>
      {children}
    </InstallToolContext.Provider>
  );
} 