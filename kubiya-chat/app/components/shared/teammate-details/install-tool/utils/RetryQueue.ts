import { CommunityTool, RetryQueueItem } from "@/app/types/tools";
import { wait } from "./index";

export const MAX_RETRIES = 3;
export const INITIAL_BACKOFF = 2000;

export class RetryQueue {
  private queue: RetryQueueItem[] = [];
  private isProcessing = false;

  add(tool: CommunityTool, error: string): void {
    const existingItem = this.queue.find(item => item.tool.path === tool.path);
    if (existingItem) {
      existingItem.retryCount++;
      existingItem.lastError = error;
    } else {
      this.queue.push({ tool, retryCount: 0, lastError: error });
    }
  }

  async process(processItem: (tool: CommunityTool) => Promise<void>): Promise<void> {
    if (this.isProcessing) return;
    this.isProcessing = true;

    while (this.queue.length > 0) {
      const item = this.queue[0];
      
      if (item.retryCount >= MAX_RETRIES) {
        this.queue.shift();
        continue;
      }

      try {
        const backoff = INITIAL_BACKOFF * Math.pow(2, item.retryCount);
        await wait(backoff);
        await processItem(item.tool);
        this.queue.shift();
      } catch (error) {
        item.retryCount++;
        item.lastError = error instanceof Error ? error.message : 'Unknown error';
        if (item.retryCount >= MAX_RETRIES) {
          this.queue.shift();
        }
      }
    }

    this.isProcessing = false;
  }
} 