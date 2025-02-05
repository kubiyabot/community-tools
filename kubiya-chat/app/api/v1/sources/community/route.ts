import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@auth0/nextjs-auth0/edge';
import { kv } from '@vercel/kv';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

interface CommunityTool {
  name: string;
  path: string;
  description: string;
  tools_count: number;
  icon_url?: string;
  readme?: string;
  tools: CommunityTool[];
  isDiscovering: boolean;
  error?: string;
  lastUpdated?: string;
  stars?: number;
  source?: {
    name: string;
    url: string;
    metadata: {
      git_branch: string;
      last_updated: string;
    };
  };
  lastCommit?: {
    sha: string;
    date: string;
    message: string;
    author: {
      name: string;
      avatar?: string;
    };
  };
  id: string;
  type: string;
  loadingState: 'idle' | 'loading' | 'error' | 'success';
}

const CACHE_KEY = 'community_tools_cache';
const CACHE_TTL = 60 * 5; // 5 minutes in seconds
const STALE_TTL = 60 * 60; // 1 hour in seconds for stale-while-revalidate

const TOOL_DESCRIPTIONS: Record<string, string> = {
  aws: 'AWS tools for cloud resource management',
  azure: 'Azure cloud tools and automation',
  kubernetes: 'Kubernetes tools for cluster management',
  github: 'GitHub tools for repository and workflow management',
  gitlab: 'GitLab tools for repository and CI/CD management',
  jira: 'Jira tools for issue and project management',
  slack: 'Slack tools for messaging and notifications',
  terraform: 'Infrastructure as Code with Terraform',
  okta: 'Okta identity and access management',
  docker: 'Docker container management tools',
  databricks: 'Databricks data platform tools',
  gcp: 'Google Cloud Platform tools',
  jenkins: 'Jenkins CI/CD automation tools',
  argocd: 'ArgoCD GitOps deployment tools',
  bitbucket: 'Bitbucket repository management'
};

const TOOL_ICONS: Record<string, string> = {
  aws: 'https://www.pngplay.com/wp-content/uploads/3/Amazon-Web-Services-AWS-Logo-Transparent-PNG.png',
  azure: 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Microsoft_Azure.svg/150px-Microsoft_Azure.svg.png',
  kubernetes: 'https://kubernetes.io/images/favicon.png',
  github: 'https://cdn-icons-png.flaticon.com/512/25/25231.png',
  gitlab: 'https://about.gitlab.com/images/press/logo/png/gitlab-icon-rgb.png',
  jira: 'https://wac-cdn.atlassian.com/assets/img/favicons/atlassian/favicon.png',
  slack: 'https://a.slack-edge.com/80588/marketing/img/meta/favicon-32.png',
  terraform: 'https://th.bing.com/th/id/OIP.R8tGUJWfp63WrJ4c_lteRQHaHa?rs=1&pid=ImgDetMain',
  okta: 'https://logos-world.net/wp-content/uploads/2021/04/Okta-Emblem.png',
  docker: 'https://cdn3.iconfinder.com/data/icons/logos-and-brands-adobe/512/97_Docker-1024.png',
  databricks: 'https://th.bing.com/th/id/OIP.3hZukm_S83N97DXM2v8xyQHaHa?rs=1&pid=ImgDetMain',
  gcp: 'https://static-00.iconduck.com/assets.00/google-cloud-platform-icon-1024x823-mrdn81d1.png',
  jenkins: 'https://th.bing.com/th/id/OIP.ppwanwyvxo7Y2Jit0udbBQHaIl?rs=1&pid=ImgDetMain',
  argocd: 'https://redhat-scholars.github.io/argocd-tutorial/argocd-tutorial/_images/argocd-logo.png',
  bitbucket: 'https://static-00.iconduck.com/assets.00/bitbucket-icon-2048x2048-5a4hz8hr.png'
};

// Keywords for partial matching
const TOOL_KEYWORDS: Record<string, string[]> = {
  aws: ['aws', 'amazon', 'amazon web services'],
  azure: ['azure', 'microsoft azure', 'microsoft cloud'],
  kubernetes: ['kubernetes', 'k8s', 'kube'],
  github: ['github', 'gh'],
  gitlab: ['gitlab', 'gl'],
  jira: ['jira', 'atlassian'],
  slack: ['slack', 'slackbot'],
  terraform: ['terraform', 'tf', 'hashicorp'],
  okta: ['okta', 'identity'],
  docker: ['docker', 'container'],
  databricks: ['databricks', 'spark'],
  gcp: ['gcp', 'google cloud', 'google cloud platform'],
  jenkins: ['jenkins', 'jenkinsfile'],
  argocd: ['argocd', 'argo', 'gitops'],
  bitbucket: ['bitbucket', 'bb']
};

function findMatchingTool(name: string, readme: string = ''): string | null {
  name = name.toLowerCase();
  readme = readme.toLowerCase();
  
  // First try exact matches
  if (TOOL_ICONS[name]) {
    return name;
  }

  // Then try keyword matches in name and readme
  for (const [tool, keywords] of Object.entries(TOOL_KEYWORDS)) {
    if (keywords.some(keyword => 
      name.includes(keyword) || 
      readme.includes(keyword)
    )) {
      return tool;
    }
  }

  return null;
}

function extractSummaryFromReadme(readme: string): string {
  if (!readme) return '';
  
  // Try to get the first paragraph after removing any headers
  const lines = readme.split('\n')
    .filter(line => !line.startsWith('#'))
    .map(line => line.trim())
    .filter(Boolean);

  // Get first non-empty paragraph
  const firstParagraph = lines.find(line => line.length > 30);
  return firstParagraph || '';
}

const GITHUB_API_URL = 'https://api.github.com';
const REPO_PATH = 'kubiyabot/community-tools';

interface CacheEntry {
  data: CommunityTool[];
  timestamp: number;
}

interface CacheResult {
  data: CommunityTool[];
  fresh: boolean;
}

async function getCachedTools(): Promise<CacheResult | null> {
  try {
    const cached = await kv.get<CacheEntry>(CACHE_KEY);
    if (cached && typeof cached === 'object' && 'data' in cached && 'timestamp' in cached) {
      const age = (Date.now() - cached.timestamp) / 1000; // age in seconds
      
      if (age < CACHE_TTL) {
        // Cache is fresh
        return { data: cached.data, fresh: true };
      } else if (age < STALE_TTL) {
        // Cache is stale but usable
        return { data: cached.data, fresh: false };
      }
    }
    return null;
  } catch (error) {
    console.warn('Cache read error:', error);
    return null;
  }
}

async function setCachedTools(tools: CommunityTool[]): Promise<void> {
  try {
    const cacheEntry: CacheEntry = {
      data: tools,
      timestamp: Date.now()
    };
    
    await kv.set(CACHE_KEY, cacheEntry, {
      ex: STALE_TTL // Set expiration for stale TTL
    });
  } catch (error) {
    console.warn('Cache write error:', error);
  }
}

async function fetchWithGitHub(url: string, headers: Record<string, string> = {}) {
  const response = await fetch(url, {
    headers: {
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'kubiya-chat-ui',
      ...headers
    }
  });

  if (response.status === 403 && response.headers.get('X-RateLimit-Remaining') === '0') {
    const resetTime = response.headers.get('X-RateLimit-Reset');
    const resetDate = resetTime ? new Date(parseInt(resetTime) * 1000) : new Date();
    throw new Error(`GitHub API rate limit exceeded. Resets at ${resetDate.toLocaleString()}`);
  }

  if (response.status === 404) {
    throw new Error('Resource not found on GitHub');
  }

  if (!response.ok) {
    const error = await response.text().catch(() => 'Unknown error');
    throw new Error(`GitHub API error: ${error}`);
  }

  return response;
}

export async function GET(req: NextRequest) {
  try {
    const res = NextResponse.next();
    const session = await getSession(req, res);
    
    if (!session?.idToken) {
      return NextResponse.json({ 
        error: 'Not authenticated',
        details: 'No ID token found'
      }, { status: 401 });
    }

    // Check if this is a force refresh request
    const { searchParams } = new URL(req.url);
    const forceRefresh = searchParams.get('refresh') === 'true';

    let cachedTools = null;
    // Check cache first (unless force refresh)
    if (!forceRefresh) {
      cachedTools = await getCachedTools();
      if (cachedTools && Array.isArray(cachedTools.data)) {
        return NextResponse.json(cachedTools.data, {
          headers: {
            'Cache-Control': cachedTools.fresh 
              ? `public, max-age=${CACHE_TTL}, stale-while-revalidate=${STALE_TTL - CACHE_TTL}`
              : 'public, max-age=0, must-revalidate',
            'X-Cache': cachedTools.fresh ? 'HIT' : 'STALE'
          }
        });
      }
    }

    // If no cache or stale, fetch fresh data
    let contentsResponse;
    try {
      contentsResponse = await fetchWithGitHub(`${GITHUB_API_URL}/repos/${REPO_PATH}/contents`);
    } catch (error) {
      console.error('Failed to fetch contents:', error);
      
      // If we have stale data, return it on error
      if (cachedTools && Array.isArray(cachedTools.data)) {
        return NextResponse.json(cachedTools.data, {
          headers: {
            'Cache-Control': 'public, max-age=0, must-revalidate',
            'X-Cache': 'STALE-ON-ERROR'
          }
        });
      }
      
      return NextResponse.json({
        error: 'Failed to fetch community tools directory',
        details: error instanceof Error ? error.message : 'Unknown error'
      }, { status: 500 });
    }

    const contents = await contentsResponse.json();
    
    if (!Array.isArray(contents)) {
      // Try to use stale data if available
      if (cachedTools && Array.isArray(cachedTools.data)) {
        return NextResponse.json(cachedTools.data, {
          headers: {
            'Cache-Control': 'public, max-age=0, must-revalidate',
            'X-Cache': 'STALE-ON-ERROR'
          }
        });
      }
      
      return NextResponse.json({
        error: 'Invalid response format',
        details: 'Expected an array of directory contents'
      }, { status: 500 });
    }

    // Filter directories and exclude dotfiles
    const toolDirs = contents.filter(item => 
      item.type === 'dir' && !item.name.startsWith('.')
    );

    // Get repository info with error handling
    let repoInfo = null;
    try {
      const repoResponse = await fetchWithGitHub(`${GITHUB_API_URL}/repos/${REPO_PATH}`);
      repoInfo = await repoResponse.json();
    } catch (error) {
      console.warn('Failed to fetch repo info:', error);
      // Continue without repo info
    }

    // Process each directory in parallel with error handling
    const tools = await Promise.all(
      toolDirs.map(async (dir) => {
        try {
          let readme = '';
          try {
            const readmeResponse = await fetchWithGitHub(
              `${GITHUB_API_URL}/repos/${REPO_PATH}/contents/${dir.path}/README.md`
            );
            const readmeData = await readmeResponse.json();
            readme = readmeData.content ? atob(readmeData.content) : '';
          } catch (error) {
            console.warn(`Failed to fetch README for ${dir.name}:`, error);
          }

          const dirName = dir.name.toLowerCase();
          const matchedTool = findMatchingTool(dirName, readme);
          const summary = extractSummaryFromReadme(readme);

          return {
            name: dir.name,
            path: dir.path,
            description: summary || (matchedTool ? TOOL_DESCRIPTIONS[matchedTool] : `Tools for ${dir.name}`),
            tools_count: 0,
            icon_url: matchedTool ? TOOL_ICONS[matchedTool] : '',
            readme,
            id: dir.name,
            type: 'community',
            isDiscovering: false,
            loadingState: 'idle' as const,
            lastUpdated: repoInfo?.updated_at,
            stars: repoInfo?.stargazers_count,
            source: {
              name: dir.name,
              url: `${GITHUB_API_URL}/repos/${REPO_PATH}/contents/${dir.path}`,
              metadata: {
                git_branch: 'main',
                last_updated: repoInfo?.updated_at
              }
            },
            lastCommit: repoInfo?.commit ? {
              sha: repoInfo.commit.sha,
              date: repoInfo.updated_at,
              message: repoInfo.commit.message,
              author: {
                name: repoInfo.commit.author?.name || 'Unknown',
                avatar: repoInfo.commit.author?.avatar_url
              }
            } : undefined,
            tools: []
          };
        } catch (error) {
          console.error(`Error processing ${dir.name}:`, error);
          const dirName = dir.name.toLowerCase();
          return {
            name: dir.name,
            path: dir.path,
            description: TOOL_DESCRIPTIONS[dirName] || `Tools for ${dir.name}`,
            tools_count: 0,
            icon_url: TOOL_ICONS[dirName] || '',
            id: dir.name,
            type: 'community',
            isDiscovering: false,
            loadingState: 'idle' as const,
            source: {
              name: dir.name,
              url: `${GITHUB_API_URL}/repos/${REPO_PATH}/contents/${dir.path}`,
              metadata: {
                git_branch: 'main',
                last_updated: repoInfo?.updated_at
              }
            },
            lastCommit: repoInfo?.commit ? {
              sha: repoInfo.commit.sha,
              date: repoInfo.updated_at,
              message: repoInfo.commit.message,
              author: {
                name: repoInfo.commit.author?.name || 'Unknown',
                avatar: repoInfo.commit.author?.avatar_url
              }
            } : undefined,
            tools: []
          };
        }
      })
    );

    // Filter out any null results from failed processing
    const validTools = tools.filter(Boolean);

    // Cache the valid tools
    await setCachedTools(validTools);

    return NextResponse.json(validTools, {
      headers: {
        'Cache-Control': `public, max-age=${CACHE_TTL}, stale-while-revalidate=${STALE_TTL - CACHE_TTL}`,
        'X-Cache': 'MISS'
      }
    });
  } catch (error) {
    console.error('Error fetching community tools:', error);
    
    // Try to use stale data on error
    const cachedTools = await getCachedTools();
    if (cachedTools && Array.isArray(cachedTools.data)) {
      return NextResponse.json(cachedTools.data, {
        headers: {
          'Cache-Control': 'public, max-age=0, must-revalidate',
          'X-Cache': 'STALE-ON-ERROR'
        }
      });
    }
    
    return NextResponse.json({ 
      error: 'Failed to fetch community tools',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
} 