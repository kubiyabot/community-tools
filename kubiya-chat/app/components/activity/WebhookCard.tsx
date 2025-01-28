import * as React from 'react';
import { useState } from 'react';
import { format } from 'date-fns';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../ui/tooltip';
import { 
  Webhook as WebhookIcon, 
  Info, 
  MessageSquare, 
  Trash2, 
  Copy, 
  CheckCircle2, 
  Code, 
  Filter, 
  Bot, 
  ExternalLink,
  Loader2,
  PlayCircle,
  Terminal,
  Clipboard,
  ClipboardCheck,
  Search,
  RefreshCw
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ContextVariable } from './ContextVariable';
import { Avatar, AvatarImage, AvatarFallback } from '../ui/avatar';
import { Slack as SlackIcon } from '../icons/slack';
import { Teams as TeamsIcon } from '../icons/teams';
import { toast } from '../ui/use-toast';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger
} from '../ui/alert-dialog';
import { MarkdownWithContext } from './MarkdownWithContext';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../ui/dialog';
import { Textarea } from '../ui/textarea';
import { Label } from '../ui/label';
import { ScrollArea } from '../ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';

const AVATAR_IMAGES = [
  'Accountant.png',
  'Chemist-scientist.png',
  'Postman.png',
  'Security-guard.png',
  'builder-1.png',
  'builder-2.png',
  'builder-3.png',
  'capitan-1.png',
  'capitan-2.png',
  'capitan-3.png'
];

function generateAvatarUrl(teammate: { uuid: string; name: string }) {
  const seed = (teammate.uuid + teammate.name).split('').reduce((acc, char, i) => 
    acc + (char.charCodeAt(0) * (i + 1)), 0);
  const randomIndex = Math.abs(Math.sin(seed) * AVATAR_IMAGES.length) | 0;
  return `/images/avatars/${AVATAR_IMAGES[randomIndex]}`;
}

interface TestWebhookData {
  webhook_id: string;
  data: string;
}

function formatJson(json: string): string {
  try {
    const parsed = JSON.parse(json);
    return JSON.stringify(parsed, null, 2);
  } catch {
    return json;
  }
}

// Add template examples based on source
const WEBHOOK_TEMPLATES = {
  github: {
    push: {
      event: {
        type: "push",
        source: "github",
        data: {
          repository: "user/repo",
          ref: "refs/heads/main",
          commits: [
            {
              id: "abc123",
              message: "Update README.md",
              author: {
                name: "John Doe",
                email: "john@example.com"
              },
              timestamp: new Date().toISOString()
            }
          ]
        }
      }
    },
    pull_request: {
      event: {
        type: "pull_request",
        source: "github",
        data: {
          action: "opened",
          pull_request: {
            title: "Feature: Add new functionality",
            number: 123,
            html_url: "https://github.com/user/repo/pull/123",
            user: {
              login: "johndoe"
            },
            body: "This PR adds exciting new features"
          }
        }
      }
    }
  },
  jira: {
    issue_updated: {
      event: {
        type: "issue_updated",
        source: "jira",
        data: {
          issue: {
            key: "PROJ-123",
            fields: {
              summary: "Bug: Fix login issue",
              status: { name: "In Progress" },
              priority: { name: "High" }
            }
          },
          user: {
            displayName: "John Doe"
          }
        }
      }
    }
  }
};

// Enhanced JSON validation
function validateJson(json: string): { isValid: boolean; error?: string } {
  try {
    const parsed = JSON.parse(json);
    
    // Basic schema validation
    if (!parsed.event) {
      return { isValid: false, error: "Missing required 'event' object" };
    }
    if (!parsed.event.type) {
      return { isValid: false, error: "Missing required 'event.type' field" };
    }
    if (!parsed.event.source) {
      return { isValid: false, error: "Missing required 'event.source' field" };
    }
    if (!parsed.event.data) {
      return { isValid: false, error: "Missing required 'event.data' object" };
    }
    
    return { isValid: true };
  } catch (e) {
    return { 
      isValid: false, 
      error: e instanceof Error ? e.message : 'Invalid JSON format'
    };
  }
}

interface Webhook {
  id: string;
  webhook_url: string;
  source: string;
  event_type: string;
  prompt: string;
  filter?: string;
  created_at?: string;
  communication: {
    method: 'Slack' | 'Teams';
    destination?: string;
  };
  teammate?: TeammateInfo;
  selected_agent?: TeammateInfo;
}

interface TeammateInfo {
  uuid: string;
  name: string;
  avatar?: string;
}

interface WebhookCardProps {
  webhook: Webhook;
  onTest: (id: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

// Add interface for test history
interface TestAttempt {
  timestamp: string;
  request: any;
  response?: any;
  status: 'success' | 'error' | 'pending';
  error?: string;
  duration?: number; // Add duration tracking
}

export const WebhookCard: React.FC<WebhookCardProps> = ({ webhook, onTest, onDelete }) => {
  const [isCopied, setIsCopied] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [testData, setTestData] = useState(() => {
    const templates = WEBHOOK_TEMPLATES[webhook.source as keyof typeof WEBHOOK_TEMPLATES];
    if (templates) {
      const template = templates[webhook.event_type as keyof typeof templates];
      if (template) {
        return JSON.stringify(template, null, 2);
      }
    }
    
    return JSON.stringify({
      event: {
        type: webhook.event_type,
        source: webhook.source,
        data: {
          timestamp: new Date().toISOString(),
          example_field: "value"
        }
      }
    }, null, 2);
  });
  const [jsonError, setJsonError] = useState<string | undefined>();
  const [testHistory, setTestHistory] = useState<TestAttempt[]>([]);
  const [activeTab, setActiveTab] = useState<string>('payload');
  const [showRawResponse, setShowRawResponse] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const handleCopy = async () => {
    await navigator.clipboard.writeText(webhook.webhook_url);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const handleTestDataChange = (value: string) => {
    setTestData(value);
    const { error } = validateJson(value);
    setJsonError(error);
  };

  const handleFormatJson = () => {
    setTestData(formatJson(testData));
  };

  const handleTest = async () => {
    try {
      console.log('Testing webhook:', webhook.id);
      console.log('Test data:', testData);
      
      const startTime = performance.now();
      const attempt: TestAttempt = {
        timestamp: new Date().toISOString(),
        request: JSON.parse(testData),
        status: 'pending'
      };
      
      setIsTesting(true);
      setTestHistory(prev => [attempt, ...prev]);
      
      await onTest(webhook.id);
      
      const duration = performance.now() - startTime;
      
      // Update the attempt with success
      attempt.status = 'success';
      attempt.response = { status: 'Webhook triggered successfully' };
      attempt.duration = Math.round(duration);
      setTestHistory(prev => [
        { ...attempt },
        ...prev.slice(1)
      ]);
      
      console.log('Webhook test successful');
      toast({
        title: "Webhook Tested",
        description: "The webhook was tested successfully.",
      });
    } catch (error) {
      console.error('Webhook test failed:', error);
      
      // Update the attempt with error
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setTestHistory(prev => [
        { ...prev[0], status: 'error', error: errorMessage },
        ...prev.slice(1)
      ]);
      
      toast({
        title: "Error",
        description: "Failed to test webhook. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleDelete = async () => {
    try {
      await onDelete(webhook.id);
      toast({
        title: "Webhook Deleted",
        description: "The webhook was deleted successfully.",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete webhook. Please try again.",
        variant: "destructive",
      });
    }
  };

  const applyTemplate = (templateKey: string) => {
    const templates = WEBHOOK_TEMPLATES[webhook.source as keyof typeof WEBHOOK_TEMPLATES];
    if (templates) {
      const template = templates[templateKey as keyof typeof templates];
      if (template) {
        setTestData(JSON.stringify(template, null, 2));
        setSelectedTemplate(templateKey);
      }
    }
  };

  const handleCopyResponse = (content: any) => {
    navigator.clipboard.writeText(JSON.stringify(content, null, 2));
    toast({
      title: "Copied",
      description: "Content copied to clipboard",
    });
  };

  // Add function to filter test history
  const filteredHistory = testHistory.filter(attempt => {
    if (!searchTerm) return true;
    const searchContent = JSON.stringify(attempt).toLowerCase();
    return searchContent.includes(searchTerm.toLowerCase());
  });

  // Add function to render test history
  const renderTestHistory = () => {
    if (testHistory.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center h-[300px] text-slate-400">
          <Terminal className="h-8 w-8 mb-2 opacity-50" />
          <p>No test attempts yet</p>
          <p className="text-sm opacity-70">Test history will appear here</p>
        </div>
      );
    }

    return filteredHistory.map((attempt, index) => (
      <div
        key={attempt.timestamp}
        className={cn(
          "p-4 rounded-lg border",
          "mb-3 last:mb-0 hover:border-opacity-100",
          attempt.status === 'success' 
            ? "bg-green-500/5 border-green-500/50" 
            : attempt.status === 'error'
            ? "bg-red-500/5 border-red-500/50"
            : "bg-blue-500/5 border-blue-500/50"
        )}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-slate-200">
              {format(new Date(attempt.timestamp), 'MMM d, HH:mm:ss')}
            </span>
            {attempt.duration && (
              <span className="text-xs text-slate-400">
                Duration: {attempt.duration}ms
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className={cn(
                "px-2 py-0.5",
                attempt.status === 'success' && "bg-green-500/10 text-green-300 border-green-500/30",
                attempt.status === 'error' && "bg-red-500/10 text-red-300 border-red-500/30",
                attempt.status === 'pending' && "bg-blue-500/10 text-blue-300 border-blue-500/30"
              )}
            >
              {attempt.status.charAt(0).toUpperCase() + attempt.status.slice(1)}
            </Badge>
          </div>
        </div>
        
        <div className="space-y-3">
          <div className="text-sm">
            <div className="flex items-center justify-between mb-1">
              <div className="font-medium text-slate-200">Request Payload</div>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-xs hover:bg-slate-800"
                onClick={() => handleCopyResponse(attempt.request)}
              >
                <Clipboard className="h-3 w-3 mr-1" />
                Copy
              </Button>
            </div>
            <pre className="bg-slate-800/50 p-3 rounded-md text-xs overflow-x-auto border border-slate-700">
              {JSON.stringify(attempt.request, null, 2)}
            </pre>
          </div>
          
          {attempt.response && (
            <div className="text-sm">
              <div className="flex items-center justify-between mb-1">
                <div className="font-medium text-slate-200">Response</div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2 text-xs hover:bg-slate-800"
                    onClick={() => setShowRawResponse(!showRawResponse)}
                  >
                    <Code className="h-3 w-3 mr-1" />
                    {showRawResponse ? 'Pretty' : 'Raw'}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2 text-xs hover:bg-slate-800"
                    onClick={() => handleCopyResponse(attempt.response)}
                  >
                    <Clipboard className="h-3 w-3 mr-1" />
                    Copy
                  </Button>
                </div>
              </div>
              <pre className="bg-slate-800/50 p-3 rounded-md text-xs overflow-x-auto border border-slate-700">
                {showRawResponse 
                  ? JSON.stringify(attempt.response)
                  : JSON.stringify(attempt.response, null, 2)
                }
              </pre>
            </div>
          )}
          
          {attempt.error && (
            <div className="text-sm">
              <div className="flex items-center justify-between mb-1">
                <div className="font-medium text-red-300">Error Details</div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 px-2 text-xs hover:bg-slate-800"
                  onClick={() => handleCopyResponse(attempt.error)}
                >
                  <Clipboard className="h-3 w-3 mr-1" />
                  Copy
                </Button>
              </div>
              <pre className="bg-red-950/20 text-red-200 p-3 rounded-md text-xs overflow-x-auto border border-red-500/30">
                {attempt.error}
              </pre>
            </div>
          )}
        </div>
      </div>
    ));
  };

  return (
    <div className={cn(
      "p-4 rounded-lg border bg-slate-900/50",
      "border-slate-800/60 hover:border-slate-700/60",
      "transition-all duration-200"
    )}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {/* Header with Source Badge and Teammate */}
          <div className="flex items-center gap-3 mb-3 flex-wrap">
            <Badge variant="outline" className="bg-blue-500/10 text-blue-300 border-blue-500/30">
              <Bot className="h-3 w-3 mr-1" />
              {webhook.source}
            </Badge>
            
            {/* Teammate Info */}
            {(webhook.teammate || webhook.selected_agent) ? (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="flex items-center gap-2 px-2 py-1 rounded-md bg-purple-500/10 border border-purple-500/20">
                      <Avatar className="h-5 w-5">
                        <AvatarImage 
                          src={
                            (webhook.teammate || webhook.selected_agent)?.avatar || 
                            generateAvatarUrl(webhook.teammate || webhook.selected_agent!)
                          } 
                          alt={(webhook.teammate || webhook.selected_agent)?.name} 
                        />
                        <AvatarFallback className="bg-purple-500/20 text-purple-200">
                          {(webhook.teammate || webhook.selected_agent)?.name.charAt(0)}
                        </AvatarFallback>
                      </Avatar>
                      <span className="text-sm text-purple-200">
                        {(webhook.teammate || webhook.selected_agent)?.name}
                      </span>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Handling Teammate</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            ) : (
              <Badge variant="outline" className="bg-red-500/10 text-red-300 border-red-500/30">
                <Bot className="h-3 w-3 mr-1" />
                No Teammate Assigned
              </Badge>
            )}

            {/* Communication Method */}
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Badge variant="outline" className="bg-blue-500/10 text-blue-300 border-blue-500/30">
                    {webhook.communication.method === 'Slack' ? (
                      <SlackIcon className="h-4 w-4 mr-1" />
                    ) : (
                      <TeamsIcon className="h-4 w-4 mr-1" />
                    )}
                    {webhook.communication.destination || 'Default Channel'}
                  </Badge>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Communication Channel</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>

          {/* Webhook Details */}
          <div className="space-y-2">
            {/* Webhook URL */}
            <div className="flex items-center gap-2 text-sm text-slate-300">
              <WebhookIcon className="h-4 w-4 text-blue-400" />
              <code className="px-2 py-0.5 bg-slate-900/50 rounded text-xs font-mono">
                {webhook.webhook_url}
              </code>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCopy}
                className="h-6 px-2 text-xs hover:bg-blue-500/10 hover:text-blue-400"
              >
                {isCopied ? (
                  <CheckCircle2 className="h-3 w-3 text-green-400" />
                ) : (
                  <Copy className="h-3 w-3" />
                )}
              </Button>
            </div>

            {/* Prompt Template with Context Variables */}
            <div className="flex items-start gap-2">
              <Code className="h-4 w-4 text-purple-400 mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <MarkdownWithContext content={webhook.prompt} />
              </div>
            </div>

            {/* Filter */}
            {webhook.filter && (
              <div className="flex items-start gap-2">
                <Filter className="h-4 w-4 text-green-400 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <MarkdownWithContext content={webhook.filter} />
                </div>
              </div>
            )}

            {/* Created At */}
            {webhook.created_at && (
              <div className="flex items-center gap-2 text-xs text-slate-400 mt-4 pt-4 border-t border-slate-800">
                <Info className="h-3.5 w-3.5" />
                <span>Created {format(new Date(webhook.created_at), 'MMM d, yyyy')}</span>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Dialog>
            <DialogTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className={cn(
                  "text-blue-400 hover:text-blue-300",
                  "bg-blue-500/10 hover:bg-blue-500/20"
                )}
                disabled={isTesting}
              >
                {isTesting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <PlayCircle className="h-4 w-4" />
                )}
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[900px] bg-slate-800 border-slate-700">
              <DialogHeader>
                <DialogTitle className="text-xl font-semibold text-slate-100">Test Webhook</DialogTitle>
                <DialogDescription className="text-slate-300">
                  Test your webhook with example data and view test history.
                </DialogDescription>
              </DialogHeader>

              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="w-full bg-slate-900/50 border-b border-slate-700">
                  <TabsTrigger
                    value="payload"
                    className="flex-1 data-[state=active]:bg-slate-800"
                  >
                    <Code className="h-4 w-4 mr-2" />
                    Payload Editor
                  </TabsTrigger>
                  <TabsTrigger
                    value="history"
                    className="flex-1 data-[state=active]:bg-slate-800"
                  >
                    <Terminal className="h-4 w-4 mr-2" />
                    Test History
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="payload" className="mt-4">
                  {/* Template Selection */}
                  {WEBHOOK_TEMPLATES[webhook.source as keyof typeof WEBHOOK_TEMPLATES] && (
                    <div className="flex gap-2 mb-4 items-center">
                      <Label className="text-slate-300 shrink-0">Quick Templates:</Label>
                      <div className="w-full overflow-x-auto">
                        <div className="flex gap-2 pb-2">
                          {Object.keys(WEBHOOK_TEMPLATES[webhook.source as keyof typeof WEBHOOK_TEMPLATES]).map((templateKey) => (
                            <Button
                              key={templateKey}
                              variant={selectedTemplate === templateKey ? "default" : "outline"}
                              size="sm"
                              onClick={() => applyTemplate(templateKey)}
                              className={cn(
                                "capitalize whitespace-nowrap",
                                selectedTemplate === templateKey
                                  ? "bg-blue-500 hover:bg-blue-600"
                                  : "hover:bg-slate-700"
                              )}
                            >
                              {templateKey.replace(/_/g, ' ')}
                            </Button>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  <div className="grid gap-4">
                    <div className="grid gap-2">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="test-data" className="text-slate-200 font-medium">
                          JSON Payload
                        </Label>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleFormatJson}
                          className="h-8 text-blue-400 hover:text-blue-300 hover:bg-blue-500/10"
                        >
                          <Code className="h-4 w-4 mr-2" />
                          Format JSON
                        </Button>
                      </div>
                      <Textarea
                        id="test-data"
                        value={testData}
                        onChange={(e) => handleTestDataChange(e.target.value)}
                        className={cn(
                          "font-mono text-sm bg-slate-900 border-slate-700",
                          "focus-visible:ring-blue-500 focus-visible:ring-offset-slate-800",
                          jsonError && "border-red-500 focus-visible:ring-red-500"
                        )}
                        rows={12}
                      />
                      {jsonError && (
                        <p className="text-sm text-red-400 bg-red-500/10 p-2 rounded border border-red-500/20">
                          <span className="font-semibold">Error:</span> {jsonError}
                        </p>
                      )}
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="history" className="mt-4">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="relative flex-1">
                      <Search className="absolute left-2 top-2.5 h-4 w-4 text-slate-400" />
                      <input
                        type="text"
                        placeholder="Search test history..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className={cn(
                          "w-full pl-8 pr-4 py-2 text-sm",
                          "bg-slate-900 border border-slate-700 rounded-md",
                          "focus:outline-none focus:ring-2 focus:ring-blue-500",
                          "placeholder-slate-400"
                        )}
                      />
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setTestHistory([])}
                      className="text-slate-300 hover:text-slate-200"
                    >
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Clear
                    </Button>
                  </div>
                  <ScrollArea className="h-[400px] pr-4">
                    {renderTestHistory()}
                  </ScrollArea>
                </TabsContent>
              </Tabs>

              <DialogFooter className="mt-4">
                <Button 
                  onClick={handleTest} 
                  disabled={isTesting || !!jsonError}
                  className={cn(
                    "bg-blue-500 hover:bg-blue-600",
                    "text-white font-medium",
                    "disabled:bg-slate-700",
                    "min-w-[140px]"
                  )}
                >
                  {isTesting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Testing...
                    </>
                  ) : (
                    <>
                      <PlayCircle className="mr-2 h-4 w-4" />
                      Test Webhook
                    </>
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className={cn(
                  "text-red-400 hover:text-red-300",
                  "bg-red-500/10 hover:bg-red-500/20"
                )}
                disabled={isDeleting}
              >
                {isDeleting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete Webhook</AlertDialogTitle>
                <AlertDialogDescription>
                  Are you sure you want to delete this webhook? This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleDelete}>Delete</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>
    </div>
  );
}; 