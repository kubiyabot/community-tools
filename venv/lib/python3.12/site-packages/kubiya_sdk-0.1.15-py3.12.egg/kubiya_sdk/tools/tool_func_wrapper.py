import re
import inspect
from typing import Callable
from functools import wraps

from kubiya_sdk.tools.models import Arg, Tool, FileSpec
from kubiya_sdk.tools.registry import tool_registry


def _get_on_build(requirements: list[str]) -> str:
    req_str = " ".join(requirements)
    return f"""
apt-get update && apt-get install -y curl > /dev/null 2>&1

curl -LsSf https://astral.sh/uv/0.4.27/install.sh | sh > /dev/null 2>&1

export PATH="/root/.cargo/bin/:$PATH"

uv venv > /dev/null 2>&1

. .venv/bin/activate > /dev/null 2>&1

uv pip install {req_str} > /dev/null 2>&1
"""


def _get_content(args: list[Arg], requirements: list[str]) -> str:
    arg_names = [arg.name for arg in args]
    arg_str = " ".join([f'"{{{{ .{arg} }}}}"' for arg in arg_names])
    return f"""
. .venv/bin/activate > /dev/null 2>&1

python /tmp/main.py {arg_str}
"""


def _get_main(func_name: str, func_source: str) -> str:
    function_regex = rf"^(@function_tool.*)(def {func_name}\(.*$)"
    match = re.match(function_regex, func_source, re.DOTALL)
    if match is None:
        raise ValueError("Function regex found no match")

    only_func_source = match.group(2)
    return f"""
from typing import Annotated

import typer

app = typer.Typer(rich_markup_mode=None, add_completion=False)

{only_func_source}

app.command()({func_name})

if __name__ == "__main__":
    app()
"""


def _get_arg_def(param: inspect.Parameter) -> str:
    if param.annotation == bool:
        return f"Input param for arg: {param.name}, type: string, Options: true, false"
    elif param.annotation == int:
        return f"Input param for arg: {param.name}, type: int"
    else:
        return f"Input param for arg: {param.name}, type: string"


def function_tool(
    description: str,
    env: list[str] = [],
    name: str | None = None,
    # image: str = "python:3.12-slim-bullseye",
    image: str = "python:3.12-slim",
    secrets: list[str] = [],
    requirements: list[str] = [],
):
    def f(func: Callable):
        func_name = func.__name__
        source_code = inspect.getsource(func)
        sig = inspect.signature(func)
        args = [
            Arg(
                name=param.name,
                # type="str", this does not work for now...
                default=(param.default if param.default != inspect.Parameter.empty else None),
                required=True if param.default == inspect.Parameter.empty else False,
                description=_get_arg_def(param),
            )
            for param in sig.parameters.values()
        ]
        requirements.append("typer==0.12.5")  # Add typer as a requirement
        content = _get_content(args, requirements)
        main_code = _get_main(func_name, source_code)

        tool = Tool(
            name=name or func_name,
            type="docker",
            image=image,
            description=description,
            args=args,
            env=env,
            secrets=secrets,
            content=content,
            on_build=_get_on_build(requirements),
            with_files=[
                FileSpec(
                    destination="/tmp/main.py",
                    content=main_code,
                ),
            ],
        )

        tool_registry.register(tool)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return f
