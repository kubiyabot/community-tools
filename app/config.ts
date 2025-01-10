interface KubiyaConfig {
  baseUrl: string;
  apiKey: string;
  debug?: boolean;
  autoSession?: boolean;
}

export function getKubiyaConfig(): KubiyaConfig {
  const baseUrl = process.env.NEXT_PUBLIC_KUBIYA_API_URL || 'https://api.kubiya.ai/api/v1';
  const apiKey = process.env.NEXT_PUBLIC_KUBIYA_API_KEY;

  if (!apiKey) {
    throw new Error('NEXT_PUBLIC_KUBIYA_API_KEY is not configured');
  }

  // Ensure the base URL is properly formatted
  const normalizedBaseUrl = baseUrl.endsWith('/')
    ? baseUrl.slice(0, -1)
    : baseUrl;

  return {
    baseUrl: normalizedBaseUrl,
    apiKey,
    debug: false,
    autoSession: true
  };
}

export function hasKubiyaConfig(): boolean {
  try {
    const config = getKubiyaConfig();
    return !!(config.baseUrl && config.apiKey);
  } catch {
    return false;
  }
} 