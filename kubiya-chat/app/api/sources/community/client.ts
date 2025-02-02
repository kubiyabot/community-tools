import { CommunityTool, GitHubContentsResponse } from './types';
import fs from 'fs/promises';
import path from 'path';
import os from 'os';
import { execSync } from 'child_process';
import { fetchSource } from './utils';
import { NextRequest } from 'next/server';

const KUBIYA_API_URL = process.env.KUBIYA_API_URL || 'https://api.kubiya.ai';
const REPO_URL = 'https://github.com/kubiyabot/community-tools.git';
const REPO_PATH = path.join(os.tmpdir(), 'kubiya-community-tools');

interface ErrorResponse {
  error?: string;
  message?: string;
}

export class CommunityToolsClient {
  private static instance: CommunityToolsClient;
  private cache: Map<string, { data: any; timestamp: number }> = new Map();
  private CACHE_TTL = 5 * 60 * 1000; // 5 minutes
  private isInitializing: boolean = false;
  private initPromise: Promise<void> | null = null;
  private request: NextRequest | undefined;

  private constructor(request?: NextRequest) {
    this.request = request;
  }

  static getInstance(request?: NextRequest): CommunityToolsClient {
    if (!this.instance) {
      this.instance = new CommunityToolsClient(request);
    }
    return this.instance;
  }

  private async ensureRepo() {
    if (this.isInitializing) {
      // Wait for existing initialization
      await this.initPromise;
      return;
    }

    try {
      this.isInitializing = true;
      this.initPromise = (async () => {
        const exists = await fs.access(REPO_PATH).then(() => true).catch(() => false);
        
        if (exists) {
          try {
            // Try to update existing repo
            console.log('Updating community tools repo...');
            execSync('git pull', { cwd: REPO_PATH });
          } catch (error) {
            // If update fails, remove and clone fresh
            console.log('Update failed, re-cloning repo...');
            await fs.rm(REPO_PATH, { recursive: true, force: true });
            execSync(`git clone ${REPO_URL} ${REPO_PATH}`);
          }
        } else {
          // Fresh clone
          console.log('Cloning community tools repo...');
          execSync(`git clone ${REPO_URL} ${REPO_PATH}`);
        }
      })();

      await this.initPromise;
    } catch (error) {
      console.error('Failed to initialize repo:', error);
      throw new Error('Failed to initialize community tools repository');
    } finally {
      this.isInitializing = false;
      this.initPromise = null;
    }
  }

  private async readDir(dirPath: string) {
    try {
      await this.ensureRepo();
      const entries = await fs.readdir(dirPath, { withFileTypes: true });
      
      // Filter for directories that aren't dotfiles and have README.md
      const validDirs = await Promise.all(
        entries
          .filter(entry => 
            entry.isDirectory() && 
            !entry.name.startsWith('.')
          )
          .map(async entry => {
            const fullPath = path.join(dirPath, entry.name);
            try {
              // Check for README.md
              await fs.access(path.join(fullPath, 'README.md'));
              return {
                name: entry.name,
                path: path.relative(REPO_PATH, fullPath),
                type: 'dir'
              };
            } catch {
              return null;
            }
          })
      );

      return validDirs.filter((dir): dir is NonNullable<typeof dir> => dir !== null);
    } catch (error) {
      console.error('Error reading directory:', error);
      throw new Error('Failed to read community tools directory');
    }
  }

  private async loadSource(url: string) {
    try {
      return await fetchSource(url, this.request);
    } catch (error) {
      console.warn('Failed to load source:', error);
      throw error;
    }
  }

  async listTools(): Promise<CommunityTool[]> {
    const cacheKey = 'community-tools-list';
    const cached = this.getCached<CommunityTool[]>(cacheKey);
    
    if (cached) {
      return cached;
    }

    try {
      const contents = await this.readDir(REPO_PATH);
      
      const tools = await Promise.all(
        contents.map(async item => {
          const url = `https://github.com/kubiyabot/community-tools/tree/main/${item.path}`;
          try {
            const data = await this.loadSource(url);
            
            // Ensure we have a valid response format
            const tools = Array.isArray(data.tools) ? data.tools : 
                         Array.isArray(data) ? data : 
                         [];

            return {
              name: item.name,
              path: item.path,
              description: data.description || '',
              tools_count: tools.length,
              loadingState: 'success' as const,
              tools: tools,
              error: undefined
            };
          } catch (error) {
            console.warn(`Failed to load source for ${item.name}:`, error);
            return {
              name: item.name,
              path: item.path,
              description: '',
              tools_count: 0,
              loadingState: 'error' as const,
              tools: [],
              error: error instanceof Error ? error.message : 'Failed to load source'
            };
          }
        })
      ).then(results => results.filter(tool => tool !== null));

      // Only cache if we have valid results
      if (tools.length > 0) {
        this.setCache(cacheKey, tools);
      }

      return tools;
    } catch (error) {
      console.error('Error listing tools:', error);
      
      // Try to return stale cache on error
      const staleCache = this.cache.get(cacheKey);
      if (staleCache?.data) {
        console.log('Returning stale cache due to error');
        return staleCache.data;
      }

      // Return empty array instead of throwing
      return [];
    }
  }

  private getCached<T>(key: string): T | null {
    const cached = this.cache.get(key);
    if (cached && (Date.now() - cached.timestamp) < this.CACHE_TTL) {
      return cached.data as T;
    }
    return null;
  }

  private setCache(key: string, data: any) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  async getToolMetadata(path: string): Promise<any> {
    const url = `https://github.com/kubiyabot/community-tools/tree/main/${path}`;
    return this.loadSource(url);
  }
} 