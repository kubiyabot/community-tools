from .tools.terraform_operations import (
    terraform_init,
    terraform_plan,
    terraform_apply,
    terraform_destroy,
    terraform_output,
    terraform_show,
    terraform_validate,
    terraform_workspace_list,
    terraform_workspace_select,
    terraform_state_list,
    terraform_state_show
)

__all__ = [
    'init',
    'plan',
    'apply',
    'destroy',
    'output',
    'show',
    'validate',
    'workspace_list',
    'workspace_select',
    'state_list',
    'state_show'
]

# Create a dictionary mapping the short names to the full tool names
tools_dict = {
    name.replace('terraform_', ''): globals()[name]
    for name in globals()
    if name.startswith('terraform_')
}

# Update the global namespace with the short names
globals().update(tools_dict)