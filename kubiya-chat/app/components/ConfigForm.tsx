import React, { useState } from 'react';
import { setKubiyaConfig } from '../config';
import { getKubiyaConfig } from '../config';

export function ConfigForm({ onConfigured }: { onConfigured: () => void }) {
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState<string>();
  const [isConfiguring, setIsConfiguring] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(undefined);
    setIsConfiguring(true);

    try {
      // Save the configuration first
      setKubiyaConfig({ 
        apiKey: apiKey.trim(),
        baseUrl: 'https://api.kubiya.ai/api/v1'
      });

      // Test the API key by making a request
      const config = getKubiyaConfig();
      const response = await fetch(`${config.baseUrl}/agents?mode=all`, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `UserKey ${apiKey.trim()}`,
        },
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.message || `API Error: ${response.status} ${response.statusText}`);
      }

      // Configuration is valid
      onConfigured();
    } catch (err) {
      console.error('Configuration error:', err);
      setError(err instanceof Error ? err.message : 'Failed to configure API key');
      
      // Clear the invalid configuration
      localStorage.removeItem('kubiya_config');
    } finally {
      setIsConfiguring(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0F172A]">
      <div className="w-full max-w-md space-y-8 rounded-xl bg-[#1E293B] p-8 shadow-lg">
        <div>
          <h2 className="text-center text-3xl font-bold text-white">
            Welcome to Kubiya
          </h2>
          <p className="mt-2 text-center text-sm text-[#94A3B8]">
            Please enter your API key to get started
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="apiKey" className="sr-only">
              API Key
            </label>
            <input
              id="apiKey"
              name="apiKey"
              type="password"
              required
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="relative block w-full appearance-none rounded-lg border border-[#64748B]/20 bg-[#0F172A] px-3 py-2 text-white placeholder-[#64748B] focus:z-10 focus:border-[#7C3AED] focus:outline-none focus:ring-[#7C3AED] sm:text-sm"
              placeholder="Enter your API key"
            />
          </div>

          {error && (
            <div className="rounded-md bg-red-500/10 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-red-400"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-400">{error}</p>
                </div>
              </div>
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={isConfiguring}
              className="group relative flex w-full justify-center rounded-lg bg-[#7C3AED] px-4 py-2 text-sm font-medium text-white hover:bg-[#6D28D9] focus:outline-none focus:ring-2 focus:ring-[#7C3AED] focus:ring-offset-2 disabled:opacity-50"
            >
              {isConfiguring ? (
                <>
                  <span className="absolute inset-y-0 left-0 flex items-center pl-3">
                    <svg
                      className="h-5 w-5 animate-spin text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                  </span>
                  Configuring...
                </>
              ) : (
                'Configure'
              )}
            </button>
          </div>

          <div className="text-center text-xs text-[#94A3B8]">
            <p>
              Don&apos;t have an API key?{' '}
              <a
                href="https://app.kubiya.ai/api-keys"
                target="_blank"
                rel="noopener noreferrer"
                className="text-[#7C3AED] hover:text-[#6D28D9]"
              >
                Get one here
              </a>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
} 