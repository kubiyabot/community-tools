import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card';
import { ScrollArea } from '@/app/components/ui/scroll-area';
import { Skeleton } from '@/app/components/ui/skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/app/components/ui/dialog';
import { formatDate } from '@/app/lib/utils';

interface KnowledgeEntry {
  uuid: string;
  name: string;
  description: string;
  content: string;
  created_at: string;
  updated_at: string;
  source: string;
}

interface KnowledgeTabProps {
  teammateId: string;
}

export function KnowledgeTab({ teammateId }: KnowledgeTabProps) {
  const [knowledge, setKnowledge] = useState<KnowledgeEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEntry, setSelectedEntry] = useState<KnowledgeEntry | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  if (loading) {
    return (
      <div className="space-y-4 p-6">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-32 w-full" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-center text-red-500">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <>
      <ScrollArea className="h-[calc(100vh-12rem)]">
        <div className="grid gap-4 p-6">
          {knowledge.map((entry) => (
            <Card
              key={entry.uuid}
              className="cursor-pointer hover:bg-slate-800/50 transition-colors"
              onClick={() => setSelectedEntry(entry)}
            >
              <CardHeader>
                <CardTitle className="text-lg">{entry.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-400">{entry.description}</p>
                <div className="mt-2 flex gap-4 text-xs text-slate-500">
                  <span>Source: {entry.source}</span>
                  <span>Created: {formatDate(entry.created_at)}</span>
                  <span>Updated: {formatDate(entry.updated_at)}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </ScrollArea>

      <Dialog open={!!selectedEntry} onOpenChange={() => setSelectedEntry(null)}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedEntry?.name}</DialogTitle>
          </DialogHeader>
          <div className="mt-4">
            <p className="text-sm text-slate-400 mb-4">{selectedEntry?.description}</p>
            <div className="bg-slate-900 p-4 rounded-lg">
              <pre className="whitespace-pre-wrap text-sm">
                {selectedEntry?.content}
              </pre>
            </div>
            <div className="mt-4 flex gap-4 text-xs text-slate-500">
              <span>Source: {selectedEntry?.source}</span>
              <span>Created: {formatDate(selectedEntry?.created_at || '')}</span>
              <span>Updated: {formatDate(selectedEntry?.updated_at || '')}</span>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
} 