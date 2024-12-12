from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

repo_stats = GitHubCliTool(
    name="github_repo_stats",
    description="Get key repository statistics",
    content="""
#!/bin/bash
set -euo pipefail

echo "📊 Analyzing repository: $repo"

# Get repository info (focused metrics)
echo "🔍 Fetching repository information..."
REPO_INFO=$(gh api "repos/$repo" --jq '{
    stars: .stargazers_count,
    forks: .forks_count,
    open_issues: .open_issues_count,
    language: .language,
    updated_at: .updated_at,
    license: .license.name
}' || echo '{}')

# Get recent contributor stats (top 3) with error handling
echo "👥 Analyzing recent contributors..."
CONTRIB_STATS=$(gh api "repos/$repo/stats/contributors" --jq 'if . == null then 
    []
else
    map({
        author: .author.login,
        total_commits: .total,
        recent_commits: ([.weeks[-4:][].c] | add)
    })
    | sort_by(-.recent_commits)
    | .[0:3]
end' || echo '[]')

# Format output with error handling
if [ "$format" = "json" ]; then
    jq -n --argjson repo "$REPO_INFO" \
          --argjson contribs "$CONTRIB_STATS" \
        '{
            repository: $repo,
            top_contributors: ($contribs | if . == null then [] else . end)
        }'
else
    echo "=== Repository Overview ==="
    if [ "$REPO_INFO" != "{}" ]; then
        echo "$REPO_INFO" | jq -r '
            "⭐ Stars: \(.stars // 0)",
            "🔱 Forks: \(.forks // 0)",
            "❗ Open Issues: \(.open_issues // 0)",
            "💻 Main Language: \(.language // "Unknown")",
            "🔄 Last Updated: \(.updated_at | fromdate | strftime("%Y-%m-%d"))",
            "📜 License: \(.license // "None")"
        '
    else
        echo "❌ Could not fetch repository information"
    fi
    
    echo -e "\\n=== Top Recent Contributors ==="
    if [ "$CONTRIB_STATS" != "[]" ]; then
        echo "$CONTRIB_STATS" | jq -r '.[] |
            "👤 \(.author):\\n   Recent Commits: \(.recent_commits // 0) (Total: \(.total_commits // 0))"
        '
    else
        echo "ℹ️  No contributor data available"
    fi
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="format", type="str", description="Output format (text/json)", required=False, default="text"),
    ],
)

security_analysis = GitHubCliTool(
    name="github_security_analysis",
    description="Get recent security alerts and vulnerabilities",
    content="""
#!/bin/bash
set -euo pipefail

echo "🔒 Analyzing security for: $repo"
LIMIT="${limit:-5}"  # Default to 5 alerts if not specified

# Get recent security alerts
echo "🔍 Fetching recent security alerts..."
ALERTS=$(gh api "repos/$repo/security-alerts?per_page=$LIMIT" --jq '[
    .[] | {
        severity: .severity,
        state: .state,
        summary: .security_advisory.summary,
        created: .created_at
    }
]')

# Get recent dependabot alerts
echo "📦 Checking recent vulnerabilities..."
DEPENDABOT=$(gh api "repos/$repo/dependabot/alerts?per_page=$LIMIT" --jq '[
    .[] | {
        severity: .severity,
        state: .state,
        package: .dependency.package.name,
        manifest: .dependency.manifest_path
    }
]')

# Format output
if [ "$format" = "json" ]; then
    jq -n --argjson alerts "$ALERTS" \
          --argjson dependabot "$DEPENDABOT" \
        '{
            security_alerts: $alerts,
            dependency_alerts: $dependabot
        }'
else
    echo "=== Recent Security Alerts ==="
    echo "$ALERTS" | jq -r '.[] |
        "❗ [\(.severity)] \(.summary)\\n   Status: \(.state)\\n   Created: \(.created)\\n"
    '
    
    echo "=== Recent Dependency Alerts ==="
    echo "$DEPENDABOT" | jq -r '.[] |
        "⚠️  [\(.severity)] \(.package)\\n   In: \(.manifest)\\n   Status: \(.state)\\n"
    '
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="limit", type="str", description="Number of alerts to show (default: 5)", required=False, default="5"),
        Arg(name="format", type="str", description="Output format (text/json)", required=False, default="text"),
    ],
)

commit_history = GitHubCliTool(
    name="github_commit_history",
    description="Analyze recent commit history and patterns",
    content="""
#!/bin/bash
set -euo pipefail

echo "📜 Analyzing commit history for: $repo"
LIMIT="${limit:-5}"  # Default to 5 commits if not specified

# Get recent commits (limited)
echo "🔍 Fetching recent commits..."
COMMITS=$(gh api "repos/$repo/commits?per_page=$LIMIT" --jq '[
    .[] | {
        sha: .sha[0:7],  # Short SHA
        author: .author.login,
        date: .commit.author.date,
        message: (.commit.message | split("\\n")[0]),  # Just first line
        changes: {
            additions: .stats.additions,
            deletions: .stats.deletions
        }
    }
]')

# Get recent activity (last 4 weeks)
echo "📊 Analyzing recent activity..."
ACTIVITY=$(gh api "repos/$repo/stats/commit_activity" --jq '{
    last_month: ([.[-4:] | .[] | .total] | add),
    last_week: .[-1].total,
    by_day: .[-1].days
}')

# Format output
if [ "$format" = "json" ]; then
    jq -n --argjson commits "$COMMITS" \
          --argjson activity "$ACTIVITY" \
        '{
            recent_commits: $commits,
            recent_activity: $activity
        }'
else
    echo "=== Recent Commits ==="
    echo "$COMMITS" | jq -r '.[] |
        "🔨 \(.date | fromdate | strftime("%Y-%m-%d")):\\n   By: \(.author)\\n   SHA: \(.sha)\\n   Message: \(.message)\\n   Changes: +\(.changes.additions)/-\(.changes.deletions)\\n"
    '
    
    echo "=== Recent Activity ==="
    echo "$ACTIVITY" | jq -r '
        "📊 Last Month: \(.last_month) commits\\n" +
        "📈 Last Week: \(.last_week) commits\\n" +
        "📅 Last Week by Day (Sun-Sat):\\n   " + 
        (.by_day | map(tostring) | join(" "))
    '
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="limit", type="str", description="Number of commits to show (default: 5)", required=False, default="5"),
        Arg(name="format", type="str", description="Output format (text/json)", required=False, default="text"),
    ],
)

workflow_analytics = GitHubCliTool(
    name="github_workflow_analytics",
    description="Get GitHub Actions workflow statistics and insights",
    content="""
#!/bin/bash
set -euo pipefail

echo "📊 Analyzing GitHub Actions for: $repo"
DAYS="${days:-7}"  # Default to last 7 days
LIMIT="${limit:-50}"  # Default to 50 runs

# Get workflow runs with error handling
echo "🔍 Fetching workflow runs..."
RUNS=$(gh run list \
    --repo "$repo" \
    --limit "$LIMIT" \
    --json "conclusion,createdAt,event,headBranch,name,startedAt,status,updatedAt,url,displayTitle" || echo '[]')

# Analyze the runs with null checks
echo "📈 Analyzing workflow performance..."
ANALYSIS=$(echo "$RUNS" | jq '
    def safe_date_diff(start; end):
        if (start != null and end != null) then
            ((end | fromdateiso8601) - (start | fromdateiso8601)) / 60
        else 0 end;

    def safe_success_rate(arr):
        if (length > 0) then
            (([arr[] | select(.conclusion == "success")] | length) * 100.0 / length)
        else 0 end;

    def safe_avg(arr):
        if (length > 0) then (add / length) else 0 end;

    {
        summary: {
            total_runs: length,
            success_rate: safe_success_rate(.),
            avg_duration_minutes: ([.[] | safe_date_diff(.startedAt; .updatedAt)] | safe_avg)
        },
        status_breakdown: (
            group_by(.conclusion // "pending") | 
            map({
                status: .[0].conclusion // "pending",
                count: length,
                percentage: (length * 100.0 / ($RUNS | length))
            })
        ),
        by_workflow: (
            group_by(.name // "unknown") | 
            map({
                name: (.[0].name // "unknown"),
                runs: length,
                success_rate: safe_success_rate(.),
                avg_duration: ([.[] | safe_date_diff(.startedAt; .updatedAt)] | safe_avg)
            }) | 
            sort_by(-.runs) | 
            .[0:5]
        ),
        recent_failures: (
            . | map(select(.conclusion == "failure")) |
            map({
                workflow: (.displayTitle // .name // "unknown"),
                branch: (.headBranch // "unknown"),
                started: .startedAt,
                url: .url
            }) |
            sort_by(.started) |
            reverse |
            .[0:3]
        )
    }
')

# Format output with error handling
if [ "$format" = "json" ]; then
    echo "$ANALYSIS"
else
    echo "=== Workflow Summary (Last $DAYS days) ==="
    echo "$ANALYSIS" | jq -r '
        .summary |
        "📊 Total Runs: \(.total_runs // 0)",
        "✨ Success Rate: \((.success_rate // 0) | round)%",
        "⏱️  Average Duration: \((.avg_duration_minutes // 0) | round)min"
    '
    
    if (echo "$ANALYSIS" | jq -e '.status_breakdown | length > 0' >/dev/null); then
        echo -e "\\n=== Status Breakdown ==="
        echo "$ANALYSIS" | jq -r '
            .status_breakdown[] |
            "[\(.status // "unknown")] \(.count // 0) runs (\((.percentage // 0) | round)%)"
        '
    fi
    
    if (echo "$ANALYSIS" | jq -e '.by_workflow | length > 0' >/dev/null); then
        echo -e "\\n=== Top Workflows ==="
        echo "$ANALYSIS" | jq -r '
            .by_workflow[] |
            "🔄 \(.name):\\n   Runs: \(.runs // 0)\\n   Success Rate: \((.success_rate // 0) | round)%\\n   Avg Duration: \((.avg_duration // 0) | round)min"
        '
    fi
    
    if (echo "$ANALYSIS" | jq -e '.recent_failures | length > 0' >/dev/null); then
        echo -e "\\n=== Recent Failures ==="
        echo "$ANALYSIS" | jq -r '
            .recent_failures[] |
            "❌ \(.workflow // "unknown")\\n   Branch: \(.branch // "unknown")\\n   Started: \(.started // "unknown")\\n   URL: \(.url // "#")"
        '
    else
        echo -e "\\n✅ No recent failures found"
    fi
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="days", type="str", description="Days of history to analyze (default: 7)", required=False, default="7"),
        Arg(name="limit", type="str", description="Maximum number of runs to analyze (default: 50)", required=False, default="50"),
        Arg(name="format", type="str", description="Output format (text/json)", required=False, default="text"),
    ],
)

workflow_job_analytics = GitHubCliTool(
    name="github_workflow_job_analytics",
    description="Analyze specific workflow job performance and failures",
    content="""
#!/bin/bash
set -euo pipefail

echo "🔍 Analyzing workflow jobs for: $repo"
LIMIT="${limit:-10}"  # Default to 10 runs

# Get specific workflow runs
echo "📊 Fetching job details..."
WORKFLOW_ID=$(gh api "repos/$repo/actions/workflows" --jq ".workflows[] | select(.name == \\"$workflow\\" or .path == \\"$workflow\\") | .id")
if [ -z "$WORKFLOW_ID" ]; then
    echo "❌ Workflow not found: $workflow"
    exit 1
fi

# Get recent runs with job details
JOBS=$(gh api "repos/$repo/actions/workflows/$WORKFLOW_ID/runs?per_page=$LIMIT" --jq '[
    .workflow_runs[] | {
        run_id: .id,
        jobs: (
            # Get jobs for each run
            ($run_id = .id | 
             $api_result = (["repos", $repo, "actions", "runs", (.id | tostring), "jobs"] | join("/") | @sh | "gh api " + . | @sh | sh) |
             ($api_result | fromjson).jobs)
        )
    } | .jobs[] | {
        name: .name,
        status: .conclusion,
        duration: (if .completed_at != null then
            (.completed_at | fromdateiso8601) - (.started_at | fromdateiso8601)
        else 0 end),
        run_id: $run_id,
        url: .html_url
    }
]')

# Analyze jobs
ANALYSIS=$(echo "$JOBS" | jq '{
    job_stats: (group_by(.name) | map({
        name: .[0].name,
        total_runs: length,
        success_rate: (([.[] | select(.status == "success")] | length) * 100.0 / length),
        avg_duration: ([.[] | .duration] | add / length),
        failures: [.[] | select(.status == "failure") | {
            run_id: .run_id,
            url: .url
        }] | .[0:3]
    })),
    slowest_jobs: (sort_by(-.duration) | .[0:5])
}')

# Format output
if [ "$format" = "json" ]; then
    echo "$ANALYSIS"
else
    echo "=== Job Performance Summary ==="
    echo "$ANALYSIS" | jq -r '
        .job_stats[] |
        "🔄 \(.name):\\n" +
        "   Runs: \(.total_runs), Success Rate: \(.success_rate | round)%\\n" +
        "   Avg Duration: \(.avg_duration | round)s\\n" +
        if (.failures | length > 0) then
            "   Recent Failures:\\n" +
            (.failures | map("     • \(.url)") | join("\\n"))
        else "" end + "\\n"
    '
    
    echo "=== Slowest Job Runs ==="
    echo "$ANALYSIS" | jq -r '
        .slowest_jobs[] |
        "⏱️  \(.name) (\(.duration | round)s)\\n   URL: \(.url)"
    '
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="workflow", type="str", description="Workflow name or file path", required=True),
        Arg(name="limit", type="str", description="Number of runs to analyze (default: 10)", required=False, default="10"),
        Arg(name="format", type="str", description="Output format (text/json)", required=False, default="text"),
    ],
)

repo_insights = GitHubCliTool(
    name="github_repo_insights",
    description="Get detailed repository insights using GitHub Traffic API",
    content="""
#!/bin/bash
set -euo pipefail

echo "📊 Gathering insights for: $repo"

# Get traffic data (views)
echo "👀 Fetching view statistics..."
VIEWS=$(gh api "repos/$repo/traffic/views" --jq '{
    total_views: .count,
    unique_visitors: .uniques,
    daily_views: [
        .views[] | {
            date: .timestamp,
            total: .count,
            unique: .uniques
        }
    ]
}')

# Get clone statistics
echo "📥 Fetching clone statistics..."
CLONES=$(gh api "repos/$repo/traffic/clones" --jq '{
    total_clones: .count,
    unique_cloners: .uniques,
    daily_clones: [
        .clones[] | {
            date: .timestamp,
            total: .count,
            unique: .uniques
        }
    ]
}')

# Get top referrers
echo "🔗 Fetching referrer sources..."
REFERRERS=$(gh api "repos/$repo/traffic/popular/referrers" --jq 'map({
    source: .referrer,
    views: .count,
    unique_visitors: .uniques
})')

# Get popular content
echo "📈 Fetching popular content..."
POPULAR=$(gh api "repos/$repo/traffic/popular/paths" --jq 'map({
    path: .path,
    views: .count,
    unique_visitors: .uniques
})')

# Get release download stats if available
echo "📦 Fetching release statistics..."
RELEASES=$(gh api "repos/$repo/releases" --jq '[
    .[] | select(.assets != null) | {
        name: .name,
        downloads: ([.assets[].download_count] | add),
        assets: [
            .assets[] | {
                name: .name,
                downloads: .download_count,
                size: .size,
                updated: .updated_at
            }
        ]
    }
] | sort_by(-.downloads)')

# Format output
if [ "$format" = "json" ]; then
    jq -n --argjson views "$VIEWS" \
          --argjson clones "$CLONES" \
          --argjson referrers "$REFERRERS" \
          --argjson popular "$POPULAR" \
          --argjson releases "$RELEASES" \
        '{
            traffic: {
                views: $views,
                clones: $clones
            },
            referrers: $referrers,
            popular_content: $popular,
            releases: $releases
        }'
else
    echo "=== Traffic Overview (Last 14 days) ==="
    echo "$VIEWS" | jq -r '
        "👀 Total Views: \(.total_views)",
        "   Unique Visitors: \(.unique_visitors)",
        "\\n📅 Daily Views:",
        (.daily_views[] | "   \(.date | fromdate | strftime("%Y-%m-%d")): \(.total) views (\(.unique) unique)")
    '
    
    echo -e "\\n=== Clone Statistics (Last 14 days) ==="
    echo "$CLONES" | jq -r '
        "📥 Total Clones: \(.total_clones)",
        "   Unique Cloners: \(.unique_cloners)"
    '
    
    echo -e "\\n=== Top Referrers ==="
    echo "$REFERRERS" | jq -r '.[] |
        "🔗 \(.source):\\n   Views: \(.views) (\(.unique_visitors) unique)"
    '
    
    echo -e "\\n=== Popular Content ==="
    echo "$POPULAR" | jq -r '.[] |
        "📄 \(.path):\\n   Views: \(.views) (\(.unique_visitors) unique)"
    '
    
    if [ -n "$(echo "$RELEASES" | jq '. | length')" ]; then
        echo -e "\\n=== Release Statistics ==="
        echo "$RELEASES" | jq -r '.[] |
            "📦 \(.name):\\n" +
            "   Total Downloads: \(.downloads)\\n" +
            "   Assets:\\n" +
            (.assets[] | "     • \(.name): \(.downloads) downloads (\(.size/1024/1024 | round)MB)")
        '
    fi
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="format", type="str", description="Output format (text/json)", required=False, default="text"),
    ],
)

dependency_insights = GitHubCliTool(
    name="github_dependency_insights",
    description="Get insights about repository dependencies and their usage",
    content="""
#!/bin/bash
set -euo pipefail

echo "📦 Analyzing dependencies for: $repo"

# Get dependency graph
echo "🔍 Fetching dependency information..."
DEPS=$(gh api "repos/$repo/dependency-graph/snapshots" --jq '{
    manifests: [
        .[] | {
            filename: .manifest.name,
            resolved: [
                .resolved[] | {
                    package: .package.name,
                    version: .version,
                    scope: .scope,
                    dependencies: (.metadata.dependencies | length)
                }
            ] | sort_by(.package)
        }
    ],
    summary: {
        total_deps: ([.[] | .resolved | length] | add),
        manifest_count: length
    }
}')

# Get vulnerability alerts
echo "⚠️ Checking for vulnerabilities..."
VULNS=$(gh api "repos/$repo/dependabot/alerts?state=open" --jq '[
    .[] | {
        package: .dependency.package.name,
        severity: .security_advisory.severity,
        summary: .security_advisory.summary,
        created: .created_at,
        manifest: .dependency.manifest_path
    }
] | group_by(.severity)')

# Format output
if [ "$format" = "json" ]; then
    jq -n --argjson deps "$DEPS" \
          --argjson vulns "$VULNS" \
        '{
            dependencies: $deps,
            vulnerabilities: $vulns
        }'
else
    echo "=== Dependency Overview ==="
    echo "$DEPS" | jq -r '
        .summary |
        "📊 Total Dependencies: \(.total_deps)",
        "📑 Manifest Files: \(.manifest_count)"
    '
    
    echo -e "\\n=== Dependencies by Manifest ==="
    echo "$DEPS" | jq -r '
        .manifests[] |
        "📄 \(.filename):\\n" +
        (.resolved | group_by(.scope) | map({
            scope: .[0].scope,
            count: length,
            deps: map(.package)
        }) | .[] |
        "   [\(.scope // "runtime")] \(.count) packages:\\n" +
        (.deps | map("     • " + .) | join("\\n")))
    '
    
    if [ -n "$(echo "$VULNS" | jq '. | length')" ]; then
        echo -e "\\n=== Security Vulnerabilities ==="
        echo "$VULNS" | jq -r '.[] |
            "[\(.[0].severity)] \(length) issues:\\n" +
            (.[] | "   • \(.package): \(.summary)\\n     In: \(.manifest)")
        '
    fi
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="format", type="str", description="Output format (text/json)", required=False, default="text"),
    ],
)

# Register tools
ANALYTICS_TOOLS = [
    repo_stats,
    security_analysis,
    commit_history,
    workflow_analytics,
    workflow_job_analytics,
    repo_insights,
    dependency_insights,
]

for tool in ANALYTICS_TOOLS:
    tool_registry.register("github", tool)

__all__ = ['repo_stats', 'security_analysis', 'commit_history', 'workflow_analytics', 'workflow_job_analytics', 'repo_insights', 'dependency_insights'] 