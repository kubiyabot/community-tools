import { makeAssistantToolUI, ToolCallContentPart } from "@assistant-ui/react";
import { Terminal, Code, CheckCircle2, AlertCircle, ChevronDown, ChevronUp, Loader2, Copy } from 'lucide-react';
import { useState, useEffect, useRef, useMemo } from 'react';
import { cn } from "@/lib/utils";
import { toolRegistry, getToolMetadata } from './ToolRegistry';

interface ToolArgs extends Record<string, unknown> {
  command?: string;
  arguments?: Record<string, any>;
  message?: string;
  status?: 'initializing' | 'running' | 'success' | 'error';
  output?: string;
  id?: string;
  name?: string;
  type?: string;
  tool_name?: string;
  tool_init?: boolean;
  tool_description?: string;
}

interface ToolMetadata {
  icon?: React.ComponentType<any> | string;
  customComponent?: React.ComponentType<any>;
  description?: string;
}

const toolContainerStyles = "bg-[#1E293B] rounded-lg border border-[#2D3B4E] overflow-hidden mb-3 max-w-[calc(100vw-4rem)] w-full";
const toolHeaderStyles = "px-4 py-3 bg-[#2D3B4E] border-b border-[#3D4B5E] flex items-center gap-3";
const toolIconStyles = "h-4 w-4";
const toolContentStyles = "p-4";

const formatOutput = (output: string) => {
  // Remove emojis from the start of the line
  output = output.replace(/^[\u{1F300}-\u{1F9FF}]/gu, '').trim();

  // Handle tool initialization message first
  if (output.includes('Tool:') && output.includes('Arguments:')) {
    try {
      const [_, toolName, argsStr] = output.match(/Tool: (\w+)\nArguments: (.+)/) || [];
      const args = JSON.parse(argsStr);
      return `Executing ${toolName}:\n${JSON.stringify(args, null, 2)}`;
    } catch {
      return output;
    }
  }

  // Handle table-like output (any command that outputs in columns)
  const lines = output.split('\n')
    .map(line => line.trim())
    .filter(Boolean);

  // Detect if output looks like a table (has consistent spacing or column headers)
  const hasTableFormat = lines.length > 1 && lines.every(line => 
    line.includes('\t') || 
    line.includes('|') || 
    /\s{2,}/.test(line) || // Has 2 or more spaces between "columns"
    line.match(/\S+\s+\S+/g)?.length === lines[0].match(/\S+\s+\S+/g)?.length // Consistent number of columns
  );

  if (hasTableFormat) {
    // Split each line into columns based on whitespace or delimiters
    const rows = lines.map(line => 
      line.split(/\s{2,}|\t|\|/)
        .map(cell => cell.trim())
        .filter(Boolean)
    );

    // Calculate max width for each column
    const columnWidths = rows.reduce((widths, row) => {
      row.forEach((cell, i) => {
        widths[i] = Math.max(widths[i] || 0, cell.length);
      });
      return widths;
    }, [] as number[]);

    // Format each row with consistent column widths
    return rows.map(row => 
      row.map((cell, i) => cell.padEnd(columnWidths[i] + 2)).join('')
    ).join('\n');
  }

  try {
    // Try to parse as JSON
    const parsed = JSON.parse(output);
    return JSON.stringify(parsed, null, 2);
  } catch {
    // Handle command success/failure indicators
    const successIndicator = '✅ Command executed successfully';
    if (output.includes(successIndicator)) {
      return output.replace(successIndicator, '\n' + successIndicator);
    }

    // Handle streaming output - don't wrap if it's still streaming
    if (output.endsWith('...') || 
        output.includes('Running') || 
        output.includes('Executing') ||
        output.includes('Initializing')) {
      return output;
    }

    // Wrap long lines for better readability
    return output.split('\n').map(line => {
      if (line.length > 120) {
        const words = line.split(' ');
        let currentLine = '';
        let result = '';
        
        words.forEach(word => {
          if ((currentLine + word).length > 120) {
            result += currentLine.trimEnd() + '\n';
            currentLine = '  ' + word + ' '; // Indent continued lines
          } else {
            currentLine += word + ' ';
          }
        });
        
        return result + currentLine.trimEnd();
      }
      return line;
    }).join('\n');
  }
};

const ToolHeader = ({ args, metadata }: { args: ToolArgs; metadata?: ToolMetadata }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const status = args.status || (args.tool_init ? 'initializing' : 'running');
  const toolName = args.tool_name || args.name;
  const toolInfo = getToolMetadata(toolName || '');
  const icon = metadata?.icon || toolInfo?.icon || Terminal;
  const IconComponent = typeof icon === 'string' ? 
    () => <img src={icon} alt={toolName} className="h-4 w-4 object-contain" /> 
    : icon;

  return (
    <div className={cn(toolHeaderStyles, "justify-between")}>
      <div className="flex items-center gap-3">
        <div className={cn(
          "p-1.5 rounded transition-colors",
          status === 'initializing' && "bg-blue-500/10",
          status === 'running' && "bg-purple-500/10",
          status === 'success' && "bg-green-500/10",
          status === 'error' && "bg-red-500/10"
        )}>
          <IconComponent className={cn(
            toolIconStyles,
            status === 'initializing' && "text-blue-400",
            status === 'running' && "text-purple-400",
            status === 'success' && "text-green-400",
            status === 'error' && "text-red-400"
          )} />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <p className="font-medium text-white">
              {toolInfo.name}
            </p>
            {args.id && (
              <code className="px-1.5 py-0.5 bg-[#1A1F2E] rounded text-xs text-slate-400 font-mono">
                {args.id}
              </code>
            )}
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            {args.tool_init ? (
              <p className="text-xs text-blue-400 animate-pulse flex items-center gap-1.5">
                <Loader2 className="h-3 w-3 animate-spin" />
                {args.tool_description || toolInfo.description}
              </p>
            ) : (
              <>
                <p className="text-xs text-slate-400">
                  {toolInfo.description}
                </p>
                {args.arguments?.command && (
                  <code className="text-xs text-purple-400 font-mono">
                    $ {args.arguments.command}
                  </code>
                )}
              </>
            )}
          </div>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {status === 'initializing' && (
          <div className="flex items-center gap-1.5 text-xs text-blue-400">
            <Loader2 className="h-3 w-3 animate-spin" />
            <span>Initializing</span>
          </div>
        )}
        {status === 'running' && (
          <div className="flex items-center gap-1.5 text-xs text-purple-400">
            <Loader2 className="h-3 w-3 animate-spin" />
            <span>Running</span>
          </div>
        )}
        {status === 'success' && (
          <div className="flex items-center gap-1.5 text-xs text-green-400">
            <CheckCircle2 className="h-3 w-3" />
            <span>Completed</span>
          </div>
        )}
        {status === 'error' && (
          <div className="flex items-center gap-1.5 text-xs text-red-400">
            <AlertCircle className="h-3 w-3" />
            <span>Failed</span>
          </div>
        )}
        <button 
          onClick={() => setIsExpanded(!isExpanded)}
          className="p-1 hover:bg-[#3D4B5E] rounded-md transition-colors"
        >
          {isExpanded ? (
            <ChevronUp className="h-4 w-4 text-slate-400" />
          ) : (
            <ChevronDown className="h-4 w-4 text-slate-400" />
          )}
        </button>
      </div>
    </div>
  );
};

const ToolContent = ({ args, isHistory = false }: { args: ToolArgs; isHistory?: boolean }) => {
  const [activeTab, setActiveTab] = useState<'args' | 'output'>('output');
  const [outputChunks, setOutputChunks] = useState<{id: string; text: string; timestamp: number}[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const outputRef = useRef<HTMLDivElement>(null);
  const currentToolRef = useRef<string | null>(null);
  const lastOutputRef = useRef<string>('');
  const hasOutput = args.output || args.message || outputChunks.length > 0;
  const lastChunksToShow = 5;

  useEffect(() => {
    // Show tool initialization immediately when tool changes
    if (args.id && args.id !== currentToolRef.current) {
      currentToolRef.current = args.id;
      lastOutputRef.current = '';
      setOutputChunks([]);

      // Show tool initialization with arguments
      if (args.tool_name && args.arguments) {
        const toolInfo = getToolMetadata(args.tool_name);
        const initMessage = {
          id: `init_${args.id}`,
          text: `${args.tool_description || toolInfo?.description || `Running ${args.tool_name}`}\n${JSON.stringify(args.arguments, null, 2)}`,
          timestamp: Date.now()
        };
        setOutputChunks([initMessage]);
      }
    }

    // Handle new output
    if (args.output && args.output !== lastOutputRef.current) {
      setOutputChunks(prev => {
        const lastChunk = prev[prev.length - 1];
        const formattedOutput = formatOutput(args.output || '');
        
        // If this is a continuation of the last chunk, update it
        if (lastChunk && formattedOutput.startsWith(lastChunk.text)) {
          return [
            ...prev.slice(0, -1),
            { id: lastChunk.id, text: formattedOutput, timestamp: Date.now() }
          ];
        }
        
        // Add as new chunk
        return [
          ...prev,
          { id: `output_${args.id}_${Date.now()}`, text: formattedOutput, timestamp: Date.now() }
        ];
      });
      
      lastOutputRef.current = args.output;
    }

    // Auto scroll to bottom if not expanded
    if (outputRef.current && !isExpanded) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [args.id, args.output, args.tool_name, args.arguments, args.tool_description, isExpanded]);

  // Filter and sort chunks for display
  const displayChunks = useMemo(() => {
    const filtered = outputChunks
      .filter(chunk => chunk.text.trim())
      .filter((chunk, index, self) => 
        index === self.findIndex(c => c.text === chunk.text)
      )
      .sort((a, b) => a.timestamp - b.timestamp);

    return isExpanded ? filtered : filtered.slice(-lastChunksToShow);
  }, [outputChunks, isExpanded, lastChunksToShow]);

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className={cn(toolContentStyles, isHistory && "p-2")}>
      {!isHistory && (
        <div className="flex items-center gap-2 mb-3 border-b border-[#2D3B4E]">
          <div
            onClick={() => setActiveTab('args')}
            className={cn(
              "px-3 py-1.5 text-sm font-medium transition-colors cursor-pointer",
              activeTab === 'args' 
                ? "text-purple-400 border-b-2 border-purple-400" 
                : "text-slate-400 hover:text-slate-300"
            )}
          >
            Parameters
          </div>
          <div
            onClick={() => setActiveTab('output')}
            className={cn(
              "px-3 py-1.5 text-sm font-medium transition-colors cursor-pointer",
              !hasOutput && "opacity-50",
              activeTab === 'output'
                ? "text-purple-400 border-b-2 border-purple-400"
                : "text-slate-400 hover:text-slate-300"
            )}
          >
            Output {outputChunks.length > 0 && `(${outputChunks.length})`}
          </div>
        </div>
      )}
      
      {activeTab === 'args' && args.arguments && !isHistory && (
        <div className="space-y-2 max-w-[calc(100vw-16rem)]">
          {Object.entries(args.arguments).map(([key, value]) => (
            <div key={key} className="group relative flex items-start gap-2 bg-[#1A1F2E] p-2 rounded-md">
              <span className="text-xs font-medium text-purple-400 min-w-[100px]">{key}:</span>
              <code className="text-xs text-slate-300 font-mono flex-1 whitespace-pre-wrap break-all">
                {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
              </code>
              <div 
                onClick={() => handleCopy(typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value))}
                className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 cursor-pointer"
              >
                <Copy className="h-4 w-4 text-slate-400 hover:text-slate-300" />
              </div>
            </div>
          ))}
        </div>
      )}
      
      {(activeTab === 'output' || isHistory) && (
        <div className="relative">
          <div 
            ref={outputRef}
            className={cn(
              "bg-[#1A1F2E] p-3 rounded-md overflow-y-auto relative group transition-all duration-200",
              !isExpanded && "max-h-[300px]",
              isExpanded && "max-h-[80vh]",
              args.status === 'running' && "border border-purple-500/20",
              args.status === 'success' && "border border-green-500/20",
              args.status === 'error' && "border border-red-500/20",
              args.tool_init && "border border-blue-500/20"
            )}
          >
            {!isExpanded && displayChunks.length > lastChunksToShow && (
              <div className="text-xs text-slate-400 mb-2 pb-2 border-b border-slate-700">
                Showing last {lastChunksToShow} of {displayChunks.length} lines...
              </div>
            )}
            <pre className={cn(
              "text-sm text-slate-300 font-mono whitespace-pre-wrap break-words max-w-[calc(100vw-20rem)]",
              isHistory && "text-xs opacity-80"
            )}>
              <code>
                {displayChunks.map((chunk, i) => {
                  const formattedText = formatOutput(chunk.text);
                  const isCommand = chunk.text.includes('Executing:');
                  const isSuccess = chunk.text.includes('✅');
                  const isStreaming = i === displayChunks.length - 1 && 
                    (args.status === 'running' || args.tool_init);
                  
                  return (
                    <div key={chunk.id} className={cn(
                      "block transition-opacity duration-200",
                      i === displayChunks.length - 1 && "animate-fadeIn",
                      isCommand && "text-purple-400 font-bold",
                      isSuccess && "text-green-400"
                    )}>
                      {formattedText}
                      {isStreaming && (
                        <span className="inline-block w-2 h-4 bg-purple-400 animate-pulse ml-1" />
                      )}
                      {i < displayChunks.length - 1 && '\n'}
                    </div>
                  );
                })}
              </code>
            </pre>
            {hasOutput && (
              <div className="absolute right-2 top-2 flex items-center gap-1 opacity-0 group-hover:opacity-100">
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="p-1.5 hover:bg-[#3D4B5E] rounded-md transition-colors"
                  title={isExpanded ? "Show less" : "Show more"}
                >
                  {isExpanded ? (
                    <ChevronUp className="h-4 w-4 text-slate-400" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-slate-400" />
                  )}
                </button>
                <button
                  onClick={() => handleCopy(displayChunks.map(c => c.text).join('\n'))}
                  className="p-1.5 hover:bg-[#3D4B5E] rounded-md transition-colors"
                  title="Copy output"
                >
                  <Copy className="h-4 w-4 text-slate-400" />
                </button>
              </div>
            )}
            {args.status === 'running' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5">
                <div className="max-w-[200px] mx-auto h-full bg-purple-500/20">
                  <div className="h-full bg-purple-500 animate-progress"></div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

type ToolStatus = { 
  readonly type: "running" | "complete" | "incomplete"; 
  readonly reason?: "error" | "cancelled" | "length" | "content-filter" | "other";
  readonly error?: unknown;
};

type ToolRenderProps = ToolCallContentPart<ToolArgs, { isHistory?: boolean }> & {
  readonly argsText: string;
  readonly status: ToolStatus;
};

export const GenericToolUI = makeAssistantToolUI<ToolArgs, { isHistory?: boolean }>({
  toolName: "*",
  render: (props) => {
    const { args, status } = props;
    const isHistory = (props as any).isHistory;
    
    // Get tool metadata
    const toolName = args.tool_name || args.name;
    const toolInfo = getToolMetadata(toolName || '');
    const metadata = {
      icon: toolInfo?.icon,
      description: toolInfo?.description,
      customComponent: toolInfo?.component,
    };
    
    if (metadata?.customComponent) {
      const CustomComponent = metadata.customComponent;
      return <CustomComponent args={args} status={status} isHistory={isHistory} />;
    }

    return (
      <div className={cn(
        toolContainerStyles,
        isHistory && "opacity-90 hover:opacity-100 transition-opacity"
      )}>
        <ToolHeader args={args} metadata={metadata} />
        <ToolContent args={args} isHistory={isHistory} />
      </div>
    );
  }
});