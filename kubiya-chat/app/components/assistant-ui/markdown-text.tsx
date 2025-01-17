"use client";

import { makeMarkdownText } from "@assistant-ui/react-markdown";
import { ToolExecution } from "./ToolExecution";

export const MarkdownText = makeMarkdownText({
  components: {
    p: ({ children }) => (
      <p className="whitespace-pre-wrap">{children}</p>
    ),
    pre: ({ children }) => {
      try {
        const text = children?.toString() || '';
        
        // Handle tool init message in plain text format
        if (text.includes('🔧 Executing:')) {
          const toolName = text.replace('🔧 Executing: ', '');
          return (
            <ToolExecution
              type="tool-call"
              toolName={toolName}
              args={{}}
              toolCallId={crypto.randomUUID()}
              argsText={toolName}
              status={{ type: "running" }}
              addResult={() => {}}
            />
          );
        }

        // First try to parse as JSON
        try {
          const messageObj = JSON.parse(text);
          
          // Handle tool init message in JSON format
          if (messageObj.type === 'tool_init') {
            return (
              <ToolExecution
                type="tool-call"
                toolName={messageObj.content.replace('🔧 Executing: ', '')}
                args={{}}
                toolCallId={crypto.randomUUID()}
                argsText={messageObj.content.replace('🔧 Executing: ', '')}
                status={{ type: "running" }}
                addResult={() => {}}
              />
            );
          }

          // Handle tool output message
          if (messageObj.type === 'tool_output') {
            return (
              <ToolExecution
                type="tool-call"
                toolName={messageObj.name || 'Tool Output'}
                args={{}}
                toolCallId={crypto.randomUUID()}
                argsText={messageObj.content}
                status={{ type: "complete" }}
                addResult={() => {}}
              />
            );
          }

          // Handle tool message
          if (messageObj.type === 'tool') {
            const lines = messageObj.message.split('\n');
            const toolName = lines[1]?.replace('Tool:', '')?.trim() || '';
            let args = {};
            
            try {
              const argsLine = lines[2];
              if (argsLine && argsLine.includes('Arguments:')) {
                const argsJson = argsLine.replace('Arguments:', '').trim();
                args = JSON.parse(argsJson);
              }
            } catch (e) {
              console.error('Error parsing tool arguments:', e);
            }

            return (
              <ToolExecution
                toolName={toolName}
                args={args}
                status={{ type: "running" }}
                type="tool-call"
                toolCallId={crypto.randomUUID()}
                argsText={JSON.stringify(args)}
                addResult={() => {}}
              />
            );
          }
        } catch {
          // Not a JSON, try parsing as tool message
          if (text.includes('Tool:')) {
            const lines = text.split('\n');
            const toolName = lines[1]?.replace('Tool:', '')?.trim() || '';
            let args = {};
            
            try {
              const argsLine = lines.find(line => line.includes('Arguments:'));
              if (argsLine) {
                const argsJson = argsLine.replace('Arguments:', '').trim();
                args = JSON.parse(argsJson);
              }
            } catch (e) {
              console.error('Error parsing tool arguments:', e);
            }

            return (
              <ToolExecution
                toolName={toolName}
                args={args}
                status={{ type: "running" }}
                type="tool-call"
                toolCallId={crypto.randomUUID()}
                argsText={JSON.stringify(args)}
                addResult={() => {}}
              />
            );
          }
        }
        
        // Not a valid tool message format, render as normal pre
        return <pre className="bg-black/30 rounded-md p-3 text-sm font-mono text-white/90 overflow-x-auto ring-1 ring-white/10">{text}</pre>;
      } catch {
        // Fallback for any parsing errors
        return <pre className="bg-black/30 rounded-md p-3 text-sm font-mono text-white/90 overflow-x-auto ring-1 ring-white/10">{children}</pre>;
      }
    }
  }
});
