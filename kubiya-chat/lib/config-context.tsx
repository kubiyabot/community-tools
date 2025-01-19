"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';

export type AuthType = 'sso' | 'apiKey';

interface ConfigContextType {
  apiKey: string | null;
  authType: AuthType | null;
  setApiKey: (key: string) => void;
  setAuthType: (type: AuthType) => void;
  clearApiKey: () => void;
}

const ConfigContext = createContext<ConfigContextType | undefined>(undefined);

export function ConfigProvider({ children }: { children: React.ReactNode }) {
  const [apiKey, setApiKeyState] = useState<string | null>(null);
  const [authType, setAuthTypeState] = useState<AuthType | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    try {
      const storedKey = localStorage.getItem('kubiya_api_key');
      const storedAuthType = localStorage.getItem('kubiya_auth_type') as AuthType | null;
      const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

      console.log('Initial storage load:', {
        hasKey: !!storedKey,
        authType: storedAuthType,
        isLocalhost
      });

      if (storedKey) setApiKeyState(storedKey);
      if (storedAuthType) setAuthTypeState(storedAuthType);
      setIsInitialized(true);
    } catch (error) {
      console.error('Error initializing from localStorage:', error);
      setIsInitialized(true);
    }
  }, []);

  const setApiKey = (key: string) => {
    try {
      localStorage.setItem('kubiya_api_key', key);
      setApiKeyState(key);
    } catch (error) {
      console.error('Error saving API key to localStorage:', error);
    }
  };

  const setAuthType = (type: AuthType) => {
    try {
      localStorage.setItem('kubiya_auth_type', type);
      setAuthTypeState(type);
    } catch (error) {
      console.error('Error saving auth type to localStorage:', error);
    }
  };

  const clearApiKey = () => {
    try {
      localStorage.removeItem('kubiya_api_key');
      localStorage.removeItem('kubiya_auth_type');
      setApiKeyState(null);
      setAuthTypeState(null);
    } catch (error) {
      console.error('Error clearing API key from localStorage:', error);
    }
  };

  if (!isInitialized) {
    return null;
  }

  return (
    <ConfigContext.Provider value={{ apiKey, authType, setApiKey, setAuthType, clearApiKey }}>
      {children}
    </ConfigContext.Provider>
  );
}

export function useConfig() {
  const context = useContext(ConfigContext);
  if (context === undefined) {
    throw new Error('useConfig must be used within a ConfigProvider');
  }
  return context;
} 