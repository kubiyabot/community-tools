import * as React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/app/components/ui/button';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/app/components/ui/hover-card';
import { Card, CardContent } from '@/app/components/ui/card';
import { styles } from '../styles';

interface ErrorMessageProps {
  message: string;
  onRetry: () => void;
  className?: string;
}

export function ErrorMessage({ message, onRetry, className }: ErrorMessageProps) {
  return (
    <Card className={`border-red-500/30 bg-red-500/10 ${className}`}>
      <CardContent className="p-4 flex items-start gap-3">
        <AlertCircle className="h-5 w-5 text-red-400 mt-0.5" />
        <div className="space-y-2 flex-1">
          <h4 className="text-sm font-medium text-red-400">Failed to load community tools</h4>
          <p className="text-sm text-red-400/80">{message}</p>
          <div className="flex items-center gap-3 mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={onRetry}
              className="h-8 bg-red-500/10 text-red-400 hover:text-red-300 hover:bg-red-500/20 border-red-500/20"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Try again
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
} 