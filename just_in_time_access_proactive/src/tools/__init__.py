from .base import JustInTimeAccessTool


def __getattr__(name):
    if name == "list_active_access_requests_tool":
        from .list_active_access_requests import list_active_access_requests_tool

        return list_active_access_requests_tool
    elif name == "view_user_requests_tool":
        from .view_user_requests import view_user_requests_tool

        return view_user_requests_tool
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "JustInTimeAccessTool",
    "list_active_access_requests_tool",
    "view_user_requests_tool",
]
