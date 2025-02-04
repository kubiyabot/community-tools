import { NextRequest, NextResponse } from 'next/server';
import { readdir, readFile, access } from 'fs/promises';
import { join, relative } from 'path';
import { execSync } from 'child_process';
import { REPO_PATH, updateRepo } from './git-utils';
import { fetchSource } from './utils';
import { CommunityTool, CommitInfo } from './types';

async function readDir(dirPath: string) {
  try {
    await updateRepo();
    const entries = await readdir(dirPath, { withFileTypes: true });
    
    const validDirs = await Promise.all(
      entries
        .filter(entry => 
          entry.isDirectory() && 
          !entry.name.startsWith('.')
        )
        .map(async entry => {
          const fullPath = join(dirPath, entry.name);
          try {
            await access(join(fullPath, 'README.md'));
            return {
              name: entry.name,
              path: relative(REPO_PATH, fullPath),
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
    const fullPath = join(REPO_PATH, dirPath);
    
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
    const fullPath = join(REPO_PATH, dirPath);
    
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
  
  const withoutHeaders = readme.replace(/^#.*$/gm, '').trim();
  const paragraphs = withoutHeaders.split('\n\n')
    .filter(p => p.trim().length > 0)
    .slice(0, 2);
  
  const summary = paragraphs.join('\n\n');
  return summary.length > 300 ? summary.slice(0, 297) + '...' : summary;
}

export async function GET(request: NextRequest) {
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
          
          const tools = Array.isArray(data.tools) ? data.tools : 
                       Array.isArray(data) ? data : 
                       [];

          const readme = await readFile(join(REPO_PATH, item.path, 'README.md'), 'utf-8');
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

    return NextResponse.json(tools);
  } catch (error) {
    console.error('Error listing tools:', error);
    return NextResponse.json({ error: 'Failed to list tools' }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const { path } = await request.json();
    if (!path) {
      return NextResponse.json({ error: 'Path is required' }, { status: 400 });
    }
    
    const url = `https://github.com/kubiyabot/community-tools/tree/main/${path}`;
    const data = await fetchSource(url, request);
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error getting tool metadata:', error);
    return NextResponse.json({ error: 'Failed to get tool metadata' }, { status: 500 });
  }
} 