# Okta Tools for Kubiya SDK

This package provides a set of tools designed to assist with Okta user and group management tasks. It enables automated user access management through Okta's identity platform.

## Prerequisites

Before using these tools, ensure you have:
1. An Okta account with administrative access
2. API Token from Okta
3. Your Okta organization URL

## Environment Variables

The following environment variables must be set:
- `OKTA_API_TOKEN`: Your Okta API token
- `OKTA_ORG_URL`: Your Okta organization URL (e.g., "https://your-org.okta.com" or just "your-org")

## Installation

```bash
pip install requests
```

## Available Actions

### User Management

#### 1. Get User Information
Get detailed information about a specific user.

**Tool Name:** `get_user`

**Parameters:**
- `identifier` (required): User ID or email address
- `fields` (optional): Comma-separated list of fields to return (e.g., 'profile,status,lastLogin')

#### 2. Search Users
Search for users using advanced query options.

**Tool Name:** `search_users`

**Parameters:**
- `query` (optional): SCIM filter (e.g., 'profile.firstName eq "John"')
- `filter` (optional): Okta filter expression (e.g., 'status eq "ACTIVE"')
- `search` (optional): Free-form text search
- `limit` (optional): Maximum number of results (1-200)
- `after` (optional): Pagination cursor

#### 3. List Users
List all users in the Okta organization.

**Tool Name:** `list_users`

**Parameters:**
- `limit` (optional): Maximum number of results per page (1-200)
- `after` (optional): Pagination cursor

### Group Management

#### 1. List Groups
List all groups with optional filtering.

**Tool Name:** `list_groups`

**Parameters:**
- `query` (optional): Search query to filter groups
- `filter` (optional): Filter expression for groups
- `after` (optional): Pagination cursor
- `limit` (optional): Number of results (max 200)

#### 2. Create Group
Create a new Okta group.

**Tool Name:** `create_group`

**Parameters:**
- `name` (required): Name of the group
- `description` (optional): Description of the group
- `skip_naming_conflict_resolution` (optional): Skip name conflict checking

#### 3. Update Group
Update an existing Okta group.

**Tool Name:** `update_group`

**Parameters:**
- `group_id` (required): ID of the group to update
- `name` (required): New name for the group
- `description` (optional): New description for the group

#### 4. Delete Group
Delete an Okta group.

**Tool Name:** `delete_group`

**Parameters:**
- `group_id` (required): ID of the group to delete

#### 5. Get Group Info
Get information about a specific group.

**Tool Name:** `get_group`

**Parameters:**
- `group_id` (required): ID of the group

### Group Membership Management

#### 1. List Group Members
List all members of a group.

**Tool Name:** `list_members`

**Parameters:**
- `group_id` (required): ID of the group
- `after` (optional): Pagination cursor
- `limit` (optional): Number of members to return (max 200)

#### 2. Add Member to Group
Add a user to a group.

**Tool Name:** `add_member`

**Parameters:**
- `group_name` (required): Name of the group to add the user to
- `user_id` (required): ID or login of the user to add

#### 3. Remove Member from Group
Remove a user from a group.

**Tool Name:** `remove_member`

**Parameters:**
- `group_name` (required): Name of the group to remove the user from
- `user_id` (required): ID or login of the user to remove

## Usage Examples

### User Operations
```python
# Get user information
user_info = okta_get_user.execute(
    identifier="user@example.com",
    fields="profile,status,lastLogin"
)

# Search for users
users = okta_search_users.execute(
    query='profile.department eq "Engineering"',
    filter='status eq "ACTIVE"',
    limit=50
)

# List all users
all_users = okta_list_users.execute(limit=100)
```

### Group Operations
```python
# Create a new group
new_group = okta_create_group.execute(
    name="DevOps Team",
    description="DevOps Engineering Team"
)

# Add user to group
result = okta_add_member.execute(
    group_name="DevOps Team",
    user_id="user@example.com"
)
```

## SCIM Filter Examples

Here are some examples of SCIM filters for user searching:

```python
# Find users by first name
query = 'profile.firstName eq "John"'

# Find users by email domain
query = 'profile.email co "@example.com"'

# Complex query
query = 'profile.department eq "Engineering" and profile.employeeType eq "Full-time"'
```

## Response Format

All tools return a JSON response with the following structure:

```json
{
    "success": true|false,
    "message": "Success/error message",
    "error": "Error details (if success is false)",
    "data": {} // Response data if applicable
}
```

## Error Handling

The tools handle various error scenarios including:
- Invalid credentials
- Resource not found
- Permission issues
- Rate limiting
- Network connectivity issues

## Logging

The tools provide detailed logging for troubleshooting:
- INFO level: Normal operation logs
- ERROR level: Error details
- DEBUG level: API interaction details

## Best Practices

1. Always handle pagination for large result sets
2. Use specific fields selection when possible to improve performance
3. Implement proper error handling
4. Use SCIM filters for precise user searching
5. Keep API tokens secure and rotate regularly

## Security Considerations

1. Store API tokens securely
2. Use the principle of least privilege
3. Implement audit logging
4. Monitor API usage
5. Regular security review

## Support

For issues and feature requests:
1. Check error logs
2. Verify environment variables
3. Ensure proper permissions
4. Contact Okta support for API issues