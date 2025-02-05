import * as React from 'react';
import { Code } from 'lucide-react';
import { Badge } from '@/app/components/ui/badge';
import { cn } from '@/lib/utils';
import type { Tool } from '../types';
import type { ExtendedSourceInfo } from './SourceGroup';

interface ToolCardProps {
  tool: Tool;
  source: ExtendedSourceInfo;
}

export function ToolCard({ tool, source }: ToolCardProps) {
  const paramCount = tool.args?.length || 0;
  const secretCount = tool.secrets?.length || 0;
  const envCount = Number(tool.env?.length) || 0;

  return (
    <div className="group relative bg-[#1E293B]/50 hover:bg-[#1E293B] rounded-lg border border-[#1E293B] hover:border-[#7C3AED]/50 transition-all duration-200 cursor-pointer overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-[#1E293B]/0 to-[#1E293B] opacity-0 group-hover:opacity-100 transition-opacity" />
      <div className="p-4 relative">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-md bg-[#2A3347] border border-[#2A3347] group-hover:border-[#7C3AED]/20 transition-colors">
              {tool.icon_url ? (
                <img src={tool.icon_url} alt={tool.name} className="h-5 w-5" />
              ) : (
                <Code className="h-5 w-5 text-[#7C3AED]" />
              )}
            </div>
            <div>
              <h4 className="text-sm font-medium text-white tracking-wide flex items-center gap-2">
                {tool.name}
                {tool.type && (
                  <Badge 
                    variant="outline" 
                    className={cn(
                      "text-xs font-medium tracking-wide",
                      tool.type === 'docker' 
                        ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                        : "bg-purple-500/10 text-purple-400 border-purple-500/20"
                    )}
                  >
                    {tool.type === 'docker' ? (
                      <div className="flex items-center gap-1">
                        <img 
                          src="https://cdn4.iconfinder.com/data/icons/logos-and-brands/512/97_Docker_logo_logos-512.png"
                          alt="Docker"
                          className="h-3 w-3 mr-1"
                        />
                        docker
                      </div>
                    ) : tool.type}
                  </Badge>
                )}
              </h4>
              <p className="text-xs text-[#94A3B8] mt-1 leading-relaxed">{tool.description}</p>
              
              {/* Tool Metadata */}
              <div className="flex items-center gap-3 mt-3">
                {paramCount > 0 && (
                  <div className="flex items-center gap-1.5 text-xs text-[#94A3B8]">
                    <span>{paramCount} params</span>
                  </div>
                )}

                {secretCount > 0 && (
                  <div className="flex items-center gap-1.5 text-xs text-[#94A3B8]">
                    <span>{secretCount} secrets</span>
                  </div>
                )}

                {envCount > 0 && (
                  <div className="flex items-center gap-1.5 text-xs text-[#94A3B8]">
                    <span>{envCount} env vars</span>
                  </div>
                )}

                {tool.image && (
                  <div className="flex items-center gap-1.5 text-xs text-[#94A3B8]">
                    <span>Docker</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 