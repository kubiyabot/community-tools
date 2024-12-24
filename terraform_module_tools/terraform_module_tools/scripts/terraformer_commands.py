#!/usr/bin/env python3
"""Helper script for terraformer commands."""

import os
import sys
import json
import subprocess
from typing import Dict, Any, List

def validate_env_vars(provider: str) -> bool:
    """Validate required environment variables are set."""
    required_vars = {
        'aws': ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION'],
        'gcp': ['GOOGLE_CREDENTIALS', 'GOOGLE_PROJECT'],
        'azure': ['AZURE_SUBSCRIPTION_ID', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET', 'AZURE_TENANT_ID']
    }
    
    if provider not in required_vars:
        print(f"Unsupported provider: {provider}")
        return False
        
    missing = [var for var in required_vars[provider] if not os.getenv(var)]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        return False
    
    return True

def run_terraformer_command(command: str, provider: str, args: List[str]) -> Dict[str, Any]:
    """Run terraformer command with proper arguments."""
    if not validate_env_vars(provider):
        return {'success': False, 'error': 'Environment validation failed'}

    try:
        cmd = ['terraformer', command, provider] + args
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
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
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: terraformer_commands.py <command> <provider> [args...]")
        sys.exit(1)
        
    command = sys.argv[1]
    provider = sys.argv[2]
    args = sys.argv[3:]
    
    result = run_terraformer_command(command, provider, args)
    print(json.dumps(result))
    sys.exit(0 if result['success'] else 1) 