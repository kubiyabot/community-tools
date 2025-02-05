"use client";

import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

interface MermaidProps {
  chart: string;
  className?: string;
  onError?: (error: Error) => void;
  onRenderStart?: () => void;
  onRenderEnd?: () => void;
  timeoutMs?: number;
}

mermaid.initialize({
  startOnLoad: true,
  theme: 'dark',
  securityLevel: 'loose',
  themeVariables: {
    darkMode: true,
    background: '#1E293B',
    primaryColor: '#7C3AED',
    primaryTextColor: '#FFFFFF',
    primaryBorderColor: '#2A3347',
    lineColor: '#94A3B8',
    secondaryColor: '#4B5563',
    tertiaryColor: '#374151'
  },
  maxTextSize: 50000,
  fontFamily: 'monospace'
});

export default function Mermaid({ 
  chart, 
  className = '', 
  onError, 
  onRenderStart, 
  onRenderEnd,
  timeoutMs = 5000
}: MermaidProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const renderDiagram = async () => {
      if (!containerRef.current || !chart.trim()) return;

      setRenderError(null);
      setIsLoading(true);

      try {
        if (onRenderStart) onRenderStart();

        // Set a timeout to prevent infinite rendering
        const timeoutPromise = new Promise<never>((_, reject) => {
          timeoutRef.current = setTimeout(() => {
            reject(new Error('Diagram rendering timed out'));
          }, timeoutMs);
        });

        // Try to render with a timeout
        await Promise.race([
          (async () => {
            // Basic validation before attempting to render
            if (chart.length > 50000) {
              throw new Error('Diagram is too large to render safely');
            }

            // First validate the syntax
            await mermaid.parse(chart);
            
            // If syntax is valid, render the diagram
            const { svg } = await mermaid.render('mermaid-svg-' + Math.random(), chart);
            if (containerRef.current) {
              containerRef.current.innerHTML = svg;
            }
            return svg;
          })(),
          timeoutPromise
        ]);

        if (onRenderEnd) onRenderEnd();
      } catch (error) {
        console.error('Error rendering mermaid diagram:', error);
        const errorMessage = error instanceof Error ? error.message : 'Failed to render diagram';
        setRenderError(errorMessage);
        
        if (onError && error instanceof Error) {
          onError(error);
        }
        
        if (containerRef.current) {
          containerRef.current.innerHTML = '';
        }
        
        if (onRenderEnd) onRenderEnd();
      } finally {
        setIsLoading(false);
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
      }
    };

    renderDiagram();

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, [chart, onError, onRenderStart, onRenderEnd, timeoutMs]);

  if (renderError) {
    return (
      <div className={`${className} p-4 border border-red-500 rounded bg-red-50 dark:bg-red-900/20`}>
        <p className="text-sm text-red-600 dark:text-red-400">Failed to render diagram: {renderError}</p>
        <pre className="mt-2 text-xs text-gray-600 dark:text-gray-400 overflow-auto max-h-[200px]">
          {chart}
        </pre>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={`${className} p-4 border border-gray-200 dark:border-gray-700 rounded animate-pulse`}>
        <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded" />
      </div>
    );
  }

  return (
    <div 
      ref={containerRef} 
      className={className}
    />
  );
} 