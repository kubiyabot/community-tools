from typing import TypedDict, List

class WorkflowStep(TypedDict):
    name: str
    status: str  # success, failure, skipped
    conclusion: str  # success, failure, cancelled, skipped
    number: int  # Step number for ordering

class WorkflowFailure(TypedDict):
    step: str  # Step name
    error: str  # Error message
    file: str  # File where error occurred (if applicable)
    line: str  # Line number (if applicable)

class WorkflowFix(TypedDict):
    step: str  # Step name
    description: str  # Fix description
    code_sample: str  # Example code fix (if applicable)

class FileChange(TypedDict):
    filename: str
    status: str  # added, modified, removed
    additions: int
    deletions: int
    changes: int
    patch: str  # Git diff patch
    previous_filename: str  # For renamed files

class PullRequestDetails(TypedDict):
    title: str
    description: str
    author: str
    created_at: str
    updated_at: str
    changed_files: List[FileChange]
    commits_count: int
    additions: int
    deletions: int
    labels: List[str]
    base_branch: str
    head_branch: str

class WorkflowRunDetails(TypedDict):
    id: str  # Run ID
    name: str  # Workflow name
    started_at: str  # ISO timestamp
    status: str  # completed, in_progress, queued
    conclusion: str  # success, failure, cancelled
    actor: str  # User who triggered the workflow
    trigger_event: str  # push, pull_request, etc.
    pr_details: PullRequestDetails  # Add PR details

# Example data structures
EXAMPLE_WORKFLOW_STEPS = [
    {
        "name": "Install Dependencies",
        "status": "success",
        "conclusion": "success",
        "number": 1
    },
    {
        "name": "Run Tests",
        "status": "failure",
        "conclusion": "failure",
        "number": 2
    }
]

EXAMPLE_FAILURES = [
    {
        "step": "Run Tests",
        "error": "fmt.Errorf format %w has arg err of wrong type",
        "file": "internal/tui/execution.go",
        "line": "23"
    }
]

EXAMPLE_FIXES = [
    {
        "step": "Run Tests",
        "description": "Ensure error type matches format specifier",
        "code_sample": "fmt.Errorf(\"error: %v\", err)"
    }
]

EXAMPLE_RUN_DETAILS = {
    "id": "12345678",
    "name": "CI Pipeline",
    "started_at": "2024-01-20T10:00:00Z",
    "status": "completed",
    "conclusion": "failure",
    "actor": "octocat",
    "trigger_event": "pull_request"
}

EXAMPLE_FILE_CHANGES = [
    {
        "filename": "src/main.go",
        "status": "modified",
        "additions": 15,
        "deletions": 5,
        "changes": 20,
        "patch": "@@ -23,7 +23,15 @@ func main() {\n...",
        "previous_filename": None
    },
    {
        "filename": "tests/test_main.go",
        "status": "added",
        "additions": 50,
        "deletions": 0,
        "changes": 50,
        "patch": "@@ -0,0 +1,50 @@ package tests\n...",
        "previous_filename": None
    }
] 