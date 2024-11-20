import os
import sys
import json
import warnings
from typing import Any, Dict

import click
from rich.table import Table
from rich.console import Console

from kubiya_sdk.project_init import CLIProjectInitializer
from kubiya_sdk.utils.logger import sdk_logger, configure_logger
from kubiya_sdk.utils.discovery import discover_workflows_and_tools
from kubiya_sdk.kubiya_cli.bundle import bundle as bundle_func

from .serialization import KubiyaJSONEncoder


def _json_echo(data):
    click.echo(json.dumps(data, cls=KubiyaJSONEncoder, indent=2))


def _get_workflows_and_tools(source) -> Dict[str, Any]:
    """Load workflows and tools from the given source."""
    try:
        return discover_workflows_and_tools(source)
    except Exception as e:
        return {"error": str(e)}


@click.group()
@click.option("--json", is_flag=True, help="Output in JSON format only")
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]),
    help="Set the logging level",
)
@click.pass_context
def cli(ctx, json, log_level):
    """Kubiya SDK Command Line Interface."""
    ctx.ensure_object(dict)
    ctx.obj["JSON_OUTPUT"] = json
    configure_logger(level=log_level, json_mode=json)


@cli.command()
@click.option("--host", default="0.0.0.0", show_default=True, help="Host to bind the server to")
@click.option("--port", default=8000, show_default=True, help="Port to bind the server to")
@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload on code changes")
@click.pass_context
def server(ctx, host, port, reload):
    """Start the Kubiya SDK server."""
    try:
        import uvicorn
        import sentry_sdk

        from kubiya_sdk.server.app import create_app

        with sentry_sdk.start_transaction(op="server", name="Start Kubiya SDK Server"):
            app = create_app()
            if ctx.obj["JSON_OUTPUT"]:
                _json_echo(
                    {
                        "message": f"Starting the Kubiya SDK server on {host}:{port}",
                        "host": host,
                        "port": port,
                    }
                )
            else:
                sdk_logger.log(
                    f"Starting the Kubiya SDK server on {host}:{port}...",
                    component="Server",
                )
            uvicorn.run(app, host=host, port=port, reload=reload)
    except ImportError:
        warnings.warn("You need to install fastapi addon to use server command... try pip install kubiya-sdk[server]")
    except Exception as e:
        error_message = f"Error starting the server: {str(e)}"
        if ctx.obj["JSON_OUTPUT"]:
            _json_echo({"error": error_message})
        else:
            sdk_logger.log(error_message, component="Server", level="ERROR")
        sentry_sdk.capture_exception(e)
        sys.exit(1)


@cli.command()
@click.option(
    "--source",
    required=True,
    type=click.Path(exists=True),
    help="Source to discover workflows and tools from",
)
@click.pass_context
def discover(ctx, source: str):
    """Discover workflows and tools from the given source."""
    results = _get_workflows_and_tools(source)
    if ctx.obj["JSON_OUTPUT"]:
        _json_echo(results)
    else:
        sdk_logger.log("Discovering workflows and tools...", component="Discovery")
        click.echo(json.dumps(results, cls=KubiyaJSONEncoder, indent=2))


@cli.command()
@click.option(
    "--source",
    required=True,
    type=click.Path(exists=True),
    help="Path to the project directory or source",
)
@click.option("--name", required=True, help="Name of the workflow or tool to describe")
@click.pass_context
def describe(ctx, source: str, name: str):
    """Describe a workflow or tool."""
    results = _get_workflows_and_tools(source)
    workflow = next((w for w in results["workflows"] if w["name"] == name), None)
    tool = next((t for t in results["tools"] if t.name == name), None)

    try:
        if workflow:
            if not ctx.obj["JSON_OUTPUT"]:
                click.echo(f"📋 Describing workflow '{name}'...")
            description = {
                "type": "workflow",
                "name": workflow["name"],
                "description": workflow["instance"].description,
                "steps": [
                    {
                        "name": step_name,
                        "description": step.description,
                        "icon": step.icon,
                        "label": step.label,
                        "next_steps": step.next_steps,
                        "conditions": step.conditions,
                    }
                    for step_name, step in workflow["instance"].steps.items()
                ],
                "entry_point": workflow["instance"].entry_point,
            }
        elif tool:
            if not ctx.obj["JSON_OUTPUT"]:
                click.echo(f"🔧 Describing tool '{name}'...")
            description = {
                "type": "tool",
                "name": tool.name,
                "description": tool.description,
                "args": [arg.dict() for arg in tool.args],
                "env": tool.env,
            }
        else:
            error_message = f"Workflow or tool '{name}' not found in the source"
            if ctx.obj["JSON_OUTPUT"]:
                _json_echo({"error": error_message})
            else:
                sdk_logger.log(error_message, component="Describe", level="ERROR")
            sys.exit(1)

        _json_echo(description)
    except Exception as e:
        error_message = f"Error describing '{name}': {str(e)}"
        if ctx.obj["JSON_OUTPUT"]:
            _json_echo({"error": error_message})
        else:
            sdk_logger.log(error_message, component="Describe", level="ERROR")
        sys.exit(1)


@cli.command()
@click.option(
    "--source",
    required=True,
    type=click.Path(exists=True),
    help="Path to the project directory or source",
)
@click.option("--workflow", required=True, help="Name of the workflow to visualize")
@click.pass_context
def visualize(ctx, source: str, workflow: str):
    """Visualize a workflow."""
    results = _get_workflows_and_tools(source)
    workflow_obj = next((w for w in results["workflows"] if w["name"] == workflow), None)

    try:
        if not workflow_obj:
            error_message = f"Workflow '{workflow}' not found in the source"
            if ctx.obj["JSON_OUTPUT"]:
                _json_echo({"error": error_message})
            else:
                sdk_logger.log(error_message, component="Visualize", level="ERROR")
            sys.exit(1)
        if not ctx.obj["JSON_OUTPUT"]:
            click.echo(f"🎨 Visualizing workflow '{workflow}'...")
        mermaid_diagram = workflow_obj["instance"].to_mermaid()
        if ctx.obj["JSON_OUTPUT"]:
            _json_echo({"mermaid": mermaid_diagram})
        else:
            click.echo(mermaid_diagram)
    except Exception as e:
        error_message = f"Error visualizing workflow '{workflow}': {str(e)}"
        if ctx.obj["JSON_OUTPUT"]:
            _json_echo({"error": error_message})
        else:
            sdk_logger.log(error_message, component="Visualize", level="ERROR")
        sys.exit(1)


@cli.command()
def init():
    """Initialize a new Kubiya project."""
    CLIProjectInitializer().initialize()


@cli.command()
@click.option("-i", "--ignore-dir", "ignore_dirs", multiple=True, help="Directories to ignore")
def bundle(ignore_dirs: tuple[str]):
    """Bundle Kubiya tools in the project"""
    try:
        current_dir = os.getcwd()
        bundle_obj = bundle_func(
            current_dir,
            ignore_dirs=ignore_dirs,
            save_to_file=True,
        )

        console = Console()

        # Print a pretty bundle summary
        console.rule("[bold blue]Bundle Summary[/bold blue]")

        console.print(f"[bold]Python Version:[/bold] [bold green]{bundle_obj.python_bundle_version}[/bold green]")
        console.print(f"[bold]Tools Discovered:[/bold] [bold green]{len(bundle_obj.tools)}[/bold green]")

        table = Table(title="Tools Summary", show_header=True, header_style="bold magenta")
        table.add_column("Tool Name", style="bold", width=30)
        table.add_column("Args", justify="center")
        table.add_column("Env Vars", justify="center")
        table.add_column("Secrets", justify="center")
        table.add_column("Files", justify="center")

        for tool in bundle_obj.tools:
            table.add_row(
                tool.name,
                str(len(tool.args)),
                str(len(tool.env)),
                str(len(tool.secrets) if tool.secrets is not None else 0),
                str(len(tool.with_files) if tool.with_files is not None else 0),
            )

        console.print(table)

        if bundle_obj.errors:
            console.print(f"[bold red]Number of Errors: {len(bundle_obj.errors)}[/bold red]")
            for error in bundle_obj.errors:
                console.print(f"[red]Error:[/red] {error.error}")
        else:
            console.print("[bold green]No Errors[/bold green]")

        console.rule("[bold blue]End of Summary[/bold blue]")

    except Exception as e:
        sdk_logger.log(f"Error bundling tools: {str(e)}", component="Bundle", level="ERROR")


if __name__ == "__main__":
    cli()
