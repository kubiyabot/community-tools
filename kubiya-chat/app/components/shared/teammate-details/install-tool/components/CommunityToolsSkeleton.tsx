import * as React from 'react';

export function CommunityToolsSkeleton() {
  return (
    <div className="space-y-4">
      {[...Array(3)].map((_, i) => (
        <div key={i} className="animate-pulse">
          <div className="h-24 bg-gray-700/20 rounded-lg" />
        </div>
      ))}
    </div>
  );
} 