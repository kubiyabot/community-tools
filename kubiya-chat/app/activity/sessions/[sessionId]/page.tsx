'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { SessionDetails } from '../../../components/activity';
import { Loader2 } from 'lucide-react';
import { use } from 'react';

interface PageProps {
  params: Promise<{
    sessionId: string;
  }>;
}

interface ActivityEvent {
  id: string;
  org: string;
  email: string;
  version: number;
  category_type: string;
  category_name: string;
  resource_type: string;
  resource_text: string;
  action_type: string;
  action_successful: boolean;
  timestamp: string;
  extra: {
    is_user_message?: boolean;
    session_id?: string;
    tool_name?: string;
    tool_args?: any;
    tool_execution_status?: string;
    teammate_id?: string;
    teammate_name?: string;
  };
  scope: string;
}

interface SessionData {
  sessionId: string;
  events: ActivityEvent[];
  teammate?: string;
}

export default function SessionPage({ params }: PageProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [sessionData, setSessionData] = useState<SessionData | null>(null);
  const eventId = searchParams.get('event');
  const resolvedParams = use(params);

  useEffect(() => {
    const fetchSessionData = async () => {
      try {
        const filter = {
          'extra.session_id': resolvedParams.sessionId
        };

        const queryParams = new URLSearchParams({
          filter: JSON.stringify(filter),
          sort: JSON.stringify({ timestamp: 1 })
        });

        const response = await fetch(`/api/auditing/items?${queryParams}`);
        if (!response.ok) {
          throw new Error('Failed to fetch session data');
        }

        const events = await response.json();
        if (events && events.length > 0) {
          // Find teammate from agent events
          const agentEvent = events.find((event: ActivityEvent) => 
            event.category_type === 'agents' && event.category_name
          );
          
          setSessionData({
            sessionId: resolvedParams.sessionId,
            events,
            teammate: agentEvent?.category_name
          });
        } else {
          // Handle session not found
          router.push('/activity');
        }
      } catch (error) {
        console.error('Error fetching session data:', error);
        router.push('/activity');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSessionData();
  }, [resolvedParams.sessionId, router]);

  if (isLoading || !sessionData) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-900">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
          <p className="text-slate-400">Loading session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-slate-900">
      <SessionDetails
        sessionId={sessionData.sessionId}
        events={sessionData.events}
        teammate={sessionData.teammate}
        onBack={() => router.push('/sessions')}
        initialEventId={eventId}
      />
    </div>
  );
} 