# Kubiya Enforcer Stack Deployment Guide

## Basic Steps

1. **Verify that `kubectl` is installed and configured**
2. **Deploy a runner from the Kubiya App Portal**
3. **Connect to your Kubernetes cluster where the Kubiya Runner is installed**

## Overview Diagram

To understand how the Kubiya Enforcer integrates within your infrastructure, leveraging Open Policy Agent (OPA) and OPAL, refer to the following diagram:

```mermaid
sequenceDiagram
    participant User
    participant KubiyaRunner as Kubiya Runner
    participant Enforcer
    participant OPA
    participant OPAL
    participant GitHub
    participant Okta
    participant Resource

    Note over User,Resource: Just-In-Time Access Flow with Enforcer, OPA, and OPAL

    User->>KubiyaRunner: Request Access (e.g., "Create EC2 in eu-west-1")
    KubiyaRunner->>Enforcer: Validate Access Request
    Enforcer->>OPA: Query Policy Decision
    OPA->>OPAL: Ensure Latest Policies
    OPAL->>GitHub: Sync Policies
    GitHub-->>OPAL: Provide Policy Updates
    OPAL-->>OPA: Update Policies
    OPA-->>Enforcer: Policy Decision
    Enforcer->>Okta: Fetch User Group Membership
    Okta-->>Enforcer: Return User Groups
    Enforcer->>Enforcer: Evaluate Policies
    alt Access Allowed
        Enforcer-->>KubiyaRunner: Access Granted
        KubiyaRunner->>Resource: Perform Action
        Resource-->>KubiyaRunner: Action Completed
        KubiyaRunner-->>User: Notifies User of Success
    else Access Denied
        Enforcer-->>KubiyaRunner: Access Denied
        KubiyaRunner-->>User: Notifies User of Denial
    end
```

## Policy Configuration with OPA and OPAL

The Enforcer uses Open Policy Agent (OPA) to evaluate access policies synchronized via OPAL from your GitHub repository. Below are multiple policy examples covering different scenarios to help you define your access control policies effectively.

### Example Policies: `policy.rego`

```rego
package kubiya.tool_manager

# Default deny all access
default allow = false

# Allow members of the "DevOps" group to access specific tools
allow {
    group := input.user.groups[_]
    group == "DevOps"
    tool := input.tool.name
    tool == "deploy_application"  # Specify the tool name
}

# Allow users with specific email domains to access monitoring tools
allow {
    endswith(input.user.email, "@kubiya.ai")
    tool := input.tool.name
    tool == "view_metrics"
}

# Grant access based on user roles
allow {
    role := input.user.roles[_]
    role == "SRE"
    tool := input.tool.name
    tool != "modify_security_groups"  # Deny access to this tool
}

# Time-based access control: Allow access during business hours
allow {
    tool := input.tool.name
    tool == "restart_service"
    time := input.time.hour  # Assume input includes current time
    time >= 9
    time <= 17
}

# IP-based access control: Allow access only from specific IP ranges
allow {
    tool := input.tool.name
    tool == "access_database"
    ip := input.client_ip
    net.cidr_contains("10.0.0.0/8", ip)
}

# Allow access to emergency tools for on-call engineers
allow {
    group := input.user.groups[_]
    group == "OnCall"
    tool := input.tool.name
    tool == "trigger_failover"
}

# Allow access to all tools for administrators except specified ones
allow {
    group := input.user.groups[_]
    group == "Administrators"
    tool := input.tool.name
    not restricted_tools[tool]
}

# Define a set of restricted tools
restricted_tools := {
    "delete_production_data",
    "shutdown_server",
}

# Allow access to a tool if the user has a specific attribute
allow {
    input.user.attributes.region == "EU"
    tool := input.tool.name
    tool == "deploy_europe"
}

# Example of denying access explicitly
deny[msg] {
    input.user.email == "user_to_block@example.com"
    msg := sprintf("User %s is denied access", [input.user.email])
}
```

**Important Notes:**

- **Okta Group Alignment**: The group names and roles used in the policies must exist in Okta.
- **User Attributes**: Ensure that user attributes required by the policies are provided by Okta and included in the `input`.
- **Tool Parameters**: Tools must include the relevant parameters as specified in the policy conditions.
- **Time and IP Data**: For time-based and IP-based policies, ensure that the necessary data (e.g., `input.time`, `input.client_ip`) is passed to OPA.

### Using Helper Functions

You can define helper functions within your policies to simplify complex conditions.

```rego
package kubiya.tool_manager

# Helper function to check if the user's email is from a corporate domain
is_corporate_email(email) {
    endswith(email, "@kubiya.ai")
}

# Allow access if the email is from a corporate domain
allow {
    is_corporate_email(input.user.email)
    tool := input.tool.name
    tool == "view_internal_docs"
}
```

### Contextual Policies Based on Tool Parameters

```rego
package kubiya.tool_manager

# Allow deployment to staging environment for all developers
allow {
    group := input.user.groups[_]
    group == "Developers"
    tool := input.tool.name
    tool == "deploy_application"
    env := input.tool.parameters.environment
    env == "staging"
}

# Restrict deployment to production environment
allow {
    group := input.user.groups[_]
    group == "Release Managers"
    tool := input.tool.name
    tool == "deploy_application"
    env := input.tool.parameters.environment
    env == "production"
}
```

### Policy for Temporary Access with Just-In-Time (JIT)

```rego
package kubiya.tool_manager

# Allow temporary access if a valid JIT token is provided
allow {
    input.tool.name == "access_sensitive_data"
    valid_jit_token(input.user.email, input.jit_token)
}

# Function to validate JIT token (simplified example)
valid_jit_token(email, token) {
    # Implement token validation logic here
    # For example, check if the token exists in a database and is not expired
    true
}
```

### Deny with Detailed Messages

Provide detailed denial messages to help users understand why access was denied.

```rego
package kubiya.tool_manager

default allow = false

# Deny access and provide a message
deny[msg] {
    not allow
    msg := "Access denied. Please contact the administrator if you believe this is an error."
}
```

## Important Considerations

- **Testing Policies**: Before deploying policies to production, thoroughly test them to ensure they behave as expected.
- **Policy Organization**: Keep your policies well-organized and documented for maintainability.
- **Version Control**: Use version control (e.g., Git) for your policy repository to track changes over time.
- **Audit Logging**: Implement audit logging to track policy decisions and access attempts.

## Adding Policies to Your Repository

1. **Create a Policy File**: Add a `.rego` file (e.g., `policy.rego`) to your policy repository.
2. **Define Policies**: Include the policy rules as shown in the examples above.
3. **Commit and Push**: Commit the changes and push them to the repository.

The OPAL service will automatically detect changes and synchronize the updated policies to the Enforcer's OPA engine.

## Step 1: Obtaining Okta Credentials

1. **Log in to Okta Administration**

2. **Navigate to** `https://{ORG}-admin.okta.com/admin/apps/active`

3. **Create a new app integration**:
   - **Select type**: _API Services_
   - **Choose an appropriate name** and save
   - **Edit general settings** and disable _Require Proof Key for Code Exchange (PKCE)_

4. **Configure API Access**:
   - Under **API Scopes**, grant:
     - `okta.users.read`
     - `okta.groups.read`
   - Under **Admin Roles**:
     - Click **Edit Assignments**
     - Select **Read Only Administrator**

5. **Set Up Client Credentials**:
   - Click **Edit** under **Client Credentials**
   - Change to **Public Key/Private Key**
   - Click **Add Key** followed by **Generate New Key**
   - Under **Private Key**, switch to the **PEM** tab
   - **Copy the content** to a local file named `private.pem`

## Step 2: Setting Up Deploy Key for Source Code Repository

Before deploying, you need to prepare an SSH key to be used as the deploy key for accessing the source code repository.

1. **Generate an SSH key**:
   ```bash
   ssh-keygen -t ed25519 -C "user@example.com" -f /tmp/kubiya_deploy_key -N ""
   ```

2. **Print the public key** to add as a deploy key in your Git repository provider:
   ```bash
   cat /tmp/kubiya_deploy_key.pub
   ```

### Configuring Deploy Key on GitHub and GitLab

- **GitHub**:
  - **Navigate to Your Repository Settings**:
    - Go to your repository on GitHub.
    - Click on **Settings** > **Deploy keys**.
  - **Add the Deploy Key**:
    - Click on **Add deploy key**.
    - Provide a title (e.g., _Kubiya Deploy Key_).
    - Paste the contents of your public key.
    - Save.

- **GitLab**:
  - **Navigate to Your Repository Settings**:
    - Go to your repository on GitLab.
    - Click on **Settings** > **Repository** > **Deploy keys**.
  - **Add the Deploy Key**:
    - Click on **Expand** next to the **Deploy Keys** section.
    - Provide a title (e.g., _Kubiya Deploy Key_).
    - Paste the contents of your public key.
    - Save.

## Step 3: Deploying the Enforcer

### 1. Set Environment Variables

Set all required environment variables in your terminal:

```bash
# Set your OKTA credentials
export OKTA_ORG_URL="your-okta-domain.okta.com"
export OKTA_CLIENT_ID="your-client-id"
export OKTA_PRIVATE_KEY_PATH="/path/to/your/private.pem"

# Set your Git repository details
export OPAL_POLICY_REPO_URL="git@github.com:your-org/your-policy-repo.git"
export OPAL_POLICY_REPO_MAIN_BRANCH="main"

# Set the content of your deploy key
export GIT_DEPLOY_KEY=$(cat /tmp/kubiya_deploy_key)

# Base64 encode the values
export OKTA_TOKEN_ENDPOINT_B64=$(echo -n "https://${OKTA_ORG_URL}/oauth2/v1/token" | base64 | tr -d '\n')
export OKTA_BASE_URL_B64=$(echo -n "https://${OKTA_ORG_URL}" | base64 | tr -d '\n')
export OKTA_CLIENT_ID_B64=$(echo -n "${OKTA_CLIENT_ID}" | base64 | tr -d '\n')
export PRIVATE_KEY_B64=$(cat "${OKTA_PRIVATE_KEY_PATH}" | base64 | tr -d '\n')
export OPAL_POLICY_REPO_URL_B64=$(echo -n "${OPAL_POLICY_REPO_URL}" | base64 | tr -d '\n')
export OPAL_POLICY_REPO_MAIN_BRANCH_B64=$(echo -n "${OPAL_POLICY_REPO_MAIN_BRANCH}" | base64 | tr -d '\n')
export GIT_DEPLOY_KEY_B64=$(echo -n "${GIT_DEPLOY_KEY}" | base64 | tr -d '\n')
```

### 2. Deploy the Stack

Apply the Kubernetes manifest to deploy the Kubiya Enforcer stack:

```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: kubiya
---
apiVersion: v1
kind: Secret
metadata:
  name: opawatchdog-secrets
  namespace: kubiya
type: Opaque
data:
  POSTGRES_DB: cG9zdGdyZXM=
  POSTGRES_USER: cG9zdGdyZXM=
  POSTGRES_PASSWORD: cG9zdGdyZXM=
  GIT_DEPLOY_KEY: ${GIT_DEPLOY_KEY_B64}
  OPAL_POLICY_REPO_URL: ${OPAL_POLICY_REPO_URL_B64}
  OPAL_POLICY_REPO_MAIN_BRANCH: ${OPAL_POLICY_REPO_MAIN_BRANCH_B64}
  OKTA_BASE_URL: ${OKTA_BASE_URL_B64}
  OKTA_TOKEN_ENDPOINT: ${OKTA_TOKEN_ENDPOINT_B64}
  OKTA_CLIENT_ID: ${OKTA_CLIENT_ID_B64}
  private.pem: ${PRIVATE_KEY_B64}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: enforcer
  namespace: kubiya
spec:
  replicas: 1
  selector:
    matchLabels:
      app: enforcer
  template:
    metadata:
      labels:
        app: enforcer
    spec:
      volumes:
        - name: private-key-volume
          secret:
            secretName: opawatchdog-secrets
            items:
              - key: private.pem
                path: private.pem
      containers:
        - name: postgres
          image: postgres:alpine
          env:
            - name: POSTGRES_DB
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: POSTGRES_DB
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: POSTGRES_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: POSTGRES_PASSWORD
          ports:
            - containerPort: 5432
          volumeMounts:
            - name: private-key-volume
              mountPath: /etc/ssl/private

        - name: opal-server
          image: permitio/opal-server:latest
          env:
            - name: OPAL_BROADCAST_URI
              value: "postgres://postgres:postgres@localhost:5432/postgres"
            - name: OPAL_SERVER_TOKEN
              value: "your-opal-server-token"
            - name: OPAL_POLICY_REPO_SSH_KEY
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: GIT_DEPLOY_KEY
            - name: OPAL_POLICY_REPO_URL
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: OPAL_POLICY_REPO_URL
            - name: OPAL_POLICY_REPO_MAIN_BRANCH
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: OPAL_POLICY_REPO_MAIN_BRANCH
          ports:
            - containerPort: 7002

        - name: opal-client
          image: permitio/opal-client:latest
          env:
            - name: OPAL_SERVER_URL
              value: "http://opal-server:7002"
          ports:
            - containerPort: 7000
            - containerPort: 8181

        - name: enforcer
          image: ghcr.io/kubiyabot/opawatchdog:latest
          env:
            - name: OKTA_BASE_URL
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: OKTA_BASE_URL
            - name: OKTA_TOKEN_ENDPOINT
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: OKTA_TOKEN_ENDPOINT
            - name: OKTA_CLIENT_ID
              valueFrom:
                secretKeyRef:
                  name: opawatchdog-secrets
                  key: OKTA_CLIENT_ID
            - name: OKTA_PRIVATE_KEY_PATH
              value: "/etc/ssl/private/private.pem"
          ports:
            - containerPort: 5001
          volumeMounts:
            - name: private-key-volume
              mountPath: /etc/ssl/private
EOF
```

### 3. Verify Deployment

Run the following commands to verify that the deployment was successful:

```bash
# Check if pods are running
kubectl get pods -n kubiya

# Check if services are created
kubectl get svc -n kubiya

# Check secrets (without revealing values)
kubectl get secrets -n kubiya
```

### 4. Patch Tool-Manager Deployment

To allow the Tool Manager to communicate with the Enforcer, patch its deployment:

```bash
kubectl patch deployment tool-manager -n kubiya --type=json -p='[
  {
    "op": "add",
    "path": "/spec/template/spec/containers/0/env/-",
    "value": {
      "name": "KUBIYA_AUTH_SERVER_URL",
      "value": "http://enforcer.kubiya:5001"
    }
  }
]'
```

### Updating the Enforcer Configuration

Ensure that the `OPAL_POLICY_REPO_URL` and `OPAL_POLICY_REPO_MAIN_BRANCH` environment variables are correctly set to point to your policy repository.

```bash
export OPAL_POLICY_REPO_URL="git@github.com:your-org/your-policy-repo.git"
export OPAL_POLICY_REPO_MAIN_BRANCH="main"
```

## Step 4: Clean Up Environment Variables (Optional)

For security reasons, it's recommended to unset environment variables containing sensitive information:

```bash
unset OKTA_ORG_URL
unset OKTA_CLIENT_ID
unset OKTA_PRIVATE_KEY_PATH
unset OPAL_POLICY_REPO_URL
unset OPAL_POLICY_REPO_MAIN_BRANCH
unset GIT_DEPLOY_KEY
unset OKTA_TOKEN_ENDPOINT_B64
unset OKTA_BASE_URL_B64
unset OKTA_CLIENT_ID_B64
unset PRIVATE_KEY_B64
unset OPAL_POLICY_REPO_URL_B64
unset OPAL_POLICY_REPO_MAIN_BRANCH_B64
unset GIT_DEPLOY_KEY_B64
```

## Troubleshooting

If you encounter issues during deployment or operation:

- **Check pod logs**:
  ```bash
  kubectl logs <pod-name> -n kubiya
  ```
- **Check pod status**:
  ```bash
  kubectl describe pod <pod-name> -n kubiya
  ```
- **Verify secrets are correctly created**:
  ```bash
  kubectl describe secret opawatchdog-secrets -n kubiya
  ```

## Security Notes

- **Keep all environment variables secure**:
  - Do not expose or commit them to version control.
  - Use a secure method for managing environment variables in production.

- **Regularly rotate credentials**:
  - Follow best practices for key rotation and management.

- **Store private keys securely**:
  - Ensure that private keys are stored in secure, access-controlled locations.

- **Principle of Least Privilege**:
  - Assign the minimal set of permissions required for services and users to function.
  