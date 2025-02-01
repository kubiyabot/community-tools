'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { 
  Filter,
  Search,
  Clock,
  Users,
  Bot,
  Loader2,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { Input } from '@/app/components/ui/input';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { Card } from '@/app/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/app/components/ui/select';
import { ScrollArea } from '@/app/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/app/components/ui/alert';
import { cn } from '@/lib/utils';

interface Session {
  sessionId: string;
  user: string;
  category: string;
  startTime: string;
  endTime: string;
  teammate?: string;
  events: Array<{
    id: string;
    email: string;
    timestamp: string;
    category_type: string;
    category_name?: string;
    action_successful: boolean;
    extra?: {
      session_id?: string;
    };
  }>;
  success: boolean;
}

export default function SessionsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [searchTerm, setSearchTerm] = useState(searchParams.get('search') || '');
  const [timeRange, setTimeRange] = useState('24h');
  const [categoryFilter, setCategoryFilter] = useState(searchParams.get('category') || 'all');
  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') || 'all');
  const [userFilter, setUserFilter] = useState(searchParams.get('user') || 'all');

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const now = new Date();
        let startDate;
        switch (timeRange) {
          case '1h':
            startDate = new Date(now.getTime() - (60 * 60 * 1000));
            break;
          case '24h':
            startDate = new Date(now.getTime() - (24 * 60 * 60 * 1000));
            break;
          case '7d':
            startDate = new Date(now.getTime() - (7 * 24 * 60 * 60 * 1000));
            break;
          case '30d':
            startDate = new Date(now.getTime() - (30 * 24 * 60 * 60 * 1000));
            break;
          default:
            startDate = new Date(0);
        }

        const filter = {
          timestamp: {
            gte: startDate.toISOString(),
            lte: now.toISOString()
          }
        };

        const queryParams = new URLSearchParams({
          filter: JSON.stringify(filter),
          sort: JSON.stringify({ timestamp: -1 })
        });

        const response = await fetch(`/api/auditing/items?${queryParams}`);
        if (!response.ok) {
          throw new Error('Failed to fetch sessions data');
        }

        const data = await response.json();
        
        // Group events by session
        const sessionMap = new Map<string, Session>();
        data.forEach((event: Session['events'][0]) => {
          if (!event.extra?.session_id) return;
          
          if (!sessionMap.has(event.extra.session_id)) {
            // Find teammate from agent events
            const teammate = event.category_type === 'agents' ? event.category_name : undefined;
            
            sessionMap.set(event.extra.session_id, {
              sessionId: event.extra.session_id,
              user: event.email,
              category: event.category_type,
              startTime: event.timestamp,
              endTime: event.timestamp,
              teammate,
              events: [],
              success: false,
            });
          }
          
          const session = sessionMap.get(event.extra.session_id);
          if (session) {
            session.events.push(event);
            
            if (new Date(event.timestamp) < new Date(session.startTime)) {
              session.startTime = event.timestamp;
            }
            if (new Date(event.timestamp) > new Date(session.endTime)) {
              session.endTime = event.timestamp;
            }
            
            if (event.action_successful) {
              session.success = true;
            }
          }
        });

        setSessions(Array.from(sessionMap.values()));
      } catch (error) {
        console.error('Error fetching sessions:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSessions();
  }, [timeRange]);

  // Update URL with filters
  useEffect(() => {
    const params = new URLSearchParams();
    if (searchTerm) params.set('search', searchTerm);
    if (categoryFilter !== 'all') params.set('category', categoryFilter);
    if (statusFilter !== 'all') params.set('status', statusFilter);
    if (userFilter !== 'all') params.set('user', userFilter);
    
    const newUrl = `${window.location.pathname}${params.toString() ? '?' + params.toString() : ''}`;
    window.history.replaceState({}, '', newUrl);
  }, [searchTerm, categoryFilter, statusFilter, userFilter]);

  const filteredSessions = sessions.filter(session => {
    const matchesSearch = searchTerm === '' || 
      session.user.toLowerCase().includes(searchTerm.toLowerCase()) ||
      session.sessionId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      session.category.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCategory = categoryFilter === 'all' || 
      session.category.toLowerCase() === categoryFilter.toLowerCase();
    
    const matchesStatus = statusFilter === 'all' || 
      (statusFilter === 'success' && session.success) ||
      (statusFilter === 'failed' && !session.success);
    
    const matchesUser = userFilter === 'all' || 
      session.user === userFilter;
    
    return matchesSearch && matchesCategory && matchesStatus && matchesUser;
  });

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-50">Sessions</h1>
          <p className="text-slate-400">View and analyze all sessions</p>
        </div>
      </div>

      {/* Filters */}
      <Card className="p-4 bg-slate-800/50 border-slate-700/50">
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search by user, session ID, or category..."
                  value={searchTerm}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
                  className="w-full bg-slate-900 border-slate-700 text-slate-200 placeholder:text-slate-400 pl-10"
                />
              </div>
            </div>
            <Select value={timeRange} onValueChange={setTimeRange}>
              <SelectTrigger className="w-40 bg-slate-900 border-slate-700 text-slate-200">
                <Clock className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Time Range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1h">Last Hour</SelectItem>
                <SelectItem value="24h">Last 24 Hours</SelectItem>
                <SelectItem value="7d">Last 7 Days</SelectItem>
                <SelectItem value="30d">Last 30 Days</SelectItem>
              </SelectContent>
            </Select>
            <Button 
              variant="outline" 
              onClick={() => window.location.reload()}
              className="bg-slate-900 border-slate-700 text-slate-200 hover:bg-slate-800"
              disabled={isLoading}
            >
              <RefreshCw className={cn("h-4 w-4 mr-2", isLoading && "animate-spin")} />
              Refresh
            </Button>
          </div>
          <div className="flex items-center gap-4">
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-40 bg-slate-900 border-slate-700 text-slate-200">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="agents">Agents</SelectItem>
                <SelectItem value="webhooks">Webhooks</SelectItem>
                <SelectItem value="tools">Tools</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40 bg-slate-900 border-slate-700 text-slate-200">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="success">Success</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
            <Select value={userFilter} onValueChange={setUserFilter}>
              <SelectTrigger className="w-40 bg-slate-900 border-slate-700 text-slate-200">
                <Users className="h-4 w-4 mr-2" />
                <SelectValue placeholder="User" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Users</SelectItem>
                {Array.from(new Set(sessions.map(s => s.user))).map(user => (
                  <SelectItem key={user} value={user}>{user}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </Card>

      {/* Sessions List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
            <p className="text-slate-400">Loading sessions...</p>
          </div>
        </div>
      ) : filteredSessions.length === 0 ? (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No sessions found for the selected filters.
          </AlertDescription>
        </Alert>
      ) : (
        <ScrollArea className="h-[calc(100vh-300px)]">
          <div className="space-y-4">
            {filteredSessions.map((session) => (
              <div
                key={session.sessionId}
                className="p-4 bg-slate-800/80 border border-slate-700/50 rounded-lg hover:bg-slate-800 transition-all cursor-pointer"
                onClick={() => router.push(`/sessions/${session.sessionId}`)}
              >
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-slate-200">{session.user}</span>
                      {session.teammate && (
                        <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/30">
                          {session.teammate}
                        </Badge>
                      )}
                      <Badge variant="outline" className="bg-indigo-500/10 text-indigo-400 border-indigo-500/30">
                        {session.category}
                      </Badge>
                      <Badge variant="outline" className={cn(
                        session.success 
                          ? "bg-green-500/10 text-green-400 border-green-500/30"
                          : "bg-red-500/10 text-red-400 border-red-500/30"
                      )}>
                        {session.success ? 'Success' : 'Failed'}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-slate-400">
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        {new Date(session.startTime).toLocaleString()}
                      </div>
                      <div className="flex items-center gap-1">
                        <Bot className="h-4 w-4" />
                        {session.events.length} events
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      )}
    </div>
  );
} 