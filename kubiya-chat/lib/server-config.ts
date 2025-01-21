interface ServerConfig {
  apiKey: string | null;
  apiUrl: string;
}

export function getServerConfig(): ServerConfig {
  return {
    apiKey: process.env.KUBIYA_API_KEY || null,
    apiUrl: process.env.NEXT_PUBLIC_API_URL || 'https://api.kubiya.ai',
  };
} 