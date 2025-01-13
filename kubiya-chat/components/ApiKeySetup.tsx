import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { KeyIcon, SaveIcon, EditIcon, AlertCircleIcon, ExternalLinkIcon, CheckCircleIcon, ShieldCheckIcon, LockIcon } from "lucide-react";
import { useConfig } from "@/lib/config-context";
import Image from "next/image";
import { cn } from "@/lib/utils";

const BANNER_IMAGES = [
  "https://cdn.prod.website-files.com/66ac05ef155399c0a0aee1f3/66b62ccedc841cf9bfcf9547_bento-card-1_img.avif",
  "https://cdn.prod.website-files.com/66b2390d7d5386cb599d0345/675eaf99c38fb687722187bf_article%20banner%20.png"
];

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

  const handleSsoLogin = async () => {
    setIsLoading(true);
    try {
      // Use production Auth0 settings
      const auth0Domain = 'kubiya.us.auth0.com';
      const clientId = 'SxpP9OU7VSvvPivHFQY5Get3uC1Bx4Jf';
      const audience = 'https://kubiya.ai/api';
      
      // Store state in localStorage for validation
      const state = Math.random().toString(36).substring(7);
      localStorage.setItem('auth_state', state);
      
      // Construct Auth0 URL with proper parameters
      const auth0Url = new URL(`https://${auth0Domain}/authorize`);
      auth0Url.searchParams.append('client_id', clientId);
      auth0Url.searchParams.append('response_type', 'code');
      auth0Url.searchParams.append('redirect_uri', `${window.location.origin}/auth/callback`);
      auth0Url.searchParams.append('scope', 'openid profile email');
      auth0Url.searchParams.append('state', state);
      auth0Url.searchParams.append('audience', audience);
      auth0Url.searchParams.append('connection', 'google-oauth2');
      auth0Url.searchParams.append('prompt', 'login');

      window.location.href = auth0Url.toString();
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

      setApiKey(tempKey, 'apikey');
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
            <div className="space-y-4">
              <Button
                onClick={handleSsoLogin}
                disabled={isLoading}
                className={cn(
                  "w-full transition-all duration-200",
                  isLoading 
                    ? 'bg-[#7C3AED]/70'
                    : 'bg-[#7C3AED] hover:bg-[#6D28D9] hover:shadow-lg hover:transform hover:scale-[1.02]',
                  'text-white'
                )}
              >
                {isLoading ? (
                  <>
                    <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                    Redirecting...
                  </>
                ) : (
                  <>
                    <LockIcon className="mr-2 h-4 w-4" />
                    Continue with SSO
                  </>
                )}
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 