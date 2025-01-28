import * as React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { cn } from '@/lib/utils';
import { ContextVariable } from './ContextVariable';
import type { Components } from 'react-markdown';

interface MarkdownWithContextProps {
  content: string;
  className?: string;
}

// Define proper types for markdown components
type MarkdownComponentProps = {
  children?: React.ReactNode;
  className?: string;
  node?: any;
  [key: string]: any;
};

// Add these helper functions at the top level
function isJsonString(str: string): boolean {
  try {
    JSON.parse(str);
    return true;
  } catch {
    return false;
  }
}

function parseYamlLike(text: string): Record<string, unknown> {
  const lines = text.split('\n');
  const result: Record<string, unknown> = {};
  let currentKey: string | null = null;
  let currentValue: string[] = [];

  for (const line of lines) {
    const trimmedLine = line.trim();
    if (!trimmedLine) continue;

    if (trimmedLine.includes(':')) {
      // Save previous key-value pair if exists
      if (currentKey) {
        result[currentKey] = currentValue.length === 1 
          ? currentValue[0]
          : currentValue.join('\n');
        currentValue = [];
      }

      const [key, ...values] = trimmedLine.split(':');
      currentKey = key.trim();
      if (values.length) {
        currentValue.push(values.join(':').trim());
      }
    } else if (currentKey) {
      // Append to current value
      currentValue.push(trimmedLine);
    }
  }

  // Save last key-value pair
  if (currentKey) {
    result[currentKey] = currentValue.length === 1 
      ? currentValue[0]
      : currentValue.join('\n');
  }

  return result;
}

export const MarkdownWithContext: React.FC<MarkdownWithContextProps> = ({ content, className }) => {
  const components: Partial<Components> = {
    h1: ({ children, ...props }: MarkdownComponentProps) => (
      <h1 className="text-xl font-bold text-white mb-4" {...props}>{children}</h1>
    ),
    h2: ({ children, ...props }: MarkdownComponentProps) => (
      <h2 className="text-lg font-semibold text-white mb-3" {...props}>{children}</h2>
    ),
    h3: ({ children, ...props }: MarkdownComponentProps) => (
      <h3 className="text-base font-medium text-white mb-2" {...props}>{children}</h3>
    ),
    p: ({ children, ...props }: MarkdownComponentProps) => (
      <p className="text-sm text-slate-300 leading-relaxed mb-2" {...props}>{children}</p>
    ),
    ul: ({ children, ...props }: MarkdownComponentProps) => (
      <ul className="list-disc list-inside text-sm text-slate-300 mb-2 space-y-1" {...props}>{children}</ul>
    ),
    ol: ({ children, ...props }: MarkdownComponentProps) => (
      <ol className="list-decimal list-inside text-sm text-slate-300 mb-2 space-y-1" {...props}>{children}</ol>
    ),
    li: ({ children, ...props }: MarkdownComponentProps) => (
      <li className="text-sm text-slate-300" {...props}>{children}</li>
    ),
    code: ({ inline, className, children, ...props }: MarkdownComponentProps & { inline?: boolean }) => {
      const match = /language-(\w+)/.exec(className || '');
      const lang = match ? match[1] : 'typescript';
      const content = String(children).replace(/\n$/, '');

      if (inline) {
        return (
          <code 
            className="px-1.5 py-0.5 rounded-md bg-slate-800 text-slate-200 text-xs font-mono" 
            {...props}
          >
            {content}
          </code>
        );
      }

      return (
        <div className="my-2">
          <SyntaxHighlighter
            language={lang}
            style={vscDarkPlus}
            customStyle={{ 
              margin: '0',
              padding: '0.75rem',
              background: 'rgba(30, 41, 59, 0.5)',
              border: '1px solid rgba(51, 65, 85, 0.5)',
              borderRadius: '0.375rem',
              fontSize: '0.875rem'
            }}
          >
            {content}
          </SyntaxHighlighter>
        </div>
      );
    },
    blockquote: ({ children, ...props }: MarkdownComponentProps) => (
      <blockquote className="border-l-2 border-slate-600 pl-4 my-2 text-sm text-slate-400 italic" {...props}>
        {children}
      </blockquote>
    ),
    a: ({ href, children, ...props }: MarkdownComponentProps & { href?: string }) => (
      <a 
        href={href || '#'}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-400 hover:text-blue-300 underline underline-offset-2"
        {...props}
      >
        {children}
      </a>
    ),
    table: ({ children, ...props }: MarkdownComponentProps) => (
      <div className="overflow-x-auto my-2">
        <table className="min-w-full divide-y divide-slate-800" {...props}>
          {children}
        </table>
      </div>
    ),
    th: ({ children, ...props }: MarkdownComponentProps) => (
      <th className="px-3 py-2 text-left text-xs font-medium text-slate-300 uppercase tracking-wider bg-slate-800/50" {...props}>
        {children}
      </th>
    ),
    td: ({ children, ...props }: MarkdownComponentProps) => (
      <td className="px-3 py-2 text-sm text-slate-300 border-t border-slate-800" {...props}>
        {children}
      </td>
    ),
  };

  const formatMessageWithJson = (text: string): React.ReactNode[] => {
    // First, protect template variables by replacing them with placeholders
    const contextVarRegex = /\{\{([^}]+)\}\}/g;
    const templateVars: string[] = [];
    const protectedText = text.replace(contextVarRegex, (match, group) => {
      templateVars.push(group);
      return `__TEMPLATE_VAR_${templateVars.length - 1}__`;
    });

    // Then split and parse the JSON/YAML content
    const contentParts = protectedText.split(/(?=\{|\[)|(?<=\}|\])/g);
    
    return contentParts.map((part, index) => {
      // Restore template variables
      const restoredPart = part.replace(/__TEMPLATE_VAR_(\d+)__/g, (_, i) => {
        return `{{${templateVars[parseInt(i)]}}}`
      });

      // Handle template variables
      if (restoredPart.match(contextVarRegex)) {
        const [pre, variable, post] = restoredPart.split(contextVarRegex);
        return (
          <React.Fragment key={index}>
            {pre && <span>{pre}</span>}
            <ContextVariable variable={variable} />
            {post && <span>{post}</span>}
          </React.Fragment>
        );
      }

      // Try to parse as JSON
      try {
        if (restoredPart.trim().startsWith('{') || restoredPart.trim().startsWith('[')) {
          const parsed = JSON.parse(restoredPart);
          return (
            <div key={index} className="my-2 rounded-md overflow-hidden">
              <SyntaxHighlighter
                language="json"
                style={vscDarkPlus}
                customStyle={{ 
                  margin: 0, 
                  padding: '0.75rem',
                  background: 'rgba(30, 41, 59, 0.5)',
                  border: '1px solid rgba(51, 65, 85, 0.5)',
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem'
                }}
                wrapLongLines={true}
                showLineNumbers={true}
              >
                {JSON.stringify(parsed, null, 2)}
              </SyntaxHighlighter>
            </div>
          );
        }
      } catch {}

      // If not JSON, render as markdown
      return restoredPart ? (
        <ReactMarkdown
          key={index}
          remarkPlugins={[remarkGfm]}
          components={components}
          className={cn(
            "prose prose-invert max-w-none",
            "prose-headings:mt-0 prose-headings:mb-2",
            "prose-p:my-1 prose-p:leading-relaxed",
            "prose-pre:my-0 prose-pre:bg-transparent",
            "prose-code:px-1 prose-code:py-0.5 prose-code:rounded-md",
            "prose-code:bg-slate-800 prose-code:text-slate-200",
            "prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline",
            className
          )}
        >
          {restoredPart.replace(/\n{3,}/g, '\n\n')}
        </ReactMarkdown>
      ) : null;
    });
  };

  return <div className="text-sm text-slate-300">{formatMessageWithJson(content)}</div>;
};