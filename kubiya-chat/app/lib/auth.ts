import { toast } from '../components/ui/use-toast';

export async function handleUnauthorizedResponse(response: Response) {
  // Check if response is unauthorized by status
  if (response.status === 401) {
    return handleLogout('Session expired. Please log in again.');
  }

  // Only try to parse JSON if the response is not ok
  if (!response.ok) {
    try {
      const data = await response.json();
      if (data.shouldLogout) {
        return handleLogout(data.details || 'Please log in again to continue.');
      }
    } catch (error) {
      console.error('Error parsing response:', error);
    }
  }
  return false;
}

export function handleLogout(message?: string) {
  if (message) {
    toast({
      title: "Session Expired",
      description: message,
      variant: "destructive",
    });
  }
  
  // Get the current URL to use as returnTo after logout
  const returnTo = encodeURIComponent(window.location.origin);
  
  // Redirect to Auth0 logout endpoint
  window.location.href = `/api/auth/logout?returnTo=${returnTo}`;
  return true;
} 