# Contributing to Kubiya Community Tools

Thank you for your interest in contributing to Kubiya Community Tools! This document provides guidelines and instructions for contributing to this Python-based tools repository.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Guidelines](#development-guidelines)
- [Tool Development](#tool-development)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Community](#community)

## Code of Conduct

This project adheres to the Contributor Covenant [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

1. **Fork the Repository**: Click the "Fork" button at the top right of the repository page.

2. **Clone Your Fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/community-tools.git
   cd community-tools
   ```

3. **Add Upstream Remote**:
   ```bash
   git remote add upstream https://github.com/kubiyabot/community-tools.git
   ```

4. **Create a Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue using the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md). Include:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS, etc.)
- Relevant logs or screenshots

### Suggesting Enhancements

Feature requests are welcome! Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md) and include:

- Clear description of the proposed feature
- Use cases and benefits
- Potential implementation approach
- Any alternatives you've considered

### Contributing Code

1. Check existing issues and pull requests to avoid duplicates
2. Discuss major changes by opening an issue first
3. Follow the development guidelines below
4. Write tests for your changes
5. Update documentation as needed
6. Submit a pull request

## Development Guidelines

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and modular
- Use type hints where appropriate

### Code Quality

- Write clean, readable, and maintainable code
- Add comments for complex logic
- Use logging instead of print statements
- Handle errors gracefully with appropriate exception handling
- Avoid hardcoding values; use environment variables or configuration

### Docker Images

When creating tools:

1. **Check for Existing Images**: Before creating a custom Docker image, check if an existing base image can be used (e.g., official AWS CLI, kubectl, Python images)

2. **Image Selection Criteria**:
   - Use official images when available
   - Prefer minimal images (alpine variants)
   - Keep images up-to-date and secure
   - Document image dependencies

3. **Custom Images**:
   - Create a Dockerfile in your tool directory
   - Use multi-stage builds when appropriate
   - Minimize image layers
   - Document build process

## Tool Development

### Tool Structure

Each tool should follow this structure:

```
tool-name/
├── tool.yaml              # Tool definition (required)
├── main.py                # Main execution script (if using Python)
├── requirements.txt       # Python dependencies (if applicable)
├── Dockerfile            # Custom image (if needed)
└── README.md             # Tool documentation
```

### Tool Definition (YAML)

Your `tool.yaml` should include:

```yaml
name: tool-name
description: Clear description of what the tool does
image: docker-image:tag
args:
  - name: arg_name
    description: Argument description
    required: true/false
secrets:
  - SECRET_NAME
env:
  - ENV_VAR_NAME
long_running: false
```

### Python SDK Development

If using the Kubiya Python SDK:

```python
from kubiya_sdk.tools import Tool, Arg

tool = Tool(
    name="tool_name",
    description="Tool description",
    image="docker-image:tag",
    args=[
        Arg(name="arg_name", description="Arg description", required=True)
    ],
    secrets=["SECRET_NAME"],
    env=["ENV_VAR"]
)
```

### Best Practices

1. **Stateless Design**: Tools should be stateless and not rely on persistent storage
2. **Error Handling**: Implement comprehensive error handling
3. **Logging**: Use structured logging for debugging
4. **Security**: Never hardcode secrets or credentials
5. **Documentation**: Provide clear documentation and examples
6. **Dependencies**: Minimize external dependencies
7. **Performance**: Optimize for execution speed
8. **Idempotency**: Tools should be idempotent when possible

## Testing

### Local Testing

1. **Set Up Environment**:
   ```bash
   export SECRET_NAME="your-secret"
   export ENV_VAR="value"
   ```

2. **Test Execution**:
   ```bash
   python main.py --arg_name "value"
   ```

3. **Docker Testing**:
   ```bash
   docker build -t test-tool .
   docker run -e SECRET_NAME="secret" test-tool
   ```

### Testing via Kubiya

1. Push your branch to your fork
2. Add your fork as a source in Kubiya
3. Connect the source to a Teammate
4. Test the tool through Slack/Teams integration

### Test Script

Use the provided test script:

```bash
./setup_and_run_tests.sh
```

## Pull Request Process

1. **Update Documentation**: Ensure README and other docs reflect your changes

2. **Update CHANGELOG**: Add an entry to [CHANGELOG.md](CHANGELOG.md) under "Unreleased"

3. **Commit Messages**: Use clear, descriptive commit messages
   - Format: `type(scope): description`
   - Types: feat, fix, docs, style, refactor, test, chore
   - Example: `feat(aws): add S3 bucket listing tool`

4. **Pull Request Template**: Fill out the [PR template](.github/PULL_REQUEST_TEMPLATE.md) completely

5. **Review Process**:
   - Maintainers will review your PR
   - Address feedback and update your PR
   - Once approved, maintainers will merge

6. **PR Requirements**:
   - All tests must pass
   - Code follows style guidelines
   - Documentation is updated
   - No merge conflicts
   - At least one maintainer approval

## Community

### Getting Help

- Open an issue for questions
- Check existing issues and documentation
- Reach out to maintainers

### Recognition

Contributors will be recognized in:
- Repository contributors list
- Release notes for significant contributions
- Community acknowledgments

### License

By contributing, you agree that your contributions will be licensed under the project's [3-Clause BSD License](LICENSE).

## Additional Resources

- [Kubiya Documentation](https://docs.kubiya.ai)
- [Python Best Practices](https://docs.python-guide.org/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Git Commit Message Guidelines](https://www.conventionalcommits.org/)

Thank you for contributing to Kubiya Community Tools!
