# Python Executor Tools for Kubiya

A collection of Kubiya tools for safely executing Python code and Jupyter notebooks in isolated environments. These tools are designed to be secure, reliable, and easy to use with Kubiya's AI-powered automation platform.

## Features

### Security
- ✅ Isolated execution in Docker containers
- ✅ Temporary file cleanup
- ✅ No access to host system
- ✅ Controlled dependency installation

### Reliability
- ✅ Comprehensive error handling
- ✅ Detailed logging
- ✅ Input validation
- ✅ Proper cleanup of resources

### Flexibility
- ✅ Custom pip requirements support
- ✅ Environment variables support
- ✅ Multiple execution modes (Python scripts & Jupyter notebooks)
- ✅ Configurable Jupyter kernels
- ✅ Support for multiple files and directories
- ✅ Complex project structures

## Tools

### 1. Python Script Executor
Executes Python code in an isolated environment with support for multiple files and directories.

Features:
- Execute any Python code
- Install custom dependencies
- Set environment variables
- Create additional files and directories
- Support for complex project structures
- Automatic cleanup
- Detailed execution logs

Example usage through Kubiya:
```python
# Simple execution
result = python_executor.execute(
    code="print('Hello World')"
)

# Advanced execution with project structure
result = python_executor.execute(
    # Main script
    code="""
import yaml
from utils.helper import process_data

with open('config/settings.yaml') as f:
    config = yaml.safe_load(f)

process_data(config)
""",
    # Additional project files
    files="""
utils/helper.py:::def process_data(config):
    print(f"Processing with config: {config}")
config/settings.yaml:::database:
  host: localhost
  port: 5432
""",
    # Create directory structure
    directories="""
data/raw
data/processed
logs
""",
    # Install requirements
    requirements="pyyaml==6.0.1",
    # Set environment variables
    env_vars="DEBUG=true API_KEY=xyz"
)
```

File Format Specifications:
1. Directories:
   - Newline-separated list of directory paths
   - Paths can be nested (e.g., `data/raw`)
   - All directories are created recursively

2. Files:
   - Format: `path:::content`
   - Paths can include directories (e.g., `utils/helper.py`)
   - Content can be any text (code, config, data, etc.)
   - Parent directories are created automatically
   - Multiple files separated by newlines

### 2. Jupyter Notebook Executor
Executes Jupyter notebooks with full kernel support.

Features:
- Execute Jupyter notebooks
- Custom kernel selection
- Dependency management
- Full notebook output
- Automatic cleanup

Example usage through Kubiya:
```python
result = jupyter_executor.execute(
    notebook="{\"cells\": [...]}",  # Notebook JSON content
    requirements="matplotlib numpy",
    kernel_name="python3"
)
```

## Installation

1. Install the package:
```bash
pip install .
```

2. Register the tools:
```python
from python_executor_tools import register_tools

# Register all tools
tools = register_tools()

# Access individual tools if needed
python_executor = tools['python_executor']
jupyter_executor = tools['jupyter_executor']
```

## Error Handling

Both tools implement comprehensive error handling:

1. Input Validation
   - Checks for required inputs
   - Validates input formats
   - Verifies file paths and content

2. File System Operations
   - Handles directory creation failures
   - Manages file creation errors
   - Validates file paths and permissions

3. Execution Environment
   - Handles temporary directory creation/cleanup
   - Manages pip installation errors
   - Captures Python runtime errors

4. Resource Management
   - Ensures proper cleanup
   - Handles permission issues
   - Manages file operations

5. Logging
   - Timestamps for all operations
   - Detailed error messages
   - Operation status updates
   - File and directory operation tracking

## Security Considerations

1. Isolation
   - All code runs in isolated Docker containers
   - No access to host system files
   - Clean environment for each execution

2. Dependencies
   - Controlled pip installation
   - Temporary virtual environments
   - No system-wide package modifications

3. File Operations
   - All files created in temporary directories
   - Automatic cleanup after execution
   - No persistent storage

## Best Practices

1. File Organization
   - Use clear directory structures
   - Follow Python package conventions
   - Keep related files together
   - Use descriptive file names

2. Code Structure
   - Split complex code into multiple files
   - Use proper imports and dependencies
   - Follow Python best practices
   - Document code appropriately

3. Resource Management
   - Clean up resources when done
   - Don't store sensitive data
   - Monitor disk usage
   - Use appropriate file permissions

## Troubleshooting

Common issues and solutions:

1. Installation Failures
   ```
   ERROR: Failed to install requirements
   ```
   - Check package names and versions
   - Ensure requirements are compatible
   - Verify network connectivity

2. Execution Errors
   ```
   ERROR: Script execution failed
   ```
   - Check Python code syntax
   - Verify all required imports
   - Check environment variables

3. Jupyter Kernel Issues
   ```
   ERROR: Failed to install Jupyter kernel
   ```
   - Verify kernel name
   - Check Jupyter dependencies
   - Ensure sufficient permissions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - See LICENSE file for details 