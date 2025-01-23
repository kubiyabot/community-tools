"use client";

import ReactMarkdown from 'react-markdown';
import { Copy, Check } from 'lucide-react';
import { useState } from 'react';

interface MarkdownTextProps {
  content: string;
  isStreaming?: boolean;
}

const CodeBlock = ({ children, className }: { children: string; className?: string }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group">
      <pre className="bg-[#1A1F2E] p-4 rounded-md overflow-x-auto my-2 text-[#E2E8F0] text-sm">
        <code className={className}>{children}</code>
      </pre>
      <button
        onClick={handleCopy}
        className="opacity-0 group-hover:opacity-100 transition-opacity absolute right-2 top-2 p-1.5 rounded-md bg-[#2D3B4E] hover:bg-[#3D4B5E] text-[#94A3B8]"
        title="Copy to clipboard"
      >
        {copied ? (
          <Check className="h-4 w-4 text-green-400" />
        ) : (
          <Copy className="h-4 w-4" />
        )}
      </button>
    </div>
  );
};

export const MarkdownText = ({ content, isStreaming }: MarkdownTextProps) => {
  return (
    <ReactMarkdown
      components={{
        code(props) {
          const { children, className, node, ...rest } = props;
          const text = String(children).trim();
          
          // Check if this is a code block (starts with triple backticks)
          if (text.startsWith('```')) {
            const lines = text.split('\n');
            const language = lines[0].slice(3).trim(); // Get language from first line
            const code = lines.slice(1, -1).join('\n'); // Remove first and last lines (```)
            return <CodeBlock className={language ? `language-${language}` : undefined}>{code}</CodeBlock>;
          }
          
          // For inline code (single backticks)
          if (text.startsWith('`') && text.endsWith('`')) {
            return (
              <code className="bg-[#1A1F2E] px-1.5 py-0.5 rounded text-[#7C3AED] text-sm" {...rest}>
                {text.slice(1, -1)}
              </code>
            );
          }
          
          // For regular text, just return it
          return <>{text}</>;
        },
        p(props) {
          const { children } = props;
          return (
            <p className="mb-2 last:mb-0 leading-relaxed">
              <span className="relative">
                {children}
                {isStreaming && (
                  <span className="absolute -right-[3px] top-1 inline-block w-[2px] h-[14px] bg-purple-400 animate-cursor" />
                )}
              </span>
            </p>
          );
        },
        ul(props) {
          const { children } = props;
          return <ul className="list-disc list-inside mb-2 space-y-1 pl-1">{children}</ul>;
        },
        ol(props) {
          const { children } = props;
          return <ol className="list-decimal list-inside mb-2 space-y-1 pl-1">{children}</ol>;
        },
        li(props) {
          const { children } = props;
          return <li className="leading-relaxed pl-1">{children}</li>;
        },
        a(props) {
          const { children, href } = props;
          return (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#7C3AED] hover:underline inline-flex items-center gap-0.5"
            >
              {children}
            </a>
          );
        },
        blockquote(props) {
          const { children } = props;
          return (
            <blockquote className="border-l-2 border-[#3D4B5E] pl-3 my-2 text-[#94A3B8] italic">
              {children}
            </blockquote>
          );
        },
        h1(props) {
          const { children } = props;
          return <h1 className="text-lg font-bold mb-2 mt-3 first:mt-0">{children}</h1>;
        },
        h2(props) {
          const { children } = props;
          return <h2 className="text-base font-bold mb-2 mt-3 first:mt-0">{children}</h2>;
        },
        h3(props) {
          const { children } = props;
          return <h3 className="text-sm font-bold mb-2 mt-3 first:mt-0">{children}</h3>;
        },
        table(props) {
          const { children } = props;
          return (
            <div className="overflow-x-auto my-2">
              <table className="min-w-full divide-y divide-[#2D3B4E] text-sm">
                {children}
              </table>
            </div>
          );
        },
        thead(props) {
          const { children } = props;
          return <thead className="bg-[#1A1F2E]">{children}</thead>;
        },
        tbody(props) {
          const { children } = props;
          return <tbody className="divide-y divide-[#2D3B4E]">{children}</tbody>;
        },
        tr(props) {
          const { children } = props;
          return <tr>{children}</tr>;
        },
        th(props) {
          const { children } = props;
          return <th className="px-4 py-2 text-left text-xs font-medium text-[#94A3B8] uppercase tracking-wider">{children}</th>;
        },
        td(props) {
          const { children } = props;
          return <td className="px-4 py-2 whitespace-nowrap">{children}</td>;
        },
        hr() {
          return <hr className="my-4 border-[#2D3B4E]" />;
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );
};

// Add this to your global CSS or Tailwind config:
// @keyframes cursor {
//   0%, 100% { opacity: 1; }
//   50% { opacity: 0; }
// }
// .animate-cursor {
//   animation: cursor 1s ease-in-out infinite;
// } 