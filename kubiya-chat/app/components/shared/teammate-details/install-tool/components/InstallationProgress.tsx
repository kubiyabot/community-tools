import * as React from 'react';
import { Loader2 } from 'lucide-react';
import { styles } from '../styles';

export function InstallationProgress() {
  return (
    <div className="flex flex-col items-center justify-center gap-4">
      <div className="relative">
        <div className="absolute inset-0 animate-ping rounded-full bg-purple-400/20" />
        <Loader2 className="h-8 w-8 text-purple-400 animate-spin relative" />
      </div>
      <div className="text-center">
        <p className={styles.text.primary + " text-sm font-medium"}>Installing Tools</p>
        <p className={styles.text.secondary + " text-xs mt-1"}>
          Setting up tools and configuring runners...
        </p>
      </div>
    </div>
  );
} 