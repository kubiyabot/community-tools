"use client";

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import Cookies from 'js-cookie';

export type AuthType = 'sso' | 'apikey';

interface ConfigContextType {
  apiKey: string | null;
  baseUrl: string;
  setApiKey: (key: string, type: AuthType) => void;
  clearApiKey: () => void;
  isConfigured: boolean;
  isLoading: boolean;
  authType: AuthType | null;
}

const API_KEY_STORAGE = 'kubiya_api_key';
const AUTH_TYPE_STORAGE = 'kubiya_auth_type';
const DEFAULT_BASE_URL = 'https://app.kubiya.ai/api';

const ConfigContext = createContext<ConfigContextType | undefined>(undefined);

function isLocalhost(): boolean {
  if (typeof window === 'undefined') return false;
  const hostname = window.location.hostname;
  return hostname === 'localhost' || hostname === '127.0.0.1';
}

function setStorage(name: string, value: string) {
  try {
    console.log('Setting storage:', { name, hasValue: !!value, isLocalhost: isLocalhost() });
    
    if (isLocalhost()) {
      // For localhost, only use localStorage
      localStorage.setItem(name, value);
      const localValue = localStorage.getItem(name);
      
      console.log('Localhost storage verification:', {
        name,
        hasLocal: !!localValue,
        localMatch: localValue === value
      });
      
      return !!localValue;
    } else {
      // For production, use both cookie and localStorage
      const options = {
        expires: 365,
        path: '/',
        sameSite: 'lax' as const,
        secure: true
      };
      
      localStorage.setItem(name, value);
      Cookies.set(name, value, options);
      
      const cookieValue = Cookies.get(name);
      const localValue = localStorage.getItem(name);
      
      console.log('Production storage verification:', {
        name,
        hasCookie: !!cookieValue,
        hasLocal: !!localValue,
        cookieMatch: cookieValue === value,
        localMatch: localValue === value
      });
      
      return !!cookieValue || !!localValue;
    }
  } catch (error) {
    console.error('Error setting storage:', error);
    return false;
  }
}

function getStorage(name: string): string | null {
  try {
    if (isLocalhost()) {
      // For localhost, only check localStorage
      const value = localStorage.getItem(name);
      console.log('Getting localhost storage:', { name, hasValue: !!value });
      return value;
    }
    
    // For production, try cookie first then localStorage
    const cookieValue = Cookies.get(name);
    if (cookieValue) {
      console.log('Got value from cookie:', name);
      return cookieValue;
    }
    
    const localValue = localStorage.getItem(name);
    if (localValue) {
      console.log('Got value from localStorage:', name);
      // Try to restore cookie
      setStorage(name, localValue);
      return localValue;
    }
    
    console.log('No value found in storage:', { name });
    return null;
  } catch (error) {
    console.error('Error getting storage:', error);
    return null;
  }
}

function clearStorage(name: string) {
  try {
    console.log('Clearing storage:', name);
    
    if (isLocalhost()) {
      // For localhost, only clear localStorage
      localStorage.removeItem(name);
      const localValue = localStorage.getItem(name);
      
      console.log('Localhost clear verification:', {
        name,
        stillHasLocal: !!localValue
      });
      
      return !localValue;
    }
    
    // For production, clear both
    Cookies.remove(name, { path: '/' });
    localStorage.removeItem(name);
    
    const cookieValue = Cookies.get(name);
    const localValue = localStorage.getItem(name);
    
    console.log('Production clear verification:', {
      name,
      stillHasCookie: !!cookieValue,
      stillHasLocal: !!localValue
    });
    
    return !cookieValue && !localValue;
  } catch (error) {
    console.error('Error clearing storage:', error);
    return false;
  }
}

export function ConfigProvider({ children }: { children: ReactNode }) {
  const [apiKey, setApiKeyState] = useState<string | null>(null);
  const [authType, setAuthType] = useState<AuthType | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load stored values on mount
  useEffect(() => {
    const savedKey = getStorage(API_KEY_STORAGE);
    const savedAuthType = getStorage(AUTH_TYPE_STORAGE) as AuthType | null;
    
    console.log('Initial storage load:', { 
      hasKey: !!savedKey, 
      authType: savedAuthType,
      isLocalhost: isLocalhost()
    });
    
    if (savedKey && savedAuthType) {
      setApiKeyState(savedKey);
      setAuthType(savedAuthType);
    }
    setIsLoading(false);
  }, []);

  const setApiKey = useCallback((key: string, type: AuthType) => {
    console.log('Setting API key:', { type });
    
    try {
      // Set both storage values first
      const keySet = setStorage(API_KEY_STORAGE, key);
      const typeSet = setStorage(AUTH_TYPE_STORAGE, type);
      
      console.log('Storage set results:', { keySet, typeSet });

      // Only update state if at least one storage method worked
      if (keySet || typeSet) {
        setApiKeyState(key);
        setAuthType(type);
        
        // Verify final state
        console.log('Final state verification:', {
          storedKey: getStorage(API_KEY_STORAGE),
          storedType: getStorage(AUTH_TYPE_STORAGE)
        });
      } else {
        console.error('Failed to set storage values');
      }
    } catch (error) {
      console.error('Failed to set API key:', error);
    }
  }, []);

  const clearApiKey = useCallback(() => {
    console.log('Clearing API key');
    const keyCleared = clearStorage(API_KEY_STORAGE);
    const typeCleared = clearStorage(AUTH_TYPE_STORAGE);
    
    console.log('Clear results:', { keyCleared, typeCleared });
    
    setApiKeyState(null);
    setAuthType(null);
  }, []);

  const value = {
    apiKey,
    authType,
    baseUrl: process.env.NEXT_PUBLIC_KUBIYA_BASE_URL || DEFAULT_BASE_URL,
    setApiKey,
    clearApiKey,
    isConfigured: !!apiKey && !!authType,
    isLoading
  };

  return (
    <ConfigContext.Provider value={value}>
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