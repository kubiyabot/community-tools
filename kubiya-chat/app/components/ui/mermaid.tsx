"use client";

import { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

interface MermaidProps {
  chart: string;
  className?: string;
  onError?: (error: Error) => void;
  onRenderStart?: () => void;
  onRenderEnd?: () => void;
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
  }
});

export default function Mermaid({ chart, className = '', onError, onRenderStart, onRenderEnd }: MermaidProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const renderDiagram = async () => {
      if (!containerRef.current) return;

      try {
        if (onRenderStart) onRenderStart();
        
        // First validate the syntax
        await mermaid.parse(chart);
        
        // If syntax is valid, render the diagram
        const { svg } = await mermaid.render('mermaid-svg', chart);
        if (containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
        
        if (onRenderEnd) onRenderEnd();
      } catch (error) {
        console.error('Error rendering mermaid diagram:', error);
        if (onError && error instanceof Error) {
          onError(error);
        }
        // Clear any partial renders on error
        if (containerRef.current) {
          containerRef.current.innerHTML = '';
        }
        if (onRenderEnd) onRenderEnd();
      }
    };

    renderDiagram();
  }, [chart, onError, onRenderStart, onRenderEnd]);

  return (
    <div 
      ref={containerRef} 
      className={className}
    />
  );
} 