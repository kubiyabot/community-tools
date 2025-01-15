interface KubiyaConfig {
  apiKey: string;
  baseUrl: string;
}

export function getKubiyaConfig(): KubiyaConfig {
  const baseUrl = process.env.NEXT_PUBLIC_KUBIYA_API_URL || 'https://api.kubiya.ai/api/v1';
  
  // Only access localStorage on the client side
  const apiKey = typeof window !== 'undefined' ? localStorage.getItem('kubiya_api_key') || '' : '';
  
  return {
    apiKey,
    baseUrl,
  };
} 