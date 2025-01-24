"use client";

import { memo } from 'react';
import { ThreadMessage, ThreadAssistantContentPart, TextContentPart, ToolCallContentPart } from '@assistant-ui/react';
import { Bot, AlertTriangle, Copy, Check, Terminal, Loader2, ChevronDown, Code } from 'lucide-react';
import { MarkdownText } from './MarkdownText';
import { useTeammateContext } from "../../MyRuntimeProvider";
import { useState, useEffect, useCallback } from 'react';
import { toast } from '@/app/components/use-toast';

interface ToolCall {
  type: 'tool_init' | 'tool_output';
  id: string;
  name?: string;
  arguments?: Record<string, unknown>;
  message?: string;
  timestamp?: string;
  tool_init?: boolean;
  tool_description?: string;
  status?: string;
}

export interface AssistantMessageProps {
  message: ThreadMessage & { 
    role: 'assistant' | 'system';
    tool_calls?: ToolCall[];
  };
  isSystem?: boolean;
  isTool?: boolean;
  sourceMetadata?: {
    sourceId: string;
    metadata: {
      tools?: Array<{
        name: string;
        description: string;
        type?: string;
        icon_url?: string;
      }>;
    };
  };
}

function isTextContent(content: ThreadAssistantContentPart): content is TextContentPart {
  return content.type === 'text';
}

function isToolCallContent(content: ThreadAssistantContentPart): content is ToolCallContentPart<Record<string | number, unknown>, unknown> {
  return content.type === 'tool-call';
}

const CopyButton = ({ content }: { content: string }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      toast({
        description: "Copied to clipboard",
        duration: 2000,
      });
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
      toast({
        variant: "destructive",
        description: "Failed to copy to clipboard",
      });
    }
  }, [content]);

  return (
    <button
      onClick={handleCopy}
      className="opacity-0 group-hover:opacity-100 transition-opacity absolute right-2 top-2 p-1.5 rounded-md bg-[#2D3B4E] hover:bg-[#3D4B5E] text-[#94A3B8] z-10"
      title="Copy to clipboard"
    >
      {copied ? (
        <Check className="h-4 w-4 text-green-400" />
      ) : (
        <Copy className="h-4 w-4" />
      )}
    </button>
  );
};

const AssistantMessageComponent = ({ message, isSystem, isTool, sourceMetadata }: AssistantMessageProps) => {
  const { teammates, selectedTeammate } = useTeammateContext();
  const [isStreaming, setIsStreaming] = useState(false);
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({});
  const [jsonView, setJsonView] = useState<Record<string, boolean>>({});
  const textContent = message.content.find(isTextContent);
  const toolContent = message.content.find(isToolCallContent);
  const messageText = textContent && isTextContent(textContent) ? textContent.text : '';
  const isSystemMessage = message.role === 'system';
  const hasToolCalls = 'tool_calls' in message && Array.isArray(message.tool_calls) && message.tool_calls?.length > 0;

  const currentTeammate = teammates.find(t => t.uuid === selectedTeammate);

  const [copiedStates, setCopiedStates] = useState<Record<string, boolean>>({});

  const handleCopy = async (content: string, type: string, toolId: string) => {
    try {
      await navigator.clipboard.writeText(content);
      // Set copied state for this specific button
      setCopiedStates(prev => ({
        ...prev,
        [`${toolId}-${type}`]: true
      }));
      toast({
        description: `${type} copied to clipboard`,
        duration: 2000,
      });
      // Reset after 2 seconds
      setTimeout(() => {
        setCopiedStates(prev => ({
          ...prev,
          [`${toolId}-${type}`]: false
        }));
      }, 2000);
    } catch (error) {
      console.error(`Failed to copy ${type}:`, error);
      toast({
        variant: "destructive",
        description: `Failed to copy ${type}`,
        duration: 2000,
      });
    }
  };

  const toggleToolExpansion = (toolId: string) => {
    setExpandedTools(prev => ({
      ...prev,
      [toolId]: !prev[toolId]
    }));
  };

  const toggleJsonView = (toolId: string) => {
    setJsonView(prev => ({
      ...prev,
      [toolId]: !prev[toolId]
    }));
  };

  // Get tool icon based on name
  const getToolIcon = (toolName: string) => {
    const name = toolName?.toLowerCase() || '';
    
    // Try to find the tool in source metadata
    const tool = sourceMetadata?.metadata?.tools?.find(
      t => t.name.toLowerCase() === name || name.includes(t.name.toLowerCase())
    );

    if (tool?.icon_url) {
      return (
        <div className="p-1 rounded bg-[#2A3347]">
          <img src={tool.icon_url} alt={name} className="h-4 w-4" />
        </div>
      );
    }

    // Default icon with purple background
    return (
      <div className="p-1 rounded bg-[#2A3347]">
        <Terminal className="h-4 w-4 text-purple-400" />
      </div>
    );
  };

  // Format arguments for better display
  const formatArguments = (args: Record<string, unknown>, toolId: string) => {
    if (jsonView[toolId]) {
      return (
        <pre className="bg-[#1A1F2E] p-2 rounded overflow-x-auto">
          <code className="text-slate-300/90">
            {JSON.stringify(args, null, 2)}
          </code>
        </pre>
      );
    }

    const formattedArgs = Object.entries(args).map(([key, value]) => {
      const formattedKey = key
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');

      let formattedValue = value;
      if (typeof value === 'boolean') {
        formattedValue = value ? '✓' : '✗';
      } else if (Array.isArray(value)) {
        formattedValue = value.join(', ');
      } else if (typeof value === 'object' && value !== null) {
        formattedValue = JSON.stringify(value, null, 2);
      }

      return { key: formattedKey, value: formattedValue };
    });

    return (
      <div className="grid gap-2">
        {formattedArgs.map(({ key, value }, index) => (
          <div key={index} className="flex items-start gap-2 bg-[#1A1F2E] p-2 rounded hover:bg-[#2D3B4E]/30 transition-colors">
            <span className="text-purple-400 font-medium min-w-[100px] flex items-center gap-1">
              <span>{key}:</span>
            </span>
            <span className="text-[#E2E8F0] flex-1">
              {typeof value === 'string' && value.includes('\n') ? (
                <pre className="whitespace-pre-wrap"><code>{value}</code></pre>
              ) : (
                value?.toString()
              )}
            </span>
          </div>
        ))}
      </div>
    );
  };

  useEffect(() => {
    // Set streaming if this is the last message and it's still being updated
    const timestamp = new Date(message.createdAt).getTime();
    const isRecent = Date.now() - timestamp < 1000;
    setIsStreaming(isRecent);

    const timer = setTimeout(() => setIsStreaming(false), 1000);
    return () => clearTimeout(timer);
  }, [message, messageText]);

  if (!messageText.trim() && !toolContent && !hasToolCalls) {
    return null;
  }

  const warnings = isSystemMessage 
    ? messageText.split(/(?=WARNING:|ERROR:)/)
        .map((msg: string) => msg.trim())
        .filter((msg: string) => msg.length > 0)
    : [];

  if (isSystemMessage && !warnings.length && messageText) {
    warnings.push(messageText);
  }

  return (
    <div className="flex items-start gap-3">
      {isSystemMessage ? (
        <div className="w-full bg-amber-950/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
            </div>
            <div className="text-sm font-medium text-amber-200">System Messages</div>
          </div>
          <div className="space-y-3">
            {warnings.map((warning: string, index: number) => (
              <div key={index} className="flex items-start gap-2 text-sm text-amber-100 bg-amber-950/30 p-3 rounded group relative">
                <span className="mt-1 text-amber-400">•</span>
                <span className="flex-1"><MarkdownText content={warning} /></span>
                <CopyButton content={warning} />
              </div>
            ))}
          </div>
        </div>
      ) : (
        <>
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#2D3B4E] flex items-center justify-center relative">
            {currentTeammate?.avatar_url ? (
              <img 
                src={currentTeammate.avatar_url} 
                alt={currentTeammate.name || 'Assistant'} 
                className="w-full h-full rounded-full object-cover"
              />
            ) : (
              <Bot className="h-4 w-4 text-[#7C3AED]" />
            )}
            {isStreaming && (
              <span className="absolute -bottom-1 -right-1 h-2 w-2">
                <span className="absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75 animate-ping"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
              </span>
            )}
          </div>
          <div className="flex-1 space-y-1.5">
            <div className="flex items-center gap-2">
              <div className="text-sm font-medium text-white">
                {currentTeammate?.name || 'Assistant'}
              </div>
            </div>
            <div className="text-sm text-[#E2E8F0] prose prose-invert prose-sm max-w-none">
              {messageText && (
                <div className="group relative bg-[#1A1F2E]/50 rounded-lg p-3">
                  <div className="flex items-start">
                    <div className="flex-1">
                      <MarkdownText content={messageText} isStreaming={isStreaming} />
                    </div>
                  </div>
                  <CopyButton content={messageText} />
                </div>
              )}
              {(toolContent || hasToolCalls) && (
                <div className="mt-3 space-y-3">
                  {toolContent && isToolCallContent(toolContent) && (
                    <div className="bg-[#1E293B] rounded-lg border border-[#2D3B4E] overflow-hidden group relative">
                      <div className="px-4 py-2 bg-[#2D3B4E] border-b border-[#3D4B5E] flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Terminal className="h-4 w-4 text-purple-400" />
                          <p className="text-xs font-medium text-[#94A3B8]">Tool Call: {toolContent.toolName}</p>
                        </div>
                      </div>
                      <div className="relative group">
                        <pre className="p-4 text-xs overflow-x-auto">
                          <code className="text-[#E2E8F0]">
                            {JSON.stringify(toolContent.args, null, 2)}
                          </code>
                        </pre>
                        <CopyButton content={JSON.stringify(toolContent.args, null, 2)} />
                      </div>
                    </div>
                  )}
                  {hasToolCalls && message.tool_calls && message.tool_calls.map((tool: ToolCall, index: number) => (
                    <div key={`${tool.id}-${index}`} className="bg-[#1E293B] rounded-lg border border-[#2D3B4E] overflow-hidden group relative hover:border-purple-500/30 transition-colors">
                      <div 
                        className="px-4 py-3 bg-[#2D3B4E] border-b border-[#3D4B5E] flex items-center justify-between cursor-pointer hover:bg-[#3D4B5E] transition-colors"
                        onClick={() => toggleToolExpansion(tool.id)}
                      >
                        <div className="flex items-center gap-3">
                          {getToolIcon(tool.name || '')}
                          <div>
                            <p className="text-sm font-medium text-white mb-0.5">
                              {tool.name}
                            </p>
                            <div className="flex items-center gap-2 text-xs text-slate-400">
                              {tool.status === 'running' && (
                                <div className="flex items-center gap-1.5 text-purple-400">
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                  <span>Running</span>
                                </div>
                              )}
                              {tool.status === 'complete' && (
                                <div className="flex items-center gap-1.5 text-green-400">
                                  <Check className="h-3 w-3" />
                                  <span>Complete</span>
                                </div>
                              )}
                              <span>•</span>
                              <span>{new Date(tool.timestamp || '').toLocaleTimeString()}</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {!expandedTools[tool.id] && tool.message && (
                            <div className="text-xs text-slate-400">
                              {tool.message.length > 100 ? `${tool.message.slice(0, 100)}...` : tool.message}
                            </div>
                          )}
                          <ChevronDown 
                            className={`h-4 w-4 text-[#94A3B8] transition-transform ${expandedTools[tool.id] ? 'rotate-180' : ''}`} 
                          />
                        </div>
                      </div>
                      <div 
                        className={`transition-all duration-300 ease-in-out ${
                          expandedTools[tool.id] ? 'max-h-[800px] opacity-100' : 'max-h-0 opacity-0'
                        } overflow-hidden`}
                      >
                        <div className="relative group p-4 space-y-3">
                          {/* Arguments Section */}
                          {tool.arguments && Object.keys(tool.arguments).length > 0 && (
                            <div className="bg-[#2A3347] rounded-lg p-3 group/args relative">
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                  <p className="text-xs font-medium text-slate-400">Arguments</p>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      toggleJsonView(tool.id);
                                    }}
                                    className="p-1 rounded bg-[#1A1F2E] hover:bg-[#2D3B4E] transition-colors text-xs text-slate-400 flex items-center gap-1"
                                    title={jsonView[tool.id] ? "Switch to formatted view" : "Switch to JSON view"}
                                  >
                                    {jsonView[tool.id] ? (
                                      <>
                                        <Terminal className="h-3 w-3" />
                                        <span>Raw</span>
                                      </>
                                    ) : (
                                      <>
                                        <Code className="h-3 w-3" />
                                        <span>JSON</span>
                                      </>
                                    )}
                                  </button>
                                </div>
                                <button
                                  onClick={async (e) => {
                                    e.stopPropagation();
                                    const content = JSON.stringify(tool.arguments, null, 2);
                                    await handleCopy(content, 'Arguments', tool.id);
                                  }}
                                  className="opacity-0 group-hover/args:opacity-100 transition-opacity p-1.5 rounded-md bg-[#1A1F2E] hover:bg-[#2D3B4E] text-slate-400 flex items-center gap-1.5"
                                  title="Copy arguments"
                                >
                                  {copiedStates[`${tool.id}-Arguments`] ? (
                                    <>
                                      <Check className="h-3 w-3 text-green-400" />
                                      <span className="text-xs text-green-400">Copied!</span>
                                    </>
                                  ) : (
                                    <>
                                      <Copy className="h-3 w-3" />
                                      <span className="text-xs">Copy</span>
                                    </>
                                  )}
                                </button>
                              </div>
                              {formatArguments(tool.arguments, tool.id)}
                            </div>
                          )}

                          {/* Output Section */}
                          {(tool.message || tool.status === 'running') && (
                            <div className="bg-[#2A3347] rounded-lg p-3 group/output relative">
                              <div className="flex items-center justify-between mb-2">
                                <p className="text-xs font-medium text-slate-400">Output</p>
                                {tool.message && (
                                  <button
                                    onClick={async (e) => {
                                      e.stopPropagation();
                                      const cleanOutput = tool.message
                                        ?.replace(/🔧 Executing: .*?\n/g, '')
                                        .replace(/✅ Command executed successfully.*$/m, '')
                                        .replace(/❌ Command failed:?.*$/m, '')
                                        .replace(/^\s+|\s+$/g, '');
                                      await handleCopy(cleanOutput || '', 'Output', tool.id);
                                    }}
                                    className="opacity-0 group-hover/output:opacity-100 transition-opacity p-1.5 rounded-md bg-[#1A1F2E] hover:bg-[#2D3B4E] text-slate-400 flex items-center gap-1.5"
                                    title="Copy output"
                                  >
                                    {copiedStates[`${tool.id}-Output`] ? (
                                      <>
                                        <Check className="h-3 w-3 text-green-400" />
                                        <span className="text-xs text-green-400">Copied!</span>
                                      </>
                                    ) : (
                                      <>
                                        <Copy className="h-3 w-3" />
                                        <span className="text-xs">Copy</span>
                                      </>
                                    )}
                                  </button>
                                )}
                              </div>
                              <div className="relative">
                                <div className="max-h-[400px] overflow-y-auto rounded-md bg-[#1A1F2E] p-3">
                                  <pre className="text-sm text-slate-300/90 whitespace-pre-wrap font-mono">
                                    <code>
                                      {!tool.message && tool.status === 'running' ? (
                                        <div className="flex items-center gap-2 text-slate-400/70 animate-pulse">
                                          <Loader2 className="h-3 w-3 animate-spin" />
                                          <span>Waiting for output...</span>
                                        </div>
                                      ) : (
                                        (() => {
                                          // Clean up the output text
                                          const cleanOutput = tool.message
                                            ?.replace(/🔧 Executing: .*?\n/g, '')    // Remove all "Executing:" lines
                                            .replace(/✅ Command executed successfully.*$/m, '')  // Remove success message
                                            .replace(/❌ Command failed:?.*$/m, '')   // Remove error prefix
                                            .replace(/^\s+|\s+$/g, '');              // Trim whitespace

                                          if (!cleanOutput) return null;

                                          // Split into lines and process
                                          const lines = cleanOutput.split('\n');
                                          
                                          // Find header line (usually contains NAME, NAMESPACE, etc.)
                                          const headerIndex = lines.findIndex(line => 
                                            line.includes('NAME') || 
                                            line.includes('NAMESPACE') || 
                                            line.includes('STATUS')
                                          );

                                          if (headerIndex === -1) {
                                            // If no table format detected, return as plain text
                                            return (
                                              <div className="space-y-1">
                                                {lines.map((line, i) => (
                                                  <div 
                                                    key={i}
                                                    className={`
                                                      ${tool.status === 'running' && i === lines.length - 1 ? 'border-l-2 border-l-purple-500/50 pl-2' : ''}
                                                    `}
                                                  >
                                                    {line}
                                                  </div>
                                                ))}
                                              </div>
                                            );
                                          }

                                          // Process as table
                                          const header = lines[headerIndex];
                                          const rows = lines.slice(headerIndex + 1);

                                          return (
                                            <div className="space-y-1">
                                              {/* Header */}
                                              <div className="text-purple-400/90 font-medium pb-1 mb-1 border-b border-[#2D3B4E]/30">
                                                {header}
                                              </div>
                                              {/* Rows */}
                                              {rows.map((row, i) => (
                                                <div
                                                  key={i}
                                                  className={`
                                                    py-0.5
                                                    ${i % 2 === 0 ? 'bg-[#1A1F2E]' : 'bg-[#1E2433]/50'}
                                                    hover:bg-[#2D3B4E]/30
                                                    transition-colors duration-150
                                                    ${tool.status === 'running' && i === rows.length - 1 ? 'border-l-2 border-l-purple-500/50 pl-2' : 'pl-2.5'}
                                                    ${row.toLowerCase().includes('error') ? 'text-red-400/90' : ''}
                                                  `}
                                                >
                                                  {row}
                                                </div>
                                              ))}
                                            </div>
                                          );
                                        })()
                                      )}
                                    </code>
                                  </pre>
                                </div>
                                {tool.message && tool.message.length > 400 && !expandedTools[tool.id] && (
                                  <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-[#2A3347] to-transparent pointer-events-none" />
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export const AssistantMessage = memo(AssistantMessageComponent); 