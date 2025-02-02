import { useState, useCallback } from 'react';
import type { CommunityTool, ToolLoadingState } from '../types/tools';

export const useToolLoader = () => {
  const [loadingStates, setLoadingStates] = useState<Record<string, ToolLoadingState>>({});
  const [loadedTools, setLoadedTools] = useState<Record<string, any>>({});

  const preloadTool = useCallback(async (tool: CommunityTool) => {
    if (loadingStates[tool.path]?.isLoading || loadedTools[tool.path]) return;

    setLoadingStates(prev => ({
      ...prev,
      [tool.path]: { isLoading: true, progress: 0 }
    }));

    try {
      const response = await fetch(`/api/sources/community/${tool.path}/metadata`);
      const reader = response.body?.getReader();
      const contentLength = +(response.headers.get('Content-Length') ?? 0);
      
      if (!reader) throw new Error('Failed to read response');

      let receivedLength = 0;
      const chunks: Uint8Array[] = [];

      while(true) {
        const {done, value} = await reader.read();
        if (done) break;
        
        chunks.push(value);
        receivedLength += value.length;

        setLoadingStates(prev => ({
          ...prev,
          [tool.path]: {
            isLoading: true,
            progress: (receivedLength / contentLength) * 100
          }
        }));
      }

      const allChunks = new Uint8Array(chunks.reduce((acc, chunk) => acc + chunk.length, 0));
      let position = 0;
      chunks.forEach(chunk => {
        allChunks.set(chunk, position);
        position += chunk.length;
      });

      const data = JSON.parse(new TextDecoder().decode(allChunks));
      setLoadedTools(prev => ({ ...prev, [tool.path]: data }));
      
      setLoadingStates(prev => ({
        ...prev,
        [tool.path]: { isLoading: false, progress: 100 }
      }));
    } catch (error) {
      console.error(`Failed to preload ${tool.name}:`, error);
      setLoadingStates(prev => ({
        ...prev,
        [tool.path]: { 
          isLoading: false, 
          progress: 0,
          error: error instanceof Error ? error.message : 'Failed to load tool'
        }
      }));
    }
  }, []);

  return {
    preloadTool,
    loadingStates,
    loadedTools,
    setLoadedTools
  };
}; 