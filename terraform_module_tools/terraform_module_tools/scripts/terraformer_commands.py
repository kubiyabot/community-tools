#!/usr/bin/env python3
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from .error_handler import handle_script_error, ScriptError, validate_environment_vars, logger

def run_terraformer_command(command_type: str, provider: str, **kwargs) -> Dict[str, Any]:
    """Run terraformer commands with proper error handling."""
    try:
        if command_type == 'import':
            return _run_import_command(provider, **kwargs)
        elif command_type == 'scan':
            return _run_scan_command(provider, **kwargs)
        else:
            raise ScriptError(f"Unknown command type: {command_type}")
            
    except Exception as e:
        logger.error(f"Failed to run terraformer command: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def _run_import_command(provider: str, resource_type: str, resource_id: str, output_dir: str = 'terraform_imported') -> Dict[str, Any]:
    """Run terraformer import command."""
    try:
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Build command
        cmd = [
            'terraformer',
            'import',
            provider,
            '--resources', resource_type,
            '--filter', resource_id,
            '--path-output', output_dir
        ]
        
        # Execute command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            'success': True,
            'output': result.stdout,
            'command': ' '.join(cmd),
            'output_dir': output_dir
        }
        
    except subprocess.CalledProcessError as e:
        return {
            'success': False,
            'error': e.stderr,
            'command': ' '.join(cmd)
        }

def _run_scan_command(provider: str, resource_types: str = 'all', output_format: str = 'hcl') -> Dict[str, Any]:
    """Run terraformer scan command."""
    try:
        # Build command
        cmd = [
            'terraformer',
            'scan',
            provider,
            '--resources', resource_types,
            '--output', output_format
        ]
        
        # Execute command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            'success': True,
            'output': result.stdout,
            'command': ' '.join(cmd)
        }
        
    except subprocess.CalledProcessError as e:
        return {
            'success': False,
            'error': e.stderr,
            'command': ' '.join(cmd)
        }

__all__ = ['run_terraformer_command'] 