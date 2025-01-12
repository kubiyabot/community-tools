"use client";

import {
  ActionBarPrimitive,
  BranchPickerPrimitive,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  type TextContentPart
} from "@assistant-ui/react";
import type { FC } from "react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  ArrowDownIcon,
  AudioLinesIcon,
  CheckIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CopyIcon,
  PencilIcon,
  RefreshCwIcon,
  SendHorizontalIcon,
  StopCircleIcon,
  CalendarIcon,
  ClipboardCheckIcon,
  WebhookIcon,
  AlertTriangleIcon,
  SlackIcon,
  GitBranchIcon,
  CloudIcon,
  Loader2,
} from "lucide-react";
import { MarkdownText } from "@/components/assistant-ui/markdown-text";
import { TooltipIconButton } from "@/components/assistant-ui/tooltip-icon-button";
import { cn } from "@/lib/utils";

export const MyThread: FC = () => {
  return (
    <ThreadPrimitive.Root className="bg-background h-full">
      <ThreadPrimitive.Viewport className="flex h-full flex-col items-center overflow-y-scroll scroll-smooth bg-inherit px-4 pt-8">
        <MyThreadWelcome />

        <ThreadPrimitive.Messages
          components={{
            UserMessage: MyUserMessage,
            EditComposer: MyEditComposer,
            AssistantMessage: MyAssistantMessage,
          }}
        />

        <div className="min-h-8 flex-grow" />

        <div className="sticky bottom-0 mt-3 flex w-full max-w-2xl flex-col items-center justify-end rounded-t-lg bg-inherit pb-4">
          <MyThreadScrollToBottom />
          <MyComposer />
        </div>
      </ThreadPrimitive.Viewport>
    </ThreadPrimitive.Root>
  );
};

const MyThreadScrollToBottom: FC = () => {
  return (
    <ThreadPrimitive.ScrollToBottom asChild>
      <TooltipIconButton
        tooltip="Scroll to bottom"
        variant="outline"
        className="absolute -top-8 rounded-full disabled:invisible"
      >
        <ArrowDownIcon />
      </TooltipIconButton>
    </ThreadPrimitive.ScrollToBottom>
  );
};

const MyThreadWelcome: FC = () => {
  return (
    <ThreadPrimitive.Empty>
      <div className="flex flex-grow flex-col items-center justify-center space-y-6">
        <div className="relative">
          <Avatar className="h-16 w-16">
            <AvatarFallback className="bg-primary text-primary-foreground text-xl">K</AvatarFallback>
          </Avatar>
          <div className="absolute -bottom-1 -right-1 rounded-full bg-green-500 p-1.5 ring-2 ring-background" />
        </div>
        <div className="text-center space-y-2">
          <p className="text-2xl font-semibold text-primary">Kubiya Assistant</p>
          <p className="text-muted-foreground">I can help you manage tasks, test specifications, and trigger workflows</p>
        </div>
        
        <div className="flex gap-4 p-4 bg-card/50 rounded-lg">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-yellow-500/10 text-yellow-500">
            <SlackIcon className="h-4 w-4" />
            <span className="text-xs font-medium">Slack Disconnected</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-500/10 text-red-500">
            <GitBranchIcon className="h-4 w-4" />
            <span className="text-xs font-medium">Terraform Missing</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 text-green-500">
            <CloudIcon className="h-4 w-4" />
            <span className="text-xs font-medium">K8s Connected</span>
          </div>
        </div>

        <div className="flex flex-wrap gap-3 justify-center">
          <Button 
            variant="outline" 
            className="flex items-center gap-2 hover:bg-primary hover:text-primary-foreground transition-colors"
            onClick={() => {
              const composer = document.querySelector('textarea');
              if (composer) {
                composer.value = "I want to schedule a new task";
                composer.focus();
              }
            }}
          >
            <CalendarIcon className="h-4 w-4" />
            Schedule Task
          </Button>
          <Button 
            variant="outline"
            className="flex items-center gap-2 hover:bg-primary hover:text-primary-foreground transition-colors"
            onClick={() => {
              const composer = document.querySelector('textarea');
              if (composer) {
                composer.value = "Can you help me test this specification";
                composer.focus();
              }
            }}
          >
            <ClipboardCheckIcon className="h-4 w-4" />
            Test Specification
          </Button>
          <Button 
            variant="outline"
            className="flex items-center gap-2 hover:bg-primary hover:text-primary-foreground transition-colors"
            onClick={() => {
              const composer = document.querySelector('textarea');
              if (composer) {
                composer.value = "I need to trigger a webhook";
                composer.focus();
              }
            }}
          >
            <WebhookIcon className="h-4 w-4" />
            Trigger Hook
          </Button>
        </div>
      </div>
    </ThreadPrimitive.Empty>
  );
};

const MyComposer: FC = () => {
  return (
    <ComposerPrimitive.Root className="focus-within:border-primary/20 flex w-full flex-wrap items-end rounded-xl border bg-primary/5 px-3 shadow-md transition-colors ease-in">
      <ComposerPrimitive.Input
        autoFocus
        placeholder="Write a message or choose an action above..."
        rows={1}
        className="placeholder:text-muted-foreground max-h-40 flex-grow resize-none border-none bg-transparent px-2 py-4 text-sm outline-none focus:ring-0 disabled:cursor-not-allowed"
      />
      <ThreadPrimitive.If running={false}>
        <ComposerPrimitive.Send asChild>
          <TooltipIconButton
            tooltip="Send message"
            variant="default"
            className="my-2.5 size-8 p-2 transition-opacity ease-in bg-primary text-primary-foreground hover:bg-primary/90"
          >
            <SendHorizontalIcon />
          </TooltipIconButton>
        </ComposerPrimitive.Send>
      </ThreadPrimitive.If>
      <ThreadPrimitive.If running>
        <ComposerPrimitive.Cancel asChild>
          <TooltipIconButton
            tooltip="Cancel"
            variant="destructive"
            className="my-2.5 size-8 p-2 transition-opacity ease-in"
          >
            <CircleStopIcon />
          </TooltipIconButton>
        </ComposerPrimitive.Cancel>
      </ThreadPrimitive.If>
    </ComposerPrimitive.Root>
  );
};

const MyUserMessage: FC = () => {
  return (
    <MessagePrimitive.Root className="grid w-full max-w-2xl auto-rows-auto grid-cols-[minmax(72px,1fr)_auto] gap-y-2 py-4">
      <MyUserActionBar />

      <div className="bg-primary/10 text-foreground col-start-2 row-start-1 max-w-xl break-words rounded-2xl px-5 py-3 shadow-sm">
        <MessagePrimitive.Content components={{ Text: MarkdownText }} />
      </div>

      <MyBranchPicker className="col-span-full col-start-1 row-start-2 -mr-1 justify-end" />
    </MessagePrimitive.Root>
  );
};

const MyUserActionBar: FC = () => {
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      className="col-start-1 mr-3 mt-2.5 flex flex-col items-end"
    >
      <ActionBarPrimitive.Edit asChild>
        <TooltipIconButton tooltip="Edit">
          <PencilIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.Edit>
    </ActionBarPrimitive.Root>
  );
};

const MyEditComposer: FC = () => {
  return (
    <ComposerPrimitive.Root className="bg-muted my-4 flex w-full max-w-2xl flex-col gap-2 rounded-xl">
      <ComposerPrimitive.Input className="text-foreground flex h-8 w-full resize-none border-none bg-transparent p-4 pb-0 outline-none focus:ring-0" />

      <div className="mx-3 mb-3 flex items-center justify-center gap-2 self-end">
        <ComposerPrimitive.Cancel asChild>
          <Button variant="ghost">Cancel</Button>
        </ComposerPrimitive.Cancel>
        <ComposerPrimitive.Send asChild>
          <Button>Send</Button>
        </ComposerPrimitive.Send>
      </div>
    </ComposerPrimitive.Root>
  );
};

const ToolPreview: FC<{
  name: string;
  args?: Record<string, unknown>;
  status: "running" | "complete" | "error";
  output?: string;
}> = ({ name, args, status, output }) => {
  return (
    <div className="rounded-lg border border-primary/10 bg-primary/5 overflow-hidden">
      <div className="flex items-center gap-2 border-b border-primary/10 bg-primary/10 px-4 py-2">
        <div className="flex items-center gap-2">
          {status === "running" && <Loader2 className="h-4 w-4 animate-spin text-primary" />}
          {status === "complete" && <CheckIcon className="h-4 w-4 text-green-500" />}
          {status === "error" && <AlertTriangleIcon className="h-4 w-4 text-red-500" />}
        </div>
        <div className="flex-1">
          <p className="font-medium text-sm">{name}</p>
          {args && (
            <p className="text-xs text-muted-foreground">
              {Object.entries(args).map(([key, value]) => `${key}: ${value}`).join(", ")}
            </p>
          )}
        </div>
      </div>
      {output && (
        <div className="p-4 text-sm font-mono overflow-x-auto">
          {output}
        </div>
      )}
    </div>
  );
};

const MyAssistantMessage: FC = () => {
  return (
    <MessagePrimitive.Root className="relative grid w-full max-w-2xl grid-cols-[auto_auto_1fr] grid-rows-[auto_1fr] py-4">
      <Avatar className="col-start-1 row-span-full row-start-1 mr-4">
        <AvatarFallback className="bg-primary text-primary-foreground">K</AvatarFallback>
      </Avatar>

      <div className="text-foreground col-span-2 col-start-2 row-start-1 my-1.5 max-w-xl break-words leading-7 bg-primary/5 rounded-lg p-4 shadow-sm">
        <MessagePrimitive.Content 
          components={{ 
            Text: (props: TextContentPart) => {
              // Handle tool execution messages
              if (props.text.includes('Tool:') || props.text.includes('🔧 Executing:')) {
                try {
                  let toolName = '';
                  let toolArgs = {};
                  let isComplete = false;
                  let output = '';

                  if (props.text.includes('🔧 Executing:')) {
                    toolName = props.text.replace('🔧 Executing: ', '');
                  } else {
                    const lines = props.text.split('\n');
                    toolName = lines[1]?.replace('Tool:', '')?.trim() || '';
                    const argsLine = lines.find(line => line.includes('Arguments:'));
                    if (argsLine) {
                      const argsJson = argsLine.replace('Arguments:', '').trim();
                      toolArgs = JSON.parse(argsJson);
                    }
                    output = lines.slice(3).join('\n');
                    isComplete = output.length > 0;
                  }

                  return (
                    <ToolPreview
                      name={toolName}
                      args={toolArgs}
                      status={isComplete ? "complete" : "running"}
                      output={output}
                    />
                  );
                } catch (e) {
                  console.error('Error parsing tool message:', e);
                }
              }

              // Handle warnings and errors
              if (props.text.toLowerCase().includes('warning:') || props.text.toLowerCase().includes('error:')) {
                const isWarning = props.text.toLowerCase().includes('warning:');
                const isError = props.text.toLowerCase().includes('error:');
                
                return (
                  <div className={cn(
                    "rounded-lg p-3 mb-4 flex items-center gap-3",
                    isWarning ? "bg-yellow-500/10 text-yellow-500" : 
                    isError ? "bg-red-500/10 text-red-500" : 
                    "bg-blue-500/10 text-blue-500"
                  )}>
                    <AlertTriangleIcon className="h-5 w-5 flex-shrink-0" />
                    <span className="text-sm font-normal">{props.text}</span>
                  </div>
                );
              }

              // Regular text
              return <pre className="whitespace-pre-wrap font-normal text-foreground">{props.text}</pre>;
            }
          }} 
        />
      </div>

      <MyAssistantActionBar />
      <MyBranchPicker className="col-start-2 row-start-2 -ml-2 mr-2" />
    </MessagePrimitive.Root>
  );
};

const MyAssistantActionBar: FC = () => {
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      autohideFloat="single-branch"
      className="text-muted-foreground data-[floating]:bg-background col-start-3 row-start-2 -ml-1 flex gap-1 data-[floating]:absolute data-[floating]:rounded-md data-[floating]:border data-[floating]:p-1 data-[floating]:shadow-sm"
    >
      <MessagePrimitive.If speaking={false}>
        <ActionBarPrimitive.Speak asChild>
          <TooltipIconButton tooltip="Read aloud">
            <AudioLinesIcon />
          </TooltipIconButton>
        </ActionBarPrimitive.Speak>
      </MessagePrimitive.If>
      <MessagePrimitive.If speaking>
        <ActionBarPrimitive.StopSpeaking asChild>
          <TooltipIconButton tooltip="Stop">
            <StopCircleIcon />
          </TooltipIconButton>
        </ActionBarPrimitive.StopSpeaking>
      </MessagePrimitive.If>
      <ActionBarPrimitive.Copy asChild>
        <TooltipIconButton tooltip="Copy">
          <MessagePrimitive.If copied>
            <CheckIcon />
          </MessagePrimitive.If>
          <MessagePrimitive.If copied={false}>
            <CopyIcon />
          </MessagePrimitive.If>
        </TooltipIconButton>
      </ActionBarPrimitive.Copy>
      <ActionBarPrimitive.Reload asChild>
        <TooltipIconButton tooltip="Refresh">
          <RefreshCwIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.Reload>
    </ActionBarPrimitive.Root>
  );
};

const MyBranchPicker: FC<BranchPickerPrimitive.Root.Props> = ({
  className,
  ...rest
}) => {
  return (
    <BranchPickerPrimitive.Root
      hideWhenSingleBranch
      className={cn(
        "text-muted-foreground inline-flex items-center text-xs",
        className,
      )}
      {...rest}
    >
      <BranchPickerPrimitive.Previous asChild>
        <TooltipIconButton tooltip="Previous">
          <ChevronLeftIcon />
        </TooltipIconButton>
      </BranchPickerPrimitive.Previous>
      <span className="font-medium">
        <BranchPickerPrimitive.Number /> / <BranchPickerPrimitive.Count />
      </span>
      <BranchPickerPrimitive.Next asChild>
        <TooltipIconButton tooltip="Next">
          <ChevronRightIcon />
        </TooltipIconButton>
      </BranchPickerPrimitive.Next>
    </BranchPickerPrimitive.Root>
  );
};

const CircleStopIcon = () => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 16 16"
      fill="currentColor"
      width="16"
      height="16"
    >
      <rect width="10" height="10" x="3" y="3" rx="2" />
    </svg>
  );
};
