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
  const [isLoading, setIsLoading] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [authMethod, setAuthMethod] = useState<'sso' | 'apikey'>('sso');

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
      const audience = 'api.kubiya.ai';
      
      // Generate a random state using crypto
      const state = Array.from(crypto.getRandomValues(new Uint8Array(16)))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
      
      console.log('Starting SSO login:', {
        state,
        origin: window.location.origin
      });
      
      localStorage.setItem('auth_state', state);
      
      // Verify state was stored
      const storedState = localStorage.getItem('auth_state');
      console.log('State storage verification:', {
        state,
        storedState,
        match: state === storedState
      });
      
      // Construct Auth0 URL with proper parameters
      const auth0Url = new URL(`https://${auth0Domain}/authorize`);
      auth0Url.searchParams.append('client_id', clientId);
      auth0Url.searchParams.append('response_type', 'code');
      auth0Url.searchParams.append('redirect_uri', `${window.location.origin}/auth/callback`);
      auth0Url.searchParams.append('scope', 'openid profile email offline_access');
      auth0Url.searchParams.append('state', state);
      auth0Url.searchParams.append('audience', audience);
      auth0Url.searchParams.append('connection', 'google-oauth2');
      auth0Url.searchParams.append('prompt', 'login');

      console.log('Redirecting to Auth0:', {
        url: auth0Url.toString(),
        params: Object.fromEntries(auth0Url.searchParams.entries())
      });

      window.location.href = auth0Url.toString();
    } catch (err) {
      console.error('SSO redirect error:', {
        error: err,
        message: err instanceof Error ? err.message : String(err)
      });
      setError(`Failed to redirect to SSO provider: ${err instanceof Error ? err.message : String(err)}`);
      setIsLoading(false);
    }
  };

  const handleApiKeySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      // Test the API key
      const response = await fetch('https://api.kubiya.ai/api/v1/agents?mode=all', {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `UserKey ${tempKey.trim()}`
        }
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.message || `API Error: ${response.status} ${response.statusText}`);
      }

      // API key is valid
      setApiKey(tempKey.trim())
      setIsEditing(false);
    } catch (err) {
      console.error('API key validation error:', err);
      setError(err instanceof Error ? err.message : 'Failed to validate API key');
    } finally {
      setIsLoading(false);
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
          authMethod === 'sso' ? 'opacity-100' : 'opacity-0 pointer-events-none h-0'
        )}>
          <Button
            className="w-full h-10 bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-medium rounded-lg flex items-center justify-center gap-2"
            onClick={handleSsoLogin}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                Redirecting...
              </>
            ) : (
              <>
                <ShieldCheckIcon className="w-4 h-4" />
                Continue with SSO
              </>
            )}
          </Button>
        </div>

        <div className={cn(
          "space-y-4 transition-all duration-300",
          authMethod === 'apikey' ? 'opacity-100' : 'opacity-0 pointer-events-none h-0'
        )}>
          <form onSubmit={handleApiKeySubmit} className="space-y-4">
            <div>
              <Input
                type="password"
                value={tempKey}
                onChange={(e) => setTempKey(e.target.value)}
                placeholder="Enter your API key"
                className="w-full h-10 bg-[#0F172A] border border-[#2D3B4E] text-white placeholder-[#64748B] rounded-lg px-3"
                required
              />
            </div>

            {error && (
              <div className="rounded-md bg-red-500/10 p-4">
                <div className="flex">
                  <AlertCircleIcon className="h-5 w-5 text-red-400" />
                  <div className="ml-3">
                    <p className="text-sm text-red-400">{error}</p>
                  </div>
                </div>
              </div>
            )}

            <Button
              type="submit"
              className="w-full h-10 bg-[#7C3AED] hover:bg-[#6D28D9] text-white font-medium rounded-lg flex items-center justify-center gap-2"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                  Validating...
                </>
              ) : (
                <>
                  <SaveIcon className="w-4 h-4" />
                  Connect
                </>
              )}
            </Button>
          </form>

          <div className="text-center">
            <a
              href="https://app.kubiya.ai/api-keys"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-[#7C3AED] hover:text-[#6D28D9]"
            >
              Get an API key
              <ExternalLinkIcon className="w-4 h-4" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
} 