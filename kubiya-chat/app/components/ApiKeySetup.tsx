import { useState, useEffect } from "react";
import { Button } from "@/app/components/button";
import { Input } from "@/app/components/input";
import { KeyIcon, SaveIcon, EditIcon, AlertCircleIcon, ExternalLinkIcon, CheckCircleIcon, ShieldCheckIcon, LockIcon, SlackIcon } from "lucide-react";
import { useConfig } from "@/lib/config-context";
import Image from "next/image";
import { cn } from "@/lib/utils";
import { SVGProps } from 'react';

const BANNER_IMAGES = [
  "https://cdn.prod.website-files.com/66ac05ef155399c0a0aee1f3/66b62ccedc841cf9bfcf9547_bento-card-1_img.avif",
  "https://cdn.prod.website-files.com/66b2390d7d5386cb599d0345/675eaf99c38fb687722187bf_article%20banner%20.png"
];

const SSO_OPTIONS = [
  {
    id: 'google',
    name: 'Google',
    icon: (props: SVGProps<SVGSVGElement>) => (
      <svg viewBox="0 0 24 24" {...props}>
        <path
          fill="currentColor"
          d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        />
        <path
          fill="currentColor"
          d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        />
        <path
          fill="currentColor"
          d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
        />
        <path
          fill="currentColor"
          d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        />
      </svg>
    ),
    path: '/api/auth/auth0/login-google' as const,
    color: 'bg-white text-gray-900 hover:bg-gray-50'
  },
  {
    id: 'slack',
    name: 'Slack',
    icon: SlackIcon,
    path: '/api/auth/auth0/login-slack' as const,
    color: 'bg-[#4A154B] hover:bg-[#4A154B]/90 text-white'
  }
] as const;

export function ApiKeySetup() {
  const { apiKey, setApiKey, clearApiKey } = useConfig();
  const [isEditing, setIsEditing] = useState(!apiKey);
  const [tempKey, setTempKey] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [authMethod, setAuthMethod] = useState<'sso' | 'apikey'>('sso');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % BANNER_IMAGES.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleAuthMethodChange = (method: 'sso' | 'apikey') => {
    setAuthMethod(method);
    setError(null);
    setTempKey("");
  };

  const handleSsoLogin = async (provider: '/api/auth/auth0/login-google' | '/api/auth/auth0/login-slack') => {
    setIsLoading(true);
    try {
      // Map the provider path to the correct connection ID
      const connectionMap = {
        '/api/auth/auth0/login-google': 'google-oauth2',
        '/api/auth/auth0/login-slack': 'slack'
      } as const;
      
      const connection = connectionMap[provider];
      if (!connection) {
        throw new Error('Invalid provider');
      }
      
      // Redirect to the login endpoint with the connection parameter
      window.location.href = `/api/auth/auth0/login?connection=${connection}`;
    } catch (err) {
      setError(`Failed to redirect to SSO provider: ${err instanceof Error ? err.message : String(err)}`);
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!tempKey) return;
    setIsValidating(true);
    setError(null);
    
    try {
      const baseUrl = process.env.NEXT_PUBLIC_KUBIYA_BASE_URL || 'https://api.kubiya.ai';

      // Validate JWT format
      if (!tempKey.startsWith('ey')) {
        throw new Error('Invalid API key format. Key should start with "ey"');
      }

      // Try to validate the token by fetching agents
      const response = await fetch(`${baseUrl}/api/v1/agents`, {
        method: 'GET',
        headers: { 
          'Authorization': `userkey ${tempKey}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Origin': window.location.origin
        }
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Invalid API key");
        }
        const data = await response.json().catch(() => ({}));
        throw new Error(data.message || "Failed to validate API key");
      }

      // If we can fetch agents, the API key is valid
      const agents = await response.json();
      if (!Array.isArray(agents)) {
        throw new Error("Invalid response from server");
      }

      setApiKey(tempKey);
      setIsEditing(false);
      setTempKey("");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to validate API key");
    } finally {
      setIsValidating(false);
    }
  };

  if (!isEditing && apiKey) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#1E293B] border border-[#2D3B4E]">
        <div className="flex items-center gap-2 flex-1">
          <CheckCircleIcon className="h-5 w-5 text-green-500" />
          <span className="text-sm font-medium text-white">API Key Connected</span>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-3 text-[#94A3B8] hover:text-white hover:bg-[#2D3B4E]"
            onClick={() => setIsEditing(true)}
          >
            <EditIcon className="h-4 w-4 mr-2" />
            Change
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-3 text-red-400 hover:text-red-300 hover:bg-red-500/10"
            onClick={() => {
              clearApiKey();
              setIsEditing(true);
            }}
          >
            Remove
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-md mx-auto">
      <div className="flex flex-col items-center px-8 space-y-4">
        <div className="relative w-full h-[160px] overflow-hidden rounded-lg shadow-lg">
          {BANNER_IMAGES.map((src, index) => (
            <Image
              key={src}
              src={src}
              alt="Kubiya Banner"
              width={400}
              height={160}
              priority
              unoptimized
              style={{ width: '100%', height: 'auto' }}
              className={cn(
                "absolute top-0 left-0 w-full h-full object-cover transition-opacity duration-1000",
                index === currentImageIndex ? 'opacity-100' : 'opacity-0'
              )}
            />
          ))}
        </div>
        <div className="text-center space-y-2">
          <h2 className="text-xl font-semibold text-white">
            {authMethod === 'sso' ? 'Sign in to Kubiya' : 'Connect with API Key'}
          </h2>
          <p className="text-sm text-[#94A3B8]">
            {authMethod === 'sso' 
              ? 'Sign in with your organization credentials'
              : 'Connect with your API key to get started'}
          </p>
        </div>
      </div>

      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-3 p-1 rounded-lg bg-[#1E293B]/30">
          <Button
            variant="outline"
            className={cn(
              "h-10 font-medium transition-all duration-200 border",
              authMethod === 'sso' 
                ? 'bg-white text-[#1E293B] border-white shadow-lg transform scale-[1.02]' 
                : 'bg-transparent border-[#2D3B4E] text-white hover:bg-[#1E293B]/50'
            )}
            onClick={() => handleAuthMethodChange('sso')}
          >
            <LockIcon className="w-4 h-4 mr-2" />
            Sign in with SSO
          </Button>
          <Button
            variant="outline"
            className={cn(
              "h-10 font-medium transition-all duration-200 border",
              authMethod === 'apikey'
                ? 'bg-[#7C3AED] text-white border-[#7C3AED] shadow-lg transform scale-[1.02]'
                : 'bg-transparent border-[#2D3B4E] text-white hover:bg-[#1E293B]/50'
            )}
            onClick={() => handleAuthMethodChange('apikey')}
          >
            <KeyIcon className="w-4 h-4 mr-2" />
            Use API Key
          </Button>
        </div>

        <div className={cn(
          "space-y-4 transition-all duration-300",
          error ? 'transform -translate-y-2' : ''
        )}>
          {authMethod === 'apikey' ? (
            <>
              <div className="relative">
                <div className="flex items-center gap-2 mb-2">
                  <KeyIcon className="h-4 w-4 text-[#7C3AED]" />
                  <label htmlFor="apiKey" className="text-sm font-medium text-white">
                    Enter your API Key
                  </label>
                </div>
                <Input
                  id="apiKey"
                  type="password"
                  value={tempKey}
                  onChange={(e) => {
                    setTempKey(e.target.value);
                    setError(null);
                  }}
                  placeholder="kubiya_sk_..."
                  className="bg-[#1E293B] border-[#2D3B4E] text-white placeholder-[#94A3B8] focus:ring-[#7C3AED] focus:border-[#7C3AED]"
                />
                {error && (
                  <div className="absolute -bottom-6 left-0 flex items-center gap-1.5 text-red-400 text-xs animate-shake">
                    <AlertCircleIcon className="h-3.5 w-3.5" />
                    <span>{error}</span>
                  </div>
                )}
              </div>

              <div className="flex items-center gap-3 p-3 rounded-lg bg-[#1E293B]/50 border border-[#2D3B4E] transition-all duration-200 hover:bg-[#1E293B]">
                <ShieldCheckIcon className="h-5 w-5 text-[#7C3AED] flex-shrink-0" />
                <p className="text-xs text-[#94A3B8]">
                  Your API key is stored securely and inherits user permissions
                </p>
              </div>

              <Button
                onClick={handleSave}
                disabled={!tempKey || isValidating}
                className={cn(
                  "w-full transition-all duration-200",
                  isValidating 
                    ? 'bg-[#7C3AED]/70'
                    : 'bg-[#7C3AED] hover:bg-[#6D28D9] hover:shadow-lg hover:transform hover:scale-[1.02]',
                  'text-white'
                )}
              >
                {isValidating ? (
                  <>
                    <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                    Validating...
                  </>
                ) : (
                  <>
                    <SaveIcon className="mr-2 h-4 w-4" />
                    Connect
                  </>
                )}
              </Button>

              <div className="text-center">
                <a
                  href="https://app.kubiya.ai"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-xs text-[#7C3AED] hover:text-[#6D28D9] transition-colors duration-200"
                >
                  Need an API key? Generate one in the Management Console
                  <ExternalLinkIcon className="inline-block ml-1 h-3 w-3" />
                </a>
              </div>
            </>
          ) : (
            <div className="space-y-3">
              {SSO_OPTIONS.map((option) => (
                <Button
                  key={option.id}
                  onClick={() => handleSsoLogin(option.path)}
                  disabled={isLoading}
                  className={cn(
                    "w-full h-11 font-medium transition-all duration-200",
                    option.color
                  )}
                >
                  <option.icon className="w-5 h-5 mr-2" />
                  Continue with {option.name}
                </Button>
              ))}

              {error && (
                <div className="flex items-center gap-1.5 text-red-400 text-sm mt-2">
                  <AlertCircleIcon className="h-4 w-4" />
                  <span>{error}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 