# Kubiya Enforcer Stack Deployment Guide

## Basic Steps

1. **Verify that `kubectl` is installed and configured**
2. **Deploy a runner from the Kubiya App Portal**
3. **Connect to your Kubernetes cluster where the Kubiya Runner is installed**

## Overview Diagram

To understand how the Kubiya Enforcer integrates within your infrastructure, refer to the following diagram:

```mermaid
flowchart LR
    subgraph User Infrastructure
        A[User Requests Access]
        B[Kubiya Runner]
        C[Enforcer Service]
        D[Okta Identity Platform]
    end

    subgraph Kubiya Cloud
        E[Kubiya App Portal]
    end

    A --> B
    B --> C
    C --> D
    D --> C
    C --> B
    B --> A
    B --> E
```

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

## Diagram: Enforcer Workflow

Here's a detailed diagram illustrating how the Kubiya Enforcer works within the Just-In-Time Access workflow:

```mermaid
sequenceDiagram
    participant User
    participant KubiyaRunner as Kubiya Runner
    participant Enforcer
    participant Okta
    participant Resource

    Note over User,Resource: Just-In-Time Access Flow with Enforcer

    User->>KubiyaRunner: Request Access (e.g., "Create EC2 in eu-west-1")
    KubiyaRunner->>Enforcer: Validate Access Request
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
  