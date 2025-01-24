"use client";

import ReactMarkdown from 'react-markdown';
import { Copy, Check, Terminal, Settings2, MoreHorizontal } from 'lucide-react';
import { useState } from 'react';
import type { Components } from 'react-markdown';
import type { ReactNode } from 'react';
import type { HTMLProps } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';

interface MarkdownTextProps {
  content: string;
  isStreaming?: boolean;
}

type CodeProps = HTMLProps<HTMLElement> & {
  children?: ReactNode;
  className?: string;
};

interface CodePreferences {
  showLineNumbers: boolean;
  wrapLines: boolean;
  fontSize: number;
}

const CodeBlock = ({ children, className }: { children: ReactNode; className?: string }) => {
  const [copied, setCopied] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  
  const [preferences, setPreferences] = useState<CodePreferences>(() => {
    const saved = localStorage.getItem('code-preferences');
    return saved ? JSON.parse(saved) : {
      showLineNumbers: true,
      wrapLines: true,
      fontSize: 13
    };
  });

  const updatePreferences = (newPrefs: Partial<CodePreferences>) => {
    const updated = { ...preferences, ...newPrefs };
    setPreferences(updated);
    localStorage.setItem('code-preferences', JSON.stringify(updated));
  };

  const handleCopy = async () => {
    const text = String(children).replace(/\n$/, '');
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExecute = () => {
    const code = String(children).replace(/\n$/, '');
    // Send a prompt to execute the code
    window.postMessage({ type: 'EXECUTE_CODE', code }, '*');
  };

  // Extract language from className (format: "language-{lang}")
  const language = className?.split('-')[1] || '';

  // Detect language from content if not specified
  const detectLanguage = (content: string): string => {
    if (language) return language;

    const pythonPatterns = [
      'import ',
      'def ',
      'class ',
      'print(',
      'self.',
      '__init__',
      'from ',
      '#'
    ];
    const shellPatterns = ['kubectl', 'docker', 'npm', 'yarn', 'pip', 'apt-get', 'brew'];
    const jsPatterns = ['const ', 'let ', 'function ', '=>', 'console.log'];
    
    const content_str = String(content).toLowerCase();
    
    if (pythonPatterns.some(pattern => content_str.includes(pattern.toLowerCase()))) {
      return 'python';
    }
    if (shellPatterns.some(pattern => content_str.includes(pattern.toLowerCase()))) {
      return 'bash'; // Changed from 'shell' to 'bash' for Prism compatibility
    }
    if (jsPatterns.some(pattern => content_str.includes(pattern.toLowerCase()))) {
      return 'javascript';
    }
    
    return 'text'; // Changed default from language to 'text'
  };

  const detectedLang = detectLanguage(String(children));

  // Get language-specific styles
  const getLanguageColor = (lang: string) => {
    const colors: Record<string, { text: string; bg: string; icon?: string; name: string }> = {
      javascript: { text: '#F7DF1E', bg: '#23272E', icon: 'JS', name: 'JavaScript' },
      typescript: { text: '#3178C6', bg: '#23272E', icon: 'TS', name: 'TypeScript' },
      python: { text: '#FFD43B', bg: '#23272E', icon: '🐍', name: 'Python' },
      go: { text: '#00ADD8', bg: '#23272E', icon: 'Go', name: 'Go' },
      rust: { text: '#DEA584', bg: '#23272E', icon: '⚙️', name: 'Rust' },
      java: { text: '#E76F00', bg: '#23272E', icon: '☕', name: 'Java' },
      kotlin: { text: '#A97BFF', bg: '#23272E', icon: 'Kt', name: 'Kotlin' },
      ruby: { text: '#CC342D', bg: '#23272E', icon: '💎', name: 'Ruby' },
      php: { text: '#777BB4', bg: '#23272E', icon: '🐘', name: 'PHP' },
      swift: { text: '#F05138', bg: '#23272E', icon: '🦅', name: 'Swift' },
      csharp: { text: '#239120', bg: '#23272E', icon: 'C#', name: 'C#' },
      cpp: { text: '#00599C', bg: '#23272E', icon: 'C++', name: 'C++' },
      html: { text: '#E34F26', bg: '#23272E', icon: '🌐', name: 'HTML' },
      css: { text: '#1572B6', bg: '#23272E', icon: '🎨', name: 'CSS' },
      sql: { text: '#3492FF', bg: '#23272E', icon: '🗃️', name: 'SQL' },
      bash: { text: '#89E051', bg: '#23272E', icon: '⌘', name: 'Bash' },
      dockerfile: { text: '#384D54', bg: '#23272E', icon: '🐋', name: 'Dockerfile' },
      yaml: { text: '#CB171E', bg: '#23272E', icon: '📄', name: 'YAML' },
      json: { text: '#40A9FF', bg: '#23272E', icon: '{ }', name: 'JSON' },
      markdown: { text: '#083FA5', bg: '#23272E', icon: '📝', name: 'Markdown' },
      text: { text: '#A9B1D6', bg: '#23272E', icon: '📄', name: 'Plain Text' },
    };
    return colors[lang.toLowerCase()] || colors.text;
  };

  const langStyle = getLanguageColor(detectedLang);

  return (
    <div 
      className="relative group my-4"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => {
        setIsHovered(false);
        setShowPreferences(false);
      }}
    >
      <div 
        className={`
          absolute -top-3 left-4 right-4 flex items-center justify-between
          transition-opacity duration-200
          ${isHovered ? 'opacity-100' : 'opacity-0'}
        `}
      >
        <div className="flex items-center gap-2">
          <span 
            className="text-xs font-medium px-2 py-1 rounded-t-md flex items-center gap-1.5 font-mono"
            style={{ 
              color: langStyle.text,
              backgroundColor: langStyle.bg,
              fontFamily: 'JetBrains Mono, monospace'
            }}
          >
            {langStyle.icon && (
              <span className="font-mono text-base leading-none" style={{ fontFamily: 'JetBrains Mono, monospace' }}>
                {langStyle.icon}
              </span>
            )}
            {!langStyle.icon && <Terminal className="h-3.5 w-3.5" />}
            {langStyle.name}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <button
              onClick={() => setShowPreferences(!showPreferences)}
              className={`
                transition-all duration-200
                px-2.5 py-1 rounded-md
                bg-slate-700/50 text-slate-400 hover:bg-slate-700/70 hover:text-slate-300
                flex items-center gap-1.5 text-xs font-medium
              `}
              title="Code preferences"
            >
              <Settings2 className="h-3.5 w-3.5" />
            </button>
            
            {showPreferences && (
              <div className="absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-slate-800 ring-1 ring-black ring-opacity-5 z-50">
                <div className="py-1">
                  <div className="px-4 py-2 text-xs text-slate-400">
                    <label className="flex items-center justify-between mb-2">
                      <span>Line Numbers</span>
                      <input
                        type="checkbox"
                        checked={preferences.showLineNumbers}
                        onChange={(e) => updatePreferences({ showLineNumbers: e.target.checked })}
                        className="rounded border-slate-700 text-purple-500 focus:ring-purple-500"
                      />
                    </label>
                    <label className="flex items-center justify-between mb-2">
                      <span>Wrap Lines</span>
                      <input
                        type="checkbox"
                        checked={preferences.wrapLines}
                        onChange={(e) => updatePreferences({ wrapLines: e.target.checked })}
                        className="rounded border-slate-700 text-purple-500 focus:ring-purple-500"
                      />
                    </label>
                    <label className="flex items-center justify-between">
                      <span>Font Size</span>
                      <select
                        value={preferences.fontSize}
                        onChange={(e) => updatePreferences({ fontSize: Number(e.target.value) })}
                        className="ml-2 text-xs rounded bg-slate-700 border-slate-600 text-slate-300"
                      >
                        <option value={11}>Small</option>
                        <option value={13}>Medium</option>
                        <option value={15}>Large</option>
                      </select>
                    </label>
                  </div>
                </div>
              </div>
            )}
          </div>
          <button
            onClick={handleExecute}
            className={`
              transition-all duration-200
              px-2.5 py-1 rounded-md 
              bg-purple-500/10 text-purple-400 hover:bg-purple-500/20
              flex items-center gap-1.5 text-xs font-medium font-mono
            `}
            style={{ fontFamily: 'JetBrains Mono, monospace' }}
            title="Execute code"
          >
            <span className="font-mono text-base leading-none">▶</span>
            <span>Run</span>
          </button>
          <button
            onClick={handleCopy}
            className={`
              transition-all duration-200
              px-2.5 py-1 rounded-md 
              ${copied 
                ? 'bg-green-500/10 text-green-400 hover:bg-green-500/20' 
                : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700/70 hover:text-slate-300'
              }
              flex items-center gap-1.5 text-xs font-medium
            `}
            title="Copy to clipboard"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5" />
                <span>Copied!</span>
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>
      <div 
        className={`
          rounded-lg overflow-hidden
          border border-slate-700/50 transition-all duration-200
          ${isHovered ? 'border-slate-700 shadow-lg shadow-slate-900/20' : ''}
          ${detectedLang ? 'mt-2' : ''}
        `}
      >
        <SyntaxHighlighter
          language={detectedLang}
          style={oneDark}
          customStyle={{
            margin: 0,
            borderRadius: '0.5rem',
            fontSize: `${preferences.fontSize}px`,
            lineHeight: '1.5',
            backgroundColor: langStyle.bg,
          }}
          showLineNumbers={detectedLang !== '' && preferences.showLineNumbers}
          wrapLines={preferences.wrapLines}
          wrapLongLines={preferences.wrapLines}
          codeTagProps={{
            style: {
              fontSize: `${preferences.fontSize}px`,
              lineHeight: '1.5',
            }
          }}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      </div>
    </div>
  );
};

export const MarkdownText = ({ content, isStreaming }: MarkdownTextProps) => {
  const components: Components = {
    code(props: CodeProps) {
      const { className, children } = props;
      const match = /language-(\w+)/.exec(className || '');
      
      // If we have a language class, it's a code block
      if (match) {
        return (
          <CodeBlock className={className}>
            {String(children).replace(/\n$/, '')}
          </CodeBlock>
        );
      }

      // Check if this is a multiline code block without language
      const content = String(children);
      if (content.includes('\n')) {
        return (
          <CodeBlock>
            {content.replace(/\n$/, '')}
          </CodeBlock>
        );
      }

      // Otherwise, it's an inline code block
      return (
        <code className="bg-[#1A1F2E] px-1.5 py-0.5 rounded text-[#7C3AED] text-sm">
          {children}
        </code>
      );
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
  };

  return (
    <ReactMarkdown components={components}>
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