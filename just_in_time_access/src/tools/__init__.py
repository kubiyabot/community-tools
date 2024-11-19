from .base import JustInTimeAccessTool

def __getattr__(name):
    if name == 'approve_access_tool':
        from .approve_access import approve_access_tool
        return approve_access_tool
    elif name == 'request_access_tool':
        from .request_access import request_access_tool
        return request_access_tool
    elif name == 'describe_access_request_tool':
        from .describe_access_request import describe_access_request_tool
        return describe_access_request_tool
    elif name == 'list_active_access_requests_tool':
        from .list_active_access_requests import list_active_access_requests_tool
        return list_active_access_requests_tool
    elif name == 'view_user_requests_tool':
        from .view_user_requests import view_user_requests_tool
        return view_user_requests_tool
    elif name == 'search_access_requests_tool':
        from .search_access_requests import search_access_requests_tool
        return search_access_requests_tool
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'JustInTimeAccessTool',
    'approve_access_tool',
    'request_access_tool',
    'describe_access_request_tool',
    'list_active_access_requests_tool',
    'view_user_requests_tool',
    'search_access_requests_tool',
]
