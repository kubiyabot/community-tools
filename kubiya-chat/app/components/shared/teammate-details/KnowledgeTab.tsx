import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card';
import { ScrollArea } from '@/app/components/ui/scroll-area';
import { Skeleton } from '@/app/components/ui/skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/app/components/ui/dialog';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/app/components/ui/tooltip';
import { Badge } from '@/app/components/ui/badge';
import { Input } from '@/app/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/app/components/ui/tabs';
import { Avatar, AvatarImage, AvatarFallback } from '@/app/components/ui/avatar';
import { formatDistanceToNow } from 'date-fns';
import { Book, Calendar, Clock, Info, FileText, Tag, Search, Brain, Users, Shield, Lock } from 'lucide-react';
import { MarkdownText } from '@/app/components/assistant-ui/MarkdownText';
import { useEntity } from '@/app/providers/EntityProvider';

interface KnowledgeEntry {
  uuid: string;
  name: string;
  description: string;
  content: string;
  created_at: string;
  updated_at: string;
  source: string;
  owner: string;
  groups: string[];
  supported_agents: string[];
  labels: string[];
}

interface KnowledgeTabProps {
  teammateId: string;
}

const sourceDisplayMap: Record<string, { name: string; icon: string }> = {
  'manual': { 
    name: 'Unstructured Plain Text (via API)',
    icon: '🤖'
  },
  'terraform': { 
    name: 'Infrastructure as Code',
    icon: '⚙️'
  },
  'confluence': { 
    name: 'Confluence',
    icon: 'https://cdn.worldvectorlogo.com/logos/confluence-1.svg'
  },
  'notion': { 
    name: 'Notion',
    icon: 'https://upload.wikimedia.org/wikipedia/commons/4/45/Notion_app_logo.png'
  },
  'docs': { 
    name: 'Documentation',
    icon: '📚'
  }
};

export function KnowledgeTab({ teammateId }: KnowledgeTabProps) {
  const [knowledge, setKnowledge] = useState<KnowledgeEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEntry, setSelectedEntry] = useState<KnowledgeEntry | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const { getEntityMetadata, isLoading: isEntityLoading } = useEntity();

  useEffect(() => {
    const fetchKnowledge = async () => {
      try {
        const response = await fetch(`/api/v1/knowledge?teammateId=${teammateId}`);
        if (!response.ok) throw new Error('Failed to fetch knowledge entries');
        const data = await response.json();
        setKnowledge(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchKnowledge();
  }, [teammateId]);

  const filteredKnowledge = knowledge.filter(entry => {
    const query = searchQuery.toLowerCase();
    return (
      entry.name.toLowerCase().includes(query) ||
      entry.description.toLowerCase().includes(query) ||
      entry.content.toLowerCase().includes(query) ||
      entry.labels?.some(label => label.toLowerCase().includes(query)) ||
      entry.groups?.some(group => group.toLowerCase().includes(query))
    );
  });

  const renderTeammateInfo = (userId: string) => {
    if (isEntityLoading) {
      return (
        <div className="flex items-center gap-2">
          <Skeleton className="h-8 w-8 rounded-full" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-3 w-16" />
          </div>
        </div>
      );
    }

    const metadata = getEntityMetadata(userId);
    if (!metadata) {
      return (
        <p className="text-sm font-medium text-slate-400">
          Not available
        </p>
      );
    }

    return (
      <div className="flex items-center gap-2">
        <Avatar className="h-8 w-8">
          {metadata.image ? (
            <AvatarImage src={metadata.image} alt={metadata.name} />
          ) : (
            <AvatarFallback className="bg-purple-500/10 text-purple-400">
              {metadata.name?.charAt(0)?.toUpperCase() || '?'}
            </AvatarFallback>
          )}
        </Avatar>
        <div>
          <p className="text-sm font-medium text-white">
            {metadata.name}
          </p>
          {metadata.create_at && (
            <p className="text-xs text-slate-400">
              Member since {new Date(metadata.create_at).toLocaleDateString()}
            </p>
          )}
        </div>
      </div>
    );
  };

  const renderGroupInfo = (groupId: string) => {
    if (isEntityLoading) {
      return (
        <div className="flex items-center gap-2">
          <Skeleton className="h-8 w-8 rounded-full" />
          <Skeleton className="h-4 w-24" />
        </div>
      );
    }

    const metadata = getEntityMetadata(groupId);
    if (!metadata) {
      return (
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Shield className="h-4 w-4" />
          <span>{groupId}</span>
        </div>
      );
    }

    return (
      <div className="flex items-center gap-2">
        <div className="h-8 w-8 rounded-full bg-purple-500/10 flex items-center justify-center">
          <Shield className="h-4 w-4 text-purple-400" />
        </div>
        <div>
          <p className="text-sm font-medium text-white">
            {metadata.name}
          </p>
          <p className="text-xs text-slate-400">
            {metadata.description || 'No description'}
          </p>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        {/* Header Skeleton */}
        <div className="bg-gradient-to-br from-[#1E293B] to-[#0F172A] rounded-xl overflow-hidden border border-[#2D3B4E] p-6">
          <div className="flex gap-6">
            <Skeleton className="h-12 w-12 rounded-xl" />
            <div className="flex-1 space-y-4">
              <div className="space-y-2">
                <Skeleton className="h-6 w-48" />
                <Skeleton className="h-4 w-96" />
              </div>
              <div className="flex gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <Skeleton key={i} className="h-8 w-32 rounded-full" />
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Search Skeleton */}
        <Skeleton className="h-10 w-full rounded-lg" />

        {/* Cards Skeleton */}
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="p-4 rounded-lg border border-slate-800 space-y-3">
              <div className="flex justify-between">
                <Skeleton className="h-6 w-48" />
                <Skeleton className="h-6 w-6 rounded-full" />
              </div>
              <Skeleton className="h-16 w-full" />
              <div className="flex gap-2">
                <Skeleton className="h-6 w-24" />
                <Skeleton className="h-6 w-24" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-center">
        <div className="rounded-lg bg-red-500/10 p-4 border border-red-500/20">
          <p className="text-red-500 font-medium">{error}</p>
          <p className="text-sm text-red-400 mt-1">Please try again later or contact support if the issue persists.</p>
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <ScrollArea className="h-[calc(100vh-12rem)]">
        <div className="grid gap-6 p-6">
          {/* Header Section */}
          <div className="bg-gradient-to-br from-[#1E293B] to-[#0F172A] rounded-xl overflow-hidden border border-[#2D3B4E]">
            <div className="relative p-6">
              {/* Background Pattern */}
              <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAxOGMzLjMxIDAgNiAyLjY5IDYgNnMtMi42OSA2LTYgNi02LTIuNjktNi02IDIuNjktNiA2LTZ6IiBzdHJva2U9IiMyRDNCNEUiIG9wYWNpdHk9Ii4yIi8+PC9nPjwvc3ZnPg==')] opacity-5" />
              
              <div className="relative flex items-start gap-6">
                {/* Icon Stack */}
                <div className="flex flex-col items-center space-y-2">
                  <div className="relative w-12 h-12">
                    <div className="absolute inset-0 bg-gradient-to-br from-[#7C3AED] to-[#4F46E5] opacity-20 rounded-xl blur-lg" />
                    <div className="relative w-full h-full rounded-xl bg-[#2A3347] border border-[#2D3B4E] flex items-center justify-center">
                      <Brain className="h-6 w-6 text-purple-400" />
                    </div>
                  </div>
                  <div className="h-12 w-px bg-gradient-to-b from-[#2D3B4E] to-transparent" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <h2 className="text-lg font-semibold text-white tracking-tight">Knowledge Base</h2>
                      <p className="text-sm text-[#94A3B8] leading-relaxed max-w-3xl">
                        Extend your teammate's capabilities with knowledge from various sources
                      </p>
                    </div>

                    <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/20">
                      {knowledge.length} entries
                    </Badge>
                  </div>

                  {/* Source Icons */}
                  <div className="flex items-center gap-4 mt-4">
                    {Object.entries(sourceDisplayMap).map(([key, { name, icon }]) => (
                      <Tooltip key={key}>
                        <TooltipTrigger>
                          <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-[#2A3347] border border-[#2D3B4E]">
                            {icon.startsWith('http') ? (
                              <img src={icon} alt={name} className="h-3.5 w-3.5" />
                            ) : (
                              <span className="text-base">{icon}</span>
                            )}
                            <span className="text-xs text-[#94A3B8]">{name}</span>
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p className="text-xs">{name}</p>
                        </TooltipContent>
                      </Tooltip>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Search Section */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              type="text"
              placeholder="Search knowledge by name, content, or labels..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-slate-800/50 border-slate-700 focus:border-purple-500/50 focus:ring-purple-500/20"
            />
          </div>

          {/* Knowledge Cards */}
          <div className="grid gap-4">
            {filteredKnowledge.map((entry) => (
              <Card
                key={entry.uuid}
                className="group cursor-pointer hover:bg-slate-800/50 transition-all duration-200 border-slate-800 hover:border-purple-500/30 relative overflow-hidden"
                onClick={() => setSelectedEntry(entry)}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-purple-500/0 via-purple-500/5 to-purple-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-lg text-slate-200 flex items-center gap-2 group-hover:text-purple-400 transition-colors">
                      {entry.name}
                      {entry.labels?.length > 0 && (
                        <div className="flex gap-1">
                          {entry.labels.map(label => (
                            <Badge key={label} variant="secondary" className="text-xs">
                              {label}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </CardTitle>
                    <Tooltip>
                      <TooltipTrigger>
                        <Info className="h-4 w-4 text-slate-400 group-hover:text-purple-400 transition-colors" />
                      </TooltipTrigger>
                      <TooltipContent side="left" className="max-w-sm">
                        <div className="space-y-2">
                          <p className="font-medium">Additional Details</p>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              <span>Created {formatDistanceToNow(new Date(entry.created_at))} ago</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              <span>Last updated {formatDistanceToNow(new Date(entry.updated_at))} ago</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Tag className="h-3 w-3" />
                              <span>{sourceDisplayMap[entry.source]?.name || entry.source}</span>
                            </div>
                          </div>
                        </div>
                      </TooltipContent>
                    </Tooltip>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-400 mb-3 group-hover:text-slate-300 transition-colors line-clamp-2">
                    {entry.description}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {entry.groups?.length > 0 && (
                      <Badge variant="outline" className="text-xs group-hover:border-purple-500/30 transition-colors">
                        {entry.groups.length} groups
                      </Badge>
                    )}
                    <Badge 
                      variant="outline" 
                      className={`text-xs transition-all flex items-center gap-1.5 ${
                        entry.source === 'manual' ? 'bg-blue-500/5 text-blue-400 border-blue-500/20 group-hover:bg-blue-500/10' :
                        entry.source === 'terraform' ? 'bg-purple-500/5 text-purple-400 border-purple-500/20 group-hover:bg-purple-500/10' :
                        'bg-green-500/5 text-green-400 border-green-500/20 group-hover:bg-green-500/10'
                      }`}
                    >
                      {sourceDisplayMap[entry.source]?.icon && (
                        sourceDisplayMap[entry.source].icon.startsWith('http') ? (
                          <img src={sourceDisplayMap[entry.source].icon} alt="" className="h-3.5 w-3.5" />
                        ) : (
                          <span>{sourceDisplayMap[entry.source].icon}</span>
                        )
                      )}
                      {sourceDisplayMap[entry.source]?.name || entry.source}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </ScrollArea>

      <Dialog open={!!selectedEntry} onOpenChange={() => setSelectedEntry(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto bg-[#0F172A] border-[#2D3B4E]">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-purple-400" />
                <span className="text-slate-200">{selectedEntry?.name}</span>
              </div>
              <div className="flex items-center gap-2">
                {selectedEntry?.labels?.map(label => (
                  <Badge key={label} variant="secondary" className="text-xs">
                    {label}
                  </Badge>
                ))}
              </div>
            </DialogTitle>
          </DialogHeader>

          <Tabs defaultValue="content" className="mt-4">
            <TabsList className="bg-slate-800/50 border-b border-slate-700">
              <TabsTrigger value="content" className="data-[state=active]:bg-slate-700/50">
                Content
              </TabsTrigger>
              <TabsTrigger value="access" className="data-[state=active]:bg-slate-700/50">
                Access Control
              </TabsTrigger>
            </TabsList>

            <TabsContent value="content" className="space-y-6 pt-4">
              <div className="text-sm text-slate-400">{selectedEntry?.description}</div>
              
              <div className="grid grid-cols-3 gap-4">
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <Calendar className="h-4 w-4 text-purple-400" />
                  <span>Created {selectedEntry && formatDistanceToNow(new Date(selectedEntry.created_at))} ago</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <Clock className="h-4 w-4 text-purple-400" />
                  <span>Updated {selectedEntry && formatDistanceToNow(new Date(selectedEntry.updated_at))} ago</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  {selectedEntry?.source && sourceDisplayMap[selectedEntry.source]?.icon && (
                    sourceDisplayMap[selectedEntry.source].icon.startsWith('http') ? (
                      <img src={sourceDisplayMap[selectedEntry.source].icon} alt="" className="h-4 w-4" />
                    ) : (
                      <span className="text-base">{sourceDisplayMap[selectedEntry.source].icon}</span>
                    )
                  )}
                  <span>{selectedEntry && (sourceDisplayMap[selectedEntry.source]?.name || selectedEntry.source)}</span>
                </div>
              </div>

              <div className="bg-slate-900/50 rounded-lg border border-slate-800/50">
                <div className="p-4">
                  <MarkdownText content={selectedEntry?.content || ''} />
                </div>
              </div>
            </TabsContent>

            <TabsContent value="access" className="space-y-6 pt-4">
              <div className="grid grid-cols-2 gap-6">
                {/* Owner Section */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-slate-200">
                    <Users className="h-4 w-4 text-purple-400" />
                    <span>Owner</span>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                    {selectedEntry?.owner && renderTeammateInfo(selectedEntry.owner)}
                  </div>
                </div>

                {/* Groups Section */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm font-medium text-slate-200">
                      <Shield className="h-4 w-4 text-purple-400" />
                      <span>Authorized Groups</span>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {selectedEntry?.groups?.length || 0} groups
                    </Badge>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700 space-y-4">
                    {selectedEntry?.groups?.length ? (
                      selectedEntry.groups.map(groupId => (
                        <div key={groupId} className="group">
                          {renderGroupInfo(groupId)}
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-slate-400">No groups assigned</p>
                    )}
                  </div>
                </div>
              </div>

              <div className="rounded-lg bg-purple-500/5 border border-purple-500/10 p-4">
                <div className="flex items-start gap-3">
                  <Lock className="h-5 w-5 text-purple-400 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-medium text-purple-400">Access Control</h4>
                    <p className="text-sm text-slate-400 mt-1">
                      This knowledge entry is accessible to the owner and members of the authorized groups.
                      Group members can view and utilize this knowledge through the teammate.
                    </p>
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>
    </TooltipProvider>
  );
} 