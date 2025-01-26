import React from 'react';
import * as VendorIcons from './VendorIcons';
import { AlertTriangle, Bell, Box, Bug, Calendar, Check, CircleDollarSign, Cloud, Code, FileCode, GitBranch, GitCommit, GitPullRequest, LineChart, MessageSquare, Server, Settings, Truck, Webhook } from 'lucide-react';

export interface WebhookEvent {
  type: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  category: string;
  variables: string[];
  example: Record<string, any>;
  validation?: {
    required: string[];
    rules: Array<{
      field: string;
      type: string;
      description: string;
      format?: string;
      example?: string;
      required?: string[];
      properties?: Record<string, any>;
      optional?: boolean;
    }>;
    hints: string[];
    bestPractices: Array<{
      title: string;
      description: string;
    }>;
    jsonSchema: {
      type: string;
      required: string[];
      properties: Record<string, any>;
      additionalProperties?: boolean;
    };
  };
}

export interface WebhookProviderConfig {
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  gradient: string;
  borderColor: string;
  iconColor: string;
  events: WebhookEvent[];
}

export type WebhookProviderType = 
  | 'github' 
  | 'gitlab'
  | 'datadog' 
  | 'prometheus'
  | 'pagerduty' 
  | 'jenkins'
  | 'servicenow' 
  | 'aws_eventbridge'
  | 'custom';

export interface WebhookProvider {
  id: WebhookProviderType;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  events: WebhookEvent[];
}

export const WEBHOOK_PROVIDERS: Record<WebhookProviderType, WebhookProviderConfig> = {
  github: {
    name: "GitHub",
    icon: VendorIcons.GitHubIcon,
    description: "Repository and organization events",
    gradient: "from-[#2D333B] to-[#22272E]",
    borderColor: "border-[#444C56]",
    iconColor: "text-white",
    events: [
      {
        type: "push",
        name: "Repository Push",
        description: "When code is pushed to a repository",
        icon: VendorIcons.GitHubIcon,
        category: "Repository",
        variables: ["repository", "ref", "commits", "pusher"],
        example: {
          ref: "refs/heads/main",
          before: "6113728f27ae82c7b1a177c8d03f9e96e0adf246",
          after: "76ae82c7b1a177c8d03f9e96e0adf2466113728f",
          created: false,
          deleted: false,
          forced: false,
          base_ref: null,
          compare: "https://github.com/kubiya-ai/chat-ui/compare/6113728f27ae...76ae82c7b1a1",
          commits: [
            {
              id: "76ae82c7b1a177c8d03f9e96e0adf2466113728f",
              tree_id: "cd8274d15fa3ae2ab983129fb037999f264ba9a7",
              message: "Fix webhook implementation",
              timestamp: "2024-01-25T15:30:00Z",
              author: {
                name: "John Smith",
                email: "john.smith@example.com",
                username: "johnsmith"
              },
              committer: {
                name: "GitHub",
                email: "noreply@github.com",
                username: "web-flow"
              },
              added: ["src/webhooks/handlers.ts"],
              removed: [],
              modified: ["src/webhooks/types.ts"]
            }
          ],
          head_commit: {
            id: "76ae82c7b1a177c8d03f9e96e0adf2466113728f",
            message: "Fix webhook implementation",
            timestamp: "2024-01-25T15:30:00Z"
          },
          repository: {
            id: 123456789,
            node_id: "R_kgDOG1YLxQ",
            name: "chat-ui",
            full_name: "kubiya-ai/chat-ui",
            private: true,
            owner: {
              name: "Kubiya AI",
              email: "support@kubiya.ai",
              login: "kubiya-ai",
              id: 98765432,
              node_id: "O_kgDOBm2Xpw",
              avatar_url: "https://avatars.githubusercontent.com/u/98765432?v=4",
              url: "https://api.github.com/users/kubiya-ai"
            },
            html_url: "https://github.com/kubiya-ai/chat-ui",
            description: "Kubiya Chat UI",
            fork: false,
            created_at: 1642780800,
            updated_at: "2024-01-25T15:30:00Z",
            pushed_at: 1642780800,
            default_branch: "main"
          },
          pusher: {
            name: "johnsmith",
            email: "john.smith@example.com"
          },
          sender: {
            login: "johnsmith",
            id: 12345678,
            node_id: "U_kgDOBjK8Zg",
            avatar_url: "https://avatars.githubusercontent.com/u/12345678?v=4",
            url: "https://api.github.com/users/johnsmith"
          }
        }
      },
      {
        type: "pull_request",
        name: "Pull Request",
        description: "When a pull request is opened, closed, or synchronized",
        icon: VendorIcons.GitHubIcon,
        category: "Repository",
        variables: ["repository", "pull_request", "action", "sender"],
        example: {
          action: "opened",
          number: 123,
          pull_request: {
            url: "https://api.github.com/repos/kubiya-ai/chat-ui/pulls/123",
            id: 1234567890,
            node_id: "PR_kwDOG1YLxQ5NzI",
            html_url: "https://github.com/kubiya-ai/chat-ui/pull/123",
            diff_url: "https://github.com/kubiya-ai/chat-ui/pull/123.diff",
            patch_url: "https://github.com/kubiya-ai/chat-ui/pull/123.patch",
            number: 123,
            state: "open",
            locked: false,
            title: "Enhance webhook implementation",
            user: {
              login: "johnsmith",
              id: 12345678,
              node_id: "U_kgDOBjK8Zg",
              avatar_url: "https://avatars.githubusercontent.com/u/12345678?v=4",
              url: "https://api.github.com/users/johnsmith"
            },
            body: "This PR enhances the webhook implementation with better error handling and validation.",
            created_at: "2024-01-25T15:30:00Z",
            updated_at: "2024-01-25T15:30:00Z",
            closed_at: null,
            merged_at: null,
            merge_commit_sha: "e5bd3914e3e36a42b0e956fee987b8e2838d8744",
            assignee: null,
            assignees: [],
            requested_reviewers: [],
            requested_teams: [],
            labels: [
              {
                id: 123456789,
                node_id: "MDU6TGFiZWwxMjM0NTY3ODk=",
                url: "https://api.github.com/repos/kubiya-ai/chat-ui/labels/enhancement",
                name: "enhancement",
                color: "84b6eb",
                default: true
              }
            ],
            head: {
              label: "kubiya-ai:feature/enhance-webhooks",
              ref: "feature/enhance-webhooks",
              sha: "76ae82c7b1a177c8d03f9e96e0adf2466113728f"
            },
            base: {
              label: "kubiya-ai:main",
              ref: "main",
              sha: "6113728f27ae82c7b1a177c8d03f9e96e0adf246"
            }
          },
          repository: {
            id: 123456789,
            node_id: "R_kgDOG1YLxQ",
            name: "chat-ui",
            full_name: "kubiya-ai/chat-ui",
            private: true,
            owner: {
              login: "kubiya-ai",
              id: 98765432,
              node_id: "O_kgDOBm2Xpw",
              avatar_url: "https://avatars.githubusercontent.com/u/98765432?v=4"
            }
          },
          sender: {
            login: "johnsmith",
            id: 12345678,
            node_id: "U_kgDOBjK8Zg",
            avatar_url: "https://avatars.githubusercontent.com/u/12345678?v=4"
          }
        }
      },
      {
        type: "issues",
        name: "Issues",
        description: "When an issue is opened, closed, or modified",
        icon: VendorIcons.GitHubIcon,
        category: "Repository",
        variables: ["repository", "issue", "action", "sender"],
        example: {
          action: "opened",
          issue: {
            number: 456,
            title: "Bug: Login not working",
            body: "The login feature is broken in production",
            state: "open",
            html_url: "https://github.com/org/repo/issues/456",
            user: {
              login: "johndoe",
              avatar_url: "https://github.com/avatars/u/123?v=4"
            },
            labels: [
              {
                name: "bug",
                color: "d73a4a"
              }
            ],
            assignees: [],
            created_at: "2023-01-01T12:00:00Z"
          },
          repository: {
            name: "repo",
            full_name: "org/repo",
            private: false,
            html_url: "https://github.com/org/repo"
          },
          sender: {
            login: "johndoe",
            avatar_url: "https://github.com/avatars/u/123?v=4"
          }
        }
      }
    ]
  },
  gitlab: {
    name: "GitLab",
    icon: VendorIcons.GitLabIcon,
    description: "Repository and CI/CD events",
    gradient: "from-[#FCA326] to-[#E24329]",
    borderColor: "border-orange-500/30",
    iconColor: "text-white",
    events: [
      {
        type: "push",
        name: "Repository Push",
        description: "When code is pushed to a repository",
        icon: VendorIcons.GitLabIcon,
        category: "Repository",
        variables: ["project", "ref", "commits", "user_name"],
        example: {
          object_kind: "push",
          project: {
            id: 1234,
            name: "my-project",
            web_url: "https://gitlab.com/org/my-project",
            visibility_level: 20
          },
          ref: "refs/heads/main",
          user_name: "John Doe",
          user_email: "john@example.com",
          commits: [
            {
              id: "6dcb09b5b57875f334f61aebed695e2e4193db5e",
              message: "Fix login bug",
              timestamp: "2023-01-01T12:00:00Z",
              author: {
                name: "John Doe",
                email: "john@example.com"
              },
              added: ["src/login.ts"],
              removed: [],
              modified: ["src/auth.ts"]
            }
          ]
        }
      },
      {
        type: "merge_request",
        name: "Merge Request",
        description: "When a merge request is opened, closed, or synchronized",
        icon: VendorIcons.GitLabIcon,
        category: "Repository",
        variables: ["project", "object_attributes", "user", "changes"],
        example: {
          object_kind: "merge_request",
          project: {
            id: 1234,
            name: "my-project",
            web_url: "https://gitlab.com/org/my-project"
          },
          object_attributes: {
            id: 42,
            target_branch: "main",
            source_branch: "feature/auth",
            title: "Add new authentication feature",
            description: "This MR adds a new authentication feature",
            state: "opened",
            url: "https://gitlab.com/org/my-project/-/merge_requests/42",
            author_id: 123,
            assignee_id: 456
          },
          user: {
            name: "John Doe",
            username: "johndoe",
            avatar_url: "https://gitlab.com/uploads/-/system/user/avatar/123/avatar.png"
          },
          changes: {
            total_changes: 180,
            changes_count: 5
          }
        }
      }
    ]
  },
  datadog: {
    name: "Datadog",
    icon: VendorIcons.DatadogIcon,
    description: "Monitoring and analytics events",
    gradient: "from-[#632CA6] to-[#4B2181]",
    borderColor: "border-purple-500/30",
    iconColor: "text-white",
    events: [
      {
        type: "alert",
        name: "Alert",
        description: "When an alert is triggered or resolved",
        icon: VendorIcons.DatadogIcon,
        category: "Monitoring",
        variables: ["alert", "status", "priority", "tags"],
        example: {
          alert: {
            id: "12345",
            title: "High CPU Usage",
            message: "CPU usage is above 90% for the last 5 minutes",
            priority: "P1",
            status: "triggered",
            created_at: "2023-01-01T12:00:00Z",
            last_updated: "2023-01-01T12:05:00Z"
          },
          status: "triggered",
          priority: "P1",
          tags: [
            "env:production",
            "service:api",
            "region:us-east-1"
          ],
          metric: {
            name: "system.cpu.user",
            value: 95.5,
            threshold: 90
          }
        }
      },
      {
        type: "metric",
        name: "Metric Alert",
        description: "When a metric crosses a threshold",
        icon: VendorIcons.DatadogIcon,
        category: "Monitoring",
        variables: ["metric", "threshold", "status", "scope"],
        example: {
          metric: {
            name: "system.memory.usage",
            value: 85.5,
            unit: "percent",
            timestamp: "2023-01-01T12:00:00Z"
          },
          threshold: 80,
          status: "alert",
          scope: ["env:production", "service:api"],
          tags: ["memory", "high-usage"]
        }
      },
      {
        type: "event",
        name: "Event",
        description: "When an event is created",
        icon: VendorIcons.DatadogIcon,
        category: "Events",
        variables: ["event", "aggregation_key", "tags", "text"],
        example: {
          event: {
            title: "Deployment Completed",
            text: "Version 1.2.3 deployed successfully",
            priority: "normal",
            source_type_name: "deployment",
            timestamp: "2023-01-01T12:00:00Z"
          },
          aggregation_key: "deployment.v1.2.3",
          tags: ["deployment", "production"],
          text: "Deployment of version 1.2.3 completed successfully"
        }
      }
    ]
  },
  prometheus: {
    name: "Prometheus",
    icon: VendorIcons.PrometheusIcon,
    description: "Monitoring and analytics events",
    gradient: "from-[#E6522C] to-[#B02C12]",
    borderColor: "border-orange-500/30",
    iconColor: "text-white",
    events: [
      {
        type: "alert",
        name: "Alert",
        description: "When an alert is fired or resolved",
        icon: VendorIcons.PrometheusIcon,
        category: "Monitoring",
        variables: ["alerts", "status", "labels", "annotations"],
        example: {
          version: "4",
          groupKey: "{}:{alertname=\"HighLatency\"}",
          status: "firing",
          receiver: "team-api",
          alerts: [
            {
              status: "firing",
              labels: {
                alertname: "HighLatency",
                severity: "critical",
                instance: "api-server-1",
                job: "api"
              },
              annotations: {
                summary: "High latency detected",
                description: "API latency is above 500ms for the last 5 minutes",
                value: "750ms"
              },
              startsAt: "2023-01-01T12:00:00Z",
              endsAt: "2023-01-01T12:05:00Z",
              generatorURL: "http://prometheus.example.com/graph?..."
            }
          ]
        }
      },
      {
        type: "metric",
        name: "Metric Alert",
        description: "When a metric value changes significantly",
        icon: VendorIcons.PrometheusIcon,
        category: "Monitoring",
        variables: ["metric", "value", "labels", "threshold"],
        example: {
          metric: {
            name: "http_requests_total",
            value: 1250.5,
            timestamp: "2023-01-01T12:00:00Z"
          },
          labels: {
            method: "GET",
            status: "500",
            path: "/api/v1/users"
          },
          threshold: 1000,
          evaluation_time: "5m"
        }
      }
    ]
  },
  pagerduty: {
    name: "PagerDuty",
    icon: VendorIcons.PagerDutyIcon,
    description: "Incident management events",
    gradient: "from-[#06AC38] to-[#058C2C]",
    borderColor: "border-green-500/30",
    iconColor: "text-white",
    events: [
      {
        type: "incident.trigger",
        name: "Incident Triggered",
        description: "When a new incident is triggered",
        icon: VendorIcons.PagerDutyIcon,
        category: "Incidents",
        variables: ["incident", "service", "assignments", "urgency"],
        example: {
          event: "incident.trigger",
          incident: {
            id: "PT4KHLK",
            incident_number: 123,
            title: "Production database is down",
            description: "MySQL cluster is not responding",
            created_at: "2023-01-01T12:00:00Z",
            status: "triggered",
            urgency: "high",
            html_url: "https://org.pagerduty.com/incidents/PT4KHLK"
          },
          service: {
            id: "PDW123",
            name: "MySQL Production",
            html_url: "https://org.pagerduty.com/services/PDW123"
          },
          assignments: [
            {
              assignee: {
                id: "PA12345",
                name: "John Doe",
                email: "john@example.com",
                html_url: "https://org.pagerduty.com/users/PA12345"
              }
            }
          ]
        }
      },
      {
        type: "incident.acknowledge",
        name: "Incident Acknowledged",
        description: "When an incident is acknowledged",
        icon: VendorIcons.PagerDutyIcon,
        category: "Incidents",
        variables: ["incident", "service", "assignments", "acknowledger"],
        example: {
          event: "incident.acknowledge",
          incident: {
            id: "PT4KHLK",
            incident_number: 123,
            title: "Production database is down",
            status: "acknowledged",
            urgency: "high"
          },
          service: {
            id: "PDW123",
            name: "MySQL Production"
          },
          acknowledger: {
            id: "PA12345",
            name: "John Smith",
            email: "john.smith@example.com"
          }
        }
      },
      {
        type: "incident.resolve",
        name: "Incident Resolved",
        description: "When an incident is resolved",
        icon: VendorIcons.PagerDutyIcon,
        category: "Incidents",
        variables: ["incident", "service", "assignments", "resolver"],
        example: {
          event: "incident.resolve",
          incident: {
            id: "PT4KHLK",
            incident_number: 123,
            title: "Production database is down",
            status: "resolved",
            resolve_reason: "Database cluster restored",
            resolved_at: "2023-01-01T13:00:00Z"
          },
          service: {
            id: "PDW123",
            name: "MySQL Production"
          },
          resolver: {
            id: "PA12345",
            name: "John Smith",
            email: "john.smith@example.com"
          }
        }
      }
    ]
  },
  jenkins: {
    name: "Jenkins",
    icon: VendorIcons.JenkinsIcon,
    description: "CI/CD pipeline events",
    gradient: "from-[#335061] to-[#1C2B33]",
    borderColor: "border-blue-500/30",
    iconColor: "text-white",
    events: [
      {
        type: "job.started",
        name: "Job Started",
        description: "When a job starts running",
        icon: VendorIcons.JenkinsIcon,
        category: "CI/CD",
        variables: ["job", "build", "parameters", "timestamp"],
        example: {
          job: {
            name: "my-project-build",
            url: "https://jenkins.example.com/job/my-project-build"
          },
          build: {
            number: "124",
            phase: "STARTED",
            parameters: {
              BRANCH: "main",
              ENVIRONMENT: "staging"
            }
          },
          timestamp: 1672574400000
        }
      },
      {
        type: "job.completed",
        name: "Job Completed",
        description: "When a job finishes running",
        icon: VendorIcons.JenkinsIcon,
        category: "CI/CD",
        variables: ["job", "build", "result", "duration"],
        example: {
          job: {
            name: "my-project-build",
            url: "https://jenkins.example.com/job/my-project-build"
          },
          build: {
            number: "123",
            phase: "COMPLETED",
            status: "SUCCESS",
            url: "https://jenkins.example.com/job/my-project-build/123",
            scm: {
              url: "https://github.com/org/repo.git",
              branch: "main",
              commit: "6dcb09b5b57875f334f61aebed695e2e4193db5e"
            }
          },
          result: "SUCCESS",
          duration: 245000,
          timestamp: 1672574400000,
          artifacts: [
            {
              name: "app.jar",
              path: "target/app.jar",
              size: 15000000
            }
          ]
        }
      },
      {
        type: "job.failed",
        name: "Job Failed",
        description: "When a job fails",
        icon: VendorIcons.JenkinsIcon,
        category: "CI/CD",
        variables: ["job", "build", "error", "console_url"],
        example: {
          job: {
            name: "my-project-build",
            url: "https://jenkins.example.com/job/my-project-build"
          },
          build: {
            number: "125",
            phase: "COMPLETED",
            status: "FAILURE",
            error: "Tests failed: 3 failures"
          },
          console_url: "https://jenkins.example.com/job/my-project-build/125/console",
          timestamp: 1672574400000
        }
      }
    ]
  },
  servicenow: {
    name: "ServiceNow",
    icon: VendorIcons.ServiceNowIcon,
    description: "Service management events",
    gradient: "from-[#81B5A1] to-[#62A187]",
    borderColor: "border-green-500/30",
    iconColor: "text-white",
    events: [
      {
        type: "incident.created",
        name: "Incident Created",
        description: "When a new incident is created",
        icon: VendorIcons.ServiceNowIcon,
        category: "Incidents",
        variables: ["incident", "caller", "priority", "description"],
        example: {
          incident: {
            number: "INC0010001",
            sys_id: "9d385017c611228701d22104cc95c371",
            short_description: "Email service is down",
            description: "Users are unable to send or receive emails",
            priority: "1 - Critical",
            state: "New",
            assigned_to: {
              name: "John Doe",
              email: "john@example.com"
            },
            caller: {
              name: "Jane Smith",
              email: "jane@example.com"
            },
            category: "email",
            subcategory: "outlook",
            created_on: "2023-01-01 12:00:00"
          }
        }
      },
      {
        type: "change.requested",
        name: "Change Requested",
        description: "When a change request is submitted",
        icon: VendorIcons.ServiceNowIcon,
        category: "Changes",
        variables: ["change", "requester", "type", "risk"],
        example: {
          change: {
            number: "CHG0010234",
            type: "normal",
            short_description: "Deploy new API version",
            description: "Deploy version 2.0 of the customer API",
            risk: "moderate",
            impact: "medium",
            state: "requested"
          },
          requester: {
            name: "Jane Smith",
            email: "jane.smith@example.com",
            department: "Engineering"
          }
        }
      },
      {
        type: "problem.identified",
        name: "Problem Identified",
        description: "When a new problem is identified",
        icon: VendorIcons.ServiceNowIcon,
        category: "Problems",
        variables: ["problem", "owner", "impact", "urgency"],
        example: {
          problem: {
            number: "PRB0010567",
            short_description: "Recurring system outages",
            description: "System experiences intermittent outages during peak hours",
            state: "identified",
            impact: "high",
            urgency: "high"
          },
          owner: {
            name: "John Smith",
            email: "john.smith@example.com",
            department: "Operations"
          }
        }
      }
    ]
  },
  aws_eventbridge: {
    name: "AWS EventBridge",
    icon: VendorIcons.AWSEventBridgeIcon,
    description: "AWS service events",
    gradient: "from-[#FF9900] to-[#FF5700]",
    borderColor: "border-orange-500/30",
    iconColor: "text-white",
    events: [
      {
        type: "aws.ec2",
        name: "EC2 State Change",
        description: "When an EC2 instance state changes",
        icon: VendorIcons.AWSEventBridgeIcon,
        category: "Compute",
        variables: ["instance", "state", "region", "account"],
        example: {
          version: "0",
          id: "6a7e8feb-b491-4cf7-a9f1-bf3703467718",
          "detail-type": "EC2 Instance State-change Notification",
          source: "aws.ec2",
          account: "111122223333",
          time: "2023-01-01T12:00:00Z",
          region: "us-east-1",
          resources: [
            "arn:aws:ec2:us-east-1:111122223333:instance/i-1234567890abcdef0"
          ],
          detail: {
            "instance-id": "i-1234567890abcdef0",
            state: "running",
            previousState: "pending"
          }
        }
      },
      {
        type: "aws.s3",
        name: "S3 Object Event",
        description: "When an S3 object is created or deleted",
        icon: VendorIcons.AWSEventBridgeIcon,
        category: "Storage",
        variables: ["bucket", "object", "operation", "size"],
        example: {
          version: "0",
          id: "17793124-05d4-457e-9a4c-885d7658eee9",
          "detail-type": "AWS API Call via CloudTrail",
          source: "aws.s3",
          account: "111122223333",
          time: "2023-01-01T12:00:00Z",
          region: "us-east-1",
          detail: {
            operation: "PutObject",
            bucket: {
              name: "my-bucket",
              arn: "arn:aws:s3:::my-bucket"
            },
            object: {
              key: "uploads/file.pdf",
              size: 1048576,
              etag: "d41d8cd98f00b204e9800998ecf8427e"
            }
          }
        }
      },
      {
        type: "aws.lambda",
        name: "Lambda Function Event",
        description: "When a Lambda function is invoked",
        icon: VendorIcons.AWSEventBridgeIcon,
        category: "Serverless",
        variables: ["function", "version", "runtime", "memory"],
        example: {
          version: "0",
          id: "89d1a02d-5ec7-412e-82f5-13505f849b41",
          "detail-type": "AWS API Call via CloudTrail",
          source: "aws.lambda",
          account: "111122223333",
          time: "2023-01-01T12:00:00Z",
          region: "us-east-1",
          detail: {
            function: {
              name: "process-orders",
              version: "$LATEST",
              runtime: "nodejs18.x",
              memory: 512
            },
            requestId: "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            type: "RequestResponse",
            duration: 123.45
          }
        }
      }
    ]
  },
  custom: {
    name: "Custom",
    icon: VendorIcons.CustomIcon,
    description: "Define your own webhook events with custom JSON structures",
    gradient: "from-[#2D333B] to-[#22272E]",
    borderColor: "border-[#444C56]",
    iconColor: "text-white",
    events: [
      {
        type: "custom.event",
        name: "Custom Event",
        description: "Define your own event structure with a custom JSON payload",
        icon: VendorIcons.CustomIcon,
        category: "Custom",
        variables: ["*"], // Allows any variable from the custom JSON structure
        example: {
          // Default example that users can modify
          event_type: "custom.event",
          timestamp: "2024-01-25T15:30:00Z",
          version: "1.0",
          source: "my-system",
          data: {
            // Example of a rich custom structure
            id: "evt_123456789",
            name: "Example Event",
            status: "active",
            priority: "high",
            details: {
              category: "user_action",
              subcategory: "login",
              location: "us-east-1"
            },
            metadata: {
              client_id: "client_123",
              user_agent: "Mozilla/5.0...",
              ip_address: "192.168.1.1"
            },
            metrics: {
              duration_ms: 150,
              retry_count: 0,
              success_rate: 99.9
            },
            tags: [
              "production",
              "web",
              "auth"
            ]
          },
          context: {
            environment: "production",
            component: "authentication-service",
            trace_id: "trace_abcdef123456"
          }
        },
        // Add validation schema for custom events
        validation: {
          required: ["event_type", "timestamp", "data"],
          rules: [
            {
              field: "event_type",
              type: "string",
              description: "Unique identifier for your event type",
              example: "user.login, order.created, etc."
            },
            {
              field: "timestamp",
              type: "string",
              format: "ISO 8601",
              description: "Event occurrence time in ISO 8601 format",
              example: "2024-01-25T15:30:00Z"
            },
            {
              field: "version",
              type: "string",
              description: "Version of your event schema",
              example: "1.0, 2.1, etc."
            },
            {
              field: "source",
              type: "string",
              description: "System or service that generated the event",
              example: "auth-service, payment-processor, etc."
            },
            {
              field: "data",
              type: "object",
              description: "Main payload of your event",
              required: ["id"],
              properties: {
                id: {
                  type: "string",
                  description: "Unique identifier for this event instance"
                }
              }
            },
            {
              field: "context",
              type: "object",
              description: "Additional contextual information",
              optional: true
            }
          ],
          hints: [
            "Use descriptive event_type names in dot notation (e.g., user.created, order.updated)",
            "Always include a timestamp in ISO 8601 format",
            "Add version information to track schema changes",
            "Include relevant metadata and context for better event processing",
            "Use consistent data types across similar events",
            "Consider adding trace_id for distributed tracing",
            "Include environment information for proper routing"
          ],
          bestPractices: [
            {
              title: "Event Naming",
              description: "Use lowercase with dots for event types (e.g., user.login.succeeded)"
            },
            {
              title: "Versioning",
              description: "Include version field to manage schema evolution"
            },
            {
              title: "Timestamps",
              description: "Always use UTC timestamps in ISO 8601 format"
            },
            {
              title: "Unique Identifiers",
              description: "Include unique IDs for event deduplication"
            },
            {
              title: "Error Handling",
              description: "Include status and error details when relevant"
            }
          ],
          jsonSchema: {
            type: "object",
            required: ["event_type", "timestamp", "data"],
            properties: {
              event_type: {
                type: "string",
                pattern: "^[a-z]+([.][a-z]+)*$"
              },
              timestamp: {
                type: "string",
                format: "date-time"
              },
              version: {
                type: "string"
              },
              source: {
                type: "string"
              },
              data: {
                type: "object",
                required: ["id"],
                properties: {
                  id: {
                    type: "string"
                  }
                },
                additionalProperties: true
              },
              context: {
                type: "object",
                additionalProperties: true
              }
            },
            additionalProperties: true
          }
        }
      }
    ]
  }
};

export const getProviderConfig = (provider: WebhookProvider): WebhookProviderConfig => {
  return WEBHOOK_PROVIDERS[provider.id];
};

export const getEventConfig = (provider: WebhookProvider, eventType: string) => {
  const providerConfig = getProviderConfig(provider);
  return providerConfig.events.find(event => event.type === eventType);
};
 