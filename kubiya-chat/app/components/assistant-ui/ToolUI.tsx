import { makeAssistantToolUI, ToolCallContentPart } from "@assistant-ui/react";
import { Terminal, Code, CheckCircle2, AlertCircle, ChevronDown, ChevronUp, Loader2, Copy } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import { cn } from "@/lib/utils";
import { toolRegistry } from './ToolRegistry';

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
  icon?: React.ComponentType<any>;
  customComponent?: React.ComponentType<any>;
  description?: string;
}

const toolContainerStyles = "bg-[#1E293B] rounded-lg border border-[#2D3B4E] overflow-hidden mb-3 max-w-[calc(100vw-4rem)]";
const toolHeaderStyles = "px-4 py-3 bg-[#2D3B4E] border-b border-[#3D4B5E] flex items-center gap-3";
const toolIconStyles = "h-4 w-4";
const toolContentStyles = "p-4";

const formatOutput = (output: string) => {
  try {
    const parsed = JSON.parse(output);
    return JSON.stringify(parsed, null, 2);
  } catch {
    // Format table-like output
    const lines = output.split('\n').map(line => line.trim()).filter(line => line.length > 0);
    if (lines.some(line => line.includes('|') || line.includes('\t'))) {
      // Handle table format
      return lines.map(line => {
        const cells = line.split(/\s{2,}|\t|\|/).filter(Boolean);
        return cells.join('  ');
      }).join('\n');
    }
    return lines.join('\n');
  }
};

const ToolHeader = ({ args, metadata }: { args: ToolArgs; metadata?: ToolMetadata }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const status = args.status || (args.tool_init ? 'initializing' : 'running');
  const toolName = args.tool_name || args.name;
  const toolInfo = toolRegistry[toolName || ''];
  const Icon = metadata?.icon || toolInfo?.icon || Terminal;

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
          <Icon className={cn(
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
              {toolInfo?.name || toolName || 'Tool Execution'}
            </p>
            {args.command && (
              <code className="px-1.5 py-0.5 bg-[#1A1F2E] rounded text-xs text-slate-300 font-mono">
                {args.command}
              </code>
            )}
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            {args.tool_init ? (
              <p className="text-xs text-blue-400 animate-pulse flex items-center gap-1.5">
                <Loader2 className="h-3 w-3 animate-spin" />
                {args.tool_description || 'Determining best tool for the task...'}
              </p>
            ) : (
              <>
                <p className="text-xs text-slate-400">
                  {metadata?.description || toolInfo?.description}
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
  const [outputChunks, setOutputChunks] = useState<string[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const outputRef = useRef<HTMLDivElement>(null);
  const hasOutput = args.output || args.message || outputChunks.length > 0;
  
  useEffect(() => {
    // Handle new output chunks
    if (args.output && !outputChunks.includes(args.output)) {
      setOutputChunks(prev => [...prev, args.output!]);
      // Auto scroll to bottom of output if not expanded
      if (outputRef.current && !isExpanded) {
        outputRef.current.scrollTop = outputRef.current.scrollHeight;
      }
    }

    // Handle tool initialization message
    if (args.tool_init && !outputChunks.length) {
      setOutputChunks(['Initializing tool...']);
    }

    // Handle tool message updates
    if (args.message && !outputChunks.includes(args.message)) {
      setOutputChunks(prev => [...prev, args.message!]);
    }
  }, [args.status, args.output, args.tool_init, args.message, isExpanded]);

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const outputContent = (
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
      <pre className={cn(
        "text-sm text-slate-300 font-mono whitespace-pre-wrap break-words",
        isHistory && "text-xs opacity-80"
      )}>
        <code>
          {outputChunks.map((chunk, i) => (
            <span key={i} className={cn(
              "block",
              i === outputChunks.length - 1 && "animate-fadeIn"
            )}>
              {formatOutput(chunk)}
              {i < outputChunks.length - 1 && '\n'}
            </span>
          ))}
          {(args.status === 'running' || args.tool_init) && (
            <span className="inline-block w-2 h-4 bg-purple-400 animate-pulse ml-1" />
          )}
        </code>
      </pre>
      {hasOutput && (
        <div className="absolute right-2 top-2 flex items-center gap-1 opacity-0 group-hover:opacity-100">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 hover:bg-[#3D4B5E] rounded-md transition-colors"
          >
            {isExpanded ? (
              <ChevronUp className="h-4 w-4 text-slate-400" />
            ) : (
              <ChevronDown className="h-4 w-4 text-slate-400" />
            )}
          </button>
          <button
            onClick={() => handleCopy(outputChunks.join('\n'))}
            className="p-1.5 hover:bg-[#3D4B5E] rounded-md transition-colors"
          >
            <Copy className="h-4 w-4 text-slate-400" />
          </button>
        </div>
      )}
    </div>
  );

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
        <div className="space-y-2">
          {Object.entries(args.arguments).map(([key, value]) => (
            <div key={key} className="group relative flex items-start gap-2 bg-[#1A1F2E] p-2 rounded-md">
              <span className="text-xs font-medium text-purple-400 min-w-[100px]">{key}:</span>
              <code className="text-xs text-slate-300 font-mono flex-1">
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
      
      {(activeTab === 'output' || isHistory) && outputContent}
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
  toolName: "*", // Matches any tool
  render: (props) => {
    const { args, status } = props;
    const isHistory = (props as any).isHistory;
    
    // Get tool metadata
    const toolName = args.tool_name || args.name;
    const toolInfo = toolRegistry[toolName || ''];
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
  },
});