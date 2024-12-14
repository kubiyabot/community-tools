from setuptools import setup, find_packages

setup(
    name="kubiya-terraform-module-tools",
    version="0.1.0",
    packages=find_packages(),
    package_data={
        'terraform_module_tools': [
            'scripts/configs/*.json',
            'scripts/*.py',
            'scripts/*.sh',
        ],
    },
    include_package_data=True,
    install_requires=[
        "kubiya_sdk>=0.1.0",
        "requests>=2.25.0",
        "jsonschema>=3.2.0",
        "slack_sdk>=3.19.0"
    ],
    python_requires=">=3.8",
) 