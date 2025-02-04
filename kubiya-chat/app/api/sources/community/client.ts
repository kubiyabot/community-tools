'use server';

import { GitHubContentsResponse } from './types';
import fs from 'fs/promises';
import path from 'path';
import os from 'os';
import { execSync } from 'child_process';
import { fetchSource } from './utils';
import { NextRequest } from 'next/server';
import { formatDistanceToNow } from 'date-fns';
import { REPO_PATH, REPO_URL, updateRepo } from './git-utils';

const KUBIYA_API_URL = process.env.KUBIYA_API_URL || 'https://api.kubiya.ai';

interface ErrorResponse {
  error?: string;
  message?: string;
}

interface CommitInfo {
  sha: string;
  date: string;
  message: string;
  author: {
    name: string;
    avatar?: string;
  };
}

interface CommunityTool {
  name: string;
  path: string;
  description: string;
  tools_count: number;
  icon_url?: string;
  readme?: string;
  readme_summary?: string;
  tools?: any[];
  isDiscovering?: boolean;
  error?: string;
  lastUpdated?: string;
  stars?: number;
  lastCommit?: CommitInfo;
  contributors_count?: number;
  loadingState: 'idle' | 'loading' | 'success' | 'error';
}

async function readDir(dirPath: string) {
  try {
    await updateRepo();
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

async function getRepoMetadata() {
  try {
    const response = await fetch('https://api.github.com/repos/kubiyabot/community-tools', {
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'kubiya-chat-ui'
      }
    });
    if (!response.ok) throw new Error('Failed to fetch repo metadata');
    return await response.json();
  } catch (error) {
    console.warn('Failed to fetch repo metadata:', error);
    return null;
  }
}

async function getLastCommit(dirPath: string): Promise<CommitInfo | null> {
  try {
    await updateRepo();
    const fullPath = path.join(REPO_PATH, dirPath);
    
    // Get last commit for specific directory
    const lastCommit = execSync(
      `git log -1 --format="%H%n%at%n%s%n%an" -- "${fullPath}"`,
      { cwd: REPO_PATH, encoding: 'utf-8' }
    ).split('\n');

    return {
      sha: lastCommit[0],
      date: new Date(parseInt(lastCommit[1]) * 1000).toISOString(),
      message: lastCommit[2],
      author: {
        name: lastCommit[3]
      }
    };
  } catch (error) {
    console.warn('Failed to get commit info:', error);
    return null;
  }
}

async function getContributors(dirPath: string): Promise<number> {
  try {
    await updateRepo();
    const fullPath = path.join(REPO_PATH, dirPath);
    
    // Get unique contributors count
    const contributors = execSync(
      `git log --format="%ae" -- "${fullPath}" | sort -u | wc -l`,
      { cwd: REPO_PATH, encoding: 'utf-8' }
    );

    return parseInt(contributors.trim());
  } catch (error) {
    console.warn('Failed to get contributors:', error);
    return 0;
  }
}

function generateReadmeSummary(readme: string): string {
  if (!readme) return '';
  
  // Remove markdown headers
  const withoutHeaders = readme.replace(/^#.*$/gm, '').trim();
  
  // Get first two paragraphs
  const paragraphs = withoutHeaders.split('\n\n')
    .filter(p => p.trim().length > 0)
    .slice(0, 2);
  
  // Combine and truncate if too long
  const summary = paragraphs.join('\n\n');
  return summary.length > 300 ? summary.slice(0, 297) + '...' : summary;
}

export async function listTools(request?: NextRequest): Promise<CommunityTool[]> {
  try {
    const contents = await readDir(REPO_PATH);
    const repoMetadata = await getRepoMetadata();
    
    const tools = await Promise.all(
      contents.map(async item => {
        const url = `https://github.com/kubiyabot/community-tools/tree/main/${item.path}`;
        try {
          const data = await fetchSource(url, request);
          const lastCommit = await getLastCommit(item.path);
          const contributors_count = await getContributors(item.path);
          
          // Ensure we have a valid response format
          const tools = Array.isArray(data.tools) ? data.tools : 
                       Array.isArray(data) ? data : 
                       [];

          const readme = await fs.readFile(path.join(REPO_PATH, item.path, 'README.md'), 'utf-8');
          const readme_summary = generateReadmeSummary(readme);

          return {
            name: item.name,
            path: item.path,
            description: readme_summary || data.description || '',
            tools_count: tools.length,
            loadingState: 'success' as const,
            tools: tools,
            readme,
            readme_summary,
            lastCommit: lastCommit || undefined,
            contributors_count,
            stars: repoMetadata?.stargazers_count,
            lastUpdated: lastCommit?.date || repoMetadata?.updated_at,
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

    return tools;
  } catch (error) {
    console.error('Error listing tools:', error);
    return [];
  }
}

export async function getToolMetadata(path: string, request?: NextRequest): Promise<any> {
  const url = `https://github.com/kubiyabot/community-tools/tree/main/${path}`;
  return fetchSource(url, request);
} 