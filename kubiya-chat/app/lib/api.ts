import { handleUnauthorizedResponse } from './auth';

interface FetchOptions extends RequestInit {
  skipAuthCheck?: boolean;
}

export async function apiFetch(url: string, options: FetchOptions = {}) {
  try {
    const response = await fetch(url, options);
    
    // Skip auth check if specified
    if (options.skipAuthCheck) {
      return response;
    }

    // Clone the response before checking auth status
    const responseClone = response.clone();
    
    // Check for unauthorized response
    const isUnauthorized = await handleUnauthorizedResponse(responseClone);
    if (isUnauthorized) {
      throw new Error('Unauthorized');
    }

    return response;
  } catch (error) {
    // Re-throw the error to be handled by the caller
    throw error;
  }
}

// Helper function to handle API responses
export async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }));
    throw new Error(error.message || 'An error occurred');
  }
  return response.json();
} 