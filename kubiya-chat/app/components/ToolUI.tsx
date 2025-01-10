"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useAssistantToolUI } from "@assistant-ui/react";
import { AlertCircle, Terminal, Loader2 } from 'lucide-react';

// Shared styles for tool containers
const toolContainerStyles = "my-4 rounded-lg border bg-background shadow-sm";
const toolHeaderStyles = "flex items-center gap-3 border-b bg-muted/50 px-4 py-3";
const toolContentStyles = "p-4 text-sm bg-muted/30";
const toolIconStyles = "size-4 shrink-0";

// Define interfaces for tool arguments
interface BaseArgs extends Record<string, unknown> {
  message: string;
  id: string;
  type: string;
  session_id?: string;
}

interface SystemMessageArgs extends BaseArgs {
  type: 'system_message';
  content?: string;
}

interface ToolArgs extends BaseArgs {
  type: 'tool' | 'tool_output';
}

interface ParsedToolArgs {
  command?: string;
  namespace?: string;
  raw?: string;
  [key: string]: unknown;
}

// React components for each tool UI
const SystemMessageUI = ({ args }: { args: SystemMessageArgs }) => {
  const [mounted, setMounted] = useState(false);
  const message = args.message || args.content || 'System Message';

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className={toolContainerStyles}>
      <div className={toolHeaderStyles}>
        <AlertCircle className={`${toolIconStyles} text-primary`} />
        <div className="flex flex-1 items-center">
          <div>
            <p className="font-semibold text-foreground">System Message</p>
            <p className="text-xs text-muted-foreground">{message}</p>
            {args.id && (
              <p className="text-xs text-muted-foreground/70">ID: {args.id}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const ToolExecutionUI = ({ args }: { args: ToolArgs }) => {
  const [mounted, setMounted] = useState(false);
  const messageRef = useRef<string>('');
  const [toolArgs, setToolArgs] = useState<ParsedToolArgs>({});
  const [toolName, setToolName] = useState<string>('');

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    
    if (args.message) {
      console.log('ToolExecutionUI received message:', args.message);
      messageRef.current = args.message;
      
      try {
        const parts = messageRef.current.split('\n');
        const currentToolName = parts[0].replace('Tool:', '').trim();
        setToolName(currentToolName);

        const argsStr = parts.slice(1).join('\n').replace('Arguments:', '').trim();
        if (argsStr.startsWith('{') && argsStr.endsWith('}')) {
          const parsedArgs = JSON.parse(argsStr);
          setToolArgs(prev => ({ ...prev, ...parsedArgs }));
        } else {
          setToolArgs(prev => ({ ...prev, raw: argsStr }));
        }
      } catch (error) {
        console.error('Error parsing tool message:', error);
      }
    }
  }, [args.message, mounted]);

  if (!mounted) return null;

  return (
    <div className={toolContainerStyles}>
      <div className={toolHeaderStyles}>
        <div className="flex items-center gap-2">
          <Terminal className={`${toolIconStyles} text-primary`} />
          <Loader2 className={`${toolIconStyles} animate-spin text-primary`} />
        </div>
        <div className="flex flex-1 items-center justify-between">
          <div>
            <p className="font-semibold text-foreground">{toolName}</p>
            <p className="text-xs text-muted-foreground">Executing tool...</p>
            {args.id && (
              <p className="text-xs text-muted-foreground/70">ID: {args.id}</p>
            )}
          </div>
          <div className="flex items-center gap-2 rounded-full bg-primary/10 px-2 py-1 text-xs text-primary">
            <div className="size-1.5 rounded-full bg-primary animate-pulse" />
            <span>Running</span>
          </div>
        </div>
      </div>
      <div className={toolContentStyles}>
        <pre className="overflow-x-auto rounded-md bg-muted p-4 font-mono text-foreground">
          {JSON.stringify(toolArgs, null, 2)}
        </pre>
      </div>
    </div>
  );
};

const ToolOutputUI = ({ args }: { args: ToolArgs }) => {
  const [mounted, setMounted] = useState(false);
  const [output, setOutput] = useState('');
  const outputRef = useRef<string>('');

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    
    if (args.message) {
      console.log('ToolOutputUI received message:', args.message);
      try {
        // Handle special characters and emojis
        const decodedMessage = args.message.replace(/\\u([0-9a-fA-F]{4})/g, (_, hex) => 
          String.fromCharCode(parseInt(hex, 16))
        );
        
        // If it's a new message (contains a header like "Found resources"), reset the output
        if (decodedMessage.includes('Found resources:')) {
          outputRef.current = decodedMessage;
        } else {
          // Otherwise append to existing output
          outputRef.current = decodedMessage;
        }
        
        setOutput(outputRef.current);
      } catch (error) {
        console.error('Error processing tool output:', error);
        outputRef.current += args.message;
        setOutput(outputRef.current);
      }
    }
  }, [args.message, mounted]);

  if (!mounted) return null;

  return (
    <div className={toolContainerStyles}>
      <div className={toolHeaderStyles}>
        <Terminal className={`${toolIconStyles} text-primary`} />
        <div className="flex flex-1 items-center justify-between">
          <div>
            <p className="font-semibold text-foreground">Tool Output</p>
            {args.id && (
              <p className="text-xs text-muted-foreground/70">ID: {args.id}</p>
            )}
          </div>
          <div className="flex items-center gap-2 rounded-full bg-green-500/10 px-2 py-1 text-xs text-green-500">
            <div className="size-1.5 rounded-full bg-green-500" />
            <span>Complete</span>
          </div>
        </div>
      </div>
      <div className={toolContentStyles}>
        <pre className="overflow-x-auto rounded-md bg-muted p-4 font-mono text-foreground whitespace-pre-wrap break-words">
          {output}
        </pre>
      </div>
    </div>
  );
};

// Component that registers and renders all tool UIs
export const ToolUI = ({ children }: { children?: React.ReactNode }) => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useAssistantToolUI({
    toolName: "system_message",
    render: SystemMessageUI,
  });

  useAssistantToolUI({
    toolName: "tool",
    render: ToolExecutionUI,
  });

  useAssistantToolUI({
    toolName: "tool_output",
    render: ToolOutputUI,
  });

  if (!mounted) return null;

  return <>{children}</>;
};

// Hook to use in parent components
export const useRegisterToolUIs = () => {
  return <ToolUI />;
}; 