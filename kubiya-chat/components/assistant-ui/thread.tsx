"use client";

import {
  Thread,
  ThreadWelcome,
  Composer,
  type ThreadConfig,
  ThreadPrimitive,
  ComposerPrimitive
} from "@assistant-ui/react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { ArrowDownIcon, SendHorizontalIcon, StopCircleIcon } from "lucide-react";

const MyThreadWelcome = () => {
  return (
    <ThreadWelcome.Root>
      <ThreadWelcome.Center>
        <div className="flex flex-col items-center gap-6">
          <Avatar className="h-16 w-16 ring-2 ring-[#7C3AED]/20">
            <AvatarFallback className="bg-gradient-to-br from-[#7C3AED] to-[#6D28D9] text-white text-xl">K</AvatarFallback>
          </Avatar>
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-semibold text-white">Kubiya Assistant</h2>
            <p className="text-slate-400">How can I help you today?</p>
          </div>
        </div>
      </ThreadWelcome.Center>
      <div className="flex flex-wrap gap-3 justify-center mt-6">
        <Button variant="outline" className="bg-[#1E293B] hover:bg-[#1E293B]/80 border-[#7C3AED]/20 hover:border-[#7C3AED]/40 text-white" onClick={() => {}}>
          Help me with Terraform
        </Button>
        <Button variant="outline" className="bg-[#1E293B] hover:bg-[#1E293B]/80 border-[#7C3AED]/20 hover:border-[#7C3AED]/40 text-white" onClick={() => {}}>
          Show me my K8s clusters
        </Button>
        <Button variant="outline" className="bg-[#1E293B] hover:bg-[#1E293B]/80 border-[#7C3AED]/20 hover:border-[#7C3AED]/40 text-white" onClick={() => {}}>
          Create a new workflow
        </Button>
      </div>
    </ThreadWelcome.Root>
  );
};

const MyComposer = () => {
  return (
    <ComposerPrimitive.Root className="flex w-full items-end rounded-xl border border-[#1E293B] bg-[#0A0F1E] px-3 shadow-lg transition-colors ease-in focus-within:border-[#7C3AED]/30">
      <ComposerPrimitive.Input
        autoFocus
        placeholder="Message Kubiya..."
        rows={1}
        className="max-h-40 flex-grow resize-none border-none bg-transparent px-2 py-4 text-sm text-white placeholder:text-slate-500 outline-none focus:ring-0 disabled:cursor-not-allowed"
      />
      <ThreadPrimitive.If running={false}>
        <ComposerPrimitive.Send asChild>
          <Button size="icon" className="my-2.5 bg-[#7C3AED] hover:bg-[#6D28D9] text-white">
            <SendHorizontalIcon className="h-4 w-4" />
          </Button>
        </ComposerPrimitive.Send>
      </ThreadPrimitive.If>
      <ThreadPrimitive.If running>
        <ComposerPrimitive.Cancel asChild>
          <Button size="icon" variant="destructive" className="my-2.5">
            <StopCircleIcon className="h-4 w-4" />
          </Button>
        </ComposerPrimitive.Cancel>
      </ThreadPrimitive.If>
    </ComposerPrimitive.Root>
  );
};

const MyThread: React.FC<ThreadConfig> = (config) => {
  return (
    <Thread.Root config={config} className="bg-[#0A0F1E]">
      <Thread.Viewport className="flex h-full flex-col items-center overflow-y-auto scroll-smooth bg-inherit px-4 pt-8">
        <MyThreadWelcome />
        <Thread.Messages />
        <div className="min-h-8 flex-grow" />
        <div className="sticky bottom-0 mt-3 flex w-full max-w-2xl flex-col items-center justify-end rounded-t-lg bg-inherit pb-4">
          <Thread.ScrollToBottom asChild>
            <Button variant="outline" size="icon" className="absolute -top-8 rounded-full bg-[#1E293B] border-[#7C3AED]/20 hover:bg-[#1E293B]/80 hover:border-[#7C3AED]/40">
              <ArrowDownIcon className="h-4 w-4" />
            </Button>
          </Thread.ScrollToBottom>
          <MyComposer />
        </div>
      </Thread.Viewport>
    </Thread.Root>
  );
};

export { MyThread as Thread }; 