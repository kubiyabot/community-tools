import { useEffect, useState } from 'react';

interface ActivityUpdate {
  type: string;
  data: any;
}

export function useActivityStream() {
  const [lastUpdate, setLastUpdate] = useState<ActivityUpdate | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const eventSource = new EventSource('/api/activity/stream');

    // Handle connection established
    eventSource.addEventListener('connected', () => {
      console.log('SSE Connected');
      setIsConnected(true);
    });

    // Handle activity updates
    eventSource.addEventListener('message', (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastUpdate(data);
      } catch (error) {
        console.error('Failed to parse activity update:', error);
      }
    });

    // Handle errors
    eventSource.onerror = (error) => {
      console.error('EventSource failed:', error);
      setIsConnected(false);
      
      // Attempt to reconnect after a delay
      setTimeout(() => {
        eventSource.close();
        // The browser will automatically attempt to reconnect
      }, 1000);
    };

    return () => {
      eventSource.close();
      setIsConnected(false);
    };
  }, []);

  return { lastUpdate, isConnected };
} 