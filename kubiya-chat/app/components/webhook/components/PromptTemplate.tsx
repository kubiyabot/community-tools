import React, { useState, useEffect, useRef } from 'react';
import { WebhookEvent, WebhookProvider } from '../providers';
import { Button } from '../../ui/button';
import { cn } from '../../../lib/utils';
import { Badge } from '../../ui/badge';
import { Textarea } from '../../ui/textarea';
import { Input } from '../../ui/input';
import { 
  MessageSquare, 
  PlayCircle, 
  Eye, 
  Code, 
  ChevronRight, 
  ArrowLeft,
  Search,
  Copy,
  Edit2,
  X,
  RefreshCw,
  Filter
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Components } from 'react-markdown';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../../ui/tooltip";
import { toast } from "../../ui/use-toast";

interface PromptTemplateProps {
  selectedProvider: WebhookProvider | null;
  selectedEvent: string;
  promptTemplate: string;
  setPromptTemplate: (template: string) => void;
  onContinue: () => void;
  filter?: string;
  setFilter?: (filter: string) => void;
}

interface VariablePath {
  path: string[];
  preview: string;
  isExpandable: boolean;
}

interface VariableEdit {
  path: string[];
  value: any;
}

export function PromptTemplate({
  selectedProvider,
  selectedEvent,
  promptTemplate,
  setPromptTemplate,
  onContinue,
  filter = '',
  setFilter
}: PromptTemplateProps) {
  const [showVariables, setShowVariables] = useState(false);
  const [showRawPreview, setShowRawPreview] = useState(false);
  const [currentPath, setCurrentPath] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [editingVariable, setEditingVariable] = useState<VariableEdit | null>(null);
  const [filterType, setFilterType] = useState<'all' | 'objects' | 'values'>('all');
  const [recentVariables, setRecentVariables] = useState<string[]>([]);
  const [showJmesFilter, setShowJmesFilter] = useState(false);
  const [jmesError, setJmesError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  if (!selectedProvider) return null;

  const event = selectedProvider.events.find((e: WebhookEvent) => e.type === selectedEvent);
  if (!event) return null;

  const getValueAtPath = (obj: any, path: string[]): any => {
    return path.reduce((acc, key) => acc?.[key], obj);
  };

  const getAvailableVariables = (obj: any, basePath: string[] = []): VariablePath[] => {
    if (!obj || typeof obj !== 'object') return [];

    const currentValue = basePath.length ? getValueAtPath(event.example, basePath) : obj;
    if (!currentValue || typeof currentValue !== 'object') return [];

    return Object.entries(currentValue).map(([key, value]): VariablePath => {
      const currentPath = [...basePath, key];
      const isObject = Boolean(value && typeof value === 'object' && !Array.isArray(value));
      let preview = '';

      if (isObject) {
        const objPreview = Object.entries(value as object).slice(0, 2)
          .map(([k, v]) => `${k}: ${typeof v === 'object' ? '{...}' : v}`)
          .join(', ');
        preview = `{ ${objPreview}${Object.keys(value as object).length > 2 ? ', ...' : ''} }`;
      } else if (Array.isArray(value)) {
        preview = `[${value.slice(0, 2).map(v => typeof v === 'object' ? '{...}' : v).join(', ')}${value.length > 2 ? ', ...' : ''}]`;
      } else {
        preview = String(value);
      }

      return {
        path: currentPath,
        preview: preview.length > 60 ? preview.slice(0, 57) + '...' : preview,
        isExpandable: isObject
      };
    });
  };

  const handleInsertVariable = (path: string[]) => {
    if (!textareaRef.current) return;

    const start = textareaRef.current.selectionStart;
    const end = textareaRef.current.selectionEnd;
    const text = promptTemplate;
    const before = text.substring(0, start);
    const after = text.substring(end);
    const variableText = `{{.event.${path.join('.')}}}`;
    const newText = `${before}${variableText}${after}`;
    setPromptTemplate(newText);

    const newCursorPos = start + variableText.length;
    setTimeout(() => {
      if (textareaRef.current) {
        textareaRef.current.focus();
        textareaRef.current.setSelectionRange(newCursorPos, newCursorPos);
      }
    }, 0);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === '$' || (e.key === '{' && e.shiftKey)) {
      e.preventDefault();
      setShowVariables(true);
      setCurrentPath([]);
    }
  };

  const processTemplate = (template: string, example: any) => {
    return template.replace(/\{\{\.event\.([^}]+)\}\}/g, (_, variable) => {
      const value = example[variable];
      return typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value);
    });
  };

  const copyVariablePath = (path: string[]) => {
    const variablePath = `{{.event.${path.join('.')}}}`;
    navigator.clipboard.writeText(variablePath);
    toast({
      title: "Copied!",
      description: `Variable path ${variablePath} copied to clipboard`,
      variant: "default"
    });
  };

  const handleVariableEdit = (path: string[], value: any) => {
    setEditingVariable({ path, value });
  };

  const applyVariableEdit = () => {
    if (!editingVariable) return;
    // In a real app, you'd want to update the example data
    // For now, we'll just close the edit mode
    setEditingVariable(null);
  };

  const addToRecent = (path: string[]) => {
    const variablePath = path.join('.');
    setRecentVariables(prev => {
      const newRecent = [variablePath, ...prev.filter(p => p !== variablePath)].slice(0, 5);
      return newRecent;
    });
  };

  const filterVariables = (variables: VariablePath[]) => {
    return variables.filter(variable => {
      const matchesSearch = variable.path.join('.').toLowerCase().includes(searchTerm.toLowerCase()) ||
                          variable.preview.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesType = filterType === 'all' ||
                         (filterType === 'objects' && variable.isExpandable) ||
                         (filterType === 'values' && !variable.isExpandable);
      
      return matchesSearch && matchesType;
    });
  };

  const variables = filterVariables(getAvailableVariables(event.example, currentPath));

  const validateJmesFilter = async (filterValue: string) => {
    if (!filterValue.trim()) {
      setJmesError(null);
      return true;
    }

    try {
      // Here you could add actual JMES validation if needed
      // For now, we'll just do basic syntax validation
      if (filterValue.includes('..') || !filterValue.match(/^[a-zA-Z0-9_\[\]\.@\?\*\(\)]+$/)) {
        setJmesError('Invalid JMES filter syntax');
        return false;
      }
      setJmesError(null);
      return true;
    } catch (err) {
      setJmesError('Invalid JMES filter syntax');
      return false;
    }
  };

  const handleFilterChange = async (value: string) => {
    if (setFilter) {
      const isValid = await validateJmesFilter(value);
      if (isValid) {
        setFilter(value);
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h3 className="text-lg font-medium text-slate-200">Create Prompt Template</h3>
        <p className="text-sm text-slate-400">
          Create a prompt template that will be used to process the event data.
          Type $ or {"{{"}to access variables from the event.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-slate-200">Template</h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                const template = `# ${event.name} Analysis\n\nPlease analyze the following event details:\n\n${event.variables.map(v => `- \`${v}\`: {{.event.${v}}}`).join('\n')}`;
                setPromptTemplate(template);
              }}
              className="h-8 text-sm text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition-all"
            >
              <MessageSquare className="h-4 w-4 mr-2" />
              Use Template
            </Button>
          </div>

          <div className="relative">
            <Textarea
              ref={textareaRef}
              value={promptTemplate}
              onChange={(e) => setPromptTemplate(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setShowVariables(false)}
              placeholder="Enter your prompt template here..."
              className="min-h-[300px] bg-[#141B2B] border-[#2D3B4E] text-slate-200 resize-none"
            />
            {showVariables && (
              <div className="absolute bottom-full left-0 mb-2 w-full p-3 rounded-lg bg-[#1E293B] border border-[#2D3B4E] shadow-lg">
                <div className="space-y-3">
                  {/* Search and Filter Bar */}
                  <div className="flex items-center gap-2">
                    <div className="relative flex-1">
                      <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <Input
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="Search variables..."
                        className="pl-8 h-8 bg-[#141B2B] border-[#2D3B4E] text-slate-200"
                      />
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setFilterType(type => {
                        const types: ('all' | 'objects' | 'values')[] = ['all', 'objects', 'values'];
                        const currentIndex = types.indexOf(type);
                        return types[(currentIndex + 1) % types.length];
                      })}
                      className="h-8 px-2 text-xs gap-1.5"
                    >
                      <Filter className="h-3.5 w-3.5" />
                      {filterType === 'all' ? 'All' : filterType === 'objects' ? 'Objects' : 'Values'}
                    </Button>
                  </div>

                  {/* Navigation and Current Path */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <h5 className="text-xs font-medium text-slate-300">Variables</h5>
                      {currentPath.length > 0 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setCurrentPath(currentPath.slice(0, -1))}
                          className="h-6 px-2 text-xs text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 flex items-center gap-1"
                        >
                          <ArrowLeft className="h-3 w-3" />
                          Back
                        </Button>
                      )}
                    </div>
                    <div className="text-xs text-slate-400">
                      {currentPath.length > 0 && (
                        <code className="px-1.5 py-0.5 rounded bg-slate-800">
                          event.{currentPath.join('.')}
                        </code>
                      )}
                    </div>
                  </div>

                  {/* Recent Variables */}
                  {recentVariables.length > 0 && (
                    <div className="flex items-center gap-2 py-2 border-y border-[#2D3B4E]">
                      <span className="text-xs text-slate-400">Recent:</span>
                      <div className="flex items-center gap-1.5 overflow-x-auto">
                        {recentVariables.map(path => (
                          <Button
                            key={path}
                            variant="ghost"
                            size="sm"
                            onClick={() => handleInsertVariable(path.split('.'))}
                            className="h-6 px-2 text-xs text-slate-400 hover:text-emerald-400 bg-slate-800/50"
                          >
                            {path}
                          </Button>
                        ))}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setRecentVariables([])}
                          className="h-6 w-6 p-0 text-slate-400 hover:text-red-400"
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* Variables List */}
                  <div className="grid grid-cols-1 gap-2 max-h-[300px] overflow-y-auto">
                    {variables.map((variable) => (
                      <TooltipProvider key={variable.path.join('.')}>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <div className="group relative">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  if (variable.isExpandable) {
                                    setCurrentPath(variable.path);
                                  } else {
                                    handleInsertVariable(variable.path);
                                    addToRecent(variable.path);
                                    setShowVariables(false);
                                  }
                                }}
                                className="h-8 w-full justify-between text-sm text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10"
                              >
                                <div className="flex items-center gap-2">
                                  <Badge 
                                    variant="outline" 
                                    className={cn(
                                      "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
                                      variable.isExpandable && "bg-blue-500/10 border-blue-500/30 text-blue-400"
                                    )}
                                  >
                                    {variable.path[variable.path.length - 1]}
                                    {variable.isExpandable && <ChevronRight className="h-3 w-3 ml-1 inline-block" />}
                                  </Badge>
                                </div>
                                <span className="truncate text-xs text-slate-500 max-w-[200px]">
                                  {variable.preview}
                                </span>
                              </Button>
                              <div className="absolute right-0 top-1/2 -translate-y-1/2 hidden group-hover:flex items-center gap-1 px-2 bg-[#1E293B]">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => copyVariablePath(variable.path)}
                                  className="h-6 w-6 p-0 text-slate-400 hover:text-emerald-400"
                                >
                                  <Copy className="h-3 w-3" />
                                </Button>
                                {!variable.isExpandable && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleVariableEdit(variable.path, getValueAtPath(event.example, variable.path))}
                                    className="h-6 w-6 p-0 text-slate-400 hover:text-emerald-400"
                                  >
                                    <Edit2 className="h-3 w-3" />
                                  </Button>
                                )}
                              </div>
                            </div>
                          </TooltipTrigger>
                          <TooltipContent side="right" className="max-w-sm">
                            <p className="text-xs font-medium mb-1">Preview:</p>
                            <pre className="text-xs bg-slate-900 p-2 rounded overflow-auto max-h-32">
                              {variable.preview}
                            </pre>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    ))}
                  </div>

                  {/* Variable Edit Modal */}
                  {editingVariable && (
                    <div className="absolute inset-0 bg-[#1E293B]/95 backdrop-blur-sm flex items-center justify-center">
                      <div className="w-full max-w-md p-4 bg-[#1E293B] rounded-lg border border-[#2D3B4E] shadow-xl">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-sm font-medium text-slate-200">
                            Edit Variable: {editingVariable.path.join('.')}
                          </h3>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setEditingVariable(null)}
                            className="h-6 w-6 p-0 text-slate-400 hover:text-red-400"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                        <div className="space-y-4">
                          <Textarea
                            value={JSON.stringify(editingVariable.value, null, 2)}
                            onChange={(e) => {
                              try {
                                const newValue = JSON.parse(e.target.value);
                                setEditingVariable(prev => prev ? { ...prev, value: newValue } : null);
                              } catch {} // Ignore invalid JSON while typing
                            }}
                            placeholder="Enter value..."
                            className="min-h-[100px] bg-[#141B2B] border-[#2D3B4E] text-slate-200 font-mono text-sm"
                          />
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setEditingVariable(null)}
                              className="h-8 text-slate-400"
                            >
                              Cancel
                            </Button>
                            <Button
                              variant="default"
                              size="sm"
                              onClick={applyVariableEdit}
                              className="h-8 bg-emerald-500 hover:bg-emerald-600 text-white"
                            >
                              Apply Changes
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-slate-200">Live Preview</h4>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowRawPreview(!showRawPreview)}
                className="h-8 text-sm text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10"
              >
                {showRawPreview ? <Eye className="h-4 w-4" /> : <Code className="h-4 w-4" />}
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={onContinue}
                className="h-8 bg-emerald-500 hover:bg-emerald-600 text-white shadow-sm shadow-emerald-500/20"
                disabled={!promptTemplate.trim()}
              >
                <PlayCircle className="h-4 w-4 mr-2" />
                Continue
              </Button>
            </div>
          </div>

          <div 
            className="prose prose-invert prose-sm max-w-none p-4 rounded-md bg-[#141B2B] border border-[#2D3B4E] overflow-auto min-h-[300px]"
          >
            {showRawPreview ? (
              <pre className="text-sm text-slate-300 whitespace-pre-wrap">
                {processTemplate(promptTemplate, event.example)}
              </pre>
            ) : (
              <div className="markdown-preview">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {processTemplate(promptTemplate, event.example)}
                </ReactMarkdown>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="p-6 rounded-lg bg-[#1E293B] border border-[#2D3B4E]">
        <div className="flex items-center justify-between mb-4">
          <div className="space-y-1">
            <h4 className="text-sm font-medium text-slate-200">Event Data Filter</h4>
            <p className="text-xs text-slate-400">Optionally filter events using JMES path expressions</p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowJmesFilter(!showJmesFilter)}
            className="text-xs text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 flex items-center gap-2"
          >
            <Filter className="h-3 w-3" />
            {showJmesFilter ? 'Hide Filter' : 'Show Filter'}
          </Button>
        </div>

        {showJmesFilter && (
          <div className="space-y-3">
            <div className="relative">
              <Input
                value={filter}
                onChange={(e) => handleFilterChange(e.target.value)}
                placeholder="Enter JMES filter (e.g., locations[?state == 'WA'].name)"
                className="w-full bg-[#141B2B] border-[#2D3B4E] text-slate-200"
              />
              {jmesError && (
                <div className="absolute -bottom-6 left-0 text-xs text-red-400">
                  {jmesError}
                </div>
              )}
            </div>
            <div className="text-xs text-slate-400">
              <p>Examples:</p>
              <ul className="list-disc pl-4 mt-1 space-y-1">
                <li><code className="text-emerald-400">locations[?state == 'WA'].name</code> - Get names of locations in Washington</li>
                <li><code className="text-emerald-400">users[?age {'>'}20]</code> - Filter users older than 20</li>
                <li><code className="text-emerald-400">data.items[*].id</code> - Get all item IDs</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 