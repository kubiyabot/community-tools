"use client";

import ReactMarkdown from 'react-markdown';

interface MarkdownTextProps {
  content: string;
}

export const MarkdownText = ({ content }: MarkdownTextProps) => {
  return (
    <ReactMarkdown
      components={{
        code({ className, children }) {
          return (
            <code className="bg-[#1A1F2E] px-1.5 py-0.5 rounded text-[#7C3AED]">
              {children}
            </code>
          );
        },
        pre({ children }) {
          return (
            <pre className="bg-[#1A1F2E] p-4 rounded-md overflow-x-auto my-4 text-[#E2E8F0]">
              {children}
            </pre>
          );
        },
        p({ children }) {
          return <p className="mb-4 last:mb-0 leading-relaxed">{children}</p>;
        },
        ul({ children }) {
          return <ul className="list-disc list-inside mb-4 space-y-1">{children}</ul>;
        },
        ol({ children }) {
          return <ol className="list-decimal list-inside mb-4 space-y-1">{children}</ol>;
        },
        li({ children }) {
          return <li className="leading-relaxed">{children}</li>;
        },
        a({ children, href }) {
          return (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#7C3AED] hover:underline"
            >
              {children}
            </a>
          );
        },
        blockquote({ children }) {
          return (
            <blockquote className="border-l-2 border-[#3D4B5E] pl-4 mb-4 italic">
              {children}
            </blockquote>
          );
        },
        h1({ children }) {
          return <h1 className="text-xl font-bold mb-4">{children}</h1>;
        },
        h2({ children }) {
          return <h2 className="text-lg font-bold mb-3">{children}</h2>;
        },
        h3({ children }) {
          return <h3 className="text-base font-bold mb-2">{children}</h3>;
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );
}; 