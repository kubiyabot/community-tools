# Just-In-Time Access Module 🔐

The `just_in_time_access` module provides a secure and auditable way to manage temporary access to resources and tools. It implements a complete Just-In-Time (JIT) access workflow - from request initiation through approval and access provisioning, with automatic revocation after the specified time period.

## 🛠️ Available Tools

### 1. `request_tool_access`
Request temporary access to a specific tool or resource.

**Arguments:**
- `tool_name` (required): Name of the tool (e.g., `create_ec2`, `restart_service`)
- `user_email` (required): Requestor's email address
- `tool_params` (required): Tool-specific parameters as JSON (e.g., `{"region": "eu-west-1"}`)
- `ttl` (optional): Requested access duration (default: `1h`)

### 2. `approve_tool_access_request` 
Process approval/rejection of access requests.

**Arguments:**
- `request_id` (required): The request ID to approve/reject
- `approval_action` (required): Either `approve` or `reject`
- `ttl` (optional): Override the requested TTL when approving

### 3. `describe_access_request`
View details of a specific access request.

**Arguments:**
- `request_id` (required): Request ID to describe

### 4. `list_active_access_requests`
List all pending access requests.

**Arguments:** None required

## 🔄 Workflow

The following diagram illustrates the complete Just-In-Time access workflow:
```mermaid
sequenceDiagram
    participant U as 👤 User
    participant K as 🤖 Kubiya
    participant R as 📚 RAG Engine
    participant O as 🔐 Okta
    participant A as 👥 Approvers
    participant S as 💻 System

    Note over U,S: Just-In-Time Access Workflow

    U->>K: 1️⃣ Request Access<br/>(e.g., "Create EC2 in eu-west-1")
    
    rect rgb(240, 248, 255)
        Note right of K: Validation Phase
        K->>K: 2️⃣ Verify Available Tools
        K->>K: 3️⃣ Validate Request Attributes
    end

    rect rgb(255, 248, 240)
        Note right of K: Authorization Phase
        K->>R: 4️⃣ Query Organization Knowledge
        R->>K: Return Matching Okta Groups
        K->>O: 5️⃣ Fetch Eligible Approvers
        O->>K: Return Approver List
    end

    rect rgb(245, 255, 245)
        Note right of K: Approval Phase
        K->>A: 6️⃣ Send Request to<br/>Dedicated Slack Channel
        A->>K: 7️⃣ Approve Request<br/>(with TTL X)
    end

    rect rgb(255, 240, 245)
        Note right of K: Access Phase
        K->>S: 8️⃣ Create Temporary Policy
        K->>U: Notify Access Granted
        Note over U,S: ⏳ Access Valid for TTL X
    end

    Note over U,S: 🔄 Policy Auto-Revokes After TTL
```